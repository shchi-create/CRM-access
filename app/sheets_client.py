import json
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings

READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


class SheetsClient:
    def __init__(self, spreadsheet_id: str, service_account_json: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.service_account_json = service_account_json
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service
        if not self.service_account_json:
            raise RuntimeError("service account json missing")
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        info = json.loads(self.service_account_json)
        creds = Credentials.from_service_account_info(info, scopes=[READONLY_SCOPE])
        self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return self._service

    def get_timezone(self) -> str:
        service = self._get_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        props = spreadsheet.get("properties", {})
        return props.get("timeZone", "UTC")

    def read_sheet(self, sheet_name: str) -> List[List[Any]]:
        service = self._get_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
            .execute()
        )
        values = result.get("values", [])
        return values


sheets_client = SheetsClient(settings.spreadsheet_id, settings.google_service_account_json)


def get_header_map(rows: List[List[Any]]) -> Tuple[List[str], List[List[Any]], Dict[str, int]]:
    if not rows:
        return [], [], {}
    headers = [str(h).strip() for h in rows[0]]
    data_rows = rows[1:]
    header_map: Dict[str, int] = {}
    for idx, header in enumerate(headers):
        normalized = normalize_header(header)
        if normalized:
            header_map[normalized] = idx
    return headers, data_rows, header_map


def normalize_header(value: str) -> str:
    raw = value.lower().strip()
    raw = raw.replace("_", " ")
    raw = " ".join(raw.split())
    return raw


def pick_header(header_map: Dict[str, int], options: List[str]) -> Optional[int]:
    for option in options:
        normalized = normalize_header(option)
        if normalized in header_map:
            return header_map[normalized]
    return None
