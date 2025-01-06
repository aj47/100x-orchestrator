document.addEventListener('DOMContentLoaded', () => {
    // Load current configuration
    loadCurrentConfig();

    // Handle form submission
    document.getElementById('configForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const resultDiv = document.getElementById('result');
        const alertDiv = resultDiv.querySelector('.alert');
        
        try {
            const configData = {
                orchestrator_model: document.getElementById('orchestratorModel').value.trim(),
                aider_model: document.getElementById('aiderModel').value.trim(),
                agent_model: document.getElementById('agentModel').value.trim(),
                aider_prompt_suffix: document.getElementById('aiderPromptSuffix').value.trim() || ''
            };


            const response = await fetch('/config/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(configData)
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
            ${config.aider_prompt_suffix ? `
            <div class="mt-3">
                <h6>Additional Instructions</h6>
                <pre class="bg-light text-dark p-2 rounded">${config.aider_prompt_suffix}</pre>
            </div>
            ` : ''}
        `;

        // Populate form fields from server config
        ['orchestrator', 'aider', 'agent'].forEach(type => {
            document.getElementById(`${type}Model`).value = config[`${type}_model`];
        });
        document.getElementById('aiderPromptSuffix').value = config.aider_prompt_suffix || '';
    } catch (error) {
        currentConfig.innerHTML = `
            <div class="alert alert-danger">
                Error loading configuration: ${error.message}
            </div>
        `;
    }
}
