from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_setup import get_logger
from app.models import ApiRequest
from app.search import get_trip, search_by_surname
from app.security import check_api_key, is_allowed_user, rate_limiter

router = APIRouter()


@router.post("/api")
async def handle_api(request: Request, payload: ApiRequest):
    logger = get_logger("api")
    header_key = request.headers.get(settings.x_api_key_header_name)
    api_key = payload.api_key or header_key
    if not check_api_key(api_key):
        raise HTTPException(status_code=401, detail="Unauthorized - invalid API key")

    user_id = request.headers.get("x-user-id")
    if not is_allowed_user(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    rate_key = f"api:{api_key}"
    if not rate_limiter.allow(rate_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    action = payload.action
    try:
        if action == "search":
            surname = payload.surname or payload.lastName or payload.lastname
            if not surname:
                raise HTTPException(status_code=400, detail="surname missing")
            result = search_by_surname(surname)
            logger.info(
                "action=search status=ok count=%s",
                result.get("count", 0),
            )
            return JSONResponse(result)
        if action == "get_trip":
            trip_id = payload.trip_id or payload.tripId or payload.trip
            if not trip_id:
                raise HTTPException(status_code=400, detail="trip_id missing")
            result = get_trip(trip_id)
            logger.info("action=get_trip status=ok")
            return JSONResponse(result)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("action=%s status=error", action)
        raise HTTPException(status_code=500, detail="internal error") from exc

    raise HTTPException(status_code=400, detail="unknown action")
