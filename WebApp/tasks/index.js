// index.js

// Get the input and list elements globally
const taskInput = document.getElementById('taskInput');
const taskList = document.getElementById('taskList');

// Function to add a new task (Must be global for onclick="addTask()" in HTML)
function addTask(taskText, isNew = true) {
    // If called without a specific text (e.g., from user input), get value from the field
    if (!taskText) {
        taskText = taskInput.value.trim();
    }
    
    if (taskText === "") {
        if (isNew) { // Only alert if user tried to add an empty task manually
             alert("You must write something!");
        }
        return;
    }

    // 1. Create the list item (<li>) and set its content/style
    const listItem = document.createElement('li');
    
    // Apply initial classes: task-item (from index.css), w3-white background, 
    // and w3-border-theme-l1 for the Deep Purple border highlight.
    listItem.className = 'w3-display-container task-item w3-white w3-border-theme-l1';
    
    listItem.innerHTML = `
        ${taskText}
        <span class="close-btn w3-display-right w3-padding w3-text-red">&times;</span>
    `;

    // 2. Add 'Toggle Complete' functionality
    listItem.addEventListener('click', function(event) {
        // Ensure the click was not directly on the close button
        if (!event.target.classList.contains('close-btn')) {
             listItem.classList.toggle('completed');
             
             // Toggle the green border on completion (W3.CSS Status Color)
             listItem.classList.toggle('w3-border-green'); 
             
             // Toggle the purple border when uncompleted
             listItem.classList.toggle('w3-border-theme-l1'); 
        }
    });

    // 3. Add 'Remove Task' functionality for the close button
    const closeSpan = listItem.querySelector('.close-btn');
    closeSpan.addEventListener('click', function() {
        listItem.remove(); // Remove the parent <li> element
    });

    // 4. Append the new task to the list
    taskList.appendChild(listItem);

    // 5. Clear the input field only if the task was added manually by the user
    if (isNew) {
        taskInput.value = "";
    }
}

// Allow adding tasks by pressing the Enter key in the input field
taskInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        addTask(null, true); // Call with isNew = true
    }
});


// ----------------------------------------------------
// UPDATED window.onload SECTION
// ----------------------------------------------------
window.onload = function() {
    const dummyTasks = [
        "Set up the local storage function.",
        "Review the Flexbox CSS for the footer.",
        "Check mobile responsiveness (max-width test).",
        "Write documentation for the project.",
        "Clear all browser cache and cookies.",
        "Buy new deep purple-themed coffee mug.",
        "Schedule weekly project review meeting.",
        "Refactor addTask() function for clarity.",
        "Integrate a time-stamping feature.",
        "Watch W3.CSS Flexbox tutorial video.",
        "Test task deletion on completed items.",
        "Finalize the project color scheme.",
        "Debug the window.onload default tasks.",
        "Push all changes to the Git repository.",
        "Research different to-do app designs.",
        "Find a new background image for the body.",
        "Write a success message upon task addition.",
        "Test scrolling in the list section.",
        "Pay the electricity bill online.",
        "Send the project link to a colleague.",
        "Plan out the next major feature (e.g., categories).",
        "Take a quick 15-minute break.",
        "Read Chapter 5 of 'Effective JavaScript.'",
        "Verify the theme links are loading correctly.",
        "Clean up the unused code comments."
    ];

    // Loop through the array and add each task
    dummyTasks.forEach(task => {
        addTask(task, false); // Pass task text and isNew=false
    });

    taskInput.value = ""; // Ensure the input field is clear for the user
};