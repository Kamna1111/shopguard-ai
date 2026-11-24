"""Authenticated customer's shopping basket endpoints."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import current_user
from app.core.database import get_session
from app.domain.models import CartItem, Product, User
from app.domain.schemas import CartItemCreate, CartItemUpdate, CartLineRead, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


def cart_line(item: CartItem) -> CartLineRead:
    product = item.product
    return CartLineRead(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        unit_price=product.price,
        quantity=item.quantity,
        line_total=product.price * item.quantity,
    )


def cart_query(user_id: int):
    return (
        select(CartItem)
        .options(joinedload(CartItem.product).joinedload(Product.inventory))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id)
    )


@router.get("", response_model=CartRead)
def read_cart(
    session: Session = Depends(get_session), user: User = Depends(current_user)
) -> CartRead:
    items = list(session.scalars(cart_query(user.id)).unique().all())
    lines = [cart_line(item) for item in items]
    return CartRead(items=lines, subtotal=sum((line.line_total for line in lines), Decimal("0.00")))


@router.post("/items", response_model=CartLineRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    request: CartItemCreate,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> CartLineRead:
    product = session.scalar(
        select(Product)
        .options(joinedload(Product.inventory))
        .where(Product.id == request.product_id, Product.is_active.is_(True))
    )
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    item = session.scalar(
        select(CartItem)
        .where(CartItem.user_id == user.id, CartItem.product_id == product.id)
        .with_for_update()
    )
    new_quantity = request.quantity + (item.quantity if item else 0)
    stock = product.inventory.quantity if product.inventory else 0
    if new_quantity > stock:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "There is not enough stock for that quantity.",
        )
    if item is None:
        item = CartItem(user_id=user.id, product_id=product.id, quantity=request.quantity)
        session.add(item)
    else:
        item.quantity = new_quantity
    session.commit()
    item.product = product
    return cart_line(item)


@router.patch("/items/{product_id}", response_model=CartLineRead)
def update_cart_item(
    product_id: int,
    request: CartItemUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> CartLineRead:
    item = session.scalar(
        select(CartItem)
        .options(joinedload(CartItem.product).joinedload(Product.inventory))
        .where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That product is not in your basket.")
    stock = item.product.inventory.quantity if item.product.inventory else 0
    if request.quantity > stock:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "There is not enough stock for that quantity.",
        )
    item.quantity = request.quantity
    session.commit()
    return cart_line(item)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(
    product_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Response:
    item = session.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That product is not in your basket.")
    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
