"""Regression tests for the scheduler's due-URL selection.

These guard against the `is None` vs `.is_(None)` class of bug, where a
Python identity test is accidentally used inside a SQLAlchemy filter. Such an
expression evaluates to the constant False at import time and silently drops
the whole OR branch, which previously meant every newly created URL
(next_check = NULL) was never polled.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import or_, select

from app.models.notification import NotificationRule
from app.models.tenant import Tenant
from app.models.url import Url


def _due_urls_stmt(now):
    """Mirror of the filter used in workers.polling.async_poll_urls."""
    return select(Url).where(
        Url.enabled.is_(True),
        Url.backend == "selfhosted",
        or_(Url.next_check.is_(None), Url.next_check <= now),
    )


def test_null_check_is_not_folded_to_false():
    """`Url.next_check.is_(None)` must compile to SQL, not a Python bool."""
    expr = Url.next_check.is_(None)
    assert not isinstance(expr, bool)
    assert "IS NULL" in str(expr).upper()


def test_identity_test_would_have_been_a_bug():
    """Documents the original defect: `is None` collapses to False."""
    assert (Url.next_check is None) is False


@pytest.mark.asyncio
async def test_due_query_includes_never_checked_urls(db_session):
    """A URL with next_check = NULL must be selected for polling."""
    now = datetime.now(UTC)

    never_checked = Url(
        name="never checked",
        url="https://example.com/never",
        backend="selfhosted",
        enabled=True,
        interval_seconds=7200,
        next_check=None,
    )
    overdue = Url(
        name="overdue",
        url="https://example.com/overdue",
        backend="selfhosted",
        enabled=True,
        interval_seconds=7200,
        next_check=now - timedelta(minutes=5),
    )
    not_yet_due = Url(
        name="future",
        url="https://example.com/future",
        backend="selfhosted",
        enabled=True,
        interval_seconds=7200,
        next_check=now + timedelta(hours=1),
    )
    disabled = Url(
        name="disabled",
        url="https://example.com/disabled",
        backend="selfhosted",
        enabled=False,
        interval_seconds=7200,
        next_check=None,
    )
    wrong_backend = Url(
        name="firecrawl",
        url="https://example.com/firecrawl",
        backend="firecrawl",
        enabled=True,
        interval_seconds=7200,
        next_check=None,
    )

    db_session.add_all(
        [never_checked, overdue, not_yet_due, disabled, wrong_backend]
    )
    await db_session.commit()

    result = await db_session.execute(_due_urls_stmt(now))
    selected = {u.url for u in result.scalars().all()}

    assert "https://example.com/never" in selected, (
        "URLs with a NULL next_check must be polled"
    )
    assert "https://example.com/overdue" in selected
    assert "https://example.com/future" not in selected
    assert "https://example.com/disabled" not in selected
    assert "https://example.com/firecrawl" not in selected


@pytest.mark.asyncio
async def test_tenant_wide_notification_rules_are_matched(db_session):
    """Rules with url_id = NULL apply to every URL in the tenant."""
    from sqlalchemy import and_

    tenant = Tenant(name="Acme", is_active=True)
    db_session.add(tenant)
    await db_session.flush()

    url = Url(
        tenant_id=tenant.id,
        name="page",
        url="https://example.com/page",
        backend="selfhosted",
        enabled=True,
        interval_seconds=7200,
    )
    db_session.add(url)
    await db_session.flush()

    tenant_wide = NotificationRule(
        tenant_id=tenant.id,
        url_id=None,
        type="email",
        channel="alerts@example.com",
        enabled=True,
    )
    db_session.add(tenant_wide)
    await db_session.commit()

    stmt = select(NotificationRule).where(
        NotificationRule.enabled.is_(True),
        or_(
            NotificationRule.url_id == url.id,
            and_(
                NotificationRule.tenant_id == url.tenant_id,
                NotificationRule.url_id.is_(None),
            ),
        ),
    )
    rules = (await db_session.execute(stmt)).scalars().all()
    assert len(rules) == 1
