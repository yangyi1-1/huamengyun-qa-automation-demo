import pytest

from huamengyun_qa_demo.assertions import assert_error, assert_success


@pytest.mark.smoke
def test_paid_order_updates_status_amount_inventory_and_points(api, cashier_token, business_cases):
    case = business_cases["bread_order"]
    before_inventory = api.products[case["sku"]].inventory
    before_points = api.members[business_cases["member_id"]].points

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
            transaction_id="pay_demo_1001",
            pay_amount=order["payAmount"],
        )
    )

    assert paid_order["status"] == "PAID"
    assert paid_order["totalAmount"] == "40.00"
    assert paid_order["couponAmount"] == "5.00"
    assert paid_order["payAmount"] == "35.00"
    assert api.products[case["sku"]].inventory == before_inventory - case["quantity"]
    assert api.members[business_cases["member_id"]].points == before_points + 35


def test_duplicate_payment_callback_is_idempotent(api, cashier_token, business_cases):
    case = business_cases["bread_order"]
    order = assert_success(
        api.create_order(
            cashier_token,
            member_id=business_cases["member_id"],
            items=[{"sku": case["sku"], "quantity": 1}],
            coupon_amount="0.00",
        )
    )

    first_callback = assert_success(
        api.payment_callback(order["orderId"], "pay_idempotent_001", order["payAmount"])
    )
    second_callback = assert_success(
        api.payment_callback(order["orderId"], "pay_idempotent_001", order["payAmount"])
    )

    assert first_callback["idempotent"] is False
    assert second_callback["idempotent"] is True
    assert api.products[case["sku"]].inventory == 79


def test_coupon_amount_cannot_exceed_order_total(api, cashier_token, business_cases):
    response = api.create_order(
        cashier_token,
        member_id=business_cases["member_id"],
        items=[{"sku": "coffee_001", "quantity": 1}],
        coupon_amount="99.00",
    )

    assert_error(response, "ORDER_004")
