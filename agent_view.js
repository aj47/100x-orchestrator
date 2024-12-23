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

        // Update each agent's output and PR link
        for (const [agentId, agentData] of Object.entries(tasksData.agents)) {
            const agentCard = document.getElementById(`agent-${agentId}`);
            if (!agentCard) continue;

            const outputElement = agentCard.querySelector('.agent-output');
            if (outputElement) {
                outputElement.innerHTML = agentData.aider_output;
            }

            const prLinkElement = agentCard.querySelector('.pr-link');
            if (prLinkElement) {
                if (agentData.pr_url) {
                    prLinkElement.href = agentData.pr_url;
                    prLinkElement.textContent = 'View PR';
                    prLinkElement.style.display = 'block'; // Show the link
                } else {
                    prLinkElement.style.display = 'none'; // Hide the link if no PR URL
                }
            }
        }
    } catch (error) {
        console.error('Error fetching updates:', error);
        showToast('Error fetching agent updates', 'error');
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
    toastBody.innerHTML = `<span>${message}</span>`;
    toastEl.classList.add('show');
    setTimeout(() => {
        toastEl.classList.remove('show');
    }, 5000);
}

// Initial fetch on load
document.addEventListener('DOMContentLoaded', fetchUpdates);

// Periodic updates
setInterval(fetchUpdates, 5000);
