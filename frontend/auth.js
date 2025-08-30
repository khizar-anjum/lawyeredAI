// Simple authentication system (no Supabase required)
const AUTH_KEY = 'lawyeredai_auth'

class AuthManager {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.checkAuthStatus();
    }

    initializeElements() {
        this.loginForm = document.getElementById('loginForm');
        this.signupForm = document.getElementById('signupForm');
        this.loading = document.getElementById('loading');
        
        // Login elements
        this.loginBtn = document.getElementById('loginBtn');
        this.email = document.getElementById('email');
        this.password = document.getElementById('password');
        
        // Signup elements
        this.signupBtn = document.getElementById('signupBtn');
        this.fullName = document.getElementById('fullName');
        this.signupEmail = document.getElementById('signupEmail');
        this.signupPassword = document.getElementById('signupPassword');
        
        // Switch elements
        this.showSignup = document.getElementById('showSignup');
        this.showLogin = document.getElementById('showLogin');
    }

    attachEventListeners() {
        this.loginBtn.addEventListener('click', () => this.handleLogin());
        this.signupBtn.addEventListener('click', () => this.handleSignup());
        this.showSignup.addEventListener('click', () => this.switchToSignup());
        this.showLogin.addEventListener('click', () => this.switchToLogin());
        
        // Enter key handling
        this.email.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        this.password.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
    }

    switchToSignup() {
        this.loginForm.classList.add('hidden');
        this.signupForm.classList.remove('hidden');
    }

    switchToLogin() {
        this.signupForm.classList.add('hidden');
        this.loginForm.classList.remove('hidden');
    }

    showLoading(show) {
        if (show) {
            this.loginForm.classList.add('hidden');
            this.signupForm.classList.add('hidden');
            this.loading.classList.remove('hidden');
        } else {
            this.loading.classList.add('hidden');
            this.loginForm.classList.remove('hidden');
        }
    }

    async handleLogin() {
        const email = this.email.value.trim();
        const password = this.password.value;

        if (!email || !password) {
            alert('Please fill in all fields');
            return;
        }

        this.showLoading(true);

        try {
            // Simple authentication - check if user exists
            const users = JSON.parse(localStorage.getItem('users') || '[]');
            const user = users.find(u => u.email === email && u.password === password);
            
            if (!user) {
                throw new Error('Invalid email or password');
            }

            // Store session and redirect
            const session = {
                user: {
                    id: user.id,
                    email: user.email,
                    full_name: user.full_name
                },
                access_token: 'demo_token_' + Date.now()
            };
            
            localStorage.setItem(AUTH_KEY, JSON.stringify(session));
            window.location.href = '/';

        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed: ' + error.message);
            this.showLoading(false);
        }
    }

    async handleSignup() {
        const fullName = this.fullName.value.trim();
        const email = this.signupEmail.value.trim();
        const password = this.signupPassword.value;

        if (!fullName || !email || !password) {
            alert('Please fill in all fields');
            return;
        }

        if (password.length < 6) {
            alert('Password must be at least 6 characters');
            return;
        }

        this.showLoading(true);

        try {
            // Check if user already exists
            const users = JSON.parse(localStorage.getItem('users') || '[]');
            const existingUser = users.find(u => u.email === email);
            
            if (existingUser) {
                throw new Error('User with this email already exists');
            }

            // Create new user
            const newUser = {
                id: 'user_' + Date.now(),
                email: email,
                password: password,
                full_name: fullName,
                created_at: new Date().toISOString()
            };

            users.push(newUser);
            localStorage.setItem('users', JSON.stringify(users));

            alert('Sign up successful! You can now log in.');
            this.switchToLogin();

        } catch (error) {
            console.error('Signup error:', error);
            alert('Sign up failed: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async checkAuthStatus() {
        const session = JSON.parse(localStorage.getItem(AUTH_KEY) || 'null');
        
        if (session && session.user) {
            // User is already logged in, redirect to app
            window.location.href = '/';
        }
    }
}

// Initialize auth manager
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});