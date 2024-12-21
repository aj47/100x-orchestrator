// ... (other functions remain the same)

document.addEventListener('DOMContentLoaded', async () => {
    // ... (other code remains the same)

    // Add event listener to checkboxes
    taskList.addEventListener('change', async (event) => {
        if (event.target.type === 'checkbox' && event.target.checked) {
            const taskItem = event.target.closest('.task-item');
            const title = taskItem.querySelector('.task-title').value;
            const description = taskItem.querySelector('.task-description').value;

            try {
                const response = await fetch('/add_task', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ task: { title, description } })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                console.log('Task added successfully!');
            } catch (error) {
                console.error('Error adding task:', error);
            }
        }
    });

    // ... (rest of the code remains the same)
});
