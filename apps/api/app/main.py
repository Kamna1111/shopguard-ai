"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api import ai, auth, cart, health, orders, products, quality

app = FastAPI(
    title="ShopGuard AI Shop API",
    description="A simulated online shop used to practice quality engineering.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(ai.router)
app.include_router(quality.router)
