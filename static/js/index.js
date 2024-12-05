// Token handling
const tokenForm = document.getElementById('tokenForm');
if (tokenForm) {
    tokenForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = document.getElementById('githubToken').value;
        
        try {
            const isValid = await AUTH.verifyToken(token);
            
            if (isValid) {
                AUTH.setToken(token);
                window.location.href = '/agents';
            } else {
                showAlert('Invalid token. Please check your token and try again.', 'danger');
            }
        } catch (error) {
            console.error('Error verifying token:', error);
            showAlert('Error verifying token. Please try again.', 'danger');
        }
    });
}

// GitHub Integration Functions
// GitHub Integration Functions
async function loadRepositories() {
    try {
        const response = await AUTH.fetch('/github/repositories');
        const data = await response.json();
        
        const select = document.getElementById('repoSelect');
        if (!select) return;

        select.innerHTML = '<option value="">Select a repository...</option>';
        
        if (data.repositories) {
            data.repositories.forEach(repo => {
                const option = document.createElement('option');
                option.value = repo.full_name;
                option.textContent = repo.full_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading repositories:', error);
        showAlert('Error loading repositories: ' + error.message, 'danger');
    }
}

async function loadCommits(repoName) {
    try {
        const response = await AUTH.fetch(`/github/commits/${repoName}`);
        const data = await response.json();
        
        const commitsList = document.getElementById('commitsList');
        if (!commitsList) return;

        commitsList.innerHTML = '';
        
        if (data.commits) {
            data.commits.forEach(commit => {
                const commitItem = document.createElement('div');
                commitItem.className = 'list-group-item';
                commitItem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${commit.message}</h6>
                            <small>by ${commit.author} on ${new Date(commit.date).toLocaleString()}</small>
                        </div>
                        <a href="${commit.url}" target="_blank" class="btn btn-sm btn-outline-secondary">View</a>
                    </div>
                `;
                commitsList.appendChild(commitItem);
            });
        }
    } catch (error) {
        console.error('Error loading commits:', error);
        showAlert('Error loading commits: ' + error.message, 'danger');
    }
}

// Add utility function for showing alerts
function showAlert(message, type) {
    const resultDiv = document.getElementById('result');
    if (!resultDiv) return;

    const alertDiv = resultDiv.querySelector('.alert');
    resultDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
}

// Task Management
function createTaskItem(initialValue = '', isFirst = false) {
    const taskItem = document.createElement('div');
    taskItem.classList.add('task-item');
    
    const input = document.createElement('input');
    input.type = 'text';
    input.classList.add('form-control', 'task-description');
    input.placeholder = 'Describe the task for the agent...';
    input.required = true;
    input.value = initialValue;
    
    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.classList.add('btn', 'btn-danger', 'remove-task');
    removeButton.textContent = '-';
    removeButton.style.display = isFirst ? 'none' : 'inline-block';
    
    removeButton.addEventListener('click', (e) => {
        const taskItems = document.getElementById('taskList').querySelectorAll('.task-item');
        if (taskItems.length > 1) {
            e.target.closest('.task-item').remove();
            
            if (taskItems.length === 2) {
                taskItems[0].querySelector('.remove-task').style.display = 'none';
            }
        }
    });
    
    taskItem.appendChild(input);
    taskItem.appendChild(removeButton);
    return taskItem;
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    const token = getGitHubToken();
    
    // Only load repositories if we're on the authenticated page
    if (document.getElementById('repoSelect')) {
        if (token) {
            await loadRepositories();
        } else {
            console.log('No GitHub token found, skipping repository load');
        }
    }

    // Rest of the initialization code...
    const taskList = document.getElementById('taskList');
    const addTaskButton = document.getElementById('addTask');
    const repoUrl = document.getElementById('repoUrl');

    if (taskList) {  // Only run this code if we're on the page with tasks
    try {
        const tasksResponse = await fetch('/tasks/tasks.json');
        const tasksData = await tasksResponse.json();
        if (repoUrl) {
            repoUrl.value = tasksData.repository_url;
        }
        // Populate initial tasks
        if (tasksData.tasks && taskList) {
            tasksData.tasks.forEach((taskDescription, index) => {
                const taskItem = createTaskItem(taskDescription, index === 0);
                taskList.appendChild(taskItem);
            });
        }
    } catch (error) {
        console.error('Error fetching tasks:', error);
    }

    // Add task button functionality
    if (addTaskButton && taskList) {
        addTaskButton.addEventListener('click', () => {
            const taskItems = taskList.querySelectorAll('.task-item');
            taskItems.forEach(item => {
                item.querySelector('.remove-task').style.display = 'inline-block';
            });
            const newTaskItem = createTaskItem();
            taskList.appendChild(newTaskItem);
        });
    }

    // Form submission handler
    const agentForm = document.getElementById('agentForm');
    if (agentForm) {
        agentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const resultDiv = document.getElementById('result');
            const alertDiv = resultDiv.querySelector('.alert');
            
            try {
                const tasks = Array.from(document.querySelectorAll('.task-description'))
                    .map(input => input.value.trim())
                    .filter(task => task !== '');
                
                const agentCount = parseInt(document.getElementById('agentCount').value, 10);
                
                const response = await fetch('/create_agent', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
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
    }

    // Repository selection handlers
    const repoSelect = document.getElementById('repoSelect');
    if (repoSelect) {
        repoSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                loadCommits(e.target.value);
            }
        });
    }

    const refreshReposButton = document.getElementById('refreshRepos');
    if (refreshReposButton) {
        refreshReposButton.addEventListener('click', loadRepositories);
    }
});