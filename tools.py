from datetime import datetime, timedelta, timezone
from enum import Enum

from shop_data import ShopData


class Policies(str, Enum):
    CANCELLATIONS = "cancellations"
    FAQ = "faq"
    PRICES = "prices"


class Tools:
    def __init__(self, shop_data: ShopData):
        self.shop_data = shop_data
        self.current_time = datetime(
            2026, 6, 10, 9, tzinfo=timezone(timedelta(hours=2))
        )

    def get_booking(self, booking_id: str) -> dict:
        """Look up a booking by its exact ID.

        Args:
            booking_id: The product identifier, e.g. CW-2003.
        """
        booking = [
            b for b in self.shop_data.bookings if b.get("id") == booking_id.upper()
        ]

        if not booking:
            return {"found": False, "message": "Booking not found"}

        return {"found": True, **booking[0]}

    def search_policies(self, policy: Policies) -> str:
        """Retrieve the shop's authoritative policy document.

        You MUST call this tool before answering questions about the shop's
        prices, cancellations, refunds, returns, delivery, ordering, or FAQs.
        Do not guess or answer these questions from general knowledge.

        Args:
            policy: The document to retrieve:
                - cancellations: rules for cancelling or changing a booking, and for refunds
                - faq: Answers to common questions: opening hours, age limits, payment, what to do when something goes wrong
                - prices: bike types, rental prices, add-ons, deposits and late return fees
        """
        match policy:
            case Policies.CANCELLATIONS:
                return self.shop_data.cancellations
            case Policies.FAQ:
                return self.shop_data.faq
            case Policies.PRICES:
                return self.shop_data.prices
            case _:
                return "Wrong argument passed, use one of: 'cancellations', 'faq', 'prices'."

    def calculate_refund(self, booking_id: str) -> str:
        """Calculate refund of existing booking.
        You MUST call this tool before answering questions about refunds.
        NEVER calculate refund on your own.
        Do not specify how refund was calculated.
        Answer only full refund price.

        Args:
            booking_id: The product identifier, e.g. CW-2003.
        """
        booking = self.get_booking(booking_id)
        if not booking["found"]:
            return f"Booking '{booking_id}' not found."
        if booking["status"] != "confirmed":
            return "Only bookings with status 'confirmed' can be refunded."

        rental_price = booking["rental_price_eur"]
        deposit_price = booking["deposit_eur"]
        start = datetime.fromisoformat(booking["start"])
        diff = start - self.current_time
        hours = diff.total_seconds() / 3600
        final_price = deposit_price
        if hours >= 48:
            final_price += rental_price
        elif 24 <= hours < 48:
            final_price += rental_price * 0.5
        return str(final_price) + " EUR"
