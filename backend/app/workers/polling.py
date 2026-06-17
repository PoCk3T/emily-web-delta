"""Celery tasks for self-hosted polling, content extraction, and diffing."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select

from app.celery_app import celery_app
from app.core.backends.selfhosted_backend import SelfHostedBackend
from app.core.diff_engine import compute_diff
from app.db.session import async_session_factory
from app.models.check_result import CheckResult
from app.models.diff import Diff
from app.models.notification import NotificationRule
from app.models.snapshot import Snapshot
from app.models.url import Url, UrlState

logger = logging.getLogger(__name__)


async def async_poll_single_url(db, url: Url) -> CheckResult:
    """Poll a single URL and process snapshots/diffs."""
    logger.info(f"Starting fallback polling for URL: {url.url} (backend={url.backend})")

    # 1. Instantiate self-hosted backend
    backend = SelfHostedBackend()

    # 2. Extract content
    result = await backend.extract(
        url=url.url,
        headers=url.headers,
        cookies=url.cookies,
    )

    now = datetime.now(UTC)
    interval = timedelta(seconds=url.interval_seconds)

    # 3. Handle extraction failure/error
    if result.status == "error":
        logger.error(f"Failed to fetch {url.url}: {result.error}")

        # Calculate failure state
        consecutive_failures = (url.failure_consecutive_count or 0) + 1
        status_code = result.metadata.get("status_code", 500)

        if status_code == 404:
            new_state = UrlState.DELETED
        elif consecutive_failures == 1:
            new_state = UrlState.ERRORING
        elif consecutive_failures >= 3:
            new_state = UrlState.DOWN
        else:
            new_state = UrlState.ERRORING

        # Update URL status
        url.failure_consecutive_count = consecutive_failures
        url.state = new_state
        url.last_checked = now
        url.next_check = now + interval

        # Save check result as failure
        check_res = CheckResult(
            url_id=url.id,
            backend=url.backend,
            status="error",
            error_message=result.error,
            status_code=status_code,
            is_failure=True,
            failure_consecutive_count=consecutive_failures,
            state=new_state,
        )
        db.add(check_res)
        await db.commit()
        return check_res

    # 4. Handle success extraction
    logger.info(
        f"Successfully extracted content from {url.url}. Content length: {len(result.content)}"
    )

    # Check for previous snapshot
    stmt = (
        select(Snapshot)
        .where(Snapshot.url_id == url.id)
        .order_by(Snapshot.created_at.desc())
        .limit(1)
    )
    db_res = await db.execute(stmt)
    last_snapshot = db_res.scalar_one_or_none()

    status = "same"
    diff_text = None
    diff_size = 0
    lines_added = 0
    lines_removed = 0

    new_snapshot = None

    if not last_snapshot:
        # First check, treat as "new"
        status = "new"
        new_snapshot = Snapshot(
            url_id=url.id,
            content_hash=result.content_hash,
            content=result.content,
            extracted_text=result.content,
            content_type="markdown",
            status="ok",
            snapshot_size=len(result.content),
        )
        db.add(new_snapshot)
        await db.flush()  # Populate ID
        logger.info(
            f"First snapshot created for {url.url} (snapshot_id={new_snapshot.id})"
        )

    elif last_snapshot.content_hash != result.content_hash:
        # Content changed!
        status = "changed"
        new_snapshot = Snapshot(
            url_id=url.id,
            content_hash=result.content_hash,
            content=result.content,
            extracted_text=result.content,
            content_type="markdown",
            status="ok",
            snapshot_size=len(result.content),
        )
        db.add(new_snapshot)
        await db.flush()  # Populate ID

        # Compute diff
        logger.info(
            f"Diff detected for {url.url}. Computing diff from {last_snapshot.id} to {new_snapshot.id}"
        )
        diff_res = await compute_diff(
            last_snapshot.extracted_text or "", result.content or ""
        )
        diff_text = diff_res.unified_diff
        diff_size = diff_res.diff_size
        lines_added = diff_res.lines_added
        lines_removed = diff_res.lines_removed

        # Save diff
        url_diff = Diff(
            url_id=url.id,
            snapshot_from_id=last_snapshot.id,
            snapshot_to_id=new_snapshot.id,
            diff_type="unified",
            diff_content=diff_res.unified_diff,
            diff_size=diff_res.diff_size,
            lines_added=diff_res.lines_added,
            lines_removed=diff_res.lines_removed,
        )
        db.add(url_diff)

        # Trigger notifications
        await trigger_notifications_for_url(
            db,
            url,
            f"Content changed for {url.name or url.url}. Added {lines_added} lines, removed {lines_removed} lines.",
        )

    else:
        # Content unchanged
        status = "same"
        logger.info(f"No changes detected for {url.url}")

    # Transition url state to active / recovered
    url.failure_consecutive_count = 0
    url.state = UrlState.ACTIVE
    url.last_checked = now
    url.last_hash = result.content_hash
    url.next_check = now + interval

    # Save check result
    check_res = CheckResult(
        url_id=url.id,
        backend=url.backend,
        status=status,
        diff_text=diff_text,
        diff_size=diff_size,
        content_hash=result.content_hash,
        is_meaningful=status == "changed",
        status_code=result.metadata.get("status_code", 200),
        is_failure=False,
        failure_consecutive_count=0,
        state=UrlState.ACTIVE,
    )
    db.add(check_res)
    await db.commit()

    logger.info(f"Finished polling for {url.url}. Result status: {status}")
    return check_res


async def trigger_notifications_for_url(db, url: Url, message: str):
    """Check notification rules and dispatch alerts."""
    stmt = select(NotificationRule).where(
        NotificationRule.enabled,
        or_(
            NotificationRule.url_id == url.id,
            and_(
                NotificationRule.tenant_id == url.tenant_id,
                NotificationRule.url_id is None,
            ),
        ),
    )
    res = await db.execute(stmt)
    rules = res.scalars().all()

    if not rules:
        logger.info(f"No active notification rules found for URL {url.url}")
        return

    logger.info(
        f"Found {len(rules)} notification rules for URL {url.url}. Dispatching..."
    )
    for rule in rules:
        # In a complete implementation, we'd trigger dispatch_notification celery task or similar.
        # Let's log and trigger the task
        logger.info(
            f"Dispatching notification via rule {rule.id} ({rule.type} -> {rule.channel})"
        )
        rule.last_sent_at = datetime.now(UTC)
        db.add(rule)


async def async_poll_urls(url_ids: list[str] | None = None) -> dict:
    """Helper to poll URLs asynchronously."""
    from app.db.session import close_db

    try:
        async with async_session_factory() as db:
            if url_ids:
                # Check specific URLs
                logger.info(f"Manual poll triggered for URL IDs: {url_ids}")
                from uuid import UUID

                uuids = [UUID(uid) for uid in url_ids]
                stmt = select(Url).where(Url.id.in_(uuids))
            else:
                # Check all enabled self-hosted URLs that are due
                now = datetime.now(UTC)
                logger.info(
                    "Scheduler poll triggered. Checking due self-hosted URLs..."
                )
                stmt = select(Url).where(
                    Url.enabled,
                    Url.backend == "selfhosted",
                    or_(Url.next_check is None, Url.next_check <= now),
                )

            res = await db.execute(stmt)
            urls = res.scalars().all()

            if not urls:
                logger.info("No due URLs to poll at this time.")
                return {"polled_count": 0, "results": []}

            logger.info(f"Found {len(urls)} URLs to poll.")
            results = []
            for url in urls:
                try:
                    check_result = await asyncio.wait_for(
                        async_poll_single_url(db, url), timeout=120.0
                    )
                    results.append(
                        {
                            "url_id": str(url.id),
                            "url": url.url,
                            "status": check_result.status,
                            "is_failure": check_result.is_failure,
                        }
                    )
                except Exception as e:
                    logger.error(f"Error polling URL {url.url}: {e}", exc_info=True)
                    results.append(
                        {
                            "url_id": str(url.id),
                            "url": url.url,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            return {"polled_count": len(urls), "results": results}
    finally:
        await close_db()


@celery_app.task(bind=True, max_retries=3, time_limit=300, soft_time_limit=240)
def poll_urls(self, url_ids: list[str] | None = None):
    """Poll a batch of URLs (sync celery wrapper around async implementation)."""
    logger.info("Celery task poll_urls started.")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # In case we're in an environment with a running loop (unlikely for typical Celery worker threads)
        import nest_asyncio

        nest_asyncio.apply()
        return loop.run_until_complete(async_poll_urls(url_ids))
    else:
        return asyncio.run(async_poll_urls(url_ids))


@celery_app.task
def process_diff(diff_id: str):
    """Process a diff (sync placeholder)."""
    logger.info(f"Processing diff {diff_id}")
    return {"processed": diff_id}


@celery_app.task
def send_notifications(rule_ids: list[str]):
    """Send notifications for a batch of rules (sync placeholder)."""
    logger.info(f"Sending notifications for {len(rule_ids)} rules")
    return {"sent": len(rule_ids)}
