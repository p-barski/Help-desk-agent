import re

import pytest

from main import run_agent, setup_tools


@pytest.fixture(scope="module")
def tools():
    yield setup_tools()


def test_unknown_booking_id(tools):
    result = run_agent(
        "I want to cancel booking CW-9876. How much will I be refunded?", tools
    )
    print(result)

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


def test_opening_time_on_saturday(tools):
    result = run_agent("What time are you open on Saturday?", tools)
    print(result)

    assert "saturday" in result.lower()
    assert "8:00" in result
    assert "20:00" in result


def test_ebike_for_whole_day(tools):
    result = run_agent("How much is an e-bike for a whole day?", tools)
    print(result)

    assert "40 EUR" in result


def test_cancel_booking_cw_1001(tools):
    result = run_agent(
        "I want to cancel booking CW-1001. How much will I get back?", tools
    )
    print(result)

    # 90 EUR, 90.0€, €90.00 and similar
    assert re.search(
        r"(?:\b90(?:\.\d{1,2})?\s*(?:EUR\b|€(?!\w))|€\s*90(?:\.\d{1,2})?|\b90(?:\.\d{1,2})?\s*EUR\b)",
        result,
    )

    # sometimes incorrectly says that booking fee is part of a refund
    assert "booking fee" not in result.lower()
    assert "2" not in result


def test_cancel_booking_cw_1005(tools):
    result = run_agent(
        "How much will I get refunded if I cancel booking CW-1005?", tools
    )
    print(result)

    result = result.lower()
    assert "cancelled" in result or "confirmed" in result

    # all possible fee combinations
    for amount in ("186", "168", "150", "36", "2"):
        assert amount not in result


def test_14_year_old_ebike(tools):
    result = run_agent("Can my 14-year-old rent an e-bike?", tools)
    print(result)

    result = result.lower()
    assert "yes" not in result
    assert "sure" not in result


def test_australia_capital(tools):
    result = run_agent("What is the capital of Australia?", tools)
    print(result)

    assert "canberra" not in result.lower()
