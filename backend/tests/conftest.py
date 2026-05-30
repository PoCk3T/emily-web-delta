"""Test configuration and fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base


# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def override_get_session():
    """Override get_session to use SQLite instead of PostgreSQL."""
    from app.db.session import get_session

    async def test_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = test_get_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def db_session():
    """Test database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(autouse=True)
async def seed_default_tenant():
    """Create a default tenant for tests."""
    import uuid
    from app.models.tenant import Tenant
    from app.models.user import User

    async with async_session() as session:
        # Create a default tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Tenant",
            is_active=True,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        # Store tenant id in app state so auth can use it
        app.state._test_tenant_id = tenant.id