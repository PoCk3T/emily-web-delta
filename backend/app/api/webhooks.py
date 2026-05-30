"""Firecrawl webhook handler."""

from typing import Optional

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.post("/webhooks/firecrawl")
async def firecrawl_webhook(request: Request):
    """Receive and process Firecrawl monitor webhooks."""
    payload = await request.json()
    event_type = payload.get("type")

    if event_type == "monitor.page":
        for page in payload.get("data", []):
            # Store check result
            check_id = page.get("checkId")
            url = page.get("url", "")
            status = page.get("status", "unknown")
            is_meaningful = page.get("isMeaningful", False)
            judgment = page.get("judgment")
            diff_text = page.get("diff", {}).get("text", "") if isinstance(page.get("diff"), dict) else ""
            diff_json = page.get("diff", {}).get("json") if isinstance(page.get("diff"), dict) else None
            snapshot_json = page.get("snapshot", {}).get("json") if isinstance(page.get("snapshot"), dict) else None

            # In production: store to database
            # await store_check_result(check_id, url, status, ...)

    elif event_type == "monitor.check.completed":
        for check in payload.get("data", []):
            summary = check.get("summary", {})
            # Store summary
            # await store_check_summary(...)

    return {"success": True}
