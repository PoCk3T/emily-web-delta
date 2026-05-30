"""Seed admin user and default monitoring URLs.

Populates the first admin user (admin@emily.dev) and six default
monitored URLs (Terms of Service and Privacy Policy for OpenAI,
Google/Gemini, and Anthropic). Idempotent — safe to run multiple times.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-29
"""

from datetime import datetime, timezone
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


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
    # Google / Gemini
    {
        "name": "Google Terms of Service",
        "url": "https://policies.google.com/terms",
        "tags": ["google", "gemini", "tos"],
    },
    {
        "name": "Google Privacy Policy",
        "url": "https://policies.google.com/privacy",
        "tags": ["google", "gemini", "privacy"],
    },
    # Anthropic
    {
        "name": "Anthropic Terms of Service",
        "url": "https://www.anthropic.com/legal/consumer-terms",
        "tags": ["anthropic", "tos"],
    },
    {
        "name": "Anthropic Privacy Policy",
        "url": "https://www.anthropic.com/legal/privacy",
        "tags": ["anthropic", "privacy"],
    },
]


def _hash_password(password: str) -> str:
    """Hash a password using the app's existing hash_password function."""
    import sys
    sys.path.insert(0, "/app")
    from app.core.security import hash_password
    return hash_password(password)


def upgrade() -> None:
    conn = op.get_bind()

    # --- Seed default tenant ---
    tenant_table = sa.table(
        "tenants",
        sa.column("id", PG_UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("plan", sa.String),
        sa.column("max_urls", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(timezone.utc)
    tenant_id = uuid4()

    tenant_row = conn.execute(
        sa.select(tenant_table.c.id).where(tenant_table.c.name == "Emily")
    ).scalar_one_or_none()

    if tenant_row:
        tenant_id = tenant_row
    else:
        conn.execute(
            tenant_table.insert().values(
                id=tenant_id,
                name="Emily",
                plan="free",
                max_urls=10,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

    # --- Seed admin user ---
    user_table = sa.table(
        "users",
        sa.column("id", PG_UUID(as_uuid=True)),
        sa.column("email", sa.String),
        sa.column("name", sa.String),
        sa.column("password_hash", sa.Text),
        sa.column("tenant_id", PG_UUID(as_uuid=True)),
        sa.column("is_active", sa.Boolean),
        sa.column("is_superuser", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_user = conn.execute(
        sa.select(user_table.c.id).where(user_table.c.email == "admin@emily.dev")
    ).scalar_one_or_none()

    if not existing_user:
        conn.execute(
            user_table.insert().values(
                id=uuid4(),
                email="admin@emily.dev",
                name="Admin",
                password_hash=_hash_password("emilyadmin123"),
                tenant_id=tenant_id,
                is_active=True,
                is_superuser=True,
                created_at=now,
                updated_at=now,
            )
        )
        print("Seeded admin user: admin@emily.dev")

    # --- Seed default URLs ---
    url_table = sa.table(
        "urls",
        sa.column("id", PG_UUID(as_uuid=True)),
        sa.column("tenant_id", PG_UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("url", sa.Text),
        sa.column("backend", sa.String),
        sa.column("interval_seconds", sa.Integer),
        sa.column("enabled", sa.Boolean),
        sa.column("tags", sa.JSON),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_urls = conn.execute(
        sa.select(url_table.c.url).where(url_table.c.tenant_id == tenant_id)
    ).scalars().all()
    existing_url_set = set(existing_urls)

    inserted = 0
    for entry in DEFAULT_URLS:
        if entry["url"] in existing_url_set:
            continue
        conn.execute(
            url_table.insert().values(
                id=uuid4(),
                tenant_id=tenant_id,
                name=entry["name"],
                url=entry["url"],
                backend="firecrawl",
                interval_seconds=3600,
                enabled=True,
                tags=entry["tags"],
                created_at=now,
                updated_at=now,
            )
        )
        inserted += 1

    if inserted:
        print(f"Seeded {inserted} default URLs")
    else:
        print("All default URLs already exist")


def downgrade() -> None:
    """Remove seeded data. Safe because the seed is idempotent in upgrade."""
    conn = op.get_bind()

    # Delete URLs seeded by this migration
    url_table = sa.table(
        "urls",
        sa.column("tenant_id", PG_UUID(as_uuid=True)),
        sa.column("url", sa.Text),
    )
    conn.execute(
        url_table.delete().where(
            sa.and_(
                url_table.c.tenant_id == sa.select(
                    sa.table("tenants", sa.column("id", PG_UUID(as_uuid=True))).c.id
                ).where(sa.table("tenants", sa.column("name", sa.String)).c.name == "Emily"),
                url_table.c.url.in_([u["url"] for u in DEFAULT_URLS]),
            )
        )
    )

    # Delete admin user
    user_table = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("tenant_id", PG_UUID(as_uuid=True)),
    )
    conn.execute(
        user_table.delete().where(
            sa.and_(
                user_table.c.email == "admin@emily.dev",
                user_table.c.tenant_id == sa.select(
                    sa.table("tenants", sa.column("id", PG_UUID(as_uuid=True))).c.id
                ).where(sa.table("tenants", sa.column("name", sa.String)).c.name == "Emily"),
            )
        )
    )

    # Delete tenant
    tenant_table = sa.table(
        "tenants",
        sa.column("id", PG_UUID(as_uuid=True)),
        sa.column("name", sa.String),
    )
    conn.execute(
        tenant_table.delete().where(tenant_table.c.name == "Emily")
    )

    print("Downgraded: removed seeded admin user and default URLs")
