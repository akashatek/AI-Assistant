# task_tools.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import dateparser
from datetime import datetime

# --- Pydantic Models for Structured Tool Inputs ---
class CreateTaskInput(BaseModel):
    title: str = Field(description="The title of the new task.")
    notes: Optional[str] = Field(None, description="Additional notes for the task.")
    due_date: Optional[str] = Field(None, description="The due date of the task in YYYY-MM-DD format.")

class UpdateTaskInput(BaseModel):
    task_id: str = Field(description="The unique ID of the task to update.")
    title: Optional[str] = Field(None, description="The new title of the task.")
    notes: Optional[str] = Field(None, description="New notes for the task.")
    status: Optional[str] = Field(None, description="The status of the task. Must be 'needsAction' or 'completed'. The LLM must map user input (e.g., 'on going') to these values.")
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

# --- Utility Function ---
def parse_date(date_string: str) -> Dict[str, Any]:
    """Parses a natural language date and returns it in YYYY-MM-DD format."""
    try:
        # dateparser attempts to parse the date
        parsed_date = dateparser.parse(date_string)
        if parsed_date:
            # Format the parsed date to YYYY-MM-DD string
            return {"date": parsed_date.strftime("%Y-%m-%d")}
        else:
            return {"error": f"Could not parse date string: {date_string}"}
    except Exception as e:
        return {"error": f"An error occurred during date parsing: {e}"}

# We initialize the GoogleTasks client here, outside the agent, to pass its methods as tools
# Note: google_tasks.py must be in the same folder.
from google_tasks import GoogleTasks
google_tasks_client = GoogleTasks(creds_path="credentials.json")