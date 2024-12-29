// Function to update overview statistics
async function updateOverview() {
    try {
        const response = await fetch('/tasks/tasks.json');
        const data = await response.json();
        const agents = data.agents || {};
        const agentCount = Object.keys(agents).length;

        // Update statistics
        document.getElementById('totalAgents').textContent = agentCount;

        // Calculate unique tasks
        const uniqueTasks = new Set(Object.values(agents).map(agent => agent.task)).size;
        document.getElementById('activeTasks').textContent = uniqueTasks;

        // Update repository display
        document.getElementById('repoDisplay').textContent = data.repository_url || 'Not set';

        // Show/hide delete button based on agent count
        document.getElementById('deleteAllAgents').style.display = agentCount > 0 ? 'inline-block' : 'none';
    } catch (error) {
        console.error('Error updating overview:', error);
    }
}

// Delete all agents functionality
document.getElementById('deleteAllAgents').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete all agents? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/tasks/tasks.json');
        const data = await response.json();
        const agents = Object.keys(data.agents || {});

        let successCount = 0;
        let errorCount = 0;

        for (const agentId of agents) {
            try {
                const deleteResponse = await fetch(`/delete_agent/${agentId}`, {
                    method: 'DELETE'
                });

                if (deleteResponse.ok) {
                    successCount++;
                } else {
                    errorCount++;
                }
            } catch (error) {
                errorCount++;
                console.error(`Error deleting agent ${agentId}:`, error);
            }
        }

        // Show result in alert
        const resultDiv = document.getElementById('result');
        const alertDiv = resultDiv.querySelector('.alert');
        resultDiv.style.display = 'block';

        if (errorCount === 0) {
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = `Successfully deleted ${successCount} agent(s)`;
            // Refresh overview after successful deletion
            setTimeout(updateOverview, 1000);
        } else {
            alertDiv.className = 'alert alert-warning';
            alertDiv.textContent = `Deleted ${successCount} agent(s). Failed to delete ${errorCount} agent(s).`;
        }
    } catch (error) {
        console.error('Error in delete all operation:', error);
        const resultDiv = document.getElementById('result');
        const alertDiv = resultDiv.querySelector('.alert');
        resultDiv.style.display = 'block';
        alertDiv.className = 'alert alert-danger';
        alertDiv.textContent = `Error: ${error.message}`;
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    // Load GitHub token from sessionStorage if available
    const savedToken = sessionStorage.getItem('github_token');
    if (savedToken) {
        document.getElementById('githubToken').value = savedToken;
    }

    // Load aider commands from localStorage if available
    const savedCommands = localStorage.getItem('aider_commands');
    if (savedCommands) {
        document.getElementById('aiderCommands').value = savedCommands;
    }

    // Initial overview update
    await updateOverview();

    // Update overview every 5 seconds
    setInterval(updateOverview, 5000);
    const taskList = document.getElementById('taskList');
    const repoUrl = document.getElementById('repoUrl');
    const addTaskButton = document.getElementById('addTask');

    // Function to create a task item
    function createTaskItem(initialValue = '', isFirst = false) {
        const taskItem = document.createElement('div');
        taskItem.classList.add('task-item');

        const taskContainer = document.createElement('div');
        taskContainer.classList.add('mb-2');

        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.classList.add('form-control', 'task-title', 'mb-2');
        titleInput.placeholder = 'Task title...';
        titleInput.required = true;
        titleInput.value = initialValue.title || initialValue;

        const descriptionInput = document.createElement('textarea');
        descriptionInput.classList.add('form-control', 'task-description', 'mb-2');
        descriptionInput.placeholder = 'Detailed task description...';
        descriptionInput.rows = 3;
        descriptionInput.value = initialValue.description || '';

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.classList.add('btn', 'btn-danger', 'remove-task');
        removeButton.textContent = '-';
        removeButton.style.display = 'inline-block';

        // Remove task functionality
        removeButton.addEventListener('click', (e) => {
            const taskItems = taskList.querySelectorAll('.task-item');
            if (taskItems.length > 1) {
                e.target.closest('.task-item').remove();
            }
        });

        taskContainer.appendChild(titleInput);
        taskContainer.appendChild(descriptionInput);
        taskContainer.appendChild(removeButton);
        taskItem.appendChild(taskContainer);

        return taskItem;
    }

    // Add task button functionality
    addTaskButton.addEventListener('click', () => {
        const newTaskItem = createTaskItem();
        taskList.appendChild(newTaskItem);
    });

    // Fetch GitHub issues
    document.getElementById('fetchIssues').addEventListener('click', async () => {
        const repoUrl = document.getElementById('repoUrl').value;
        const githubToken = document.getElementById('githubToken').value;

        if (!repoUrl || !githubToken) {
            const resultDiv = document.getElementById('result');
            const alertDiv = resultDiv.querySelector('.alert');
            resultDiv.style.display = 'block';
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = 'Please enter both repository URL and GitHub token';
            return;
        }

        try {
            // Extract owner and repo from URL
            const match = repoUrl.match(/github\.com\/([^\/]+)\/([^\/\.]+)/);
            if (!match) {
                throw new Error('Invalid GitHub repository URL');
            }
            const [, owner, repo] = match;

            // Fetch issues from GitHub API
            const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues?state=open`, {
                headers: {
                    'Authorization': `token ${githubToken}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch GitHub issues');
            }

            const issues = await response.json();

            // Clear existing tasks
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';

            // Create issue selection UI
            const issueListContainer = document.createElement('div');
            issueListContainer.className = 'github-issues-list';

            issues.filter(issue => !issue.pull_request).forEach(issue => {
                const issueItem = document.createElement('div');
                issueItem.className = 'issue-item';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `issue-${issue.id}`;
                checkbox.value = issue.id;
                
                // Add change event listener to checkbox
                checkbox.addEventListener('change', () => {
                    if (checkbox.checked) {
                        // Add task when checked
                        const taskItem = createTaskItem({
                            title: issue.title,
                            description: issue.body || ''
                        });
                        taskList.appendChild(taskItem);
                    } else {
                        // Remove task when unchecked
                        const tasks = Array.from(taskList.querySelectorAll('.task-item'));
                        const matchingTask = tasks.find(task => 
                            task.querySelector('.task-title').value === issue.title
                        );
                        if (matchingTask) {
                            matchingTask.remove();
                        }
                    }
                });

                const label = document.createElement('label');
                label.htmlFor = `issue-${issue.id}`;
                
                const titleSpan = document.createElement('span');
                titleSpan.textContent = issue.title;
                
                const numberSpan = document.createElement('span');
                numberSpan.className = 'issue-number';
                numberSpan.textContent = `#${issue.number}`;

                label.appendChild(titleSpan);
                label.appendChild(numberSpan);

                issueItem.appendChild(checkbox);
                issueItem.appendChild(label);
                issueListContainer.appendChild(issueItem);
            });
            taskList.appendChild(issueListContainer);

            // Show success message
            const resultDiv = document.getElementById('result');
            const alertDiv = resultDiv.querySelector('.alert');
            resultDiv.style.display = 'block';
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = `Loaded ${issues.length} issues from GitHub`;

        } catch (error) {
            const resultDiv = document.getElementById('result');
            const alertDiv = resultDiv.querySelector('.alert');
            resultDiv.style.display = 'block';
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = `Error loading GitHub issues: ${error.message}`;
        }
    });

    // Form submission
    document.getElementById('agentForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const resultDiv = document.getElementById('result');
        const alertDiv = resultDiv.querySelector('.alert');

        try {
            // Collect tasks
            const tasks = Array.from(document.querySelectorAll('.task-item')).map(item => {
                const title = item.querySelector('.task-title').value.trim();
                const description = item.querySelector('.task-description').value.trim();
                return {
                    title: title,
                    description: description
                };
            }).filter(task => task.title !== '');

            const agentCount = parseInt(document.getElementById('agentCount').value, 10);

            // Store GitHub token in sessionStorage
            const githubToken = document.getElementById('githubToken').value.trim();
            const aiderCommands = document.getElementById('aiderCommands').value.trim();
            if (githubToken) {
                sessionStorage.setItem('github_token', githubToken);
            }
            if (aiderCommands) {
                localStorage.setItem('aider_commands', aiderCommands);
            }

            const response = await fetch('/create_agent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-GitHub-Token': sessionStorage.getItem('github_token') || ''
                },
                body: JSON.stringify({
                    repo_url: document.getElementById('repoUrl').value,
                    tasks: tasks,
                    num_agents: agentCount,
                    aider_commands: document.getElementById('aiderCommands').value.trim()
                })
            });

            const data = await response.json();

            resultDiv.style.display = 'block';
            if (data.success) {
                alertDiv.className = 'alert alert-success';
                alertDiv.textContent = `Success! Agents ${data.agent_ids.join(', ')} created. Redirecting to Agent View...`;

                // Redirect to agents view after a short delay
                setTimeout(() => {
                    window.location.href = '/agents';
                }, 2000);
            } else {
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = `Error: ${data.error}`;
            }
        } catch (error) {
            resultDiv.style.display = 'block';
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = `Error: ${error.message}`;
        }
    });
});
