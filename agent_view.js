document.addEventListener('DOMContentLoaded', () => {
    fetch('/agents')
        .then(response => response.json())
        .then(agents => {
            const agentList = document.getElementById('agent-list');
            agents.forEach(agent => {
                const agentDiv = document.createElement('div');
                agentDiv.innerHTML = `
                    <h2>Agent ${agent.id}</h2>
                    <p>Status: ${agent.status}</p>
                    ${agent.pr_url ? `<a href="${agent.pr_url}">Pull Request</a>` : ''}
                `;
                agentList.appendChild(agentDiv);
            });
        });
});

