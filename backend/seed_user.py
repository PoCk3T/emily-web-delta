"""Seed a first admin user and default monitoring URLs."""

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

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
    {
        "name": "OpenAI Terms of Use",
        "url": "https://openai.com/terms",
        "tags": ["openai", "tos"],
    },
    {
        "name": "OpenAI Privacy Policy",
        "url": "https://openai.com/policies/privacy-policy/",
        "tags": ["openai", "privacy"],
    },
    {
        "name": "OpenAI Business Terms",
        "url": "https://openai.com/policies/business-terms",
        "tags": ["openai", "business", "tos"],
    },
    # Google / Gemini
    {
        "name": "Google Terms of Service",
        "url": "https://policies.google.com/terms",
        "tags": ["google", "gemini", "tos"],
    },
    {
        "name": "Google Cloud Platform Terms of Service",
        "url": "https://cloud.google.com/terms",
        "tags": ["google", "cloud", "business", "tos"],
    },
    {
        "name": "Google Privacy Policy",
        "url": "https://policies.google.com/privacy",
        "tags": ["google", "gemini", "privacy"],
    },
    # Microsoft / Azure
    {
        "name": "Microsoft Services Agreement",
        "url": "https://www.microsoft.com/en-us/servicesagreement",
        "tags": ["microsoft", "tos"],
    },
    {
        "name": "Microsoft Azure Legal Information",
        "url": "https://azure.microsoft.com/en-us/support/legal/subscription-agreement/",
        "tags": ["microsoft", "azure", "business", "tos"],
    },
    # Anthropic
    {
        "name": "Anthropic Terms of Service",
        "url": "https://www.anthropic.com/legal/consumer-terms",
        "tags": ["anthropic", "tos"],
    },
    {
        "name": "Anthropic Commercial Terms of Service",
        "url": "https://www.anthropic.com/legal/commercial-terms",
        "tags": ["anthropic", "business", "tos"],
    },
    {
        "name": "Anthropic Privacy Policy",
        "url": "https://www.anthropic.com/legal/privacy",
        "tags": ["anthropic", "privacy"],
    },
    # Stripe
    {
        "name": "Stripe Privacy Policy",
        "url": "https://stripe.com/privacy",
        "tags": ["stripe", "privacy"],
    },
    # Stripe Pricing - International
    {
        "name": "Stripe Pricing (US)",
        "url": "https://stripe.com/pricing",
        "tags": ["stripe", "pricing", "us"],
    },
    {
        "name": "Stripe Pricing (UK)",
        "url": "https://stripe.com/gb/pricing",
        "tags": ["stripe", "pricing", "gb"],
    },
    {
        "name": "Stripe Pricing (IE)",
        "url": "https://stripe.com/ie/pricing",
        "tags": ["stripe", "pricing", "ie"],
    },
    {
        "name": "Stripe Local Payment Methods (IE)",
        "url": "https://stripe.com/ie/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "ie", "lpm"],
    },
    {
        "name": "Stripe Pricing (DE)",
        "url": "https://stripe.com/de/pricing",
        "tags": ["stripe", "pricing", "de"],
    },
    {
        "name": "Stripe Local Payment Methods (DE)",
        "url": "https://stripe.com/de/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "de", "lpm"],
    },
    {
        "name": "Stripe Pricing (SG)",
        "url": "https://stripe.com/en-sg/pricing",
        "tags": ["stripe", "pricing", "sg"],
    },
    {
        "name": "Stripe Pricing (JP)",
        "url": "https://stripe.com/en-jp/pricing",
        "tags": ["stripe", "pricing", "jp"],
    },
    {
        "name": "Stripe Pricing (BR)",
        "url": "https://stripe.com/en-br/pricing",
        "tags": ["stripe", "pricing", "br"],
    },
    {
        "name": "Stripe Connect Pricing (BR)",
        "url": "https://stripe.com/en-br/connect/pricing",
        "tags": ["stripe", "pricing", "br", "connect"],
    },
    {
        "name": "Stripe Pricing (MX)",
        "url": "https://stripe.com/mx/pricing",
        "tags": ["stripe", "pricing", "mx"],
    },
    {
        "name": "Stripe Pricing (EN-MX)",
        "url": "https://stripe.com/en-mx/pricing",
        "tags": ["stripe", "pricing", "mx", "en"],
    },
    {
        "name": "Stripe Local Payment Methods (MX)",
        "url": "https://stripe.com/mx/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "mx", "lpm"],
    },
    {
        "name": "Stripe Connect Pricing (EN-MX)",
        "url": "https://stripe.com/en-mx/connect/pricing",
        "tags": ["stripe", "pricing", "mx", "connect"],
    },
    {
        "name": "Stripe Pricing (NZ)",
        "url": "https://stripe.com/nz/pricing",
        "tags": ["stripe", "pricing", "nz"],
    },
    {
        "name": "Stripe Pricing (AT)",
        "url": "https://stripe.com/at/pricing",
        "tags": ["stripe", "pricing", "at"],
    },
    {
        "name": "Stripe Pricing (LU)",
        "url": "https://stripe.com/de-lu/pricing",
        "tags": ["stripe", "pricing", "lu"],
    },
    {
        "name": "Stripe Pricing (CH)",
        "url": "https://stripe.com/de-ch/pricing",
        "tags": ["stripe", "pricing", "ch"],
    },
    {
        "name": "Stripe Pricing (AE)",
        "url": "https://stripe.com/ae/pricing",
        "tags": ["stripe", "pricing", "ae"],
    },
    {
        "name": "Stripe Connect Pricing (AE)",
        "url": "https://stripe.com/ae/connect/pricing",
        "tags": ["stripe", "pricing", "ae", "connect"],
    },
    {
        "name": "Stripe Pricing (ES)",
        "url": "https://stripe.com/es/pricing",
        "tags": ["stripe", "pricing", "es"],
    },
]


