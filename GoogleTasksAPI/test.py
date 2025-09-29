# test.py
import unittest
import requests
import time

# The base URL for your running FastAPI service
BASE_URL = "http://localhost:8000"

class TestTaskAPI(unittest.TestCase):
    """
    Tests the CRUD and Search functionalities of the Google Tasks API.
    """
    
    # Store a test task ID to use across multiple tests
    test_task_id = None
    
    def test_01_create_task(self):
        """Test task creation (C)."""
        print("\n--- Testing 01: CREATE Task ---")
        
        # 1. Define the task data
        task_data = {
            "title": "Test Task to Create (API Test)",
            "notes": "Testing the POST endpoint functionality.",
            # Note: due_date is optional for creation
        }
        
        # 2. Make the POST request
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        
        # 3. Assertions
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Response: {response.text}")
        
        data = response.json()
        self.assertIn("id", data['task'], "Response data must contain a task ID.")
        self.assertEqual(data['task']['title'], task_data['title'], "Task title mismatch.")
        
        # Store the created ID for subsequent tests
        TestTaskAPI.test_task_id = data['task']['id']
        print(f"✅ Task Created successfully with ID: {TestTaskAPI.test_task_id}")

    def test_02_read_task(self):
        """Test reading a single task by ID (R)."""
        print("\n--- Testing 02: READ Task ---")
        
        # Ensure a task ID exists from the previous test
        self.assertIsNotNone(TestTaskAPI.test_task_id, "No task ID available for reading.")
        
        # 1. Make the GET request
        response = requests.get(f"{BASE_URL}/tasks/{TestTaskAPI.test_task_id}")
        
        # 2. Assertions
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Response: {response.text}")
        data = response.json()
        self.assertEqual(data['task']['id'], TestTaskAPI.test_task_id, "Read task ID mismatch.")
        self.assertIn("Test Task to Create", data['task']['title'], "Read task title mismatch.")
        print(f"✅ Task Read successfully.")

    def test_03_update_task(self):
        """Test updating a task (U)."""
        print("\n--- Testing 03: UPDATE Task ---")
        
        self.assertIsNotNone(TestTaskAPI.test_task_id, "No task ID available for updating.")
        
        # 1. Define the update data
        new_title = "Test Task UPDATED (API Test)"
        update_data = {"title": new_title, "status": "completed"}
        
        # 2. Make the PATCH request
        response = requests.patch(f"{BASE_URL}/tasks/{TestTaskAPI.test_task_id}", json=update_data)
        
        # 3. Assertions
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Response: {response.text}")
        data = response.json()
        self.assertEqual(data['task']['title'], new_title, "Task title was not updated.")
        self.assertEqual(data['task']['status'], "completed", "Task status was not updated to 'completed'.")
        print(f"✅ Task Updated successfully. New Title: {data['task']['title']}")

    def test_04_search_tasks(self):
        """Test searching for tasks."""
        print("\n--- Testing 04: SEARCH Tasks ---")
        
        # 1. Make the GET request to search for the test task
        response = requests.get(f"{BASE_URL}/tasks/search?query=Test Task")
        
        # 2. Assertions
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Response: {response.text}")
        data = response.json()
        self.assertIn("tasks", data, "Response must contain a list of 'tasks'.")
        self.assertTrue(len(data['tasks']) > 0, "Search should return at least one task.")
        
        # Verify the updated task is in the search results
        titles = [task['title'] for task in data['tasks']]
        self.assertIn("Test Task UPDATED (API Test)", titles, "Search results do not contain the updated test task.")
        print(f"✅ Task Search successful.")

    def test_05_list_all_tasks(self):
        """Test listing all tasks."""
        print("\n--- Testing 05: LIST ALL Tasks ---")
        
        # 1. Make the GET request without any query parameters
        response = requests.get(f"{BASE_URL}/tasks")
        
        # 2. Assertions
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Response: {response.text}")
        data = response.json()
        self.assertIn("tasks", data, "Response must contain a list of 'tasks'.")
        self.assertTrue(len(data['tasks']) >= 1, "Expected at least one task in the list.")
        print(f"✅ Task List successful. Found {len(data['tasks'])} tasks.")

    def test_06_delete_task(self):
        """Test deleting the task (D) and verifying its eventual absence."""
        print("\n--- Testing 06: DELETE Task ---")
        
        self.assertIsNotNone(TestTaskAPI.test_task_id, "No task ID available for deletion.")
        
        task_id_to_delete = TestTaskAPI.test_task_id
        
        # 1. Make the DELETE request
        response = requests.delete(f"{BASE_URL}/tasks/{task_id_to_delete}")
        self.assertEqual(response.status_code, 200, f"Expected 200 on DELETE, got {response.status_code}. Response: {response.text}")
        
        # 3. Final Assertion (will only be reached if the loop times out)
        final_read = requests.get(f"{BASE_URL}/tasks/{task_id_to_delete}")
        self.assertEqual(final_read.status_code, 404, 
                         f"Task was not deleted. Final status: {final_read.status_code}")

# Run the tests
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)