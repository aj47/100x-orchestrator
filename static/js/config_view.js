document.addEventListener('DOMContentLoaded', () => {
    // Load current configuration
    loadCurrentConfig();

    // Handle form submission
    document.getElementById('configForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const resultDiv = document.getElementById('result');
        const alertDiv = resultDiv.querySelector('.alert');
        
        try {
            const response = await fetch('/config/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    orchestrator_model: document.getElementById('orchestratorModel').value,
                    aider_model: document.getElementById('aiderModel').value,
                    agent_model: document.getElementById('agentModel').value
                })
            });

            const data = await response.json();
            
            resultDiv.style.display = 'block';
            if (data.success) {
                alertDiv.className = 'alert alert-success';
                alertDiv.textContent = 'Configuration updated successfully!';
                loadCurrentConfig();
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
});

async function loadCurrentConfig() {
    const currentConfig = document.getElementById('currentConfig');
    
    try {
        const response = await fetch('/config/models');
        const {success, config, error} = await response.json();
        
        if (!success) {
            throw new Error(error || 'Failed to load config');
        }

        currentConfig.innerHTML = `
            <div class="row">
                ${['orchestrator', 'aider', 'agent'].map(type => `
                    <div class="col-md-4">
                        <h6>${type.charAt(0).toUpperCase() + type.slice(1)} Model</h6>
                        <p>${config[`${type}_model`]}</p>
                    </div>
                `).join('')}
            </div>
        `;

        // Populate form fields
        ['orchestrator', 'aider', 'agent'].forEach(type => {
            document.getElementById(`${type}Model`).value = config[`${type}_model`];
        });
    } catch (error) {
        currentConfig.innerHTML = `
            <div class="alert alert-danger">
                Error loading configuration: ${error.message}
            </div>
        `;
    }
}
