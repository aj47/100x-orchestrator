// UI Elements
const socketStatus = document.querySelector('.socket-status');
const pageLoader = document.querySelector('.page-loader');
const agentList = document.getElementById('agentList');
const activeAgentCount = document.getElementById('activeAgentCount');

// Debug section handling
function initializeDebugSections() {
    document.querySelectorAll('.debug-header').forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            const isExpanded = header.getAttribute('aria-expanded') === 'true';
            
            header.setAttribute('aria-expanded', !isExpanded);
            content.classList.toggle('show');
            
            const icon = header.querySelector('.fa-chevron-down');
            if (icon) {
                icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
            }
        });
    });
}

// Scroll handling
function isNearBottom(element, threshold = 50) {
    return element.scrollHeight - element.scrollTop - element.clientHeight < threshold;
}

function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

// Agent count updates
function updateActiveAgentCount() {
    const activeAgents = document.querySelectorAll('.agent-card').length;
    if (activeAgentCount) {
        activeAgentCount.innerHTML = `
            <i class="fas fa-users me-2"></i>
            ${activeAgents} Active Agent${activeAgents !== 1 ? 's' : ''}
        `;
        
        // Animate count change
        activeAgentCount.classList.add('highlight');
        setTimeout(() => activeAgentCount.classList.remove('highlight'), 1000);
    }
}

// Timestamp updates
function updateTimestamp(agentCard, timestamp) {
    if (!timestamp) return;
    
    const lastUpdatedElements = agentCard.querySelectorAll('.last-updated');
    const date = new Date(timestamp);
    if (isNaN(date)) return;
    
    const formattedTime = new Intl.DateTimeFormat('default', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);

    lastUpdatedElements.forEach(element => {
        if (!element) return;
        if (element.textContent !== formattedTime) {
            element.textContent = formattedTime;
            element.classList.add('timestamp-updated');
            setTimeout(() => element.classList.remove('timestamp-updated'), 1000);
        }
    });
}

// Enhanced toast notifications
function showToast(message, type = 'success', duration = 3000) {
    const toastEl = document.getElementById('deleteToast');
    if (!toastEl) return;
    
    const toastBody = toastEl.querySelector('.toast-body');
    if (!toastBody) return;
    
    const icons = {
        success: 'check-circle',
        warning: 'exclamation-triangle',
        error: 'exclamation-circle',
        info: 'info-circle'
    };
    
    toastEl.className = `toast border-${type}`;
    toastBody.className = `toast-body text-${type}`;
    toastBody.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${icons[type]} me-2"></i>
            <div>${message}</div>
        </div>
    `;
    
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: duration
    });
    
    // Remove existing show class and force reflow
    toastEl.classList.remove('show');
    void toastEl.offsetWidth;
    
    toast.show();
}

// Socket Event Handlers
let socketConnected = false;

socket.on('connect', () => {
    socketConnected = true;
    hideLoader();
    showToast('Connected to server', 'success');
    
    // Request initial data
    const agents = document.querySelectorAll('[data-agent-id]');
    agents.forEach(agent => {
        const agentId = agent.getAttribute('data-agent-id');
        if (agentId === 'orchestrator') return;
        socket.emit('request_agent_output', { agent_id: agentId });
    });
    
    updateActiveAgentCount();
});

socket.on('disconnect', () => {
    socketConnected = false;
    showToast('Disconnected from server. Attempting to reconnect...', 'warning', 5000);
});

socket.on('connect_error', (error) => {
    showToast(`Connection error: ${error.message}`, 'error', 5000);
});

socket.on('agent_output_update', function(data) {
    const { agent_id, new_output, timestamp } = data;
    const agentCard = document.getElementById(`agent-${agent_id}`);
    if (!agentCard) return;
    
    const outputElement = agentCard.querySelector('.cli-output');
    if (!outputElement) return;
    
    const wasNearBottom = isNearBottom(outputElement);
    
    // Handle code blocks with syntax highlighting
    if (new_output.trim().startsWith('```')) {
        const code = new_output.replace(/```\w*\n?|\n?```/g, '');
        const language = detectLanguage(code);
        const highlightedCode = Prism.highlight(code, Prism.languages[language], language);
        
        outputElement.innerHTML += `
            <div class="code-block ${language}">
                ${highlightedCode}
            </div>
        `;
    } else {
        const escapedOutput = escapeHtml(new_output);
        outputElement.innerHTML += escapedOutput + "\n";
    }
    
    if (wasNearBottom) {
        scrollToBottom(outputElement);
    }
    
    updateTimestamp(agentCard, timestamp);
});

