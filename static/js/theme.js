// Theme functionality with TF theme support
function initializeTheme() {
    const themeToggleBtn = document.getElementById('themeToggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Get theme from localStorage or system preference
    const currentTheme = localStorage.getItem('theme') || 
        (prefersDarkScheme.matches ? 'dark' : 'light');
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    // Theme toggle click handler - cycles through three themes
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        let newTheme;
        
        // Cycle through themes: light -> dark -> tf -> light
        switch(currentTheme) {
            case 'light':
                newTheme = 'dark';
                break;
            case 'dark':
                newTheme = 'tf';
                initializeMatrixRain(); // Initialize rain effect when switching to tf theme
                break;
            case 'tf':
                newTheme = 'light';
                removeMatrixRain(); // Remove rain effect when switching away
                break;
            default:
                newTheme = 'light';
        }
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });

    // Initialize rain effect if starting with tf theme
    if (currentTheme === 'tf') {
        initializeMatrixRain();
    }
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    // Update icon based on current theme
    switch(theme) {
        case 'light':
            themeIcon.className = 'fas fa-sun';
            break;
        case 'dark':
            themeIcon.className = 'fas fa-moon';
            break;
        case 'tf':
            themeIcon.className = 'fas fa-terminal';
            break;
    }
}

// Matrix rain animation
function initializeMatrixRain() {
    if (document.getElementById('matrixCanvas')) return;
    
    const canvas = document.createElement('canvas');
    canvas.id = 'matrixCanvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.15';  // Increased opacity to match techfren
    document.body.prepend(canvas);

    const context = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // TechFren-style character set
    const matrix = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ日0123456789:・.";
    const matrixArray = matrix.split("");
    const fontSize = 14;  // Increased font size
    const columns = canvas.width / fontSize;
    const drops = [];
    const glowIntensity = [];  // Array to track glow intensity for each column

    for (let x = 0; x < columns; x++) {
        drops[x] = 1;
        glowIntensity[x] = Math.random();  // Random initial glow
    }

    function draw() {
        if (!document.getElementById('matrixCanvas')) return;
        
        context.fillStyle = "rgba(0, 0, 0, 0.05)";  // Slower fade effect
        context.fillRect(0, 0, canvas.width, canvas.height);
        
        for (let i = 0; i < drops.length; i++) {
            // Update glow intensity with smooth transition
            glowIntensity[i] += (Math.random() - 0.5) * 0.1;
            glowIntensity[i] = Math.max(0.3, Math.min(1, glowIntensity[i]));
            
            const text = matrixArray[Math.floor(Math.random() * matrixArray.length)];
            
            // Create gradient for each character
            const gradient = context.createLinearGradient(
                i * fontSize, drops[i] * fontSize - fontSize,
                i * fontSize, drops[i] * fontSize
            );
            
            // TechFren-style green colors with glow
            gradient.addColorStop(0, `rgba(0, 255, 0, ${0.1 * glowIntensity[i]})`);
            gradient.addColorStop(0.8, `rgba(0, 255, 0, ${0.8 * glowIntensity[i]})`);
            gradient.addColorStop(1, `rgba(0, 255, 0, ${glowIntensity[i]})`);
            
            context.fillStyle = gradient;
            context.font = `${fontSize}px 'MS Gothic', monospace`;
            context.shadowBlur = 8;
            context.shadowColor = `rgba(0, 255, 0, ${0.5 * glowIntensity[i]})`;
            
            context.fillText(text, i * fontSize, drops[i] * fontSize);
            context.shadowBlur = 0;
            
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.98) {
                drops[i] = 0;
            }
            drops[i] += 0.5;  // Slower fall speed
        }
        
        canvas.animationId = requestAnimationFrame(draw);
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        if (canvas) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
    });

    draw();
}

function removeMatrixRain() {
    const canvas = document.getElementById('matrixCanvas');
    if (canvas) {
        cancelAnimationFrame(canvas.animationId);
        canvas.remove();
    }
}

// Initialize theme when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTheme);
