"""The W2 Task API backed by Postgres (Flyrank W3 A3)."""

import os
from typing import Any

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Compose loads this from .env; fail early with a useful message when run directly.
    raise RuntimeError("DATABASE_URL is required. Copy .env.example to .env first.")

app = FastAPI(title="Task API", version="1.0")
SEED_TASKS = [
    ("Read the assignment brief", False),
    ("Build the API", False),
    ("Try Swagger UI", True),
]
CREATE_TASK_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string", "minLength": 1}},
            },
            "example": {"title": "Buy milk"},
        }
    },
}
UPDATE_TASK_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "minProperties": 1,
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "done": {"type": "boolean"},
                },
            },
            "example": {"done": True},
        }
    },
}


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


async def read_object(request: Request) -> tuple[dict[str, Any] | None, str | None]:
    # Reject malformed JSON before it can be used to build a database write.
    try:
        body = await request.json()
    except Exception:
        return None, "Request body must be valid JSON"
    if not isinstance(body, dict):
        return None, "Request body must be a JSON object"
    return body, None


@app.on_event("startup")
def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )"""
        )
        count = connection.execute("SELECT COUNT(*) AS count FROM tasks").fetchone()["count"]
        if count == 0:
            # Seed once; the named Docker volume keeps these rows through restarts.
            with connection.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)", SEED_TASKS
                )


@app.get("/", summary="Describe the Task API")
def root() -> dict[str, Any]:
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check API and database health")
def health():
    try:
        with connect() as connection:
            # A live API process is not enough; check that Postgres can answer too.
            connection.execute("SELECT 1")
    except psycopg.Error:
        return JSONResponse(status_code=503, content={"status": "error", "db": "unavailable"})
    return {"status": "ok", "db": "ok"}


@app.get("/tasks", summary="List tasks")
def list_tasks(done: bool | None = None, search: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT id, title, done FROM tasks"
    clauses: list[str] = []
    values: list[Any] = []
    if done is not None:
        clauses.append("done = %s")
        values.append(done)
    if search:
        clauses.append("title ILIKE %s")
        # `%s` placeholders keep the search term separate from the SQL command.
        values.append(f"%{search}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY id"
    with connect() as connection:
        rows = connection.execute(sql, values).fetchall()
    return rows


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    with connect() as connection:
        task = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()
    if task is None:
        return error("Task not found", 404)
    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    openapi_extra={"requestBody": CREATE_TASK_BODY},
)
async def create_task(request: Request):
    body, issue = await read_object(request)
    if issue:
        return error(issue, 400)
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return error("Field 'title' is required and must be a non-empty string", 400)
    with connect() as connection:
        task = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
            (title.strip(), False),
        ).fetchone()
    return JSONResponse(status_code=201, content=task)


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    openapi_extra={"requestBody": UPDATE_TASK_BODY},
)
async def update_task(task_id: int, request: Request):
    body, issue = await read_object(request)
    if issue:
        return error(issue, 400)
    if not body or not set(body).intersection({"title", "done"}):
        return error("Provide a non-empty 'title' and/or a boolean 'done'", 400)
    if "title" in body and (not isinstance(body["title"], str) or not body["title"].strip()):
        return error("Field 'title' must be a non-empty string", 400)
    if "done" in body and not isinstance(body["done"], bool):
        return error("Field 'done' must be a boolean", 400)

    with connect() as connection:
        current = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()
        if current is None:
            return error("Task not found", 404)
        title = body.get("title", current["title"])
        done = body.get("done", current["done"])
        task = connection.execute(
            """UPDATE tasks SET title = %s, done = %s WHERE id = %s
               RETURNING id, title, done""",
            (title.strip(), done, task_id),
        ).fetchone()
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    with connect() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        if cursor.rowcount == 0:
            return error("Task not found", 404)
    return Response(status_code=204)

