import json


class ShopData:
    def __init__(self) -> None:
        self._bookings = []
        self._cancellecations = ""
        self._faq = ""
        self._prices = ""

        # in this case data doesn't change
        with open("data/bookings.json", "r", encoding="utf-8") as f:
            self._bookings = json.load(f)
        with open("data/policies/cancellations.md", "r", encoding="utf-8") as f:
            self._cancellecations = f.read()
        with open("data/policies/faq.md", "r", encoding="utf-8") as f:
            self._faq = f.read()
        with open("data/policies/prices.md", "r", encoding="utf-8") as f:
            self._prices = f.read()

    @property
    def bookings(self) -> list:
        return self._bookings

    @property
    def cancellations(self) -> str:
        return self._cancellations

    @property
    def faq(self) -> str:
        return self._faq

    @property
    def prices(self) -> str:
        return self._prices
