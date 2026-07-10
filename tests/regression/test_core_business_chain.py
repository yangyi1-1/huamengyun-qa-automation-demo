from huamengyun_qa_demo.assertions import assert_success


def test_full_order_payment_report_ai_regression_chain(
    api, store_manager_token, cashier_token, business_cases
):
    """Core regression chain: product -> order -> payment -> report -> AI answer."""

    case = business_cases["bread_order"]
    catalog = assert_success(api.list_products(cashier_token, "cashier_app"))["products"]
    target_product = next(product for product in catalog if product["sku"] == case["sku"])

    order = assert_success(
        api.create_order(
            cashier_token,
            member_id=business_cases["member_id"],
            items=[{"sku": target_product["sku"], "quantity": case["quantity"]}],
            coupon_amount=case["coupon_amount"],
        )
    )
    paid = assert_success(api.payment_callback(order["orderId"], "pay_regression_001", order["payAmount"]))
    queried_order = assert_success(api.get_order(cashier_token, paid["orderId"]))
    report = assert_success(api.get_sales_report(store_manager_token))
    ai_answer = assert_success(
        api.ask_ai_assistant(
            store_manager_token,
            business_cases["search_questions"]["sales_report"],
        )
    )

    assert queried_order["status"] == "PAID"
    assert queried_order["payAmount"] == "35.00"
    assert report["salesAmount"] == "35.00"
    assert report["orderCount"] == 1
    assert ai_answer["evidence"]["salesAmount"] == report["salesAmount"]