async def seed_user():
    await init_db()

    async with async_session_factory() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == "emily@lclglaw.com"))
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
                email="emily@lclglaw.com",
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
            print("Password: emilyadmin123")

        # Seed default URLs (always run — idempotent via URL uniqueness)
        # Find the tenant to associate URLs with
        tenant_result = await db.execute(select(Tenant).where(Tenant.name == "Emily"))
        tenant = tenant_result.scalar_one_or_none()
        created_count = 0
        skipped_count = 0
        if not tenant:
            print("No tenant found — skipping URL seeding")
        else:
            existing_urls = await db.execute(
                select(Url).where(Url.tenant_id == tenant.id)
            )
            existing_url_map = {u.url: u for u in existing_urls.scalars().all()}

            # Calculate spacing for staggered initial checks
            # 7200 seconds (2 hours) spread across all DEFAULT_URLS
            stagger_interval = 7200 // len(DEFAULT_URLS)
            now = datetime.now(UTC)

            for idx, entry in enumerate(DEFAULT_URLS):
                next_check_time = now + timedelta(seconds=idx * stagger_interval)

                if entry["url"] in existing_url_map:
                    # Update existing URL's interval and stagger check
                    url = existing_url_map[entry["url"]]
                    url.interval_seconds = 7200
                    url.next_check = next_check_time
                    db.add(url)
                    skipped_count += 1
                    continue

                url = Url(
                    tenant_id=tenant.id,
                    name=entry["name"],
                    url=entry["url"],
                    backend="selfhosted",
                    interval_seconds=7200,
                    enabled=True,
                    tags=entry["tags"],
                    next_check=next_check_time,
                )
                db.add(url)
                created_count += 1

            if created_count:
                await db.commit()
                print(
                    f"\nSeeded {created_count} default URLs ({skipped_count} already existed)"
                )
            else:
                print(
                    f"\nAll {len(DEFAULT_URLS)} default URLs already exist ({skipped_count} skipped)"
                )


if __name__ == "__main__":
    asyncio.run(seed_user())
