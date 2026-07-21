from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional

app = FastAPI(    title="Task API",
    description="A simple task management backend API built for FlyRank BE-01.",
    version="1.0")

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish backend assignment", "done": True},
    {"id": 3, "title": "Clean the room", "done": False},
]

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
    """Fetches the full list of in-memory tasks."""
    return tasks

@app.get("/tasks/{id}", summary="Get Single Task by ID")
def get_task(id: int):
    """Fetches a specific task using its numeric ID. Returns 404 if not found."""
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@app.post("/tasks", status_code=201, summary="Create a New Task")
def create_task(payload: TaskPayload):
    """Creates a new task with an automatically assigned ID and default status of done=False."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    new_id = max([t["id"] for t in tasks], default=0) + 1
    new_task = {"id": new_id, "title": payload.title, "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{id}", summary="Update a Task")
def update_task(id: int, payload: TaskPayload):
    """Updates an existing task's title or completion status."""
    for task in tasks:
        if task["id"] == id:
            if payload.title is not None and not payload.title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            
            if payload.title is not None:
                task["title"] = payload.title
            if payload.done is not None:
                task["done"] = payload.done
            return task
            
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=204, summary="Delete a Task")
def delete_task(id: int):
    """Deletes a task by ID and returns a 204 No Content response."""
    global tasks
    initial_length = len(tasks)
    tasks = [t for t in tasks if t["id"] != id]
    
    if len(tasks) == initial_length:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
        
    return Response(status_code=204)