"""Basic health, response-time, and live API contract checks."""

from automation.api.schemas.openapi_contract import validate_openapi_response


def test_health_is_ready_and_fast_enough_for_local_smoke(api) -> None:
    response = api.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert response.elapsed.total_seconds() < 2.0


def test_product_list_matches_the_live_openapi_contract(api) -> None:
    response = api.get("/products")

    assert response.status_code == 200
    validate_openapi_response(api, response, path="/products", method="get")


def test_product_search_filter_and_price_sort(api) -> None:
    response = api.get("/products", params={"category": "Outdoor", "sort": "price_asc"})

    assert response.status_code == 200
    products = response.json()
    assert products
    assert all(product["category"] == "Outdoor" for product in products)
    prices = [float(product["price"]) for product in products]
    assert prices == sorted(prices)


def test_unknown_product_and_invalid_query_return_clear_errors(api) -> None:
    missing = api.get("/products/999999999")
    too_long_query = api.get("/products", params={"q": "x" * 101})

    assert missing.status_code == 404
    assert missing.json()["detail"] == "Product not found."
    assert too_long_query.status_code == 422
