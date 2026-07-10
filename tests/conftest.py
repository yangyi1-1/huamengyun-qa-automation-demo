import json
from pathlib import Path

import pytest

from huamengyun_qa_demo import HuamengyunFakeApi
from huamengyun_qa_demo.assertions import assert_success


@pytest.fixture
def api() -> HuamengyunFakeApi:
    return HuamengyunFakeApi()


@pytest.fixture(scope="session")
def business_cases() -> dict:
    path = Path(__file__).parents[1] / "test_data" / "business_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def store_manager_token(api: HuamengyunFakeApi) -> str:
    data = assert_success(api.login("store_manager", "123456"))
    return data["token"]


@pytest.fixture
def cashier_token(api: HuamengyunFakeApi) -> str:
    data = assert_success(api.login("cashier_001", "123456"))
    return data["token"]


@pytest.fixture
def clerk_token(api: HuamengyunFakeApi) -> str:
    data = assert_success(api.login("clerk_001", "123456"))
    return data["token"]


@pytest.fixture
def paid_bread_order(api, cashier_token, business_cases) -> dict:
    case = business_cases["bread_order"]
    order = assert_success(
        api.create_order(
            cashier_token,
            member_id=business_cases["member_id"],
            items=[{"sku": case["sku"], "quantity": case["quantity"]}],
            coupon_amount=case["coupon_amount"],
        )
    )
    paid_order = assert_success(
        api.payment_callback(
            order["orderId"],
            transaction_id="pay_demo_001",
            pay_amount=order["payAmount"],
        )
    )
    return paid_order
