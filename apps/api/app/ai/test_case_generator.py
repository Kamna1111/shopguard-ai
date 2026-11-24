"""Generate validated draft cases and mark exact title duplicates."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import AIProvider
from app.domain.models import AITestCaseDraft, User
from app.domain.schemas import TestCaseGenerationResponse


def _normalized_title(title: str) -> str:
    return " ".join(title.casefold().split())


def generate_drafts(
    session: Session, user: User, requirement: str, provider: AIProvider
) -> TestCaseGenerationResponse:
    """Call provider, assign IDs, flag duplicates, and save every result as a draft."""
    batch = provider.generate_test_cases(requirement)
    generation_id = str(uuid4())
    title_to_id: dict[str, str] = {}
    drafts: list[dict] = []
    for case in batch.test_cases:
        case_id = str(uuid4())
        normalized = _normalized_title(case.title)
        duplicate_of = title_to_id.get(normalized)
        if duplicate_of is None:
            title_to_id[normalized] = case_id
        draft = AITestCaseDraft(
            test_case_id=case_id,
            generation_id=generation_id,
            created_by_user_id=user.id,
            requirement=requirement,
            category=case.category,
            title=case.title,
            preconditions=case.preconditions,
            steps=case.steps,
            expected_result=case.expected_result,
            automation_type=case.automation_type,
            status="draft",
            duplicate_of=duplicate_of,
        )
        session.add(draft)
        drafts.append(draft)
    session.commit()
    for draft in drafts:
        session.refresh(draft)
    return TestCaseGenerationResponse(
        generation_id=generation_id,
        provider=provider.name,
        test_cases=drafts,
    )


def list_user_drafts(session: Session, user: User) -> list[AITestCaseDraft]:
    """Return this user's suggestions, newest generation first."""
    return list(
        session.scalars(
            select(AITestCaseDraft)
            .where(AITestCaseDraft.created_by_user_id == user.id)
            .order_by(AITestCaseDraft.created_at.desc(), AITestCaseDraft.id)
        ).all()
    )
