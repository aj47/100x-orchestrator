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
                    'thought': (agentData.progress || '') + (agentData.thought ? `\n${agentData.thought}` : ''),
                    'progress': '', // Progress moved to thought
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
                    if (field === 'progress') {
                        const headerProgress = agentCard.querySelector('[data-field="header-progress"]');
                        if (headerProgress) {
                            headerProgress.innerHTML = value;
                        }
                    }
                });

                // Toggle visibility based on thought
                agentState.style.display = agentData.thought ? 'block' : 'none';
            }

            // Update CLI output if it has changed
            const outputElement = agentCard.querySelector('.cli-output');

            if (outputElement && agentData.aider_output) {
                const currentText = outputElement.textContent || '';
                
                // Only update if output has changed
                if (agentData.aider_output !== currentText) {
                    outputElement.innerHTML = agentData.aider_output;
                    outputElement.scrollTop = outputElement.scrollHeight;
                    
                    // Flash effect for new content
                    outputElement.style.transition = 'background-color 0.5s';
                    outputElement.style.backgroundColor = '#2e4052';
                    setTimeout(() => {
                        outputElement.style.backgroundColor = '#1e1e1e';
                    }, 500);
                }
            }

            // Update status and timestamps
            const statusBadge = agentCard.querySelector('.badge');
            if (statusBadge && agentData.status) {
                statusBadge.textContent = agentData.status;
                statusBadge.className = `badge ${agentData.status === 'in_progress' ? 'bg-primary' : 
                                    agentData.status === 'pending' ? 'bg-warning' : 'bg-success'}`;
            }

            // Update PR info if it exists
            const prInfoSection = agentCard.querySelector('#pr-info-' + agentId);
            if (prInfoSection && agentData.pr_url) {
                prInfoSection.style.display = 'block';
                const prLink = prInfoSection.querySelector('a.alert-link');
                if (prLink) {
                    prLink.href = agentData.pr_url;
                    prLink.textContent = 'View on GitHub';
                }
            }

            // Update timestamps
            const lastUpdated = agentCard.querySelector('.card-footer div:last-child');
            if (lastUpdated && agentData.last_updated) {
                lastUpdated.innerHTML = `<i class="fas fa-clock me-1"></i>Last Updated: ${agentData.last_updated}`;
            }

            // Update task in header
            const taskElement = agentCard.querySelector('[data-field="task"]');
            if (taskElement) {
                taskElement.textContent = agentData.task || 'No task assigned';
            }
        }
        
        // Create temporary div to parse HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = await responseClone.text(); // Use cloned response
        
        // Update each agent's output
        const agents = document.querySelectorAll('.agent-card');
        agents.forEach(agent => {
            const agentId = agent.id.replace('agent-', '');
            const newAgentCard = tempDiv.querySelector(`#agent-${agentId}`);
            
            // ... (rest of the code remains the same)
        });
    } catch (error) {
        console.error('Error fetching updates:', error);
    }
}

// ... (rest of the code remains the same)
