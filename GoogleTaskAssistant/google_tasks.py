# google_tasks.py
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from typing import Optional, Dict, Any

SCOPES = ["https://www.googleapis.com/auth/tasks"]

class GoogleTasks:
    def __init__(self, token_path="token.json", creds_path="credentials.json"):
        self.token_path = token_path
        self.creds_path = creds_path
        self.service = self._authenticate_google_tasks()
        self.default_tasklist_id = self._get_default_tasklist_id()
        
    def _authenticate_google_tasks(self):
        """Authenticates and returns the Google Tasks API service."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    print(f"Error: {self.creds_path} not found.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        try:
            service = build("tasks", "v1", credentials=creds)
            print("Successfully authenticated with the Google Tasks API.")
            return service
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def _get_default_tasklist_id(self) -> Optional[str]:
        """Retrieves the ID of the default task list."""
        if not self.service:
            print("Failed to get default task list ID. Service not available.")
            return None
        try:
            results = self.service.tasklists().list().execute()
            items = results.get("items", [])
            if not items:
                print("No task lists found. Cannot determine default ID.")
                return None
            return items[0]['id']
        except HttpError as error:
            print(f"An error occurred while getting task lists: {error}")
            return None

    def create_task(self, title: str, notes: Optional[str], due_date: Optional[str]) -> Dict[str, Any]:
        """Creates a new task."""
        if not self.service or not self.default_tasklist_id:
            return {"error": "Failed to create task. Service or default task list not available."}
        
        task = {"title": title}
        if notes:
            task["notes"] = notes
        
        if due_date:
            try:
                # Convert YYYY-MM-DD to ISO format required by the API
                dt_object = datetime.strptime(due_date, "%Y-%m-%d")
                # Add a time part (00:00:00) and convert to Zulu time 'Z'
                task['due'] = dt_object.isoformat() + '.000Z'
            except ValueError:
                return {"error": "Invalid date format. Please use YYYY-MM-DD."}

        try:
            new_task = self.service.tasks().insert(
                tasklist=self.default_tasklist_id, body=task
            ).execute()
            return {"message": "Task created successfully.", "task": new_task}
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Updates a Google Task. Only provided fields are updated."""
        if not self.service or not self.default_tasklist_id:
            return {"error": "Service or default task list not available."}

        update_body = {}
        if title is not None:
            update_body['title'] = title
        if notes is not None:
            update_body['notes'] = notes
        if status is not None:
            update_body['status'] = status
        if due_date is not None:
            # Convert YYYY-MM-DD to ISO format for the 'due' field
            try:
                dt_object = datetime.strptime(due_date, "%Y-%m-%d")
                update_body['due'] = dt_object.isoformat() + '.000Z'
            except ValueError:
                return {"error": "Invalid date format for due date. Please use YYYY-MM-DD."}

        if not update_body:
            return {"warning": "No fields provided to update."}
        
        try:
            # Use patch() for partial updates
            updated_task = self.service.tasks().patch(
                tasklist=self.default_tasklist_id,
                task=task_id,
                body=update_body
            ).execute()
            return {"message": f"Task {task_id} updated successfully.", "task": updated_task}
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}


    def list_tasks(self, due_date: Optional[str]) -> Dict[str, Any]:
        """Lists tasks, optionally filtered by due date."""
        tasks = self._list_all_raw_tasks()
        if "error" in tasks:
            return tasks

        filtered_tasks = tasks
        
        if due_date:
            try:
                # Convert input YYYY-MM-DD to a standard comparison string
                due_date_str = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                
                filtered_tasks = []
                for task in tasks:
                    if 'due' in task:
                        # Parse the ISO date from the task and compare
                        task_due_date = datetime.fromisoformat(task['due'].replace('Z', '')).strftime("%Y-%m-%d")
                        if task_due_date == due_date_str:
                            filtered_tasks.append(task)
                            
            except ValueError:
                return {"error": "Invalid date format for filtering. Please use YYYY-MM-DD."}
        
        return {"tasks": filtered_tasks}

    def _list_all_raw_tasks(self) -> Dict[str, Any]:
        """Internal method to fetch all tasks without filtering."""
        if not self.service or not self.default_tasklist_id:
            return {"error": "Failed to list tasks. Service or default task list not available."}
        
        try:
            results = self.service.tasks().list(tasklist=self.default_tasklist_id).execute()
            tasks = results.get("items", [])
            return tasks
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Deletes a task by ID."""
        if not self.service or not self.default_tasklist_id:
            return {"error": "Failed to delete task. Service or default task list not available."}
        
        try:
            self.service.tasks().delete(
                tasklist=self.default_tasklist_id, task=task_id
            ).execute()
            return {"message": f"Task {task_id} deleted successfully."}
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}

    def search_tasks(self, query: str, due_date: Optional[str]) -> Dict[str, Any]:
        """Searches for tasks by title, optionally filtered by due date."""
        tasks_result = self.list_tasks(due_date)
        if "error" in tasks_result:
            return tasks_result
        
        tasks = tasks_result.get("tasks", [])
        matching_tasks = [task for task in tasks if query.lower() in task.get('title', '').lower()]
        return {"tasks": matching_tasks}

    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """Retrieves a single task by its ID."""
        if not self.service or not self.default_tasklist_id:
            return {"error": "Failed to retrieve task. Service or default task list not available."}

        try:
            task = self.service.tasks().get(
                tasklist=self.default_tasklist_id, task=task_id
            ).execute()
            return {"task": task}
        except HttpError as error:
            if error.resp.status == 404:
                 return {"error": f"Task with ID {task_id} not found."}
            return {"error": f"An error occurred: {error}"}