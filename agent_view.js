function getOutputLength(debugElement) {
    const lengthElement = debugElement.querySelector('.label');
    if (lengthElement && lengthElement.textContent.includes('Output Length')) {
        const lengthText = lengthElement.parentElement.textContent;
        return parseInt(lengthText.split(':')[1].trim());
    }
    return 0;
}

async function fetchUpdates() {
    try {
        const response = await fetch('/tasks/tasks.json');
        const responseClone = response.clone(); // Clone the response
        const tasksData = await response.json();
        // Update each agent's output
        for (const [agentId, agentData] of Object.entries(tasksData.agents)) {
            const agentCard = document.getElementById(`agent-${agentId}`);
            if (!agentCard) continue;

            const agentHistoryDiv = agentCard.querySelector('.agent-history');
            if (!agentHistoryDiv) {
                const newDiv = document.createElement('div');
                newDiv.classList.add('agent-history');
                newDiv.style.overflowY = 'auto';
                newDiv.style.height = '200px';
                agentCard.appendChild(newDiv);
            } else {
                agentHistoryDiv.innerHTML = ''; // Clear existing content before updating
            }

            // Assuming existing agent state elements are children of agentCard.  Adjust if needed.
            const children = [...agentCard.children];
            children.forEach(child => {
                if (child.classList.contains('agent-history')) return; // Skip the agent-history div itself
                agentCard.querySelector('.agent-history').appendChild(child);
            });

            // ... rest of the fetchUpdates function ...
        }
    } catch (error) {
        console.error('Error fetching updates:', error);
    }
}

function forceUpdate() {
    fetchUpdates();
}

function showToast(message, type = 'success') {
    const toastEl = document.getElementById('deleteToast');
    const toastBody = document.getElementById('toastMessage');

    // Remove existing classes
    toastBody.classList.remove('success', 'error');
    // Add appropriate class
    toastBody.classList.add(type);

    // Add icon based on type
    // ...
}
