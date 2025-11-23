# tools.py
import requests
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import dateparser
from datetime import datetime

BASE_URL = "http://localhost:8000/"

# Pydantic models for structured tool inputs
class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the new task.")
    notes: Optional[str] = Field(None, description="Additional notes for the task.")
    due_date: Optional[str] = Field(None, description="The due date of the task in YYYY-MM-DD format.")

class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The unique ID of the task to update.")
    title: Optional[str] = Field(None, description="The new title of the task.")
    notes: Optional[str] = Field(None, description="New notes for the task.")
    status: Optional[str] = Field(None, description="The status of the task. Can be 'needsAction' or 'completed'.")
    due_date: Optional[str] = Field(None, description="The new due date in YYYY-MM-DD format.")

class DeleteTaskInput(BaseModel):
    task_id: str = Field(description="The unique ID of the task to delete.")

class ListTasksInput(BaseModel):
    due_date: Optional[str] = Field(None, description="Optional due date to filter tasks by in YYYY-MM-DD format.")
    
class SearchTasksInput(BaseModel):
    query: str = Field(description="A query string to search for in task titles.")
    due_date: Optional[str] = Field(None, description="Optional due date to filter tasks by in YYYY-MM-DD format.")

class ReadTaskInput(BaseModel):
    task_id: str = Field(description="The unique ID of the task to read.")

class ParseDateInput(BaseModel):
    date_string: str = Field(description="A natural language date string, e.g., 'tomorrow', 'next week', 'in 2 weeks'.")


# Functions that wrap your API calls
def create_task(title: str, notes: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new Google Task."""
    response = requests.post(
        f"{BASE_URL}/tasks",
        json={"title": title, "notes": notes, "due_date": due_date}
    )
    response.raise_for_status()
    return response.json()

def update_task(task_id: str, title: Optional[str] = None, notes: Optional[str] = None, status: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Updates an existing Google Task."""
    response = requests.patch(
        f"{BASE_URL}/tasks/{task_id}",
        json={"title": title, "notes": notes, "status": status, "due_date": due_date}
    )
    response.raise_for_status()
    return response.json()

def delete_task(task_id: str) -> Dict[str, Any]:
    """Deletes a Google Task."""
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()

def list_tasks(due_date: Optional[str] = None) -> Dict[str, Any]:
    """Lists all Google Tasks, optionally filtered by due date."""
    params = {"due_date": due_date} if due_date else {}
    response = requests.get(f"{BASE_URL}/tasks", params=params)
    response.raise_for_status()
    return response.json()

def search_tasks(query: str, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Searches for Google Tasks by title, optionally filtered by due date."""
    params = {"query": query, "due_date": due_date}
    response = requests.get(f"{BASE_URL}/tasks/search", params=params)
    response.raise_for_status()
    return response.json()

def read_task(task_id: str) -> Dict[str, Any]:
    """Reads a single Google Task by its ID."""
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()

def parse_date(date_string: str) -> Dict[str, Any]:
    """Parses a natural language date and returns it in YYYY-MM-DD format."""
    try:
        parsed_date = dateparser.parse(date_string)
        if parsed_date:
            return {"parsed_date": parsed_date.strftime("%Y-%m-%d")}
        else:
            return {"error": "Could not parse date string."}
    except Exception as e:
        return {"error": str(e)}