socket.on('agent_status_update', function(data) {
    const { agent_id, status, state_info, last_updated } = data;
    const agentCard = document.getElementById(`agent-${agent_id}`);
    if (!agentCard) return;
    
    const statusBadge = agentCard.querySelector('.status-badge');
    const outputElement = agentCard.querySelector('.cli-output');
    
    if (statusBadge) {
        updateAgentStatus(statusBadge, status, state_info);
    }
    
    if (outputElement && state_info?.last_error) {
        outputElement.classList.add('error-state');
        showToast(state_info.last_error, 'error');
    }
    
    updateTimestamp(agentCard, last_updated);
});

socket.on('agent_error', function(data) {
    const { error, agent_id } = data;
    showToast(error, 'error', 5000);
    
    if (agent_id) {
        const agentCard = document.getElementById(`agent-${agent_id}`);
        if (agentCard) {
            const outputElement = agentCard.querySelector('.cli-output');
            if (outputElement) {
                outputElement.classList.add('error-state');
                // Trigger error animation
                void outputElement.offsetWidth;
                outputElement.classList.add('error-shake');
                setTimeout(() => outputElement.classList.remove('error-shake'), 500);
            }
        }
    }
});

// Initialize UI Elements and Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeDebugSections();
    
    // Initialize tooltips
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Initialize CLI outputs
    const outputs = document.querySelectorAll('.cli-output');
    outputs.forEach(output => {
        scrollToBottom(output);
    });

    // Search functionality with debounce
    const searchInput = document.getElementById('agentSearch');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.toLowerCase();
                const agents = document.querySelectorAll('.agent-card');
                let foundMatch = false;
                
                agents.forEach(card => {
                    const wrapper = card.closest('.agent-wrapper');
                    const task = card.getAttribute('data-task') || '';
                    const id = card.getAttribute('data-id') || '';
                    const matches = task.includes(query) || id.includes(query);
                    
                    if (wrapper) {
                        wrapper.style.display = matches ? '' : 'none';
                        if (matches) {
                            wrapper.style.animation = 'fadeIn 0.3s ease';
                            foundMatch = true;
                        }
                    }
                });
                
                // Show no results message
                const noResultsEl = document.getElementById('noResults');
                if (!foundMatch && query.length > 0) {
                    if (!noResultsEl) {
                        const message = document.createElement('div');
                        message.id = 'noResults';
                        message.className = 'alert alert-warning mt-3';
                        message.innerHTML = `
                            <i class="fas fa-search me-2"></i>
                            No agents match your search criteria
                        `;
                        agentList.appendChild(message);
                    }
                } else if (noResultsEl) {
                    noResultsEl.remove();
                }
            }, 300);
        });
    }

    // Delete agent handlers with improved feedback
    agentList?.addEventListener('click', async (e) => {
        const deleteBtn = e.target.closest('.delete-agent-btn');
        if (!deleteBtn) return;
            
        const agentId = deleteBtn.getAttribute('data-agent-id');
        const agentCard = document.getElementById(`agent-${agentId}`);
        
        // Disable button and show loading state
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
        if (confirm(`Are you sure you want to delete agent ${agentId}?`)) {
            try {
                const response = await fetch(`/delete_agent/${agentId}`, { 
                    method: 'DELETE' 
                });
                const result = await response.json();
                    
                if (result.success) {
                    const wrapper = agentCard.closest('.agent-wrapper');
                    wrapper.style.animation = 'fadeOut 0.3s ease';
                    
                    showToast(`Agent ${agentId} deleted successfully`, 'success');
                    
                    setTimeout(() => {
                        wrapper.remove();
                        updateActiveAgentCount();
                    }, 300);
                } else {
                    showToast(result.error || `Failed to delete agent ${agentId}`, 'error');
                }
            } catch (error) {
                showToast(`Error deleting agent: ${error.message}`, 'error');
            } finally {
                // Reset button state if operation failed
                if (deleteBtn) {
                    deleteBtn.disabled = false;
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                }
            }
        } else {
            // Reset button state if cancelled
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
        }
    });
});

