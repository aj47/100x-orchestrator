// Global variables and state management
const lastOutputLengths = {};
let updateInterval;

// Helper function to get output length from debug info
function getOutputLength(debugElement) {
    const lengthElement = debugElement.querySelector('.label');
    if (lengthElement && lengthElement.textContent.includes('Output Length')) {
        const lengthText = lengthElement.parentElement.textContent;
        return parseInt(lengthText.split(':')[1].trim());
    }
    return 0;
}

// Function to fetch updates via AJAX
async function fetchUpdates() {
    try {
        const response = await fetch('/tasks/tasks.json');
        const responseClone = response.clone(); // Clone the response
        const tasksData = await response.json();

        // Update each agent's output and history
        for (const [agentId, agentData] of Object.entries(tasksData.agents)) {
            updateAgentCard(agentId, agentData, responseClone);
        }
    } catch (error) {
        console.error('Error fetching updates:', error);
    }
}

// Function to update a single agent's card
function updateAgentCard(agentId, agentData, responseClone) {
    const agentCard = document.getElementById(`agent-${agentId}`);
    if (!agentCard) return;

    // Update agent state
    updateAgentState(agentCard, agentData);

    // Update CLI output
    updateCliOutput(agentCard, agentData);

    // Update status and timestamps
    updateStatusBadge(agentCard, agentData);

    // Update PR info
    updatePrInfo(agentCard, agentData);

    // Update history
    updateHistory(agentCard, agentData);

    // Update debug info (using cloned response)
    updateDebugInfo(agentCard, responseClone);
}


// Function to update agent state
function updateAgentState(agentCard, agentData) {
    const agentState = agentCard.querySelector('.agent-state');
    if (agentState) {
        const fields = {
            'thought': agentData.thought || '',
            'progress': agentData.progress || '',
            'future': agentData.future || '',
            'action': agentData.last_action || ''
        };

        Object.entries(fields).forEach(([field, value]) => {
            const elements = agentCard.querySelectorAll(`[data-field="${field}"]`);
            elements.forEach(element => {
                element.innerHTML = value || (field === 'thought' ? 'Thinking...' : 'Planning...');
            });
            if (field === 'task') {
                const headerProgress = agentCard.querySelector('[data-field="header-task"]');
                if (headerProgress) {
                    headerProgress.innerHTML = value;
                }
            }
        });
        agentState.style.display = agentData.thought ? 'block' : 'none';
    }
}

// Function to update CLI output
function updateCliOutput(agentCard, agentData) {
    const outputElement = agentCard.querySelector('.cli-output');
    if (outputElement && agentData.aider_output) {
        const currentText = outputElement.textContent || '';
        if (agentData.aider_output !== currentText) {
            outputElement.innerHTML = agentData.aider_output;
            outputElement.scrollTop = outputElement.scrollHeight;
            outputElement.style.transition = 'background-color 0.5s';
            outputElement.style.backgroundColor = '#2e4052';
            setTimeout(() => {
                outputElement.style.backgroundColor = '#1e1e1e';
            }, 500);
        }
    }
}

// Function to update status badge
function updateStatusBadge(agentCard, agentData) {
    const statusBadge = agentCard.querySelector('.badge');
    if (statusBadge && agentData.status) {
        statusBadge.textContent = agentData.status;
        statusBadge.className = `badge ${agentData.status === 'in_progress' ? 'bg-primary' :
            agentData.status === 'pending' ? 'bg-warning' : 'bg-success'}`;
    }
}

// Function to update PR info
function updatePrInfo(agentCard, agentData) {
    const prInfoSection = agentCard.querySelector('#pr-info-' + agentId);
    if (prInfoSection && agentData.pr_url) {
        prInfoSection.style.display = 'block';
        const prLink = prInfoSection.querySelector('a.alert-link');
        if (prLink) {
            prLink.href = agentData.pr_url;
            prLink.textContent = 'View on GitHub';
        }
    }
}

// Function to update history
function updateHistory(agentCard, agentData) {
    const historySection = agentCard.querySelector('.agent-history');
    if (historySection && agentData.history) {
        const historyList = historySection.querySelector('ul');
        historyList.innerHTML = ''; // Clear existing history

        agentData.history.forEach(entry => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Progress:</strong> ${entry.progress || 'N/A'}<br><strong>Thought:</strong> ${entry.thought || 'N/A'}`;
            historyList.appendChild(listItem);
        });
    }
}

// Function to update debug info
function updateDebugInfo(agentCard, responseClone) {
    const agentId = agentCard.id.replace('agent-', '');
    const currentDebug = agentCard.querySelector('.debug-info');
    
    responseClone.text().then(html => {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const newDebug = tempDiv.querySelector(`#agent-${agentId} .debug-info`);
        if (currentDebug && newDebug) {
            const currentLength = getOutputLength(currentDebug);
            const newLength = getOutputLength(newDebug);
            if (currentLength !== newLength) {
                currentDebug.innerHTML = newDebug.innerHTML;
                console.log(`Agent ${agentId} debug info updated:`, {
                    previousLength: currentLength,
                    newLength: newLength
                });
            }
        }
    });
}


