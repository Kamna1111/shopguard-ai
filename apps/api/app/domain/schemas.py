"""Pydantic request and response shapes used by the REST API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)
    category: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    initial_stock: int = Field(ge=0, le=100000)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str
    category: str
    price: Decimal
    available_quantity: int


class InventoryUpdate(BaseModel):
    quantity: int = Field(ge=0, le=100000)


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=50)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0, le=50)


class CartLineRead(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class CartRead(BaseModel):
    items: list[CartLineRead]
    subtotal: Decimal


class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=8, max_length=500)
    coupon_code: str | None = Field(default=None, max_length=40)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=100)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: str
    shipping_address: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    payment_reference: str
    created_at: datetime
    items: list[OrderItemRead]


class SupportQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class SupportAnswer(BaseModel):
    answer: str
    source_documents: list[str]
    provider: str


class TestCaseContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["functional", "negative", "boundary", "security"]
    title: str = Field(min_length=5, max_length=240)
    preconditions: list[str] = Field(max_length=10)
    steps: list[str] = Field(min_length=1, max_length=12)
    expected_result: str = Field(min_length=5, max_length=1000)
    automation_type: Literal["ui", "api", "manual"]


class TestCaseBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_cases: list[TestCaseContent] = Field(min_length=1, max_length=20)


class GenerateTestCasesRequest(BaseModel):
    requirement: str = Field(min_length=10, max_length=4000)


class AITestCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case_id: str
    generation_id: str
    requirement: str
    category: str
    title: str
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    automation_type: str
    status: str
    duplicate_of: str | None


class TestCaseGenerationResponse(BaseModel):
    generation_id: str
    provider: str
    status: Literal["draft"] = "draft"
    test_cases: list[AITestCaseRead]


class TestCaseReviewRequest(BaseModel):
    status: Literal["approved", "rejected"]


class QualityRunMetric(BaseModel):
    label: str
    value: str


class QualityRunRead(BaseModel):
    run_id: str
    suite_id: Literal[
        "project-tests",
        "browser",
        "api",
        "api-components",
        "ai-security",
        "ai-evaluation",
        "performance",
    ]
    suite_name: str
    status: Literal["passed", "failed", "not_run"]
    summary: str
    run_at: datetime | None
    report_file: str | None
    metrics: list[QualityRunMetric]


class QualityDashboardRead(BaseModel):
    overall_status: Literal["passed", "failed", "partial", "not_run"]
    total_suites: int
    passing_suites: int
    saved_run_count: int
    last_updated: datetime | None
    latest_runs: list[QualityRunRead]
    recent_runs: list[QualityRunRead]
