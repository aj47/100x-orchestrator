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

        // ... (rest of the existing fetchUpdates function remains unchanged) ...
    } catch (error) {
        console.error('Error fetching updates:', error);
        // Display a user-friendly error message here
        alert('Error fetching agent updates. Please check your network connection.');
    }
}

// Function to fetch and display agent history
async function fetchAndDisplayHistory(agentId) {
    const historyContainer = document.getElementById(`history-${agentId}`);
    if (!historyContainer) return;

    try {
        const response = await fetch(`/agent/${agentId}/history`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const history = data.history || [];

        historyContainer.innerHTML = ''; // Clear existing history

        if (history.length === 0) {
            historyContainer.innerHTML = '<p>No history available.</p>';
            return;
        }

        const historyList = document.createElement('ul');
        history.forEach(item => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<strong>Progress:</strong> ${item.progress}<br>
                                 <strong>Thought:</strong> ${item.thought}<br>
                                 <strong>Action:</strong> ${item.action}`;
            historyList.appendChild(listItem);
        });
        historyContainer.appendChild(historyList);
    } catch (error) {
        console.error('Error fetching agent history:', error);
        historyContainer.innerHTML = `<p>Error loading history: ${error.message}</p>`;
    }
}


// Function to force an immediate update
function forceUpdate() {
    fetchUpdates();
}

// Update toast show function
function showToast(message, type = 'success') {
    // ... (existing showToast function remains unchanged) ...
}

// DOM Ready handlers
document.addEventListener('DOMContentLoaded', () => {
    // ... (existing DOMContentLoaded handlers remain unchanged) ...

    // Fetch and display history for each agent
    const agents = document.querySelectorAll('.agent-card');
    agents.forEach(agent => {
        const agentId = agent.id.replace('agent-', '');
        fetchAndDisplayHistory(agentId);
    });
});

// Delete agent functionality
document.getElementById('agentList').addEventListener('click', async (e) => {
    // ... (existing delete agent handler remains unchanged) ...
});

// Delete all agents functionality
document.getElementById('deleteAllAgents').addEventListener('click', async () => {
    // ... (existing delete all agents handler remains unchanged) ...
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // ... (existing keyboard shortcuts handler remains unchanged) ...
});

