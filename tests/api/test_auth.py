import pytest

from huamengyun_qa_demo.assertions import assert_error, assert_success


@pytest.mark.smoke
def test_store_manager_login_returns_token(api):
    data = assert_success(api.login("store_manager", "123456"))

    assert data["token"].startswith("token_store_manager_")
    assert data["role"] == "store_manager"
    assert data["storeId"] == "store_001"


def test_invalid_password_is_rejected(api):
    response = api.login("store_manager", "wrong-password")

    assert_error(response, "AUTH_001")
