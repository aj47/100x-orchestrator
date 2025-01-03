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
        
        // Update each agent's output
        for (const [agentId, agentData] of Object.entries(tasksData.agents)) {
            const agentCard = document.getElementById(`agent-${agentId}`);
            if (!agentCard) continue;

            // Find agent state container
            const agentState = agentCard.querySelector('.agent-state');
            if (agentState) {
                // Update all fields using data attributes
                const fields = {
                    'thought': agentData.thought || '',
                    'progress': agentData.progress || '',
                    'future': agentData.future || '',
                    'action': agentData.last_action || ''
                };

                // Update each field
                Object.entries(fields).forEach(([field, value]) => {
                    // Update all elements with this data-field, both in agent state and footer
                    const elements = agentCard.querySelectorAll(`[data-field="${field}"]`);
                    elements.forEach(element => {
                        element.innerHTML = value || (field === 'thought' ? 'Thinking...' : 'Planning...');
                    });
                
                    // Also update header progress if this is the progress field
                    if (field === 'task') {
                        const headerProgress = agent