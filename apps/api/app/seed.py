"""Add a few safe demo products and the documented sample coupon."""

from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain.models import DiscountCode, Inventory, Product, User

DEMO_PRODUCTS = (
    ("DEMO-BOTTLE", "Trail Bottle", "Insulated bottle for day trips.", "Outdoor", "19.99", 12),
    ("DEMO-LAMP", "Desk Lamp", "Adjustable lamp with a warm light.", "Home", "34.50", 8),
    ("DEMO-MUG", "Travel Mug", "Reusable mug with a secure lid.", "Outdoor", "14.25", 5),
)


def seed() -> None:
    with SessionLocal() as session:
        for sku, name, description, category, price, quantity in DEMO_PRODUCTS:
            product = session.scalar(select(Product).where(Product.sku == sku))
            if product is None:
                product = Product(
                    sku=sku,
                    name=name,
                    description=description,
                    category=category,
                    price=Decimal(price),
                    inventory=Inventory(quantity=quantity),
                )
                session.add(product)

        coupon = session.scalar(select(DiscountCode).where(DiscountCode.code == "WELCOME10"))
        if coupon is None:
            session.add(DiscountCode(code="WELCOME10", percent_off=Decimal("10.00")))

        if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
            email = settings.bootstrap_admin_email.lower()
            admin = session.scalar(select(User).where(User.email == email))
            if admin is None:
                session.add(
                    User(
                        email=email,
                        password_hash=hash_password(settings.bootstrap_admin_password),
                        role="admin",
                    )
                )
        session.commit()
    print("Demo products and WELCOME10 coupon are ready.")


if __name__ == "__main__":
    seed()
