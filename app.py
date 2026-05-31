from fasthtml.common import *
from starlette.responses import RedirectResponse
from db import get_db
from session import get_session, set_session, clear_session
from auth import hash_password, verify_password

app, rt = fast_app(sess_use_cookie=False)


# --- helpers ---

def require_session(request):
    user = get_session(request)
    if not user:
        raise HTTPException(status_code=302, headers={"location": "/login"})
    return user


def todo_item(t, filter_val):
    return Li(
        Label(
            Input(
                type="checkbox",
                checked=bool(t["completed"]),
                hx_patch=f"/todos/{t['id']}",
                hx_target="#todo-list",
                hx_swap="outerHTML",
            ),
            Span(t["text"], cls="completed" if t["completed"] else ""),
        ),
        Button(
            "×",
            hx_delete=f"/todos/{t['id']}",
            hx_target="#todo-list",
            hx_swap="outerHTML",
            hx_vals=f'{{"filter": "{filter_val}"}}',
            cls="delete-btn",
            aria_label="Delete task",
        ),
        hx_vals=f'{{"filter": "{filter_val}"}}',
        data_id=t["id"],
    )


def todo_list(todos, filter_val):
    items = [todo_item(t, filter_val) for t in todos]
    active_count = sum(1 for t in todos if not t["completed"])
    # fetch all todos count to distinguish empty filter vs empty list
    return Ul(*items, id="todo-list")


def auth_page(title, *content):
    return Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title(title),
            Style(CSS),
        ),
        Body(Div(*content, cls="container")),
    )


def app_page(email, todos, filter_val):
    active_count = sum(1 for t in todos if not t["completed"])
    shown = (
        [t for t in todos if not t["completed"]] if filter_val == "active"
        else [t for t in todos if t["completed"]] if filter_val == "completed"
        else todos
    )

    if len(shown) == 0:
        if len(todos) == 0:
            empty_msg = "No tasks yet."
        elif filter_val == "active":
            empty_msg = "No active tasks."
        else:
            empty_msg = "No completed tasks."
    else:
        empty_msg = None

    return Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("TodoApp"),
            Style(CSS),
        ),
        Body(
            Div(
                Div(
                    H1("todos"),
                    Span(f"({email})", cls="user-email"),
                    Form(
                        method="post", action="/logout",
                        style="display:inline",
                        children=[Button("Logout", type="submit", cls="logout-btn")]
                    ),
                    cls="header",
                ),
                Form(
                    Input(id="task-input", type="text", name="text",
                          placeholder="What needs to be done?", autocomplete="off"),
                    Button("Add", type="submit"),
                    hx_post="/todos",
                    hx_target="#todo-list",
                    hx_swap="outerHTML",
                    hx_vals=f'{{"filter": "{filter_val}"}}',
                    id="add-form",
                ),
                Div(
                    Button("All", data_filter="all",
                           cls="active" if filter_val == "all" else "",
                           onclick="location.href='/?filter=all'"),
                    Button("Active", data_filter="active",
                           cls="active" if filter_val == "active" else "",
                           onclick="location.href='/?filter=active'"),
                    Button("Completed", data_filter="completed",
                           cls="active" if filter_val == "completed" else "",
                           onclick="location.href='/?filter=completed'"),
                    cls="filters",
                ),
                Ul(*[todo_item(t, filter_val) for t in shown], id="todo-list"),
                P(empty_msg, id="empty-state", hidden=empty_msg is None),
                P(f"{active_count} item{'s' if active_count != 1 else ''} left",
                  id="task-count", hidden=len(todos) == 0),
                cls="container",
            )
        ),
    )


# --- routes ---

@rt("/")
def get(request):
    user = get_session(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/todos", status_code=302)


@rt("/register")
def get(request):
    return auth_page(
        "Register",
        H1("Create Account"),
        Form(
            Label("Email", Input(type="email", name="email", required=True)),
            Label("Password", Input(type="password", name="password", required=True)),
            Button("Register", type="submit"),
            method="post", action="/register",
        ),
        P(A("Already have an account? Log in", href="/login")),
    )


@rt("/register")
async def post(request):
    form = await request.form()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    if not email or not password:
        return auth_page("Register", P("Email and password are required.", cls="error"),
                         A("Back", href="/register"))
    with get_db() as db:
        db.execute("SELECT id FROM users WHERE email = %s", (email,))
        if db.fetchone():
            return auth_page("Register", P("An account with that email already exists.", cls="error"),
                             A("Back", href="/register"))
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, hash_password(password)),
        )
        db.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = db.fetchone()
    response = RedirectResponse("/todos", status_code=302)
    set_session(response, {"user_id": user["id"], "email": email})
    return response


@rt("/login")
def get(request):
    return auth_page(
        "Login",
        H1("Log In"),
        Form(
            Label("Email", Input(type="email", name="email", required=True)),
            Label("Password", Input(type="password", name="password", required=True)),
            Button("Log In", type="submit"),
            method="post", action="/login",
        ),
        P(A("No account? Register", href="/register")),
    )


@rt("/login")
async def post(request):
    form = await request.form()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    with get_db() as db:
        db.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
        user = db.fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return auth_page("Login", P("Invalid email or password.", cls="error"),
                         A("Back", href="/login"))
    response = RedirectResponse("/todos", status_code=302)
    set_session(response, {"user_id": user["id"], "email": email})
    return response


@rt("/logout")
async def post(request):
    response = RedirectResponse("/login", status_code=302)
    clear_session(request, response)
    return response


