from decimal import Decimal

import pytest

from huamengyun_qa_demo.assertions import assert_success


@pytest.mark.smoke
def test_product_status_sync_to_zhanggui_and_mini_program(api, store_manager_token):
    sku = "bread_001"

    assert_success(api.update_product_status(store_manager_token, sku, online=False))
    zhanggui_products = assert_success(api.list_products(store_manager_token, "zhanggui_app"))[
        "products"
    ]
    mini_program_products = assert_success(api.list_products(store_manager_token, "mini_program"))[
        "products"
    ]

    assert sku not in {product["sku"] for product in zhanggui_products}
    assert sku not in {product["sku"] for product in mini_program_products}


def test_product_price_update_visible_across_clients(api, store_manager_token, business_cases):
    sku = "cake_001"
    new_price = Decimal("88.00")

    assert_success(api.update_product_price(store_manager_token, sku, new_price))

    for client in business_cases["clients"]:
        products = assert_success(api.list_products(store_manager_token, client))["products"]
        target = next(product for product in products if product["sku"] == sku)
        assert target["price"] == "88.00"
