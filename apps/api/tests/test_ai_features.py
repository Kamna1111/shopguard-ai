"""Deterministic AI-feature checks that never make an external model call."""

from app.core.security import make_access_token
from app.domain.models import User


def register_customer(client, email: str = "ai-customer@example.com") -> str:
    client.post("/auth/register", json={"email": email, "password": "safe-demo-pass-123"})
    response = client.post("/auth/login", json={"email": email, "password": "safe-demo-pass-123"})
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_support_assistant_uses_approved_shop_notes(client) -> None:
    token = register_customer(client)
    response = client.post(
        "/ai/support/chat",
        headers=headers(token),
        json={"question": "How do I use the WELCOME10 discount code?"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert response.json()["source_documents"] == ["discount-help"]
    assert "10 percent discount" in response.json()["answer"]


def test_support_assistant_does_not_guess_without_approved_evidence(client) -> None:
    token = register_customer(client)
    response = client.post(
        "/ai/support/chat",
        headers=headers(token),
        json={"question": "What is the secret code for the moon base?"},
    )

    assert response.status_code == 200
    assert response.json()["source_documents"] == []
    assert "approved shop note" in response.json()["answer"]


def test_generator_saves_unique_draft_cases_and_marks_duplicates(client) -> None:
    token = register_customer(client)
    response = client.post(
        "/ai/test-cases/generate",
        headers=headers(token),
        json={"requirement": "As a customer, I can put a product in my basket and check out."},
    )

    assert response.status_code == 201
    result = response.json()
    cases = result["test_cases"]
    assert result["provider"] == "mock"
    assert result["status"] == "draft"
    assert {case["category"] for case in cases} == {
        "functional",
        "negative",
        "boundary",
        "security",
    }
    assert len({case["test_case_id"] for case in cases}) == len(cases)
    assert all(case["status"] == "draft" for case in cases)
    assert sum(case["duplicate_of"] is not None for case in cases) == 1

    listed = client.get("/ai/test-cases", headers=headers(token))
    assert listed.status_code == 200
    assert {case["test_case_id"] for case in listed.json()} == {
        case["test_case_id"] for case in cases
    }


def test_only_admin_can_approve_a_draft_and_it_is_never_auto_executed(
    client, database_session
) -> None:
    customer_token = register_customer(client)
    generated = client.post(
        "/ai/test-cases/generate",
        headers=headers(customer_token),
        json={"requirement": "A customer can view their own order history."},
    )
    case_id = generated.json()["test_cases"][0]["test_case_id"]
    blocked = client.patch(
        f"/ai/test-cases/{case_id}/review",
        headers=headers(customer_token),
        json={"status": "approved"},
    )

    admin = User(
        email="ai-reviewer@example.com",
        password_hash="test-hash-not-used-for-token-authentication",
        role="admin",
    )
    database_session.add(admin)
    database_session.commit()
    database_session.refresh(admin)
    admin_token = make_access_token(admin.id)
    approved = client.patch(
        f"/ai/test-cases/{case_id}/review",
        headers=headers(admin_token),
        json={"status": "approved"},
    )

    assert blocked.status_code == 403
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert "execute" not in approved.json()


def test_generator_rejects_too_short_requirement_and_requires_sign_in(client) -> None:
    token = register_customer(client)
    too_short = client.post(
        "/ai/test-cases/generate",
        headers=headers(token),
        json={"requirement": "short"},
    )
    unauthenticated = client.get("/ai/test-cases")

    assert too_short.status_code == 422
    assert unauthenticated.status_code == 401
