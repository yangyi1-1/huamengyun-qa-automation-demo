from huamengyun_qa_demo.assertions import assert_success


def test_refund_restores_inventory_and_rolls_back_member_points(
    api, cashier_token, paid_bread_order, business_cases
):
    sku = business_cases["bread_order"]["sku"]
    member_id = business_cases["member_id"]
    inventory_after_payment = api.products[sku].inventory
    points_after_payment = api.members[member_id].points

    refund = assert_success(api.refund_order(cashier_token, paid_bread_order["orderId"]))
    member = assert_success(api.get_member(cashier_token, member_id))

    assert refund["status"] == "REFUNDED"
    assert api.products[sku].inventory == inventory_after_payment + business_cases["bread_order"]["quantity"]
    assert member["points"] == points_after_payment - paid_bread_order["pointsAwarded"]
    assert member["pointFlows"][-1]["type"] == "rollback"
