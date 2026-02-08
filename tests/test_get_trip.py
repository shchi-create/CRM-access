import pytest

from app.search import cache, get_trip


class DummyClient:
    def __init__(self, sheets):
        self.sheets = sheets

    def read_sheet(self, name):
        return self.sheets.get(name, [])

    def get_timezone(self):
        return "UTC"


def test_get_trip_basic(monkeypatch):
    cache.clear()
    sheets = {
        "Trips": [
            ["Trip ID", "Last Name", "First Name", "Destination", "Start Date", "Total", "Currency"],
            ["T2", "Petrov", "Petr", "Rome", "2024-03-10", "1000", "EUR"],
        ],
        "Profile": [
            ["Trip ID", "Client ID", "Last Name", "First Name", "Amount"],
            ["T2", "C1", "Petrov", "Petr", "500"],
        ],
        "Contacts": [
            ["Trip ID", "Client ID", "Phone", "Email"],
            ["T2", "C1", "+100", "test@example.com"],
        ],
    }
    dummy = DummyClient(sheets)
    monkeypatch.setattr("app.search.sheets_client", dummy)
    result = get_trip("T2")
    assert result["meta"]["trip_id"] == "T2"
    assert result["trips"][0]["destination"] == "Rome"
    assert result["clients"][0]["contacts"][0]["email"] == "test@example.com"


def test_get_trip_missing(monkeypatch):
    cache.clear()
    sheets = {
        "Trips": [["Trip ID"], ["T3"]],
        "Profile": [["Trip ID"]],
        "Contacts": [["Trip ID"]],
    }
    dummy = DummyClient(sheets)
    monkeypatch.setattr("app.search.sheets_client", dummy)
    with pytest.raises(LookupError):
        get_trip("NONE")