// Enhanced loader handling
function hideLoader() {
    if (pageLoader && socketConnected) {
        pageLoader.classList.add('hiding');
        setTimeout(() => {
            pageLoader.style.display = 'none';
            pageLoader.classList.remove('hiding');
        }, 300);
    }
}

// Enhanced status updates with animations
function updateAgentStatus(badge, status, stateInfo) {
    let badgeClass, icon, text;
    
    if (!stateInfo?.stream_active && status !== 'abandoned') {
        if (stateInfo?.last_error) {
            badgeClass = 'bg-danger';
            icon = 'exclamation-circle';
            text = 'Error';
            showToast(`Agent error: ${stateInfo.last_error}`, 'error');
        } else {
            badgeClass = 'bg-warning';
            icon = 'exclamation-triangle';
            text = 'Stalled';
            showToast('Agent connection stalled', 'warning');
        }
    } else {
        switch(status) {
            case 'error':
                badgeClass = 'bg-danger';
                icon = 'exclamation-circle';
                text = 'Error';
                break;
            case 'completed':
                badgeClass = 'bg-success';
                icon = 'check-circle';
                text = 'Completed';
                break;
            case 'in_progress':
                badgeClass = 'bg-primary';
                icon = 'spinner fa-spin';
                text = stateInfo?.conversation_phase 
                    ? stateInfo.conversation_phase.charAt(0).toUpperCase() + 
                      stateInfo.conversation_phase.slice(1)
                    : 'Processing';
                break;
            case 'abandoned':
                badgeClass = 'bg-dark';
                icon = 'question-circle';
                text = 'Abandoned';
                showToast('Agent session abandoned', 'warning');
                badge.closest('.agent-card').classList.add('abandoned-state');
                break;
            default:
                badgeClass = 'bg-secondary';
                icon = 'circle';
                text = status?.charAt(0).toUpperCase() + status?.slice(1) || 'Unknown';
        }
    }
    
    // Apply changes with animation
    badge.style.opacity = '0';
    setTimeout(() => {
        badge.className = `badge status-badge ${badgeClass}`;
        badge.innerHTML = `<i class="fas fa-${icon} me-1"></i><span class="status-text">${text}</span>`;
        badge.style.opacity = '1';
    }, 150);
}

// Language detection for syntax highlighting
function detectLanguage(code) {
    const patterns = {
        python: /\b(def|class|import|from|if\s+__name__|async|await)\b/,
        javascript: /\b(function|const|let|var|import\s+from|=>)\b/,
        html: /<\/?[a-z][\s\S]*>/i,
        css: /[{}\s\S]*(:|{)/,
        json: /^[\s\n]*[{\[]/
    };

    for (const [lang, pattern] of Object.entries(patterns)) {
        if (pattern.test(code)) return lang;
    }
    
    return 'plaintext';
}

// Safe HTML escaping
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy output functionality
function addCopyButton(outputElement) {
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.title = 'Copy output';
    
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(outputElement.textContent);
            copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            }, 2000);
        } catch (err) {
            showToast('Failed to copy output', 'error');
        }
    });
    
    outputElement.parentElement.appendChild(copyBtn);
}

// Add copy buttons to all CLI outputs
document.querySelectorAll('.cli-output').forEach(addCopyButton);