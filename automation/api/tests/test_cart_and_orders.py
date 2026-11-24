"""Basket and checkout flows through public HTTP endpoints."""

from uuid import uuid4


def first_in_stock_product(api) -> dict:
    response = api.get("/products", params={"in_stock": True})
    assert response.status_code == 200, response.text
    products = response.json()
    assert products, "Run make db-seed to add demo products before API automation."
    return products[0]


def test_cart_add_update_and_remove(api, customer) -> None:
    product = first_in_stock_product(api)
    added = api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": 1},
    )
    cart = api.get("/cart", token=customer.token)
    updated = api.patch(f"/cart/items/{product['id']}", token=customer.token, json={"quantity": 2})
    removed = api.delete(f"/cart/items/{product['id']}", token=customer.token)

    assert added.status_code == 201
    assert cart.status_code == 200
    assert cart.json()["items"][0]["quantity"] == 1
    assert updated.status_code == 200
    assert updated.json()["quantity"] == 2
    assert removed.status_code == 204
    assert api.get("/cart", token=customer.token).json()["items"] == []


def test_invalid_quantities_and_out_of_stock_are_rejected(api, customer) -> None:
    product = first_in_stock_product(api)
    negative = api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": -1},
    )
    above_stock = api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": 50},
    )

    assert negative.status_code == 422
    assert above_stock.status_code == 409
    assert "not enough stock" in above_stock.json()["detail"].lower()


def test_invalid_coupon_keeps_cart_for_customer_to_fix(api, customer) -> None:
    product = first_in_stock_product(api)
    api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": 1},
    )
    order = api.post(
        "/orders",
        token=customer.token,
        json={
            "shipping_address": "123 Demo Road, Sample Town",
            "coupon_code": "NOT-VALID",
            "idempotency_key": f"invalid-{uuid4().hex}",
        },
    )

    assert order.status_code == 400
    assert order.json()["detail"] == "That discount code is not valid."
    assert len(api.get("/cart", token=customer.token).json()["items"]) == 1


def test_checkout_retry_returns_same_order_then_cancellation_restores_stock(api, customer) -> None:
    product = first_in_stock_product(api)
    original_stock = product["available_quantity"]
    added = api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert added.status_code == 201

    checkout_body = {
        "shipping_address": "123 Demo Road, Sample Town",
        "coupon_code": "WELCOME10",
        "idempotency_key": f"checkout-{uuid4().hex}",
    }
    order = api.post("/orders", token=customer.token, json=checkout_body)
    retry = api.post("/orders", token=customer.token, json=checkout_body)

    assert order.status_code == 201
    assert order.json()["status"] == "placed"
    assert order.json()["discount_amount"] != "0.00"
    assert retry.status_code == 201
    assert retry.json()["order_number"] == order.json()["order_number"]
    assert api.get("/orders", token=customer.token).json()[0]["id"] == order.json()["id"]

    cancelled = api.post(f"/orders/{order.json()['id']}/cancel", token=customer.token)
    duplicate_cancel = api.post(f"/orders/{order.json()['id']}/cancel", token=customer.token)
    after_cancel = api.get(f"/products/{product['id']}")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert duplicate_cancel.status_code == 409
    assert after_cancel.json()["available_quantity"] == original_stock


def test_checkout_is_saved_as_order_and_order_item_in_postgresql(
    api, customer, read_only_database
) -> None:
    product = first_in_stock_product(api)
    added = api.post(
        "/cart/items",
        token=customer.token,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert added.status_code == 201

    order = api.post(
        "/orders",
        token=customer.token,
        json={"shipping_address": "123 Demo Road, Sample Town"},
    )
    assert order.status_code == 201

    saved = read_only_database.execute(
        """
        SELECT orders.status, orders.total, order_items.product_name, order_items.quantity
        FROM orders
        JOIN order_items ON order_items.order_id = orders.id
        WHERE orders.order_number = %s
        """,
        (order.json()["order_number"],),
    ).fetchone()

    assert saved is not None
    assert saved[0] == "placed"
    assert float(saved[1]) == float(order.json()["total"])
    assert saved[2] == product["name"]
    assert saved[3] == 1

    cancellation = api.post(f"/orders/{order.json()['id']}/cancel", token=customer.token)
    assert cancellation.status_code == 200
