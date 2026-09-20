$(document).ready(function() {
    const $taskList = $('#ft_list');
    const $newTaskBtn = $('#new-task-btn');

// document.addEventListener('DOMContentLoaded', function() {
//     const taskList = document.getElementById('ft_list');
//     const newTaskBtn = document.getElementById('new-task-btn');

    loadTasks();

    $newTaskBtn.on('click', function() {
        const taskText = prompt('Enter a new TO DO:');
        if (taskText) {
            addTask(taskText);
            saveTasks();
        }
    });

    // newTaskBtn.addEventListener('click', function() {
    //     const taskText = prompt('Enter a new TO DO:');
    //     if (taskText) {
    //         addTask(taskText);
    //         saveTasks();
    //     }
    // });


    function addTask(taskText) {
        const $taskDiv = $('<div></div>', {
            class: 'todo-item',
            text: taskText,
            click: function() {
                if (confirm('Do you really want to delete this TO DO?')) {
                    $taskDiv.remove();
                    saveTasks();
                }
            }
        });
        $taskList.prepend($taskDiv);
    }

    // function addTask(taskText) {
    //     const taskDiv = document.createElement('div');
    //     taskDiv.className = 'todo-item';
    //     taskDiv.textContent = taskText;
    //     taskDiv.addEventListener('click', function() {
    //         if (confirm('elete this TO DO?')) {
    //             taskDiv.remove();
    //             saveTasks();
    //         }
    //     });
    //     taskList.insertBefore(taskDiv, taskList.firstChild);
    // }

    function saveTasks() { 
        const tasks = [];
        $taskList.find('.todo-item').each(function() {
            tasks.push($(this).text());
        });
        document.cookie = `tasks=${encodeURIComponent(JSON.stringify(tasks))};path=/`;
    }

    // function saveTasks() {
    //     const tasks = [];
    //     const taskItems = taskList.getElementsByClassName('todo-item');

    //     for (let item of taskItems) {
    //         tasks.push(item.textContent);
    //     }

    //     document.cookie = `tasks=${encodeURIComponent(JSON.stringify(tasks))};path=/`;
    // }

    function loadTasks() {
        const cookies = document.cookie.split(';'); // cookies = ['tasks=fdgfg ; tasklist=fdgfg']
        for (let cookie of cookies) {
            const [name, value] = cookie.split('=').map(c => c.trim()); 
            if (name === 'tasks') {
                const tasks = JSON.parse(decodeURIComponent(value));
                for (let task of tasks.reverse()) {
                    addTask(task);
                }
            }
        }
    }

    // function loadTasks() {
    //     const cookies = document.cookie.split(';');

    //     for (let cookie of cookies) {
    //         const [name, value] = cookie.split('=').map(c => c.trim());
    //         if (name === 'tasks') {
    //             const tasks = JSON.parse(decodeURIComponent(value));
    
    //             for (let task of tasks.reverse()) {
    //                 addTask(task);
});