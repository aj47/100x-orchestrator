// Global authentication utilities and handlers
const AUTH = {
    TOKEN_KEY: 'github_token',
    
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    },

    redirectToLogin() {
        window.location.href = '/';
    },

    // Fetch wrapper with authentication
    async fetch(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            this.redirectToLogin();
            throw new Error('No GitHub token found');
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'X-GitHub-Token': token
            }
        });

        if (response.status === 401) {
            this.clearToken();
            this.redirectToLogin();
            throw new Error('GitHub token expired or invalid');
        }

        return response;
    },

    // Initialize authentication check
    init() {
        const token = this.getToken();
        const isLoginPage = document.getElementById('tokenForm') !== null;

        if (!token && !isLoginPage) {
            this.redirectToLogin();
            return false;
        }

        if (token && isLoginPage) {
            window.location.href = '/agents';
            return false;
        }

        return true;
    },

    // Verify token with GitHub
    async verifyToken(token) {
        try {
            const response = await fetch('/verify_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-GitHub-Token': token
                },
                body: JSON.stringify({ token })
            });
            
            const data = await response.json();
            return data.valid;
        } catch (error) {
            console.error('Token verification failed:', error);
            return false;
        }
    }
};

// Export for use in other files
window.AUTH = AUTH;