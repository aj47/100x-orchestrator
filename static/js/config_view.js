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
    try {
        const response = await fetch('/config/models');
        const data = await response.json();
        
        if (data.success) {
            const config = data.config;
            const configHtml = `
                <div class="row">
                    <div class="col-md-4">
                        <h6>Orchestrator Model</h6>
                        <p>${config.orchestrator_model}</p>
                    </div>
                    <div class="col-md-4">
                        <h6>Aider Model</h6>
                        <p>${config.aider_model}</p>
                    </div>
                    <div class="col-md-4">
                        <h6>Agent Model</h6>
                        <p>${config.agent_model}</p>
                    </div>
                </div>
            `;
            document.getElementById('currentConfig').innerHTML = configHtml;
            
            // Populate form fields
            document.getElementById('orchestratorModel').value = config.orchestrator_model;
            document.getElementById('aiderModel').value = config.aider_model;
            document.getElementById('agentModel').value = config.agent_model;
        } else {
            document.getElementById('currentConfig').innerHTML = 
                `<div class="alert alert-warning">Error loading configuration: ${data.error}</div>`;
        }
    } catch (error) {
        document.getElementById('currentConfig').innerHTML = 
            `<div class="alert alert-danger">Error loading configuration: ${error.message}</div>`;
    }
}
