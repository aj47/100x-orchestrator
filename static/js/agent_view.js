// ... (other code)

// WebSocket connection
let socket;
function connectSocket() {
    socket = io.connect('http://' + document.location.host, {
        path: '/socket.io'
    });

    socket.on('connect', () => {
        console.log('Connected to WebSocket');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket');
    });

    socket.on('clone_progress', (data) => {
        console.log('Received clone progress:', data);
        const agentCard = document.getElementById(`agent-${data.agent_id}`);
        if (agentCard) {
            const progressElement = agentCard.querySelector('.progress-bar');
            if (progressElement) {
                progressElement.style.width = `${data.progress}%`;
                progressElement.textContent = `${data.progress}%`;
            }
        }
    });

    socket.on('clone_error', (data) => {
        console.error('Received clone error:', data);
        const agentCard = document.getElementById(`agent-${data.agent_id}`);
        if (agentCard) {
            const errorElement = agentCard.querySelector('.error-message');
            if (errorElement) {
                errorElement.textContent = data.error;
                errorElement.style.display = 'block';
            }
        }
    });
}

// ... (rest of the code)

document.addEventListener('DOMContentLoaded', () => {
    // ... (other code)
    connectSocket();
});

