import pytest

from huamengyun_qa_demo.assertions import assert_error, assert_success


@pytest.mark.permission
def test_clerk_cannot_view_sales_report(api, clerk_token):
    response = api.get_sales_report(clerk_token)

    assert_error(response, "PERM_001")


@pytest.mark.permission
def test_store_manager_can_view_sales_report(api, store_manager_token, paid_bread_order):
    report = assert_success(api.get_sales_report(store_manager_token))

    assert report["salesAmount"] == "35.00"
    assert report["orderCount"] == 1
    assert report["topSku"] == "bread_001"
