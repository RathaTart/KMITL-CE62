document.addEventListener('DOMContentLoaded', function() {
    const taskList = document.getElementById('ft_list');
    const newTaskBtn = document.getElementById('new-task-btn');

    // Load tasks from cookies when the page loads
    loadTasks();

    // Add a new task when the button is clicked
    newTaskBtn.addEventListener('click', function() {
        const taskText = prompt('Enter a new TO DO:');
        if (taskText) {
            addTask(taskText); // Add the new task to the list
            saveTasks();       // Save the updated list to cookies
        }
    });

    // Function to add a task to the list
    function addTask(taskText) {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'todo-item';
        taskDiv.textContent = taskText;

        // Delete the task when it's clicked
        taskDiv.addEventListener('click', function() {
            if (confirm('elete this TO DO?')) {
                taskDiv.remove();
                saveTasks(); // Save the updated list to cookies
            }
        });

        // Add the new task to the top of the list
        taskList.insertBefore(taskDiv, taskList.firstChild);
    }

    // Function to save tasks to cookies
    function saveTasks() {
        const tasks = [];
        const taskItems = taskList.getElementsByClassName('todo-item');

        // Collect all task texts
        for (let item of taskItems) {
            tasks.push(item.textContent);
        }

        // Save tasks to a cookie
        document.cookie = `tasks=${encodeURIComponent(JSON.stringify(tasks))};path=/`;
    }

    // Function to load tasks from cookies
    function loadTasks() {
        const cookies = document.cookie.split(';');

        // Find the 'tasks' cookie
        for (let cookie of cookies) {
            const [name, value] = cookie.split('=').map(c => c.trim());
            if (name === 'tasks') {
                const tasks = JSON.parse(decodeURIComponent(value));
                // Add each task to the list in reverse order
                for (let task of tasks.reverse()) {
                    addTask(task);
                }
            }
        }
    }
});
