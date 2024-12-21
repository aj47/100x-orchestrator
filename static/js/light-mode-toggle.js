const lightModeToggle = document.getElementById('lightModeToggle');
const body = document.body;

lightModeToggle.addEventListener('click', () => {
    body.classList.toggle('bg-dark');
    body.classList.toggle('text-light');

    const isDarkMode = body.classList.contains('bg-dark');
    localStorage.setItem('darkMode', isDarkMode);
});


// Set initial mode based on local storage
const storedDarkMode = localStorage.getItem('darkMode');
if (storedDarkMode === 'true') {
    body.classList.add('bg-dark', 'text-light');
} else {
    body.classList.remove('bg-dark', 'text-light');
}
