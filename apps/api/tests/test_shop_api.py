"""Integration checks for the ShopGuard API using PostgreSQL's test database."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.models import Inventory, Order, User


def register_and_sign_in(client: TestClient, email: str = "buyer@example.com") -> str:
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "safe-demo-pass-123"},
    )
    assert registered.status_code == 201
    logged_in = client.post(
        "/auth/login",
        json={"email": email, "password": "safe-demo-pass-123"},
    )
    assert logged_in.status_code == 200
    return logged_in.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def add_test_mug(client: TestClient, token: str, quantity: int = 2) -> int:
    response = client.post(
        "/cart/items",
        headers=auth(token),
        json={"product_id": 1, "quantity": quantity},
    )
    assert response.status_code == 201
    return response.json()["product_id"]


def test_health_endpoint_checks_postgresql(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_register_login_and_read_account(client: TestClient) -> None:
    token = register_and_sign_in(client)

    response = client.get("/auth/me", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["email"] == "buyer@example.com"
    assert response.json()["role"] == "customer"


def test_duplicate_email_and_short_password_are_rejected(client: TestClient) -> None:
    first = client.post(
        "/auth/register",
        json={"email": "buyer@example.com", "password": "safe-demo-pass-123"},
    )
    duplicate = client.post(
        "/auth/register",
        json={"email": "buyer@example.com", "password": "safe-demo-pass-123"},
    )
    short_password = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "short"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert short_password.status_code == 422


def test_product_search_category_and_stock_filters(client: TestClient) -> None:
    response = client.get(
        "/products", params={"q": "mug", "category": "Test Goods", "in_stock": True}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Mug"
    assert response.json()[0]["available_quantity"] == 5


def test_customer_can_add_to_cart_and_checkout_once(client: TestClient) -> None:
    token = register_and_sign_in(client)
    add_test_mug(client, token)
    cart = client.get("/cart", headers=auth(token))

    assert cart.status_code == 200
    assert cart.json()["subtotal"] == "20.00"

    checkout_request = {
        "shipping_address": "123 Demo Road, Sample Town",
        "coupon_code": "WELCOME10",
        "idempotency_key": "checkout-test-0001",
    }
    first = client.post("/orders", headers=auth(token), json=checkout_request)
    retry = client.post("/orders", headers=auth(token), json=checkout_request)

    assert first.status_code == 201
    assert first.json()["subtotal"] == "20.00"
    assert first.json()["discount_amount"] == "2.00"
    assert first.json()["tax_amount"] == "1.44"
    assert first.json()["total"] == "19.44"
    assert first.json()["payment_reference"].startswith("SIM-")
    assert retry.status_code == 201
    assert retry.json()["id"] == first.json()["id"]
    assert client.get("/cart", headers=auth(token)).json()["items"] == []

    product = client.get("/products/1").json()
    assert product["available_quantity"] == 3


def test_invalid_coupon_does_not_empty_basket_or_reduce_stock(
    client: TestClient, database_session: Session
) -> None:
    token = register_and_sign_in(client)
    add_test_mug(client, token)

    response = client.post(
        "/orders",
        headers=auth(token),
        json={"shipping_address": "123 Demo Road, Sample Town", "coupon_code": "NOT-REAL"},
    )

    assert response.status_code == 400
    assert len(client.get("/cart", headers=auth(token)).json()["items"]) == 1
    assert database_session.scalar(select(Inventory).where(Inventory.product_id == 1)).quantity == 5


def test_checkout_checks_stock_again_before_confirming_order(
    client: TestClient, database_session: Session
) -> None:
    token = register_and_sign_in(client)
    add_test_mug(client, token, quantity=2)
    inventory = database_session.get(Inventory, 1)
    inventory.quantity = 1
    database_session.commit()

    response = client.post(
        "/orders",
        headers=auth(token),
        json={"shipping_address": "123 Demo Road, Sample Town"},
    )

    assert response.status_code == 409
    assert database_session.scalar(select(Order)) is None
    assert database_session.get(Inventory, 1).quantity == 1
    assert len(client.get("/cart", headers=auth(token)).json()["items"]) == 1


def test_cancellation_returns_items_to_stock(client: TestClient, database_session: Session) -> None:
    token = register_and_sign_in(client)
    add_test_mug(client, token)
    placed = client.post(
        "/orders",
        headers=auth(token),
        json={"shipping_address": "123 Demo Road, Sample Town"},
    )
    order_id = placed.json()["id"]

    cancelled = client.post(f"/orders/{order_id}/cancel", headers=auth(token))
    already_cancelled = client.post(f"/orders/{order_id}/cancel", headers=auth(token))

    assert placed.status_code == 201
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert already_cancelled.status_code == 409
    assert database_session.get(Inventory, 1).quantity == 5


def test_customer_cannot_manage_products_but_admin_can(
    client: TestClient, database_session: Session
) -> None:
    customer_token = register_and_sign_in(client)
    denied = client.post(
        "/products",
        headers=auth(customer_token),
        json={
            "sku": "NEW-LAMP",
            "name": "New Lamp",
            "category": "Home",
            "price": "25.00",
            "initial_stock": 4,
        },
    )
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("safe-admin-pass-123"),
        role="admin",
    )
    database_session.add(admin)
    database_session.commit()
    logged_in = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "safe-admin-pass-123"},
    )
    allowed = client.post(
        "/products",
        headers=auth(logged_in.json()["access_token"]),
        json={
            "sku": "NEW-LAMP",
            "name": "New Lamp",
            "category": "Home",
            "price": "25.00",
            "initial_stock": 4,
        },
    )

    assert denied.status_code == 403
    assert allowed.status_code == 201
    assert allowed.json()["available_quantity"] == 4


def test_order_history_only_shows_signed_in_users_orders(client: TestClient) -> None:
    first_token = register_and_sign_in(client, "first@example.com")
    add_test_mug(client, first_token)
    placed = client.post(
        "/orders",
        headers=auth(first_token),
        json={"shipping_address": "123 Demo Road, Sample Town"},
    )
    second_token = register_and_sign_in(client, "second@example.com")

    response = client.get("/orders", headers=auth(second_token))
    hidden_order = client.get(f"/orders/{placed.json()['id']}", headers=auth(second_token))

    assert response.status_code == 200
    assert response.json() == []
    assert hidden_order.status_code == 404
