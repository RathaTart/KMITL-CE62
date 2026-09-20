let taskIndex;

function openPrompt() {
    let task = prompt("Enter a new task:");
    if (task !== null && task !== "") {
        addTask(task);
    }
}

function addTask(task) {
    let ftList = document.getElementById("ft_list");
    let newTask = document.createElement("div");
    newTask.className = "todo";
    newTask.innerHTML = task;
    newTask.onclick = function() {
        showConfirmBox(newTask);
    };
    ftList.insertBefore(newTask, ftList.firstChild);
    setCookie(encodeURIComponent(task), encodeURIComponent("nothing"), 1);
}

function showConfirmBox(taskElement) {
    let confirmBox = document.getElementById("confirmBox");
    confirmBox.style.display = "block";
    let deleteButton = document.getElementById("deleteBtn");
    deleteButton.onclick = function() {
        removeTask(true, taskElement);
    };
}

function removeTask(confirm, taskElement) {
    let confirmBox = document.getElementById("confirmBox");
    confirmBox.style.display = "none";
    if (confirm) {
        console.log("delete: " + taskElement.innerHTML);
        deleteCookie(encodeURIComponent(taskElement.innerHTML));
        taskElement.remove();
    }
}

function setCookie(cookieName, cookieValue, expirationDays) {
    let date = new Date();
    date.setTime(date.getTime() + (expirationDays * 24 * 60 * 60 * 1000));
    let expires = "expires="+ date.toUTCString();
    document.cookie = cookieName + "=" + cookieValue + ";" + expires + ";path=/";
}

function deleteCookie(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
}

function lodeCookies() {
    let cookies = document.cookie.split("; ");
    let ftList = document.getElementById("ft_list");
    if (cookies == "") {
        return
    }
    cookies.forEach(cookie => {
        let taskData = cookie.split("=");
        let newTask = document.createElement("div");
        newTask.className = "todo";
        newTask.innerHTML = decodeURIComponent(taskData[0]);
        newTask.onclick = function() {
            showConfirmBox(newTask);
        };
        ftList.insertBefore(newTask, ftList.firstChild);
    });
}

lodeCookies();