# Product Requirements Document — TodoApp

## Overview

TodoApp is a single-page web application that allows a user to manage a personal task list. It supports adding, deleting, and completing tasks, with filtering by status and automatic persistence across page reloads. The project is designed as a learning exercise covering DOM manipulation, browser events, localStorage, and basic CRUD operations.

---

## Goals

- Provide a clean, functional task list a user can manage entirely in the browser.
- Persist tasks across sessions without a server or database.
- Serve as a self-contained teaching project for front-end fundamentals.

## Non-Goals

- User accounts, authentication, or any server-side logic.
- Multi-user or collaborative task lists.
- Backend API or database.
- Mobile app or framework-based implementation (React, Vue, etc.).
- Real-time sync or offline-first PWA features.

---

## Users

A single user type: **anonymous user** (no login required).

| Action | Authenticated? |
|---|---|
| View task list | No |
| Add a task | No |
| Delete a task | No |
| Mark a task complete / incomplete | No |
| Filter tasks by status | No |

---

## Functional Requirements

### Add Task

- User types text into an input field and submits (button click or Enter key).
- Input must not be empty or whitespace-only; submission is ignored if so.
- A new task is appended to the list and saved to localStorage immediately.
- The input field is cleared after a successful add.

### Delete Task

- Each task has a delete button visible on hover or at all times.
- Clicking delete removes the task from the list and from localStorage.
- No confirmation dialog is required.

### Toggle Complete

- Each task has a checkbox or click target that marks it complete or incomplete.
- Completed tasks are visually distinguished (e.g., strikethrough text, muted color).
- State change is persisted to localStorage immediately.

### Filter Tasks

- Three filter options are available: **All**, **Active**, **Completed**.
- **All** shows every task regardless of status.
- **Active** shows only tasks where `completed` is `false`.
- **Completed** shows only tasks where `completed` is `true`.
- The active filter persists across page reloads (stored in localStorage).
- The task count displayed reflects the current filter.

### Persistence

- All tasks are stored in `localStorage` under a single key (`tasks`).
- On page load, tasks are read from localStorage and rendered into the DOM.
- Any mutation (add, delete, toggle) writes the full updated array back to localStorage.

---

## Non-Functional Requirements

| Concern | Requirement |
|---|---|
| Persistence | All data stored client-side in `localStorage`; no network requests. |
| Compatibility | Must work in modern evergreen browsers (Chrome, Firefox, Safari, Edge). |
| Accessibility | Task items use semantic HTML; checkbox inputs have associated labels. |
| Performance | All operations (add, delete, toggle, filter) must feel instantaneous — no async required. |
| Dependencies | Zero external libraries or build tools; plain HTML/CSS/JS only. |

---

## Data Model Summary

Tasks are stored in `localStorage` as a JSON-serialized array under the key `"tasks"`. Each task is a plain object:

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (e.g., `Date.now().toString()`) |
| `text` | string | The task description entered by the user |
| `completed` | boolean | Whether the task has been marked done |
| `createdAt` | string | ISO 8601 timestamp of when the task was added |

---

## Tech Stack

| Component | Technology |
|---|---|
| Markup | HTML5 |
| Styles | CSS3 |
| Logic | Vanilla JavaScript (ES6+) |
| Persistence | Browser `localStorage` API |

---

## File Structure

```
todoapp/
├── index.html   # App shell and static markup
├── style.css    # All visual styles
└── app.js       # All application logic (task state, DOM updates, events)
```

---

## Out of Scope (Future Considerations)

- User accounts or login.
- Server-side storage or API.
- Due dates, priorities, or task categories.
- Subtasks or nested lists.
- Drag-and-drop reordering.
- Bulk actions (delete all completed, check all).
- Search or text filtering within the task list.
