# api.py
from fastapi import FastAPI, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional
from google_tasks import GoogleTasks

# Define Pydantic models for request bodies
class CreateTaskRequest(BaseModel):
    title: str
    notes: Optional[str] = None
    due_date: Optional[str] = None

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None

# Main FastAPI application instance
app = FastAPI(
    title="Google Tasks API",
    description="A simple RESTful API for managing Google Tasks.",
    version="1.0.0"
)

# Initialize the Google Tasks service
google_tasks_tool = GoogleTasks()

# API Endpoints
@app.get("/tasks", tags=["Tasks"])
def list_tasks(due_date: Optional[str] = None):
    """
    List all tasks from the default list, with optional filtering by due date.
    """
    result = google_tasks_tool.list_all_tasks(due_date)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/tasks", tags=["Tasks"])
def create_task(task_data: CreateTaskRequest = Body(...)):
    """
    Create a new task.
    """
    result = google_tasks_tool.create_task(
        title=task_data.title,
        notes=task_data.notes,
        due_date=task_data.due_date
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.patch("/tasks/{task_id}", tags=["Tasks"])
def update_task(task_id: str, task_data: UpdateTaskRequest = Body(...)):
    """
    Update a task's details.
    """
    result = google_tasks_tool.update_task(
        task_id=task_id,
        title=task_data.title,
        notes=task_data.notes,
        status=task_data.status,
        due_date=task_data.due_date
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: str):
    """
    Delete a task.
    """
    result = google_tasks_tool.delete_task(task_id=task_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/tasks/search", tags=["Tasks"])
def search_tasks(query: str, due_date: Optional[str] = None):
    """
    Search for tasks by title within the default list, with optional filtering.
    """
    result = google_tasks_tool.search_tasks_by_title(query, due_date)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the simple Google Tasks API! Go to /docs for the API reference."}