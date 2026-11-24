"""Authentication, validation, and role-access API checks."""

from uuid import uuid4


def test_register_login_and_read_account(api, customer) -> None:
    account = api.get("/auth/me", token=customer.token)
    bad_password = api.post(
        "/auth/login", json={"email": customer.email, "password": "incorrect-password"}
    )

    assert account.status_code == 200
    assert account.json()["email"] == customer.email
    assert account.json()["role"] == "customer"
    assert bad_password.status_code == 401


def test_duplicate_registration_and_missing_auth_are_rejected(api, customer) -> None:
    duplicate = api.post(
        "/auth/register",
        json={"email": customer.email, "password": "another-password-123"},
    )
    missing_auth = api.get("/auth/me")
    invalid_auth = api.get("/auth/me", token="not-a-real-token")

    assert duplicate.status_code == 409
    assert missing_auth.status_code == 401
    assert invalid_auth.status_code == 401


def test_invalid_registration_data_returns_validation_error(api) -> None:
    response = api.post(
        "/auth/register",
        json={"email": f"short-password-{uuid4().hex}@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_customer_cannot_create_an_admin_product(api, customer) -> None:
    response = api.post(
        "/products",
        token=customer.token,
        json={
            "sku": f"TEST-{uuid4().hex[:8]}",
            "name": "Unauthorized product",
            "description": "This request must not create a product.",
            "category": "Test",
            "price": "9.99",
            "initial_stock": 2,
        },
    )

    assert response.status_code == 403
