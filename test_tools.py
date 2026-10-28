import pytest

from shop_data import ShopData
from tools import Tools


@pytest.fixture(scope="module")
def tools():
    yield Tools(ShopData())


@pytest.mark.parametrize(
    ("booking_id", "expected"),
    [
        ("CW-1001", "90.0 EUR"),
        ("CW-1002", "340.0 EUR"),
        ("CW-1003", "50.0 EUR"),
        ("CW-1004", "73.0 EUR"),
        (
            "CW-1005",
            "Only bookings with status 'confirmed' can be refunded.",
        ),
        (
            "CW-1006",
            "Only bookings with status 'confirmed' can be refunded.",
        ),
        ("CW-1007", "186.0 EUR"),
    ],
)
def test_calculate_refund(tools, booking_id, expected):
    assert tools.calculate_refund(booking_id) == expected


def test_get_booking_unknown_id(tools):
    result = tools.get_booking("abc-3457")

    assert not result["found"]
    assert result["message"] == "Booking not found"


def test_get_booking_cw_1010(tools):
    result = tools.get_booking("CW-1010")

    assert result["found"]
    assert result["bike_type"] == "e-bike"
