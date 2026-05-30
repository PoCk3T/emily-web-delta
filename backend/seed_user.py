"""Seed a first admin user and default monitoring URLs."""
import asyncio
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add app to path
sys.path.insert(0, "/app")

from app.core.security import hash_password
from app.db.session import async_session_factory, init_db
from app.models.tenant import Tenant
from app.models.url import Url
from app.models.user import User

# Default URLs to monitor — Terms of Service & Privacy Policies
DEFAULT_URLS = [
    # OpenAI
    {"name": "OpenAI Terms of Use", "url": "https://openai.com/terms", "tags": ["openai", "tos"]},
    {"name": "OpenAI Privacy Policy", "url": "https://openai.com/policies/privacy-policy/", "tags": ["openai", "privacy"]},

    # Google / Gemini
    {"name": "Google Terms of Service", "url": "https://policies.google.com/terms", "tags": ["google", "gemini", "tos"]},
    {"name": "Google Privacy Policy", "url": "https://policies.google.com/privacy", "tags": ["google", "gemini", "privacy"]},

    # Anthropic
    {"name": "Anthropic Terms of Service", "url": "https://www.anthropic.com/legal/consumer-terms", "tags": ["anthropic", "tos"]},
    {"name": "Anthropic Privacy Policy", "url": "https://www.anthropic.com/legal/privacy", "tags": ["anthropic", "privacy"]},
]


async def seed_user():
    await init_db()

    async with async_session_factory() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == "admin@emily.dev"))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User {existing.email} already exists (id={existing.id})")
        else:
            # Create tenant first
            tenant = Tenant(
                name="Emily",
                is_active=True,
            )
            db.add(tenant)
            await db.flush()

            # Create user
            user = User(
                email="admin@emily.dev",
                name="Admin",
                password_hash=hash_password("emilyadmin123"),
                is_active=True,
                is_superuser=True,
                tenant_id=tenant.id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            print(f"Created user: {user.email}")
            print(f"Tenant: {tenant.name} (id={tenant.id})")
            print(f"User ID: {user.id}")
            print(f"Password: emilyadmin123")

        # Seed default URLs (always run — idempotent via URL uniqueness)
        # Find the tenant to associate URLs with
        tenant_result = await db.execute(select(Tenant).where(Tenant.name == "Emily"))
        tenant = tenant_result.scalar_one_or_none()
        created_count = 0
        skipped_count = 0
        if not tenant:
            print("No tenant found — skipping URL seeding")
        else:
            existing_urls = await db.execute(select(Url).where(Url.tenant_id == tenant.id))
            existing_url_set = {u.url for u in existing_urls.scalars().all()}

            for entry in DEFAULT_URLS:
                if entry["url"] in existing_url_set:
                    skipped_count += 1
                    continue

                url = Url(
                    tenant_id=tenant.id,
                    name=entry["name"],
                    url=entry["url"],
                    backend="firecrawl",
                    interval_seconds=3600,
                    enabled=True,
                    tags=entry["tags"],
                )
                db.add(url)
                created_count += 1

            if created_count:
                await db.commit()
                print(f"\nSeeded {created_count} default URLs ({skipped_count} already existed)")
            else:
                print(f"\nAll {len(DEFAULT_URLS)} default URLs already exist ({skipped_count} skipped)")


if __name__ == "__main__":
    asyncio.run(seed_user())
