"""Use only the dedicated test database; never point tests at the shop database."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_DIR.parents[1]
sys.path.insert(0, str(API_DIR))
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg:///shopguard_test")
os.environ["APP_ENV"] = "test"
os.environ["AI_PROVIDER"] = "mock"

from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.domain.models import DiscountCode, Inventory, Product  # noqa: E402
from app.main import app  # noqa: E402

TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client() -> TestClient:
    """Start each test with empty tables in shopguard_test and clean them after."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestSession() as session:
        product = Product(
            sku="TEST-MUG",
            name="Test Mug",
            description="A product used only by automated tests.",
            category="Test Goods",
            price=10,
            inventory=Inventory(quantity=5),
        )
        session.add(product)
        session.add(DiscountCode(code="WELCOME10", percent_off=10))
        session.commit()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture
def database_session() -> Session:
    """Open a direct connection for assertions about saved database records."""
    with TestSession() as session:
        yield session