@rt("/todos")
def get(request):
    user = require_session(request)
    filter_val = request.query_params.get("filter", "all")
    if filter_val not in ("all", "active", "completed"):
        filter_val = "all"
    with get_db() as db:
        db.execute(
            "SELECT id, text, completed FROM todos WHERE user_id = %s ORDER BY created_at",
            (user["user_id"],),
        )
        todos = db.fetchall()
    return app_page(user["email"], todos, filter_val)


@rt("/todos")
async def post(request):
    user = require_session(request)
    form = await request.form()
    text = form.get("text", "").strip()
    filter_val = form.get("filter", "all")
    if filter_val not in ("all", "active", "completed"):
        filter_val = "all"
    if text:
        with get_db() as db:
            db.execute(
                "INSERT INTO todos (user_id, text) VALUES (%s, %s)",
                (user["user_id"], text),
            )
    with get_db() as db:
        db.execute(
            "SELECT id, text, completed FROM todos WHERE user_id = %s ORDER BY created_at",
            (user["user_id"],),
        )
        all_todos = db.fetchall()
    shown = (
        [t for t in all_todos if not t["completed"]] if filter_val == "active"
        else [t for t in all_todos if t["completed"]] if filter_val == "completed"
        else all_todos
    )
    return Ul(*[todo_item(t, filter_val) for t in shown], id="todo-list")


@rt("/todos/{todo_id}")
async def delete(request, todo_id: int):
    user = require_session(request)
    form = await request.form()
    filter_val = form.get("filter", "all")
    if filter_val not in ("all", "active", "completed"):
        filter_val = "all"
    with get_db() as db:
        db.execute(
            "DELETE FROM todos WHERE id = %s AND user_id = %s",
            (todo_id, user["user_id"]),
        )
        db.execute(
            "SELECT id, text, completed FROM todos WHERE user_id = %s ORDER BY created_at",
            (user["user_id"],),
        )
        all_todos = db.fetchall()
    shown = (
        [t for t in all_todos if not t["completed"]] if filter_val == "active"
        else [t for t in all_todos if t["completed"]] if filter_val == "completed"
        else all_todos
    )
    return Ul(*[todo_item(t, filter_val) for t in shown], id="todo-list")


@rt("/todos/{todo_id}")
async def patch(request, todo_id: int):
    user = require_session(request)
    form = await request.form()
    filter_val = form.get("filter", "all")
    if filter_val not in ("all", "active", "completed"):
        filter_val = "all"
    with get_db() as db:
        db.execute(
            "SELECT completed FROM todos WHERE id = %s AND user_id = %s",
            (todo_id, user["user_id"]),
        )
        row = db.fetchone()
        if row:
            db.execute(
                "UPDATE todos SET completed = %s WHERE id = %s AND user_id = %s",
                (not row["completed"], todo_id, user["user_id"]),
            )
        db.execute(
            "SELECT id, text, completed FROM todos WHERE user_id = %s ORDER BY created_at",
            (user["user_id"],),
        )
        all_todos = db.fetchall()
    shown = (
        [t for t in all_todos if not t["completed"]] if filter_val == "active"
        else [t for t in all_todos if t["completed"]] if filter_val == "completed"
        else all_todos
    )
    return Ul(*[todo_item(t, filter_val) for t in shown], id="todo-list")


# --- styles ---

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: sans-serif; background: #f5f5f5; color: #333; }
.container { max-width: 540px; margin: 60px auto; background: white;
             border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 32px; }
h1 { font-size: 2rem; font-weight: 700; margin-bottom: 20px; color: #444; }
.header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.user-email { font-size: 0.85rem; color: #999; flex: 1; }
.logout-btn { background: none; border: 1px solid #ddd; border-radius: 4px;
              padding: 4px 10px; cursor: pointer; font-size: 0.8rem; color: #777; }
.logout-btn:hover { background: #f0f0f0; }
#add-form { display: flex; gap: 8px; margin-bottom: 16px; }
#add-form input { flex: 1; padding: 10px 12px; border: 1px solid #ddd;
                  border-radius: 4px; font-size: 1rem; }
#add-form button { padding: 10px 18px; background: #5c6bc0; color: white;
                   border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
#add-form button:hover { background: #3949ab; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.filters button { padding: 6px 14px; border: 1px solid #ddd; border-radius: 4px;
                  background: white; cursor: pointer; font-size: 0.9rem; }
.filters button.active { border-color: #5c6bc0; color: #5c6bc0; }
#todo-list { list-style: none; }
#todo-list li { display: flex; align-items: center; padding: 12px 4px;
                border-bottom: 1px solid #f0f0f0; gap: 8px; }
#todo-list li label { display: flex; align-items: center; gap: 10px; flex: 1; cursor: pointer; }
#todo-list li input[type=checkbox] { width: 18px; height: 18px; cursor: pointer; }
.completed { text-decoration: line-through; color: #aaa; }
.delete-btn { background: none; border: none; color: #ccc; font-size: 1.3rem;
              cursor: pointer; padding: 0 4px; line-height: 1; }
.delete-btn:hover { color: #e57373; }
#empty-state { color: #aaa; font-style: italic; padding: 16px 0; text-align: center; }
#task-count { color: #aaa; font-size: 0.85rem; margin-top: 12px; text-align: right; }
form label { display: flex; flex-direction: column; gap: 4px; margin-bottom: 14px;
             font-size: 0.9rem; color: #555; }
form label input { padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px;
                   font-size: 1rem; }
form button[type=submit] { width: 100%; padding: 11px; background: #5c6bc0; color: white;
                           border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
form button[type=submit]:hover { background: #3949ab; }
.error { color: #e57373; margin-bottom: 12px; }
a { color: #5c6bc0; text-decoration: none; font-size: 0.9rem; }
a:hover { text-decoration: underline; }
p { margin-top: 12px; }
"""


serve(port=8080)
