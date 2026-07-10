from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class BusinessError(Exception):
    """Raised when the fake API returns a business failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class Role(str, Enum):
    CLERK = "clerk"
    CASHIER = "cashier"
    STORE_MANAGER = "store_manager"
    PLATFORM_ADMIN = "platform_admin"


class OrderStatus(str, Enum):
    WAIT_PAY = "WAIT_PAY"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class User:
    username: str
    password: str
    role: Role
    store_id: str


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    inventory: int
    online: bool = True


@dataclass
class Member:
    member_id: str
    name: str
    points: int
    balance: Decimal
    point_flows: list[dict] = field(default_factory=list)


@dataclass
class OrderItem:
    sku: str
    quantity: int
    unit_price: Decimal

    @property
    def amount(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    order_id: str
    member_id: str
    items: list[OrderItem]
    coupon_amount: Decimal
    status: OrderStatus = OrderStatus.WAIT_PAY
    pay_transaction_id: str | None = None
    points_awarded: int = 0

    @property
    def total_amount(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0.00"))

    @property
    def pay_amount(self) -> Decimal:
        return self.total_amount - self.coupon_amount
