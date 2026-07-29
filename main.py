import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
from typing import Optional


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/taskdb")

def get_db():
    """Establishes a connection to PostgreSQL returning dictionary-like rows."""

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Stage 0: Creates tasks table and inserts seed data ONLY IF empty."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()['count']

    if count == 0:
        cursor.executemany("""
            INSERT INTO tasks (title, done) VALUES (%s, %s)
        """, [
            ("Buy groceries", False),
            ("Finish backend assignment", True),
            ("Clean the room", False)
        ])
        conn.commit()
        
    cursor.close()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Task API",
    description="A simple task management backend API using PostgreSQL for persistence.",
    version="1.0",
    lifespan=lifespan
)

class TaskPayload(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", summary="Root API Info")
def read_root():
    """Returns basic metadata and available routes for this API."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health", summary="Health Check")
def health_check():
    """Checks if the server is alive and functioning properly."""
    return {"status": "ok"}

@app.get("/tasks", summary="List All Tasks")
def get_tasks():
    """Fetches all tasks directly from the PostgreSQL database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks ORDER BY id ASC")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

@app.get("/tasks/{id}", summary="Get Single Task by ID")
def get_task(id: int):
    """Fetches a specific task by ID from the database. Returns 404 if not found."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail={"error": "Task not found"})
        
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.post("/tasks", status_code=status.HTTP_201_CREATED, summary="Create a New Task")
def create_task(payload: TaskPayload):
    """Inserts a new task into the PostgreSQL database."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Postgres uses RETURNING to get the ID of the newly inserted row
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id", 
        (payload.title.strip(), False)
    )
    new_id = cursor.fetchone()['id']
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return {"id": new_id, "title": payload.title.strip(), "done": False}

@app.put("/tasks/{id}", summary="Update a Task")
def update_task(id: int, payload: TaskPayload):
    """Updates an existing task in the database."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Task not found"})

    if payload.title is not None and not payload.title.strip():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    new_title = payload.title.strip() if payload.title is not None else existing["title"]
    new_done = payload.done if payload.done is not None else bool(existing["done"])
    
    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (new_title, new_done, id)
    )
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return {"id": id, "title": new_title, "done": new_done}

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Task")
def delete_task(id: int):
    """Deletes a task by ID from the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    deleted_count = cursor.rowcount
    conn.commit()
    
    cursor.close()
    conn.close()
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail={"error": "Task not found"})
        
    return Response(status_code=status.HTTP_204_NO_CONTENT)