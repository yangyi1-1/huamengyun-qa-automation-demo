import pytest

from huamengyun_qa_demo.assertions import assert_success


@pytest.mark.ai
def test_ai_assistant_answer_matches_sales_report(
    api, store_manager_token, paid_bread_order, business_cases
):
    answer = assert_success(
        api.ask_ai_assistant(
            store_manager_token,
            business_cases["search_questions"]["sales_report"],
        )
    )
    report = assert_success(api.get_sales_report(store_manager_token))

    assert answer["hasSensitiveData"] is True
    assert answer["evidence"] == report
    assert report["salesAmount"] in answer["answer"]
    assert f"{report['orderCount']}单" in answer["answer"]


@pytest.mark.ai
def test_ai_assistant_blocks_sensitive_report_for_clerk(api, clerk_token, business_cases):
    answer = assert_success(
        api.ask_ai_assistant(
            clerk_token,
            business_cases["search_questions"]["sales_report"],
        )
    )

    assert answer["hasSensitiveData"] is False
    assert answer["evidence"] is None
    assert "暂无权限" in answer["answer"]


@pytest.mark.ai
def test_ai_assistant_returns_fallback_for_unclear_question(api, store_manager_token, business_cases):
    answer = assert_success(
        api.ask_ai_assistant(
            store_manager_token,
            business_cases["search_questions"]["unclear"],
        )
    )

    assert answer["hasSensitiveData"] is False
    assert answer["evidence"] is None
    assert "补充" in answer["answer"]
