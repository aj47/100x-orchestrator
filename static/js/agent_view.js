// Global state
const lastOutputLengths = {};
let updateInterval;
let countdownInterval;



// Helper Functions
function getOutputLength(debugElement) {
    const lengthElement = debugElement.querySelector('.label');
    if (lengthElement && lengthElement.textContent.includes('Output Length')) {
        const lengthText = lengthElement.parentElement.textContent;
        return parseInt(lengthText.split(':')[1].trim());
    }
    return 0;
}

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

// Update Functions
function updateCountdown() {
    const countdownEl = document.getElementById('countdown');
    let timeLeft = parseInt(countdownEl.textContent);
    
    if (timeLeft > 0) {
        countdownEl.textContent = timeLeft - 1;
    } else {
        fetchUpdates();
        countdownEl.textContent = "5";
    }
}

async function fetchUpdates() {
    const updateIndicator = document.getElementById('updateIndicator');
    updateIndicator.style.display = 'inline-block';

    try {
        const response = await AUTH.fetch('/tasks/tasks.json');
        const tasksData = await response.json();
        
        for (const [agentId, agentData] of Object.entries(tasksData.agents)) {
            const agentCard = document.getElementById(`agent-${agentId}`);
            if (!agentCard) continue;

            updateAgentCard(agentCard, agentData, agentId);
        }
    } catch (error) {
        console.error('Error fetching updates:', error);
    } finally {
        updateIndicator.style.display = 'none';
    }
}

function updateAgentCard(agentCard, agentData, agentId) {
    // Update CLI output
    const outputElement = agentCard.querySelector('.cli-output');
    if (outputElement && agentData.aider_output) {
        const currentText = outputElement.textContent || '';
        
        if (agentData.aider_output !== currentText) {
            outputElement.innerHTML = agentData.aider_output;
            outputElement.scrollTop = outputElement.scrollHeight;
            
            flashElement(outputElement);
        }
    }

    // Update agent state
    updateAgentState(agentCard, agentData);

    // Update timestamps
    updateTimestamps(agentCard, agentData);
}

function updateAgentState(agentCard, agentData) {
    const stateElements = {
        progress: agentCard.querySelector('.progress-item'),
        thought: agentCard.querySelector('.thought-item'),
        future: agentCard.querySelector('.future-item'),
        action: agentCard.querySelector('.action-item')
    };

    if (stateElements.progress) stateElements.progress.innerHTML = `<strong>Progress:</strong> ${agentData.progress}`;
    if (stateElements.thought) stateElements.thought.innerHTML = `<strong>Thought:</strong> ${agentData.thought}`;
    if (stateElements.future) stateElements.future.innerHTML = `<strong>Future:</strong> ${agentData.future}`;
    if (stateElements.action) stateElements.action.innerHTML = `<strong>Last Action:</strong> ${agentData.last_action}`;
}

function updateTimestamps(agentCard, agentData) {
    const lastUpdated = agentCard.querySelector('.card-footer div:last-child');
    if (lastUpdated && agentData.last_updated) {
        lastUpdated.innerHTML = `<i class="fas fa-clock me-1"></i>Last Updated: ${agentData.last_updated}`;
    }
}

function flashElement(element) {
    element.style.transition = 'background-color 0.5s';
    element.style.backgroundColor = '#2e4052';
    setTimeout(() => {
        element.style.backgroundColor = '#1e1e1e';
    }, 500);
}

// Delete Functions
async function deleteAgent(agentId) {
    try {
        const response = await AUTH.fetch(`/delete_agent/${agentId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        const agentCard = document.getElementById(`agent-${agentId}`);
        
        if (result.success && agentCard) {
            fadeOutAndRemove(agentCard);
            delete lastOutputLengths[agentId];
            showToast(`Agent ${agentId} deleted successfully`, 'success');
        } else {
            showToast(result.error || `Failed to delete agent ${agentId}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting agent:', error);
        showToast(`Error deleting agent: ${error.message}`, 'error');
    }
}

async function deleteAllAgents() {
    if (!confirm('Are you sure you want to delete all agents? This action cannot be undone.')) {
        return;
    }

    const agents = document.querySelectorAll('.agent-card');
    let successCount = 0;
    let errorCount = 0;

    for (const agent of agents) {
        const agentId = agent.dataset.agentId;
        try {
            const response = await AUTH.fetch(`/delete_agent/${agentId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                fadeOutAndRemove(agent);
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
}

function fadeOutAndRemove(element) {
    element.style.transition = 'all 0.5s ease-out';
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    setTimeout(() => element.remove(), 500);
}

// Event Handlers
function setupEventListeners() {
    // Delete agent buttons
    document.getElementById('agentList').addEventListener('click', (e) => {
        if (e.target.closest('.delete-agent-btn')) {
            const agentCard = e.target.closest('.agent-card');
            const agentId = agentCard.dataset.agentId;
            deleteAgent(agentId);
        }
    });

    // Delete all agents button
    document.getElementById('deleteAllAgents').addEventListener('click', deleteAllAgents);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        switch(e.key.toLowerCase()) {
            case 'r':
                e.preventDefault();
                fetchUpdates();
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
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!AUTH.init()) return;

    setupEventListeners();
    
    // Initialize output lengths
    document.querySelectorAll('.cli-output').forEach(output => {
        const agentId = output.closest('.agent-card').id.replace('agent-', '');
        lastOutputLengths[agentId] = output.textContent.length;
        output.scrollTop = output.scrollHeight;
    });

    // Start intervals
    countdownInterval = setInterval(updateCountdown, 1000);
    updateInterval = setInterval(fetchUpdates, 1000);

    // Hide loader
    const loader = document.querySelector('.page-loader');
    if (loader) {
        setTimeout(() => {
            loader.style.opacity = '0';
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

// Cleanup
window.addEventListener('beforeunload', () => {
    clearInterval(updateInterval);
    clearInterval(countdownInterval);
});