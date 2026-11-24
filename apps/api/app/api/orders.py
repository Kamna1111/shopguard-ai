"""Order history, checkout, and cancellation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import current_user
from app.core.database import get_session
from app.domain.models import Order, User
from app.domain.schemas import OrderCreate, OrderRead
from app.services.checkout import cancel_order, checkout

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=201)
def place_order(
    request: OrderCreate,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Order:
    return checkout(session, user.id, request)


@router.get("", response_model=list[OrderRead])
def order_history(
    session: Session = Depends(get_session), user: User = Depends(current_user)
) -> list[Order]:
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    return list(session.scalars(query).all())


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Order:
    order = session.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user.id)
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    return order


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_my_order(
    order_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Order:
    return cancel_order(session, user.id, order_id)
