from __future__ import annotations

from decimal import Decimal


def assert_success(response: dict) -> dict:
    assert response["code"] == 0, response
    assert response["message"] == "success", response
    return response["data"]


def assert_error(response: dict, expected_code: str) -> dict:
    assert response["code"] == expected_code, response
    assert response["message"], response
    return response


def money(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))
