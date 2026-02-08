from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

from app.cache import TTLCache
from app.config import settings
from app.sheets_client import get_header_map, pick_header, sheets_client


@dataclass
class SheetData:
    headers: List[str]
    rows: List[List[Any]]
    header_map: Dict[str, int]


cache = TTLCache(settings.cache_ttl)


def _limit_rows(rows: List[List[Any]]) -> List[List[Any]]:
    if len(rows) > settings.max_sheet_rows:
        return rows[: settings.max_sheet_rows]
    return rows


def _load_sheet(sheet_name: str) -> SheetData:
    cache_key = f"sheet:{sheet_name}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    raw = sheets_client.read_sheet(sheet_name)
    headers, rows, header_map = get_header_map(raw)
    rows = _limit_rows(rows)
    data = SheetData(headers=headers, rows=rows, header_map=header_map)
    cache.set(cache_key, data)
    return data


def warm_cache() -> None:
    for sheet_name in ("Trips", "Profile", "Contacts"):
        _load_sheet(sheet_name)
    _get_timezone()


def _get_timezone() -> str:
    cache_key = "sheet:timezone"
    cached = cache.get(cache_key)
    if cached:
        return cached
    tz = sheets_client.get_timezone()
    cache.set(cache_key, tz)
    return tz


def _format_date(value: Any, tz_name: str) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        base = datetime(1899, 12, 30)
        date_value = base + timedelta(days=float(value))
        tz = ZoneInfo(tz_name)
        localized = date_value.replace(tzinfo=tz)
        return localized.strftime("%Y-%m-%d")
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return ""
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(raw, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw
    return str(value)


def search_by_surname(surname: str) -> Dict[str, Any]:
    surname = surname.strip()
    sheet = _load_sheet("Trips")
    tz_name = _get_timezone()
    last_idx = pick_header(sheet.header_map, ["lastname", "last name"])
    first_idx = pick_header(sheet.header_map, ["firstname", "first name"])
    trip_idx = pick_header(sheet.header_map, ["trip_id", "trip id"])
    start_idx = pick_header(sheet.header_map, ["startdate", "start date"])
    dest_idx = pick_header(sheet.header_map, ["destination"])

    results: List[Dict[str, Any]] = []
    text_messages: List[str] = []

    for row in sheet.rows:
        last_name = _cell(row, last_idx)
        if last_name.strip().lower() != surname.lower():
            continue
        trip_id = _cell(row, trip_idx)
        first_name = _cell(row, first_idx)
        destination = _cell(row, dest_idx)
        start_date = _format_date(_raw_cell(row, start_idx), tz_name)
        if not destination:
            destination = "не указано"
        if not start_date:
            start_date = "не указана"
        result = {
            "Trip_ID": trip_id,
            "LastName": last_name,
            "FirstName": first_name,
            "destination": destination,
            "startDate": start_date if start_date != "не указана" else "",
        }
        results.append(result)
        message = (
            "Номер заказа: {trip_id}\n"
            "Фамилия: {last_name}\n"
            "Имя: {first_name}\n"
            "Направление: {destination}\n"
            "Дата вылета: {start_date}"
        ).format(
            trip_id=trip_id,
            last_name=last_name,
            first_name=first_name,
            destination=destination,
            start_date=start_date,
        )
        text_messages.append(message)
        if len(results) >= settings.max_search_results:
            break

    return {
        "status": "ok",
        "count": len(results),
        "results": results,
        "textMessages": text_messages,
    }


def get_trip(trip_id: str) -> Dict[str, Any]:
    trip_id = trip_id.strip()
    tz_name = _get_timezone()

    trips_sheet = _load_sheet("Trips")
    profile_sheet = _load_sheet("Profile")
    contacts_sheet = _load_sheet("Contacts")

    trip_row, trip_idx_map = _find_trip_row(trips_sheet, trip_id)
    if not trip_row:
        raise LookupError("trip not found")

    trips_data = _build_trip_data(trip_row, trips_sheet, tz_name)
    clients = _build_clients(profile_sheet, contacts_sheet, trip_id)

    payments = {
        "total": trips_data.get("total", ""),
        "currency": trips_data.get("currency", ""),
        "per_client": [
            {
                "client_id": client.get("client_id", ""),
                "amount": client.get("amount", ""),
            }
            for client in clients
        ],
    }

    meta = {
        "trip_id": trip_id,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timezone": tz_name,
    }

    return {
        "meta": meta,
        "clients": clients,
        "trips": [trips_data],
        "payments": payments,
    }


def _find_trip_row(sheet: SheetData, trip_id: str) -> Tuple[Optional[List[Any]], Dict[str, int]]:
    trip_idx = pick_header(sheet.header_map, ["trip_id", "trip id"])
    for row in sheet.rows:
        if _cell(row, trip_idx) == trip_id:
            return row, sheet.header_map
    return None, sheet.header_map


def _build_trip_data(row: List[Any], sheet: SheetData, tz_name: str) -> Dict[str, Any]:
    last_idx = pick_header(sheet.header_map, ["lastname", "last name"])
    first_idx = pick_header(sheet.header_map, ["firstname", "first name"])
    trip_idx = pick_header(sheet.header_map, ["trip_id", "trip id"])
    start_idx = pick_header(sheet.header_map, ["startdate", "start date"])
    dest_idx = pick_header(sheet.header_map, ["destination"])
    total_idx = pick_header(sheet.header_map, ["total", "amount"])
    currency_idx = pick_header(sheet.header_map, ["currency"])

    start_date = _format_date(_raw_cell(row, start_idx), tz_name)
    return {
        "trip_id": _cell(row, trip_idx),
        "main_tourist": {
            "last_name": _cell(row, last_idx),
            "first_name": _cell(row, first_idx),
        },
        "destination": _cell(row, dest_idx),
        "start_date": start_date,
        "passengers": [],
        "total": _cell(row, total_idx),
        "currency": _cell(row, currency_idx),
    }


def _build_clients(profile_sheet: SheetData, contacts_sheet: SheetData, trip_id: str) -> List[Dict[str, Any]]:
    profile_trip_idx = pick_header(profile_sheet.header_map, ["trip_id", "trip id"])
    client_id_idx = pick_header(profile_sheet.header_map, ["client_id", "client id", "id"])
    last_idx = pick_header(profile_sheet.header_map, ["lastname", "last name"])
    first_idx = pick_header(profile_sheet.header_map, ["firstname", "first name"])
    amount_idx = pick_header(profile_sheet.header_map, ["amount", "total"])

    contacts_trip_idx = pick_header(contacts_sheet.header_map, ["trip_id", "trip id"])
    contact_client_idx = pick_header(contacts_sheet.header_map, ["client_id", "client id", "id"])
    phone_idx = pick_header(contacts_sheet.header_map, ["phone", "mobile"])
    email_idx = pick_header(contacts_sheet.header_map, ["email"])

    clients: List[Dict[str, Any]] = []
    for row in profile_sheet.rows:
        if _cell(row, profile_trip_idx) != trip_id:
            continue
        client_id = _cell(row, client_id_idx)
        client = {
            "client_id": client_id,
            "last_name": _cell(row, last_idx),
            "first_name": _cell(row, first_idx),
            "amount": _cell(row, amount_idx),
            "contacts": [],
        }
        for contact in contacts_sheet.rows:
            if _cell(contact, contacts_trip_idx) != trip_id:
                continue
            if client_id and _cell(contact, contact_client_idx) not in ("", client_id):
                continue
            entry = {
                "phone": _cell(contact, phone_idx),
                "email": _cell(contact, email_idx),
            }
            client["contacts"].append(entry)
        clients.append(client)
    return clients


def _cell(row: List[Any], idx: Optional[int]) -> str:
    value = _raw_cell(row, idx)
    if value is None:
        return ""
    return str(value).strip()


def _raw_cell(row: List[Any], idx: Optional[int]) -> Any:
    if idx is None:
        return ""
    if idx >= len(row):
        return ""
    return row[idx]
