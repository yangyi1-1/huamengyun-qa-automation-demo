from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

from .models import (
    BusinessError,
    Member,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Role,
    User,
)


class HuamengyunFakeApi:
    """A local fake API that mimics key retail SaaS testing scenarios.

    This class is intentionally small. It lets the pytest suite demonstrate
    business assertions without exposing real Huamengyun endpoints or data.
    """

    def __init__(self) -> None:
        self.users = {
            "store_manager": User("store_manager", "123456", Role.STORE_MANAGER, "store_001"),
            "cashier_001": User("cashier_001", "123456", Role.CASHIER, "store_001"),
            "clerk_001": User("clerk_001", "123456", Role.CLERK, "store_001"),
            "platform_admin": User("platform_admin", "123456", Role.PLATFORM_ADMIN, "platform"),
        }
        self.products = {
            "cake_001": Product("cake_001", "草莓生日蛋糕", Decimal("68.00"), 100, True),
            "bread_001": Product("bread_001", "原味吐司", Decimal("20.00"), 80, True),
            "coffee_001": Product("coffee_001", "美式咖啡", Decimal("12.00"), 60, True),
        }
        self.members = {
            "member_001": Member("member_001", "测试会员A", 100, Decimal("50.00")),
        }
        self.tokens: dict[str, User] = {}
        self.orders: dict[str, Order] = {}
        self.payment_callbacks: dict[str, str] = {}

    def login(self, username: str, password: str) -> dict:
        user = self.users.get(username)
        if not user or user.password != password:
            return self._error("AUTH_001", "invalid username or password")

        token = f"token_{username}_{uuid4().hex[:8]}"
        self.tokens[token] = user
        return self._success(
            {
                "token": token,
                "username": user.username,
                "role": user.role.value,
                "storeId": user.store_id,
            }
        )

    def update_product_status(self, token: str, sku: str, online: bool) -> dict:
        try:
            self._require_role(token, {Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            product = self._get_product(sku)
            product.online = online
            return self._success(self._product_payload(product))
        except BusinessError as error:
            return self._error(error.code, error.message)

    def update_product_price(self, token: str, sku: str, price: Decimal) -> dict:
        try:
            self._require_role(token, {Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            if price <= 0:
                raise BusinessError("PRODUCT_002", "price must be greater than zero")
            product = self._get_product(sku)
            product.price = price
            return self._success(self._product_payload(product))
        except BusinessError as error:
            return self._error(error.code, error.message)

    def list_products(self, token: str, client: str) -> dict:
        try:
            self._require_login(token)
            products = [
                self._product_payload(product)
                for product in self.products.values()
                if product.online
            ]
            return self._success({"client": client, "products": products})
        except BusinessError as error:
            return self._error(error.code, error.message)

    def create_order(
        self,
        token: str,
        member_id: str,
        items: list[dict],
        coupon_amount: Decimal | str = Decimal("0.00"),
    ) -> dict:
        try:
            self._require_role(token, {Role.CASHIER, Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            member = self._get_member(member_id)
            coupon_amount = Decimal(str(coupon_amount)).quantize(Decimal("0.01"))
            order_items = []
            for raw_item in items:
                product = self._get_product(raw_item["sku"])
                quantity = int(raw_item["quantity"])
                if quantity <= 0:
                    raise BusinessError("ORDER_001", "quantity must be greater than zero")
                if not product.online:
                    raise BusinessError("ORDER_002", "product is offline")
                if product.inventory < quantity:
                    raise BusinessError("ORDER_003", "insufficient inventory")
                order_items.append(OrderItem(product.sku, quantity, product.price))

            order = Order(
                order_id=f"HM{len(self.orders) + 1:06d}",
                member_id=member.member_id,
                items=order_items,
                coupon_amount=coupon_amount,
            )
            if order.pay_amount < Decimal("0.00"):
                raise BusinessError("ORDER_004", "coupon amount cannot exceed total amount")

            self.orders[order.order_id] = order
            return self._success(self._order_payload(order))
        except BusinessError as error:
            return self._error(error.code, error.message)

    def payment_callback(self, order_id: str, transaction_id: str, pay_amount: Decimal | str) -> dict:
        try:
            pay_amount = Decimal(str(pay_amount)).quantize(Decimal("0.01"))
            order = self._get_order(order_id)
            if transaction_id in self.payment_callbacks:
                existed_order_id = self.payment_callbacks[transaction_id]
                existed_order = self._get_order(existed_order_id)
                return self._success(self._order_payload(existed_order) | {"idempotent": True})

            if order.status != OrderStatus.WAIT_PAY:
                raise BusinessError("PAY_001", "order is not waiting for payment")
            if pay_amount != order.pay_amount:
                raise BusinessError("PAY_002", "payment amount mismatch")

            for item in order.items:
                product = self._get_product(item.sku)
                if product.inventory < item.quantity:
                    raise BusinessError("PAY_003", "insufficient inventory on payment")

            for item in order.items:
                self.products[item.sku].inventory -= item.quantity

            order.status = OrderStatus.PAID
            order.pay_transaction_id = transaction_id
            order.points_awarded = int(order.pay_amount)
            self.members[order.member_id].points += order.points_awarded
            self.members[order.member_id].point_flows.append(
                {
                    "orderId": order.order_id,
                    "type": "earn",
                    "points": order.points_awarded,
                }
            )
            self.payment_callbacks[transaction_id] = order.order_id
            return self._success(self._order_payload(order) | {"idempotent": False})
        except BusinessError as error:
            return self._error(error.code, error.message)

    def refund_order(self, token: str, order_id: str) -> dict:
        try:
            self._require_role(token, {Role.CASHIER, Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            order = self._get_order(order_id)
            if order.status != OrderStatus.PAID:
                raise BusinessError("REFUND_001", "only paid order can be refunded")

            for item in order.items:
                self.products[item.sku].inventory += item.quantity

            member = self.members[order.member_id]
            member.points -= order.points_awarded
            member.point_flows.append(
                {
                    "orderId": order.order_id,
                    "type": "rollback",
                    "points": -order.points_awarded,
                }
            )
            order.status = OrderStatus.REFUNDED
            return self._success(self._order_payload(order))
        except BusinessError as error:
            return self._error(error.code, error.message)

    def get_order(self, token: str, order_id: str) -> dict:
        try:
            self._require_login(token)
            return self._success(self._order_payload(self._get_order(order_id)))
        except BusinessError as error:
            return self._error(error.code, error.message)

    def get_member(self, token: str, member_id: str) -> dict:
        try:
            self._require_role(token, {Role.CASHIER, Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            member = self._get_member(member_id)
            return self._success(
                {
                    "memberId": member.member_id,
                    "name": member.name,
                    "points": member.points,
                    "balance": str(member.balance),
                    "pointFlows": deepcopy(member.point_flows),
                }
            )
        except BusinessError as error:
            return self._error(error.code, error.message)

    def get_sales_report(self, token: str) -> dict:
        try:
            self._require_role(token, {Role.STORE_MANAGER, Role.PLATFORM_ADMIN})
            paid_orders = [order for order in self.orders.values() if order.status == OrderStatus.PAID]
            total_sales = sum((order.pay_amount for order in paid_orders), Decimal("0.00"))
            top_sku = paid_orders[0].items[0].sku if paid_orders else None
            return self._success(
                {
                    "salesAmount": str(total_sales),
                    "orderCount": len(paid_orders),
                    "topSku": top_sku,
                }
            )
        except BusinessError as error:
            return self._error(error.code, error.message)

    def ask_ai_assistant(self, token: str, question: str) -> dict:
        try:
            user = self._require_login(token)
            normalized = question.lower()
            wants_sales = "销售" in question or "经营" in question or "sales" in normalized
            if wants_sales and user.role not in {Role.STORE_MANAGER, Role.PLATFORM_ADMIN}:
                return self._success(
                    {
                        "answer": "当前账号暂无权限查看经营数据，请联系店长或管理员。",
                        "hasSensitiveData": False,
                        "evidence": None,
                    }
                )

            if wants_sales:
                report = self.get_sales_report(token)
                if report["code"] != 0:
                    return report
                data = report["data"]
                answer = f"今日销售额{data['salesAmount']}元，订单数{data['orderCount']}单。"
                return self._success(
                    {
                        "answer": answer,
                        "hasSensitiveData": True,
                        "evidence": data,
                    }
                )

            return self._success(
                {
                    "answer": "暂时无法判断你的问题，请补充门店、时间范围或业务模块。",
                    "hasSensitiveData": False,
                    "evidence": None,
                }
            )
        except BusinessError as error:
            return self._error(error.code, error.message)

    def _require_login(self, token: str) -> User:
        user = self.tokens.get(token)
        if not user:
            raise BusinessError("AUTH_002", "token is invalid or expired")
        return user

    def _require_role(self, token: str, roles: set[Role]) -> User:
        user = self._require_login(token)
        if user.role not in roles:
            raise BusinessError("PERM_001", "permission denied")
        return user

    def _get_product(self, sku: str) -> Product:
        product = self.products.get(sku)
        if not product:
            raise BusinessError("PRODUCT_001", "product not found")
        return product

    def _get_member(self, member_id: str) -> Member:
        member = self.members.get(member_id)
        if not member:
            raise BusinessError("MEMBER_001", "member not found")
        return member

    def _get_order(self, order_id: str) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise BusinessError("ORDER_404", "order not found")
        return order

    def _product_payload(self, product: Product) -> dict:
        return {
            "sku": product.sku,
            "name": product.name,
            "price": str(product.price),
            "inventory": product.inventory,
            "online": product.online,
        }

    def _order_payload(self, order: Order) -> dict:
        return {
            "orderId": order.order_id,
            "memberId": order.member_id,
            "items": [
                {
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "unitPrice": str(item.unit_price),
                    "amount": str(item.amount),
                }
                for item in order.items
            ],
            "totalAmount": str(order.total_amount),
            "couponAmount": str(order.coupon_amount),
            "payAmount": str(order.pay_amount),
            "status": order.status.value,
            "payTransactionId": order.pay_transaction_id,
            "pointsAwarded": order.points_awarded,
        }

    def _success(self, data: dict) -> dict:
        return {"code": 0, "message": "success", "data": data}

    def _error(self, code: str, message: str) -> dict:
        return {"code": code, "message": message, "data": None}
