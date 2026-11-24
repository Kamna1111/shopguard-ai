"""Shared API test setup and isolated customer test identities."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import uuid4

import psycopg
import pytest
from automation.api.clients.shop_api import ShopApiClient

from app.core.config import settings


@dataclass(frozen=True)
class Customer:
    email: str
    password: str
    token: str


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("SHOPGUARD_API_URL", "http://127.0.0.1:8000").rstrip("/")


@pytest.fixture
def api(api_base_url: str) -> Iterator[ShopApiClient]:
    client = ShopApiClient(api_base_url)
    yield client
    client.close()


@pytest.fixture
def customer(api: ShopApiClient) -> Customer:
    email = f"api-test-{uuid4().hex}@example.com"
    password = "api-test-password-123"
    registration = api.post("/auth/register", json={"email": email, "password": password})
    assert registration.status_code == 201, registration.text
    login = api.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return Customer(email=email, password=password, token=login.json()["access_token"])


@pytest.fixture
def read_only_database() -> Iterator[psycopg.Connection]:
    """Open a read-only PostgreSQL connection for persistence checks."""
    database_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    connection = psycopg.connect(database_url)
    try:
        connection.execute("SET TRANSACTION READ ONLY")
        yield connection
    finally:
        connection.close()
