# task_tools.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import dateparser
from datetime import datetime

# Import GoogleTasks client
from google_tasks import GoogleTasks

# --- Pydantic Models for Structured Tool Inputs ---
class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the new task.")
    notes: Optional[str] = Field(None, description="Additional notes for the task.")
    due_date: Optional[str] = Field(None, description="The due date of the task in YYYY-MM-DD format.")

class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The unique ID of the task to update.")
    title: Optional[str] = Field(None, description="The new title of the task.")
    notes: Optional[str] = Field(None, description="New notes for the task.")
    status: Optional[str] = Field(None, description="The status of the task. Must be 'needsAction' or 'completed'.")
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
    date_string: str = Field(description="A natural language date string, like 'tomorrow' or 'next Tuesday'.")

# --- Initialize GoogleTasks Client ---
# NOTE: Ensure credentials.json exists and is in the same directory.
google_tasks_client = GoogleTasks(creds_path="credentials.json")

# --- Wrapper Functions (The Fix) ---

def task_create_wrapper(title: str, notes: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for creating a task."""
    return google_tasks_client.create_task(title=title, notes=notes, due_date=due_date)

def task_update_wrapper(task_id: str, title: Optional[str] = None, notes: Optional[str] = None, status: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for updating a task."""
    return google_tasks_client.update_task(task_id=task_id, title=title, notes=notes, status=status, due_date=due_date)

def task_delete_wrapper(task_id: str) -> Dict[str, Any]:
    """Wrapper for deleting a task."""
    return google_tasks_client.delete_task(task_id=task_id)

def task_list_wrapper(due_date: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for listing tasks."""
    return google_tasks_client.list_tasks(due_date=due_date)

def task_search_wrapper(query: str, due_date: Optional[str] = None) -> Dict[str, Any]:
    """Wrapper for searching tasks."""
    # Assuming the method name is search_tasks in your google_tasks.py
    return google_tasks_client.search_tasks(query=query, due_date=due_date)

def task_read_wrapper(task_id: str) -> Dict[str, Any]:
    """Wrapper for reading a single task."""
    return google_tasks_client.get_task_by_id(task_id=task_id)

def parse_date_wrapper(date_string: str) -> Dict[str, Any]:
    """Parses a natural language date and returns it in YYYY-MM-DD format."""
    try:
        parsed_date = dateparser.parse(date_string)
        if parsed_date:
            return {"date": parsed_date.strftime("%Y-%m-%d")}
        else:
            return {"error": f"Could not parse date string: {date_string}"}
    except Exception as e:
        return {"error": f"An error occurred during date parsing: {e}"}