// index.js

// --- CONFIGURATION ---
// REPLACE THIS WITH YOUR ACTUAL POSTGREST ENDPOINT
const API_URL = 'http://localhost:3000/tasks'; 

const taskInput = document.getElementById('taskInput');
const taskList = document.getElementById('taskList');

// --- HELPER FUNCTION: RENDERS a single task -------------------------------
/**
 * Creates the DOM element for a task, including click listeners.
 * @param {object} task - Task object {id: UUID, name: String, is_completed: Boolean}
 */
function renderTask(task) {
    const listItem = document.createElement('li');
    
    // Determine initial classes based on completion status
    let initialClasses = 'w3-display-container task-item w3-white';
    
    if (task.is_completed) {
        // Apply completed styles if the task is done
        initialClasses += ' completed w3-border-green';
    } else {
        // Apply theme border if not completed
        initialClasses += ' w3-border-theme-l1';
    }

    listItem.className = initialClasses;
    // Store the task ID on the list item for easy reference
    listItem.dataset.taskId = task.id;
    
    listItem.innerHTML = `
        ${task.name}
        <span class="close-btn w3-display-right w3-padding w3-text-red" style="visibility: hidden;">&times;</span>
    `;

    // 2. Add 'Toggle Complete' functionality (PATCH request)
    listItem.addEventListener('click', async function(event) {
        if (!event.target.classList.contains('close-btn')) {
            const newStatus = !listItem.classList.contains('completed');
            
            // Call the API to update the status
            await completeTask(task.id, newStatus);
            
            // Optimistically update the UI
            listItem.classList.toggle('completed');
            listItem.classList.toggle('w3-border-green'); 
            listItem.classList.toggle('w3-border-theme-l1'); 
        }
    });

    // We skip the delete button logic for simplicity, focus on add/complete
    
    // 3. Append the new task to the list
    taskList.appendChild(listItem);
}


// --- REST API FUNCTIONS --------------------------------------------------

/**
 * Loads all tasks from the PostgREST API and renders them.
 */
async function loadTasks() {
    try {
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const tasks = await response.json();
        
        // Clear existing dummy tasks before rendering fresh data
        taskList.innerHTML = ''; 
        
        // Render each task fetched from the API
        tasks.forEach(task => renderTask(task));
        
    } catch (error) {
        console.error("Could not load tasks:", error);
        alert("Failed to load tasks from API. Check console for details.");
    }
}


/**
 * REST API: Adds a new task via POST request.
 * @param {string} taskName - The name of the new task.
 */
async function addTask(taskName = taskInput.value.trim()) {
    if (taskName === "") {
        alert("You must write something!");
        return;
    }
    
    // Task payload: name is required, is_completed defaults to false
    const taskPayload = {
        name: taskName,
        is_completed: false
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // PostgREST typically returns the created record(s)
                'Prefer': 'return=representation' 
            },
            body: JSON.stringify(taskPayload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Get the single created task record from the response array
        const [newTask] = await response.json(); 
        
        // Render the new task from the API response
        renderTask(newTask);

        // Clear the input field
        taskInput.value = "";

    } catch (error) {
        console.error("Could not add task:", error);
        alert("Failed to add task via API. Check console for details.");
    }
}


/**
 * REST API: Marks a task as complete/incomplete via PATCH request.
 * @param {string} taskId - The UUID of the task to update.
 * @param {boolean} isCompleted - The new status (true/false).
 */
async function completeTask(taskId, isCompleted) {
    const updatePayload = {
        is_completed: isCompleted
    };

    try {
        const response = await fetch(`${API_URL}?id=eq.${taskId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatePayload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        console.log(`Task ${taskId} status updated to ${isCompleted}`);

    } catch (error) {
        console.error("Could not update task status:", error);
        alert("Failed to update task status via API. Check console for details.");
        // Optional: Revert UI change if API fails
    }
}

// --- INITIALIZATION ---

// Allow adding tasks by pressing the Enter key in the input field
taskInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        addTask();
    }
});

// Load tasks from the API when the page loads
window.onload = loadTasks;