import json
import uuid
import redis
import os
from dotenv import load_dotenv

load_dotenv()

SESSION_TTL = 1800
COOKIE_NAME = "session_id"


def _r():
    return redis.from_url(os.environ["REDIS_URL"])


def get_session(request) -> dict | None:
    sid = request.cookies.get(COOKIE_NAME)
    if not sid:
        return None
    r = _r()
    data = r.get(f"session:{sid}")
    if not data:
        return None
    r.expire(f"session:{sid}", SESSION_TTL)
    return json.loads(data)


def set_session(response, data: dict) -> str:
    sid = str(uuid.uuid4())
    _r().setex(f"session:{sid}", SESSION_TTL, json.dumps(data))
    response.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
    return sid


def clear_session(request, response) -> None:
    sid = request.cookies.get(COOKIE_NAME)
    if sid:
        _r().delete(f"session:{sid}")
    response.delete_cookie(COOKIE_NAME)
