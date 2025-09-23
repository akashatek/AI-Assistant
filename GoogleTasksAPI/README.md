# Google Tasks API

## Code Structure

The code file structure is designed to separate the application's core logic from its API layer. It consists of two main files:

 * `google_tasks.py`: This file contains all the business logic for interacting with the Google Tasks API. It holds the GoogleTasksTool class, which handles Google authentication and all the methods for creating, updating, listing, and deleting tasks. Think of this as the backend engine that does all the work.

 * `api.py`: This file is the API layer. It uses the FastAPI framework to define the RESTful endpoints (e.g., /tasks, /tasks/search). Its job is to receive HTTP requests, validate the data, and then call the corresponding methods from the GoogleTasksTool class to fulfill the request. This separation of concerns makes the code cleaner and easier to maintain.

## Launching from the Command Line

The recommended way to run a FastAPI application is by using **Uvicorn**, an ASGI server. The command specifies the application module and the app instance to run.

1.  **Install dependencies:** Make sure you have the required libraries installed in your Python environment.

    ```bash
    pip install fastapi uvicorn google-api-python-client google-auth-httplib2 google-auth-oauthlib pydantic
    ```

2.  **Run the application:** Use the `uvicorn` command to start the server. The format is `uvicorn <module_name>:<app_instance>`. Since your main file is `api.py` and the app instance is `app`, the command is:

    ```bash
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
    ```

      - `api:app`: This tells Uvicorn to find the `app` object inside the `api.py` file.
      - `--reload`: This is useful for development as it automatically reloads the server whenever you save a change to your code.
      - `--host 0.0.0.0`: This makes the server accessible from any machine on your network, not just your local computer.
      - `--port 8000`: This sets the port the application will run on. You can change this to any available port.

-----

## Testing

Here are some `curl` examples to interact with your FastAPI application, assuming it's running locally on port `8000`.

[Google Tasks API](http://localhost:8000/docs)

### 1\. Create a New Task (POST)

This command creates a new task with a title and optional notes.

```bash
curl -X POST "http://localhost:8000/tasks" \
-H "Content-Type: application/json" \
-d '{
  "title": "Buy groceries",
  "notes": "Milk, bread, and eggs."
}'
```

### 2\. List All Tasks (GET)

This command retrieves all tasks from the default "BACKLOG" list.

```bash
curl "http://localhost:8000/tasks"
```

### 3\. List Tasks by Due Date (GET with query parameter)

This command filters tasks to show only those due on a specific date.

```bash
curl "http://localhost:8000/tasks?due_date=2025-09-22"
```

### 4\. Search for Tasks by Title (GET with query parameter)

This command searches for any tasks containing "groceries" in their title.

```bash
curl "http://localhost:8000/tasks/search?query=groceries"
```

### 5\. Update a Task (PATCH)

This command updates a task's title and status. You'll need the `task_id` from a previous list or create command.

```bash
curl -X PATCH "http://localhost:8000/tasks/{task_id}" \
-H "Content-Type: application/json" \
-d '{
  "title": "Buy all the groceries!",
  "status": "completed"
}'
```

### 6\. Delete a Task (DELETE)

This command permanently deletes a task using its `task_id`.

```bash
curl -X DELETE "http://localhost:8000/tasks/{task_id}"
```
```

## Corresponding Dockerfile

A **Dockerfile** automates the process of setting up the environment and running your application inside a container.

To use the following `Dockerfile`, make sure you have a `requirements.txt` file in the same directory as your `google_tasks_api.py` and `google_tasks.py` files.

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the uvicorn command to start the API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### How to use this Dockerfile

1.  **Save the file:** Save the code above as `Dockerfile` in your project's root directory.

2.  **Build the image:** Open your terminal in the project directory and run the following command to build your Docker image.
    ```bash
    docker build -t akashatek/google-tasks-api:v1.00 .
    docker push akashatek/google-tasks-api:v1.00
    ```
3.  **Run the container:** Once the image is built, you can run it as a container.
    ```bash
    docker run -d --name google-tasks-api -p 8000:8000 akashatek/google-tasks-api:v1.00
    ```
      - `-p 8000:8000`: This maps port 8000 on your local machine to port 8000 inside the container, allowing you to access the API at `http://localhost:8000`.

4.  **Run the deployment:** Once the image is built, you can run it as a container.
    ```bash
    docker-compose up -d
    ```