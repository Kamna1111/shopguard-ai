"""Customer registration, login, and account information endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.core.database import get_session
from app.core.security import hash_password, make_access_token, verify_password
from app.domain.models import User
from app.domain.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, session: Session = Depends(get_session)) -> User:
    user = User(email=str(request.email).lower(), password_hash=hash_password(request.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An account with that email already exists.",
        ) from exc
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == str(request.email).lower()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")
    return TokenResponse(access_token=make_access_token(user.id), user=user)


@router.get("/me", response_model=UserRead)
def read_my_account(user: User = Depends(current_user)) -> User:
    return user
