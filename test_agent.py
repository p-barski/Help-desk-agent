import re

import pytest

from main import run_agent
from shop_data import ShopData
from tools import Policies, Tools


def assert_search_policies_spy_called_with(spy, arg: Policies):
    assert any(
        call.args and call.args[0] == arg or call.kwargs.get("policy") == arg
        for call in spy.call_args_list
    )


@pytest.fixture()
def tools_and_spies(mocker):
    shop_data = ShopData()
    tools = Tools(shop_data)

    get_booking_spy = mocker.spy(tools, "get_booking")
    search_policies_spy = mocker.spy(tools, "search_policies")
    calculate_refund_spy = mocker.spy(tools, "calculate_refund")

    return (
        {
            "get_booking": tools.get_booking,
            "search_policies": tools.search_policies,
            "calculate_refund": tools.calculate_refund,
        },
        get_booking_spy,
        search_policies_spy,
        calculate_refund_spy,
    )


def test_refund_unknown_booking_id_says_is_not_possible(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, _ = tools_and_spies
    result = run_agent(
        "I want to cancel booking CW-9876. How much will I be refunded?", tools
    )
    print(result)

    assert get_booking_spy.call_count > 0
    assert search_policies_spy.call_count == 0
    assert "EUR" not in result
    assert "€" not in result

    result = result.lower()
    assert any(
        phrase in result
        for phrase in (
            "contact",
            "staff",
            "support",
            "unable to ",
            "not able to ",
            "couldn't find",
            "couldn't locate",
            "double-check",
            "double check",
        )
    )


def test_refund_CW1001_calculates_correctly_with_tool(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent(
        "I want to cancel booking CW-1001. How much will I get back?", tools
    )
    print(result)

    assert get_booking_spy.call_count > 0
    assert search_policies_spy.call_count == 0
    assert calculate_refund_spy.call_count == 1
    # 90 EUR, 90.0€, €90.00 and similar
    assert re.search(
        r"(?:\b90(?:\.\d{1,2})?\s*(?:EUR\b|€(?!\w))|€\s*90(?:\.\d{1,2})?|\b90(?:\.\d{1,2})?\s*EUR\b)",
        result,
    )

    # sometimes incorrectly says that booking fee is part of a refund
    assert "booking fee" not in result.lower()


def test_refund_CW1002_calculates_correctly_with_tool(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent(
        "How much of a refund can I expect if I cancel booking CW-1002 right now?",
        tools,
    )
    print(result)

    assert get_booking_spy.call_count > 0
    assert search_policies_spy.call_count == 0
    assert calculate_refund_spy.call_count == 1
    # 340 EUR, 340.0€, €340.00 and similar
    assert re.search(
        r"(?:\b340(?:\.\d{1,2})?\s*(?:EUR\b|€(?!\w))|€\s*340(?:\.\d{1,2})?|\b340(?:\.\d{1,2})?\s*EUR\b)",
        result,
    )

    # sometimes incorrectly says that booking fee is part of a refund
    assert "booking fee" not in result.lower()


def test_refund_of_cancelled_booking_doesnt_make_up_fee(tools_and_spies):
    tools, get_booking_spy, _, calculate_refund_spy = tools_and_spies
    result = run_agent(
        "How much will I get refunded if I cancel booking CW-1005?", tools
    )
    print(result)

    assert get_booking_spy.call_count > 0
    assert calculate_refund_spy.call_count == 1
    result = result.lower()
    assert "cancelled" in result or "confirmed" in result

    # all possible fee combinations
    for amount in ("186", "168", "150", "36", "2"):
        assert amount not in result


def test_prices_ebike_for_whole_day_returns_from_prices(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("How much is an e-bike for a whole day?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count > 0
    assert calculate_refund_spy.call_count == 0
    assert_search_policies_spy_called_with(search_policies_spy, Policies.PRICES)
    assert "40 EUR" in result


def test_faq_14_year_old_cant_rent_an_ebike(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("Can my 14-year-old rent an e-bike?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count > 0
    assert calculate_refund_spy.call_count == 0
    print(search_policies_spy.call_args_list)
    assert_search_policies_spy_called_with(search_policies_spy, Policies.FAQ)
    result = result.lower()
    assert "yes" not in result
    assert "sure" not in result


def test_faq_citywheels_does_not_sell_bikes(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("Do you sell bikes?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count > 0
    assert calculate_refund_spy.call_count == 0
    print(search_policies_spy.call_args_list)
    assert_search_policies_spy_called_with(search_policies_spy, Policies.FAQ)
    result = result.lower()
    assert "no." in result
    assert "yes" not in result


def test_faq_opening_time_on_saturday(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("What time are you open on Saturday?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count > 0
    assert calculate_refund_spy.call_count == 0
    print(search_policies_spy.call_args_list)
    assert_search_policies_spy_called_with(search_policies_spy, Policies.FAQ)
    assert "saturday" in result.lower()
    assert "8:00" in result
    assert "20:00" in result


def test_general_knowledge_capital_of_australia_refuses_answer(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("What is the capital of Australia?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count == 0
    assert calculate_refund_spy.call_count == 0
    assert "canberra" not in result.lower()


def test_general_knowledge_sodium_chloride_formula_refuses_answer(tools_and_spies):
    tools, get_booking_spy, search_policies_spy, calculate_refund_spy = tools_and_spies
    result = run_agent("What is the chemical formula for sodium chloride?", tools)
    print(result)

    assert get_booking_spy.call_count == 0
    assert search_policies_spy.call_count == 0
    assert calculate_refund_spy.call_count == 0
    assert "nacl" not in result.lower()
