// Utility functions shared across the application

// Show a toast message with optional type (success, error, info)
export function showToast(message, type = 'success') {
    const toastEl = document.getElementById('deleteToast');
    const toastBody = document.getElementById('toastMessage');
    
    // Remove existing classes
    toastBody.classList.remove('success', 'error', 'info');
    // Add appropriate class
    toastBody.classList.add(type);
    
    // Add icon based on type
    const icon = type === 'success' ? 'check-circle' : 
                type === 'error' ? 'exclamation-circle' : 'info-circle';
    toastBody.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
    `;
    
    // Show toast
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Helper function to get output length from debug info
export function getOutputLength(debugElement) {
    const lengthElement = debugElement.querySelector('.label');
    if (lengthElement && lengthElement.textContent.includes('Output Length')) {
        const lengthText = lengthElement.parentElement.textContent;
        return parseInt(lengthText.split(':')[1].trim());
    }
    return 0;
}

// Handle common error display in result div
export function displayError(message, resultDivId = 'result') {
    const resultDiv = document.getElementById(resultDivId);
    const alertDiv = resultDiv.querySelector('.alert');
    resultDiv.style.display = 'block';
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    console.error(message);
}

// Handle common success display in result div
export function displaySuccess(message, resultDivId = 'result') {
    const resultDiv = document.getElementById(resultDivId);
    const alertDiv = resultDiv.querySelector('.alert');
    resultDiv.style.display = 'block';
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    console.log(message);
}
