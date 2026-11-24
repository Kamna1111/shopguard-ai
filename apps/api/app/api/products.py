"""Product search and administrator-only product/stock management."""

from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import admin_user
from app.core.database import get_session
from app.domain.models import Inventory, Product, User
from app.domain.schemas import InventoryUpdate, ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


class ProductSort(StrEnum):
    name = "name"
    price_asc = "price_asc"
    price_desc = "price_desc"


def product_by_id(session: Session, product_id: int) -> Product:
    product = session.scalar(
        select(Product)
        .options(joinedload(Product.inventory))
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product


@router.get("", response_model=list[ProductRead])
def list_products(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=80),
    in_stock: bool | None = None,
    sort: ProductSort = ProductSort.name,
    session: Session = Depends(get_session),
) -> list[Product]:
    query = (
        select(Product).options(joinedload(Product.inventory)).where(Product.is_active.is_(True))
    )
    if q:
        query = query.where(Product.name.ilike(f"%{q.strip()}%"))
    if category:
        query = query.where(Product.category.ilike(category.strip()))
    if in_stock is True:
        query = query.join(Inventory).where(Inventory.quantity > 0)
    elif in_stock is False:
        query = query.outerjoin(Inventory).where(
            (Inventory.quantity == 0) | (Inventory.quantity.is_(None))
        )
    if sort == ProductSort.price_asc:
        query = query.order_by(Product.price.asc())
    elif sort == ProductSort.price_desc:
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.name.asc())
    return list(session.scalars(query).unique().all())


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)) -> Product:
    return product_by_id(session, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    request: ProductCreate,
    session: Session = Depends(get_session),
    _: User = Depends(admin_user),
) -> Product:
    product = Product(
        sku=request.sku.strip().upper(),
        name=request.name.strip(),
        description=request.description.strip(),
        category=request.category.strip(),
        price=request.price,
    )
    product.inventory = Inventory(quantity=request.initial_stock)
    session.add(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That product SKU already exists.") from exc
    return product_by_id(session, product.id)


@router.patch("/{product_id}/inventory", response_model=ProductRead)
def set_inventory(
    product_id: int,
    request: InventoryUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(admin_user),
) -> Product:
    product = product_by_id(session, product_id)
    if product.inventory is None:
        product.inventory = Inventory(quantity=request.quantity)
    else:
        product.inventory.quantity = request.quantity
    session.commit()
    return product_by_id(session, product_id)
