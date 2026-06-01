import os
from dotenv import load_dotenv

# Load base credentials from .env, then override DB/Redis for test isolation.
# Must happen before any app module is imported (load_dotenv won't override
# vars already set in the environment).
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ["DB_NAME"] = "todoapp_test"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/1"

import re
import pymysql
import pymysql.cursors
import redis
import pytest
from starlette.testclient import TestClient
from app import app


def _db_conn(database=None):
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def pytest_configure(config):
    """Apply schema to the test database once per session."""
    conn = _db_conn("todoapp_test")
    with conn.cursor() as cur:
        schema = open(os.path.join(os.path.dirname(__file__), "..", "schema.sql")).read()
        for stmt in schema.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
    conn.close()


@pytest.fixture(autouse=True)
def clean_db():
    conn = _db_conn("todoapp_test")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM todos")
        cur.execute("DELETE FROM users")
    conn.close()
    yield


@pytest.fixture(autouse=True)
def clean_redis():
    r = redis.from_url(os.environ["REDIS_URL"])
    r.flushdb()
    yield
    r.flushdb()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def auth_client(client):
    """A TestClient already logged in as test@example.com."""
    client.post("/register", data={"email": "test@example.com", "password": "password123"})
    return client


def todo_ids(html):
    """Extract todo IDs from rendered HTML data-id attributes."""
    return [int(i) for i in re.findall(r'data-id="(\d+)"', html)]
