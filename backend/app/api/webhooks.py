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
            _check_id = page.get("checkId")
            _url = page.get("url", "")
            _status = page.get("status", "unknown")
            _is_meaningful = page.get("isMeaningful", False)
            _judgment = page.get("judgment")
            _diff_text = page.get("diff", {}).get("text", "") if isinstance(page.get("diff"), dict) else ""
            _diff_json = page.get("diff", {}).get("json") if isinstance(page.get("diff"), dict) else None
            _snapshot_json = page.get("snapshot", {}).get("json") if isinstance(page.get("snapshot"), dict) else None

            # In production: store to database
            # await store_check_result(_check_id, _url, _status, ...)

    elif event_type == "monitor.check.completed":
        for check in payload.get("data", []):
            _summary = check.get("summary", {})
            # Store summary
            # await store_check_summary(...)

    return {"success": True}
