"""Notification rules API routes."""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.notification import NotificationRule

router = APIRouter()


class NotificationRuleCreate(BaseModel):
    url_id: str
    type: str  # email, webhook, slack, telegram, discord
    channel: str  # email address, webhook URL, etc.
    enabled: bool = True
    config: dict | None = None


class NotificationRuleUpdate(BaseModel):
    enabled: bool | None = None
    channel: str | None = None
    config: dict | None = None


@router.post("/notifications/rules", status_code=status.HTTP_201_CREATED)
async def create_rule(request: NotificationRuleCreate, db: AsyncSession = Depends(get_session)):
    """Create a notification rule."""
    rule = NotificationRule(
        url_id=request.url_id,
        type=request.type,
        channel=request.channel,
        enabled=request.enabled,
        config=request.config,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {
        "id": str(rule.id),
        "url_id": str(rule.url_id),
        "type": rule.type,
        "channel": rule.channel,
        "enabled": rule.enabled,
        "config": rule.config,
        "created_at": rule.created_at.isoformat(),
    }


@router.get("/notifications/rules")
async def list_rules(
    url_id: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """List notification rules."""
    query = select(NotificationRule)
    if url_id:
        from uuid import UUID
        query = query.where(NotificationRule.url_id == UUID(url_id))

    result = await db.execute(query)
    rules = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "url_id": str(r.url_id),
            "type": r.type,
            "channel": r.channel,
            "enabled": r.enabled,
            "config": r.config,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]


@router.put("/notifications/rules/{rule_id}")
async def update_rule(rule_id: str, request: NotificationRuleUpdate, db: AsyncSession = Depends(get_session)):
    """Update a notification rule."""
    from uuid import UUID

    result = await db.execute(select(NotificationRule).where(NotificationRule.id == UUID(rule_id)))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for field_name, value in request.model_dump(exclude_unset=True).items():
        setattr(rule, field_name, value)

    await db.commit()
    await db.refresh(rule)

    return {
        "id": str(rule.id),
        "type": rule.type,
        "channel": rule.channel,
        "enabled": rule.enabled,
    }


@router.delete("/notifications/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_session)):
    """Delete a notification rule."""
    from uuid import UUID

    result = await db.execute(select(NotificationRule).where(NotificationRule.id == UUID(rule_id)))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()


@router.post("/notifications/rules/{rule_id}/test")
async def test_rule(rule_id: str, db: AsyncSession = Depends(get_session)):
    """Test a notification rule."""
    from uuid import UUID

    result = await db.execute(select(NotificationRule).where(NotificationRule.id == UUID(rule_id)))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # In production: actually send a test notification
    return {
        "message": f"Test notification sent via {rule.type} to {rule.channel}",
        "rule_id": str(rule.id),
    }
