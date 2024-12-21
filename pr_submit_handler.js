async function handlePRSubmission() {
    try {
        const response = await fetch('/api/pr_data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const prData = await response.json();

        const prNumberElement = document.getElementById('pr-number');
        const prLinkElement = document.getElementById('pr-link');

        prNumberElement.textContent = prData.prNumber;
        prLinkElement.href = prData.prUrl;
        prLinkElement.textContent = prData.prUrl;

    } catch (error) {
        console.error('Error fetching or processing PR data:', error);
        alert('Error: Could not retrieve PR information. Please check the console for details.');
    }
}


// Example of how to call the function (adapt to your event handling)
document.addEventListener('DOMContentLoaded', () => {
    const submitButton = document.getElementById('submit-button'); // Replace with your button ID
    if (submitButton) {
        submitButton.addEventListener('click', handlePRSubmission);
    }
});

