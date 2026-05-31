# Product Requirements Document — TodoApp

## Overview

TodoApp is a multi-user web application that allows registered users to manage their personal task lists. It supports registration, login, and per-user todo management (add, delete, complete, filter). Built with FastHTML (Python + HTMX), MySQL, and Redis.

---

## Goals

- Allow many users to register and manage their own private todo lists.
- Persist tasks server-side in MySQL, scoped to the authenticated user.
- Use Redis as a session store to manage authenticated state.
- Serve as a learning project for production Python web app architecture.

## Non-Goals

- Social login (OAuth, Google, GitHub).
- Shared or collaborative task lists.
- Admin panel or cross-user visibility.
- Mobile app or JS framework (React, Vue, etc.).
- Real-time sync or WebSockets.
- Due dates, priorities, tags, or subtasks.

---

## Users

One user type: **registered user**.

| Action | Authenticated? |
|---|---|
| Register | No |
| Log in | No |
| View own task list | Yes |
| Add a task | Yes |
| Delete a task | Yes |
| Mark a task complete / incomplete | Yes |
| Filter tasks by status | Yes |
| Log out | Yes |

---

## Functional Requirements

### Registration

- User submits email + password via `/register`.
- Email must be unique; duplicate returns an error message.
- Password is hashed with bcrypt before storage (never stored in plaintext).
- On success, session is created and user is redirected to `/todos`.

### Login

- User submits email + password via `/login`.
- Invalid credentials return a generic error (no user enumeration).
- On success, session is created and user is redirected to `/todos`.

### Logout

- POST to `/logout` clears the Redis session and cookie.
- User is redirected to `/login`.

### Session Management

- Sessions are stored in Redis as a JSON dict keyed by a UUID cookie.
- Sessions expire after 30 minutes of inactivity (TTL refreshed on each request).
- Any request to a protected route without a valid session redirects to `/login`.

### Add Task

- User types text and submits. Empty/whitespace-only input is rejected.
- Task is saved to MySQL linked to the authenticated user.
- Page updates via HTMX partial — no full reload.

### Delete Task

- Clicking delete removes the task from MySQL.
- Only the owning user can delete their own tasks (enforced server-side).
- Page updates via HTMX partial.

### Toggle Complete

- Checkbox toggles `completed` boolean in MySQL.
- Completed tasks are visually distinguished (strikethrough).
- Page updates via HTMX partial.

### Filter Tasks

- Three filters: **All**, **Active**, **Completed** (query param `?filter=`).
- Filter state is preserved in the URL, not localStorage.

---

## Non-Functional Requirements

| Concern | Requirement |
|---|---|
| Auth security | Passwords hashed with bcrypt; sessions use random UUIDs |
| Data isolation | All queries filter by authenticated `user_id` |
| Session expiry | 30-minute Redis TTL, refreshed per request |
| Config | Connection details via `.env` file (never hardcoded) |
| Schema | Managed via plain `schema.sql`, run once on setup |

---

## Data Model

### `users`

| Field | Type | Description |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `email` | VARCHAR(255) UNIQUE | Login identifier |
| `password_hash` | VARCHAR(255) | bcrypt hash |
| `created_at` | TIMESTAMP | Account creation time |

### `todos`

| Field | Type | Description |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `user_id` | INT FK → users.id | Owner |
| `text` | VARCHAR(500) | Task description |
| `completed` | BOOLEAN | Completion state |
| `created_at` | TIMESTAMP | Creation time |

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| Web framework | FastHTML |
| Frontend interactivity | HTMX (via FastHTML) |
| Database | MySQL (PyMySQL driver) |
| Session store | Redis |
| Password hashing | passlib[bcrypt] |
| Config | python-dotenv |

---

## File Structure

```
todoapp/
├── schema.sql        # DB initialization
├── .env              # Local config (gitignored)
├── .env.example      # Config template
├── requirements.txt
├── session.py        # Redis session layer
├── db.py             # MySQL connection helpers
├── auth.py           # Password hash/verify
└── app.py            # Routes and app entry point
```
