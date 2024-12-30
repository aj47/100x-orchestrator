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
        }
        
        // Create temporary div to parse HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = await responseClone.text(); // Use cloned response
        
        // Update each agent's output
        const agents = document.querySelectorAll('.agent-card');
        agents.forEach(agent => {
            const agentId = agent.id.replace('agent-', '');
            const newAgentCard = tempDiv.querySelector(`#agent-${agentId}`);
            
            if (newAgentCard) {
                // Update CLI output if it has changed
                const currentOutput = agent.querySelector('.cli-output');
                const newOutput = newAgentCard.querySelector('.cli-output');
                
                if (currentOutput && newOutput) {
                    const currentText = currentOutput.textContent || '';
                    const newText = newOutput.textContent || '';
                    
                    // Initialize last output length if not exists
                    if (!(agentId in lastOutputLengths)) {
                        lastOutputLengths[agentId] = currentText.length;
                    }
                    
                    // Check if output has changed
                    if (newText.length > lastOutputLengths[agentId]) {
                        console.log(`Agent ${agentId} output updated:`, {
                            previousLength: lastOutputLengths[agentId],
                            newLength: newText.length,
                            diff: newText.substring(lastOutputLengths[agentId])
                        });
                        
                        // Update the output
                        currentOutput.innerHTML = newOutput.innerHTML;
                        lastOutputLengths[agentId] = newText.length;
                        
                        // Auto-scroll to bottom of output
                        currentOutput.scrollTop = currentOutput.scrollHeight;
                        
                        // Flash the output box to indicate new content
                        currentOutput.style.transition = 'background-color 0.5s';
                        currentOutput.style.backgroundColor = '#2e4052';
                        setTimeout(() => {
                            currentOutput.style.backgroundColor = '#1e1e1e';
                        }, 500);
                    }
                }
                
                // Update status badge
                const currentStatus = agent.querySelector('.badge');
                const newStatus = newAgentCard.querySelector('.badge');
                if (currentStatus && newStatus) {
                    currentStatus.className = newStatus.className;
                    currentStatus.textContent = newStatus.textContent;
                }
                
                // Update debug info
                const currentDebug = agent.querySelector('.debug-info');
                const newDebug = newAgentCard.querySelector('.debug-info');
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
                
                // Update last critique if it exists
                const currentCritique = agent.querySelector('.progress-section:last-child');
                const newCritique = newAgentCard.querySelector('.progress-section:last-child');
                if (currentCritique && newCritique && currentCritique.innerHTML !== newCritique.innerHTML) {
                    currentCritique.innerHTML = newCritique.innerHTML;
                    console.log(`Agent ${agentId} critique updated`);
                }
            }
        });
    } catch (error) {
        console.error('Error fetching updates:', error);
    }
}

// Function to force an immediate update
function forceUpdate() {
    fetchUpdates();
}

// Update toast show function
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('deleteToast');
    const toastBody = document.getElementById('toastMessage');
    
    // Remove existing classes
    toastBody.classList.remove('success', 'error');
    // Add appropriate class
    toastBody.classList.add(type);
    
    // Add icon based on type
    const icon = type === 'success' ? 'check-circle' : 'exclamation-circle';
    toastBody.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
    `;
    
    // Show toast
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

    // Initial scroll to bottom
    const outputs = document.querySelectorAll('.cli-output');
    outputs.forEach(output => {
        output.scrollTop = output.scrollHeight;
        
        // Store initial output lengths
        const agentId = output.closest('.agent-card').id.replace('agent-', '');
        lastOutputLengths[agentId] = output.textContent.length;
        console.log(`Initialized agent ${agentId} output length:`, lastOutputLengths[agentId]);
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

// Handle review feedback submission
document.addEventListener('submit', async (e) => {
    if (e.target.classList.contains('review-form')) {
        e.preventDefault();
        const agentId = e.target.getAttribute('data-agent-id');
        const formData = new FormData(e.target);
        const feedback = formData.get('feedback');
        
        try {
            const response = await fetch(`/submit_review/${agentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    feedback: feedback,
                    type: 'manual'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showToast('Review feedback submitted successfully', 'success');
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById(`reviewModal-${agentId}`));
                modal.hide();
                // Refresh agent view
                forceUpdate();
            } else {
                showToast(result.error || 'Failed to submit review', 'error');
            }
        } catch (error) {
            showToast(`Error submitting review: ${error.message}`, 'error');
        }
    }
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
                    // Add fade out animation
                    agentCard.style.transition = 'all 0.5s ease-out';
                    agentCard.style.opacity = '0';
                    agentCard.style.transform = 'translateY(20px)';
                    
                    // Remove after animation
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

    // Show result message
    showToast(
        `Deleted ${successCount} agent${successCount !== 1 ? 's' : ''}` + 
        (errorCount > 0 ? `. Failed to delete ${errorCount} agent${errorCount !== 1 ? 's' : ''}.` : '.'),
        errorCount > 0 ? 'error' : 'success'
    );

    // Refresh page if all agents were deleted successfully
    if (errorCount === 0) {
        setTimeout(() => location.reload(), 1000);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts if user is typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }

    switch(e.key.toLowerCase()) {
        case 'r':
            // Force refresh
            e.preventDefault();
            forceUpdate();
            showToast('Refreshing agents...', 'info');
            break;
        case '?':
            // Show help modal
            e.preventDefault();
            const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
            helpModal.show();
            break;
        case 'escape':
            // Close all modals
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
