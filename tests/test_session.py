import json
from unittest.mock import MagicMock, patch
from session import get_session, set_session, clear_session


def test_get_session_no_cookie():
    req = MagicMock()
    req.cookies.get.return_value = None
    assert get_session(req) is None


def test_get_session_missing_redis_key():
    req = MagicMock()
    req.cookies.get.return_value = "some-sid"
    with patch("session._r") as mock_r:
        mock_r.return_value.get.return_value = None
        assert get_session(req) is None


def test_get_session_valid_returns_data():
    req = MagicMock()
    req.cookies.get.return_value = "valid-sid"
    payload = {"user_id": 1, "email": "a@b.com"}
    with patch("session._r") as mock_r:
        mock_r.return_value.get.return_value = json.dumps(payload)
        result = get_session(req)
    assert result == payload


def test_get_session_refreshes_ttl():
    req = MagicMock()
    req.cookies.get.return_value = "valid-sid"
    with patch("session._r") as mock_r:
        mock_r.return_value.get.return_value = json.dumps({"user_id": 1})
        get_session(req)
        mock_r.return_value.expire.assert_called_once_with("session:valid-sid", 1800)


def test_set_session_writes_to_redis_and_sets_cookie():
    resp = MagicMock()
    with patch("session._r") as mock_r:
        sid = set_session(resp, {"user_id": 1, "email": "a@b.com"})
    assert sid  # non-empty UUID
    mock_r.return_value.set.assert_called_once()
    resp.set_cookie.assert_called_once()


def test_clear_session_deletes_redis_key_and_cookie():
    req = MagicMock()
    req.cookies.get.return_value = "del-sid"
    resp = MagicMock()
    with patch("session._r") as mock_r:
        clear_session(req, resp)
        mock_r.return_value.delete.assert_called_once_with("session:del-sid")
    resp.delete_cookie.assert_called_once()


def test_clear_session_no_cookie_does_not_crash():
    req = MagicMock()
    req.cookies.get.return_value = None
    resp = MagicMock()
    with patch("session._r") as mock_r:
        clear_session(req, resp)
        mock_r.return_value.delete.assert_not_called()
    resp.delete_cookie.assert_called_once()