// Function to force an immediate update
function forceUpdate() {
    fetchUpdates();
}

// Update toast show function
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('deleteToast');
    const toastBody = document.getElementById('toastMessage');
    toastBody.classList.remove('success', 'error');
    toastBody.classList.add(type);
    const icon = type === 'success' ? 'check-circle' : 'exclamation-circle';
    toastBody.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
    `;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// DOM Ready handlers
document.addEventListener('DOMContentLoaded', () => {
    // Handle collapse icon rotation
    document.querySelectorAll('.card-header[data-bs-toggle="collapse"]').forEach(header => {
        header.addEventListener('click', () => {
            const icon = header.querySelector('.collapse-icon');
            const isCollapsed = header.classList.contains('collapsed');
            icon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(-90deg)';
        });
    });

    // Initial scroll to bottom and history setup
    const outputs = document.querySelectorAll('.cli-output');
    outputs.forEach(output => {
        output.scrollTop = output.scrollHeight;
        const agentId = output.closest('.agent-card').id.replace('agent-', '');
        lastOutputLengths[agentId] = output.textContent.length;
        console.log(`Initialized agent ${agentId} output length:`, lastOutputLengths[agentId]);

        // Add history toggle
        const historyToggle = output.closest('.agent-card').querySelector('.history-toggle');
        if (historyToggle) {
            historyToggle.addEventListener('click', () => {
                const history = output.closest('.agent-card').querySelector('.agent-history');
                history.classList.toggle('show');
            });
        }
    });

    // Set up updates for CLI output with a reasonable interval
    setInterval(forceUpdate, 5000); // Check for updates every 5 seconds

    // Hide loader
    const loader = document.querySelector('.page-loader');
    if (loader) {
        setTimeout(() => {
            loader.style.opacity = '0';
            loader.style.transition = 'opacity 0.5s ease-out';
            setTimeout(() => {
                loader.style.display = 'none';
            }, 500);
        }, 500);
    }

    // Add help button to header
    const header = document.querySelector('.container > .d-flex');
    const helpButton = document.createElement('button');
    helpButton.className = 'btn btn-outline-secondary ms-2';
    helpButton.innerHTML = '<i class="fas fa-keyboard me-1"></i>Shortcuts';
    helpButton.onclick = () => {
        const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
        helpModal.show();
    };
    header.querySelector('div').appendChild(helpButton);
});

// Delete agent functionality
document.getElementById('agentList').addEventListener('click', async (e) => {
    if (e.target.classList.contains('delete-agent-btn')) {
        const agentId = e.target.getAttribute('data-agent-id');
        const agentCard = document.getElementById(`agent-${agentId}`);
        try {
            const response = await fetch(`/delete_agent/${agentId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (result.success) {
                if (agentCard) {
                    agentCard.style.transition = 'all 0.5s ease-out';
                    agentCard.style.opacity = '0';
                    agentCard.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        agentCard.remove();
                        delete lastOutputLengths[agentId];
                    }, 500);
                }
                showToast(`Agent ${agentId} deleted successfully`, 'success');
            } else {
                showToast(result.error || `Failed to delete agent ${agentId}`, 'error');
            }
        } catch (error) {
            showToast(`Error deleting agent: ${error.message}`, 'error');
        }
    }
});

// Delete all agents functionality
document.getElementById('deleteAllAgents').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete all agents? This action cannot be undone.')) {
        return;
    }

    const agents = document.querySelectorAll('.agent-card');
    let successCount = 0;
    let errorCount = 0;

    for (const agent of agents) {
        const agentId = agent.id.replace('agent-', '');
        try {
            const response = await fetch(`/delete_agent/${agentId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (result.success) {
                agent.style.transition = 'all 0.5s ease-out';
                agent.style.opacity = '0';
                agent.style.transform = 'translateY(20px)';
                setTimeout(() => agent.remove(), 500);
                successCount++;
            } else {
                errorCount++;
            }
        } catch (error) {
            errorCount++;
            console.error(`Error deleting agent ${agentId}:`, error);
        }
    }

    showToast(
        `Deleted ${successCount} agent${successCount !== 1 ? 's' : ''}` +
        (errorCount > 0 ? `. Failed to delete ${errorCount} agent${errorCount !== 1 ? 's' : ''}.` : '.'),
        errorCount > 0 ? 'error' : 'success'
    );

    if (errorCount === 0) {
        setTimeout(() => location.reload(), 1000);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }

    switch (e.key.toLowerCase()) {
        case 'r':
            e.preventDefault();
            forceUpdate();
            showToast('Refreshing agents...', 'info');
            break;
        case '?':
            e.preventDefault();
            const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
            helpModal.show();
            break;
        case 'escape':
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
            break;
    }
});
