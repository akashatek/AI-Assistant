# api.py
from fastapi import FastAPI, HTTPException, Body, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from google_tasks import GoogleTasks

# Initialize FastAPI app
app = FastAPI(title="Google Tasks API")

# Initialize Google Tasks service
google_tasks_tool = GoogleTasks()

# Pydantic Models for request body validation
class TaskCreate(BaseModel):
    title: str
    notes: Optional[str] = None
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    
# Root endpoint
@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Google Tasks API is running."}

# --- Tasks Endpoints ---


@app.post("/tasks", tags=["Tasks"])
def create_task(task: TaskCreate):
    """
    Create a new task.
    """
    result = google_tasks_tool.create_task(
        title=task.title, notes=task.notes, due_date=task.due_date
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/tasks", tags=["Tasks"])
def list_tasks(due_date: Optional[str] = Query(None)):
    """
    List all tasks, optionally filtered by due date.
    """
    # The Google Tasks API requires a timezone offset for due dates
    # We will pass the date as is and let the API handle the timezone.
    result = google_tasks_tool.list_tasks(due_date=due_date)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/tasks/search", tags=["Tasks"])
def search_tasks(query: str = Query(...), due_date: Optional[str] = Query(None)):
    """
    Search for tasks by title and an optional due date.
    """
    result = google_tasks_tool.search_tasks(query=query, due_date=due_date)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/tasks/{task_id}", tags=["Tasks"])
def read_task(task_id: str):
    """
    Read a single task by its ID.
    """
    result = google_tasks_tool.get_task_by_id(task_id=task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.patch("/tasks/{task_id}", tags=["Tasks"])
def update_task(task_id: str, task: TaskUpdate):
    """
    Update a task.
    """
    update_data = task.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
        
    result = google_tasks_tool.update_task(task_id=task_id, **update_data)
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
        raise HTTPException(status_code=500, detail=result["error"]) # This handles the error case
    return result # This returns a 200 on success