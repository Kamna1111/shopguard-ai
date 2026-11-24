"""Checkout, totals, safe stock changes, and order cancellation rules."""

from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.domain.models import (
    CartItem,
    DiscountCode,
    IdempotencyKey,
    Inventory,
    Order,
    OrderItem,
)
from app.domain.schemas import OrderCreate

PENNY = Decimal("0.01")


def cash(amount: Decimal) -> Decimal:
    return amount.quantize(PENNY, rounding=ROUND_HALF_UP)


def order_with_items(session: Session, order_id: int) -> Order:
    return session.scalar(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )


def checkout(session: Session, user_id: int, request: OrderCreate) -> Order:
    key = request.idempotency_key.strip() if request.idempotency_key else None
    if key:
        previous = session.get(IdempotencyKey, key)
        if previous:
            if previous.user_id != user_id:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "That checkout key is already in use.",
                )
            return order_with_items(session, previous.order_id)

    try:
        cart_items = list(
            session.scalars(
                select(CartItem)
                .options(joinedload(CartItem.product))
                .where(CartItem.user_id == user_id)
                .with_for_update(of=CartItem)
            ).all()
        )
        if not cart_items:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your basket is empty.")

        inventory_by_product: dict[int, Inventory] = {}
        for item in cart_items:
            inventory = session.scalar(
                select(Inventory).where(Inventory.product_id == item.product_id).with_for_update()
            )
            if inventory is None or inventory.quantity < item.quantity:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"There is not enough stock for {item.product.name}.",
                )
            inventory_by_product[item.product_id] = inventory

        subtotal = cash(
            sum((item.product.price * item.quantity for item in cart_items), Decimal("0.00"))
        )
        discount_amount = Decimal("0.00")
        if request.coupon_code:
            code = session.scalar(
                select(DiscountCode).where(
                    DiscountCode.code == request.coupon_code.strip().upper(),
                    DiscountCode.is_active.is_(True),
                )
            )
            if code is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "That discount code is not valid.")
            discount_amount = cash(subtotal * code.percent_off / Decimal("100"))

        taxable_amount = subtotal - discount_amount
        tax_amount = cash(taxable_amount * settings.shop_tax_rate)
        total = cash(taxable_amount + tax_amount)
        order = Order(
            user_id=user_id,
            status="placed",
            shipping_address=request.shipping_address.strip(),
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            payment_reference=f"SIM-{uuid4().hex[:12].upper()}",
        )
        order.items = [
            OrderItem(
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
            for item in cart_items
        ]
        session.add(order)
        session.flush()

        for item in cart_items:
            inventory_by_product[item.product_id].quantity -= item.quantity
            session.delete(item)
        if key:
            session.add(IdempotencyKey(key=key, user_id=user_id, order_id=order.id))
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except IntegrityError as exc:
        session.rollback()
        if key:
            previous = session.get(IdempotencyKey, key)
            if previous and previous.user_id == user_id:
                return order_with_items(session, previous.order_id)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The order could not be saved because the request conflicts with existing data.",
        ) from exc
    except Exception:
        session.rollback()
        raise

    return order_with_items(session, order.id)


def cancel_order(session: Session, user_id: int, order_id: int) -> Order:
    order = session.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.status != "placed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a placed order can be cancelled.")

    try:
        for item in order.items:
            if item.product_id is None:
                continue
            inventory = session.scalar(
                select(Inventory).where(Inventory.product_id == item.product_id).with_for_update()
            )
            if inventory is not None:
                inventory.quantity += item.quantity
        order.status = "cancelled"
        session.commit()
    except Exception:
        session.rollback()
        raise
    return order_with_items(session, order.id)
