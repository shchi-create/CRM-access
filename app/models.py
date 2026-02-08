from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiRequest(BaseModel):
    action: str
    api_key: Optional[str] = Field(default=None, alias="api_key")
    surname: Optional[str] = None
    lastName: Optional[str] = None
    lastname: Optional[str] = None
    trip_id: Optional[str] = None
    tripId: Optional[str] = None
    trip: Optional[str] = None


class SearchResult(BaseModel):
    Trip_ID: str
    LastName: str
    FirstName: str
    destination: str
    startDate: str


class SearchResponse(BaseModel):
    status: str
    count: int
    results: List[SearchResult]
    textMessages: List[str]


class ErrorResponse(BaseModel):
    error: str
    status: str = "error"


class GetTripResponse(BaseModel):
    meta: Dict[str, Any]
    clients: List[Dict[str, Any]]
    trips: List[Dict[str, Any]]
    payments: Dict[str, Any]
