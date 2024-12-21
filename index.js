document.addEventListener('DOMContentLoaded', async () => {
    // Initial overview update
    await updateOverview();

    // Update overview every 5 seconds
    setInterval(updateOverview, 5000);
    const taskList = document.getElementById('taskList');
    const repoUrl = document.getElementById('repoUrl');
    const addTaskButton = document.getElementById('addTask');
    const githubTokenInput = document.getElementById('githubToken'); // Get the GitHub token input element

    // Function to create a task item
    function createTaskItem(initialValue = '', isFirst = false) {
        const taskItem = document.createElement('div');
        taskItem.classList.add('task-item');

        const taskContainer = document.createElement('div');
        taskContainer.classList.add('mb-2');

        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.classList.add('form-control', 'task-title', 'mb-2');
        titleInput.placeholder = 'Task Title';
        titleInput.value = initialValue.title || '';

        const descriptionInput = document.createElement('textarea');
        descriptionInput.classList.add('form-control', 'task-description');
        descriptionInput.placeholder = 'Task Description';
        descriptionInput.value = initialValue.description || '';

        taskContainer.appendChild(titleInput);
        taskContainer.appendChild(descriptionInput);
        taskItem.appendChild(taskContainer);

        if (!isFirst) {
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.classList.add('btn', 'btn-danger', 'btn-sm', 'remove-task');
            removeButton.textContent = 'Remove';
            removeButton.addEventListener('click', () => {
                taskItem.remove();
            });
            taskItem.appendChild(removeButton);
        }

        taskList.appendChild(taskItem);
    }

    // Add initial task item
    createTaskItem('', true);

    // Add task button functionality
    addTaskButton.addEventListener('click', () => {
        createTaskItem();
    });

    // Fetch GitHub issues button functionality
    document.getElementById('fetchIssues').addEventListener('click', async () => {
        const repoUrlValue = repoUrl.value;
        if (!repoUrlValue) {
            alert('Please enter a repository URL first.');
            return;
        }
        try {
            const response = await fetch(`/github_issues?repo_url=${encodeURIComponent(repoUrlValue)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const issues = await response.json();
            taskList.innerHTML = ''; // Clear existing tasks
            issues.forEach(issue => createTaskItem(issue, false));
        } catch (error) {
            console.error('Error fetching GitHub issues:', error);
            alert('Error fetching GitHub issues. Please check the repository URL.');
        }
    });

    // Submit form
    document.getElementById('agentForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        const repoUrlValue = repoUrl.value;
        const agentCountValue = document.getElementById('agentCount').value;
        const githubTokenValue = githubTokenInput.value; // Get the GitHub token value
        const aiderCommandsValue = document.getElementById('aiderCommands').value;
        const tasks = Array.from(document.querySelectorAll('.task-item')).map(item => ({
            title: item.querySelector('.task-title').value,
            description: item.querySelector('.task-description').value
        }));

        // Input validation
        if (!repoUrlValue) {
            alert('Please enter a repository URL.');
            return;
        }
        if (!tasks.length) {
            alert('Please add at least one task.');
            return;
        }
        if (!githubTokenValue) {
            alert('Please set the GITHUB_TOKEN environment variable.');
            return;
        }

        try {
            const response = await fetch('/create_agent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    repo_url: repoUrlValue,
                    num_agents: agentCountValue,
                    tasks: tasks,
                    aider_commands: aiderCommandsValue,
                    github_token: githubTokenValue // Send the token
                })
            });
            const data = await response.json();
            if (data.success) {
                alert(data.message);
                await updateOverview();
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error creating agents:', error);
            alert('Error creating agents. Please check the console for details.');
        }
    });

    // Initial overview update
    await updateOverview();
});

async function updateOverview() {
    try {
        const response = await fetch('/tasks/tasks.json');
        const data = await response.json();
        const agents = data.agents || {};
        const agentCount = Object.keys(agents).length;

        // Update statistics
        document.getElementById('totalAgents').textContent = agentCount;
        document.getElementById('repoDisplay').textContent = data.repository_url || 'Not set';
    } catch (error) {
        console.error('Error updating overview:', error);
    }
}
