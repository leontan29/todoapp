import pytest
from tests.conftest import todo_ids


# --- auth pages ---

def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Log In" in r.text


def test_register_page(client):
    r = client.get("/register")
    assert r.status_code == 200
    assert "Create Account" in r.text


def test_root_redirects_to_login_when_unauthenticated(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["location"]


def test_root_redirects_to_todos_when_authenticated(auth_client):
    r = auth_client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/todos" in r.headers["location"]


# --- register ---

def test_register_success_redirects_to_todos(client):
    r = client.post("/register",
                    data={"email": "new@example.com", "password": "pass"},
                    follow_redirects=False)
    assert r.status_code == 302
    assert "/todos" in r.headers["location"]


def test_register_sets_session_cookie(client):
    r = client.post("/register",
                    data={"email": "new@example.com", "password": "pass"},
                    follow_redirects=False)
    assert "session_id" in r.cookies


def test_register_duplicate_email_returns_error(client):
    client.post("/register", data={"email": "dup@example.com", "password": "pass"})
    # Fresh client — no session
    from starlette.testclient import TestClient
    from app import app
    c2 = TestClient(app, raise_server_exceptions=True)
    r = c2.post("/register", data={"email": "dup@example.com", "password": "other"})
    assert r.status_code == 200
    assert "already exists" in r.text


def test_register_missing_fields_returns_error(client):
    r = client.post("/register", data={"email": "", "password": ""})
    assert "required" in r.text


# --- login ---

def test_login_success_redirects(client):
    client.post("/register", data={"email": "u@example.com", "password": "mypass"})
    client.post("/logout")
    r = client.post("/login",
                    data={"email": "u@example.com", "password": "mypass"},
                    follow_redirects=False)
    assert r.status_code == 302
    assert "/todos" in r.headers["location"]


def test_login_wrong_password(client):
    client.post("/register", data={"email": "u@example.com", "password": "mypass"})
    client.post("/logout")
    r = client.post("/login", data={"email": "u@example.com", "password": "wrong"})
    assert r.status_code == 200
    assert "Invalid email or password" in r.text


def test_login_unknown_email(client):
    r = client.post("/login", data={"email": "nobody@example.com", "password": "x"})
    assert "Invalid email or password" in r.text


# --- logout ---

def test_logout_clears_session(auth_client):
    auth_client.post("/logout")
    r = auth_client.get("/todos", follow_redirects=False)
    assert r.status_code == 302


# --- todos page ---

def test_todos_requires_auth(client):
    r = client.get("/todos", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["location"]


def test_todos_page_loads(auth_client):
    r = auth_client.get("/todos")
    assert r.status_code == 200
    assert "todos" in r.text


def test_todos_page_shows_user_email(auth_client):
    r = auth_client.get("/todos")
    assert "test@example.com" in r.text


# --- add todo ---

def test_add_todo_appears_in_list(auth_client):
    r = auth_client.post("/todos", data={"text": "Buy milk", "filter": "all"})
    assert r.status_code == 200
    assert "Buy milk" in r.text


def test_add_todo_empty_text_ignored(auth_client):
    r = auth_client.post("/todos", data={"text": "   ", "filter": "all"})
    assert r.status_code == 200
    assert r.text.count('data-id=') == 0


def test_add_todo_whitespace_only_ignored(auth_client):
    r = auth_client.post("/todos", data={"text": "\t\n", "filter": "all"})
    assert r.text.count('data-id=') == 0


# --- delete todo ---

def test_delete_todo_removes_it(auth_client):
    auth_client.post("/todos", data={"text": "Delete me", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)
    assert len(ids) == 1

    r = auth_client.delete(f"/todos/{ids[0]}")
    assert r.status_code == 200
    assert "Delete me" not in r.text


def test_delete_todo_only_removes_target(auth_client):
    auth_client.post("/todos", data={"text": "Keep me", "filter": "all"})
    auth_client.post("/todos", data={"text": "Delete me", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)

    auth_client.delete(f"/todos/{ids[1]}")
    r = auth_client.get("/todos")
    assert "Keep me" in r.text
    assert "Delete me" not in r.text


def test_cannot_delete_other_users_todo(client):
    # User A adds a todo
    client.post("/register", data={"email": "a@example.com", "password": "pass"})
    client.post("/todos", data={"text": "User A task", "filter": "all"})
    r = client.get("/todos")
    ids = todo_ids(r.text)
    todo_id = ids[0]
    client.post("/logout")

    # User B tries to delete it
    from starlette.testclient import TestClient
    from app import app
    c2 = TestClient(app, raise_server_exceptions=True)
    c2.post("/register", data={"email": "b@example.com", "password": "pass"})
    r = c2.delete(f"/todos/{todo_id}")
    assert r.status_code == 200

    # User A's todo should still be there
    client.post("/login", data={"email": "a@example.com", "password": "pass"})
    r = client.get("/todos")
    assert "User A task" in r.text


# --- toggle complete ---

def test_toggle_marks_todo_complete(auth_client):
    auth_client.post("/todos", data={"text": "Finish me", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)

    r = auth_client.patch(f"/todos/{ids[0]}", data={"filter": "all"})
    assert r.status_code == 200
    assert 'class="completed"' in r.text


def test_toggle_twice_restores_incomplete(auth_client):
    auth_client.post("/todos", data={"text": "Toggle me", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)

    auth_client.patch(f"/todos/{ids[0]}", data={"filter": "all"})
    r = auth_client.patch(f"/todos/{ids[0]}", data={"filter": "all"})
    assert 'class=""' in r.text or 'class="completed"' not in r.text


def test_cannot_toggle_other_users_todo(client):
    client.post("/register", data={"email": "a@example.com", "password": "pass"})
    client.post("/todos", data={"text": "A task", "filter": "all"})
    r = client.get("/todos")
    todo_id = todo_ids(r.text)[0]
    client.post("/logout")

    from starlette.testclient import TestClient
    from app import app
    c2 = TestClient(app, raise_server_exceptions=True)
    c2.post("/register", data={"email": "b@example.com", "password": "pass"})
    c2.patch(f"/todos/{todo_id}", data={"filter": "all"})

    # Verify A's todo is still not completed
    client.post("/login", data={"email": "a@example.com", "password": "pass"})
    r = client.get("/todos")
    assert 'class="completed"' not in r.text


# --- filter ---

def test_filter_active_hides_completed(auth_client):
    auth_client.post("/todos", data={"text": "Active task", "filter": "all"})
    auth_client.post("/todos", data={"text": "Done task", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)
    auth_client.patch(f"/todos/{ids[1]}", data={"filter": "all"})

    r = auth_client.get("/todos?filter=active")
    assert "Active task" in r.text
    assert "Done task" not in r.text


def test_filter_completed_hides_active(auth_client):
    auth_client.post("/todos", data={"text": "Active task", "filter": "all"})
    auth_client.post("/todos", data={"text": "Done task", "filter": "all"})
    r = auth_client.get("/todos")
    ids = todo_ids(r.text)
    auth_client.patch(f"/todos/{ids[1]}", data={"filter": "all"})

    r = auth_client.get("/todos?filter=completed")
    assert "Done task" in r.text
    assert "Active task" not in r.text


def test_filter_invalid_value_defaults_to_all(auth_client):
    auth_client.post("/todos", data={"text": "A task", "filter": "all"})
    r = auth_client.get("/todos?filter=garbage")
    assert r.status_code == 200
    assert "A task" in r.text


# --- data isolation ---

def test_users_cannot_see_each_others_todos(client):
    client.post("/register", data={"email": "a@example.com", "password": "pass"})
    client.post("/todos", data={"text": "Secret A", "filter": "all"})
    client.post("/logout")

    from starlette.testclient import TestClient
    from app import app
    c2 = TestClient(app, raise_server_exceptions=True)
    c2.post("/register", data={"email": "b@example.com", "password": "pass"})
    r = c2.get("/todos")
    assert "Secret A" not in r.text
