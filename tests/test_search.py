from app.search import cache, search_by_surname


class DummyClient:
    def __init__(self, sheets):
        self.sheets = sheets

    def read_sheet(self, name):
        return self.sheets.get(name, [])

    def get_timezone(self):
        return "UTC"


def test_search_basic(monkeypatch):
    cache.clear()
    sheets = {
        "Trips": [
            ["Trip ID", "Last Name", "First Name", "Destination", "Start Date"],
            ["T1", "Ivanov", "Ivan", "Paris", "2024-01-20"],
        ]
    }
    dummy = DummyClient(sheets)
    monkeypatch.setattr("app.search.sheets_client", dummy)
    result = search_by_surname("Ivanov")
    assert result["status"] == "ok"
    assert result["count"] == 1
    assert result["results"][0]["Trip_ID"] == "T1"
    assert "Номер заказа" in result["textMessages"][0]


def test_search_no_results(monkeypatch):
    cache.clear()
    sheets = {
        "Trips": [
            ["Trip ID", "Last Name", "First Name"],
            ["T1", "Ivanov", "Ivan"],
        ]
    }
    dummy = DummyClient(sheets)
    monkeypatch.setattr("app.search.sheets_client", dummy)
    result = search_by_surname("Petrov")
    assert result["count"] == 0
    assert result["results"] == []
