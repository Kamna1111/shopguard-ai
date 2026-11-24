"""Support assistant and human-reviewed AI test-case suggestions."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import get_ai_provider
from app.ai.support import answer_question
from app.ai.test_case_generator import generate_drafts, list_user_drafts
from app.api.dependencies import admin_user, current_user
from app.core.database import get_session
from app.domain.models import AITestCaseDraft, User
from app.domain.schemas import (
    AITestCaseRead,
    GenerateTestCasesRequest,
    SupportAnswer,
    SupportQuestion,
    TestCaseGenerationResponse,
    TestCaseReviewRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI helpers"])


@router.post("/support/chat", response_model=SupportAnswer)
def support_chat(
    request: SupportQuestion,
    _: User = Depends(current_user),
) -> SupportAnswer:
    provider = get_ai_provider()
    try:
        answer, sources = answer_question(request.question, provider)
    except Exception as exc:
        logger.exception("Support provider failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "The support helper is unavailable right now."
        ) from exc
    return SupportAnswer(answer=answer, source_documents=sources, provider=provider.name)


@router.post("/test-cases/generate", response_model=TestCaseGenerationResponse, status_code=201)
def generate_test_cases(
    request: GenerateTestCasesRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> TestCaseGenerationResponse:
    provider = get_ai_provider()
    try:
        return generate_drafts(session, user, request.requirement, provider)
    except Exception as exc:
        session.rollback()
        logger.exception("Test-case generation failed")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "The test-case helper could not create drafts."
        ) from exc


@router.get("/test-cases", response_model=list[AITestCaseRead])
def read_my_test_case_drafts(
    session: Session = Depends(get_session), user: User = Depends(current_user)
) -> list[AITestCaseDraft]:
    return list_user_drafts(session, user)


@router.patch("/test-cases/{test_case_id}/review", response_model=AITestCaseRead)
def review_test_case(
    test_case_id: str,
    request: TestCaseReviewRequest,
    session: Session = Depends(get_session),
    _: User = Depends(admin_user),
) -> AITestCaseDraft:
    draft = session.scalar(
        select(AITestCaseDraft).where(AITestCaseDraft.test_case_id == test_case_id)
    )
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Draft test case not found.")
    if draft.status != "draft":
        raise HTTPException(status.HTTP_409_CONFLICT, "This test case has already been reviewed.")
    draft.status = request.status
    draft.reviewed_at = datetime.now(UTC)
    session.commit()
    session.refresh(draft)
    return draft
