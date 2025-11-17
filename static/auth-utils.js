/**
 * Shared authentication utilities for Creo
 * Include this script before other page scripts
 */

// Token management
function getAuthToken() {
    return localStorage.getItem('creo_auth_token');
}

function setAuthToken(token) {
    localStorage.setItem('creo_auth_token', token);
}

function clearAuthToken() {
    localStorage.removeItem('creo_auth_token');
}

// HTTP headers
function getAuthHeaders() {
    const token = getAuthToken();
    if (!token) return {};
    return {
        'Authorization': `Bearer ${token}`
    };
}

// Redirect to login with return URL
function redirectToLogin(returnUrl = null) {
    if (!returnUrl) {
        returnUrl = window.location.pathname + window.location.search;
    }
    const encodedReturnUrl = encodeURIComponent(returnUrl);
    window.location.href = `/login.html?return_url=${encodedReturnUrl}`;
}

// Check authentication and return user info
async function checkAuth(options = {}) {
    const { requireAuth = false, onSuccess = null, onFailure = null } = options;

    const token = getAuthToken();

    if (!token) {
        if (requireAuth) {
            redirectToLogin();
            return null;
        }
        if (onFailure) onFailure();
        return null;
    }

    try {
        const response = await fetch('/api/auth/me', {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            // Token expired or invalid
            clearAuthToken();
            if (requireAuth) {
                redirectToLogin();
                return null;
            }
            if (onFailure) onFailure();
            return null;
        }

        const user = await response.json();
        if (onSuccess) onSuccess(user);
        return user;
    } catch (error) {
        console.error('Auth check failed:', error);
        clearAuthToken();
        if (requireAuth) {
            redirectToLogin();
            return null;
        }
        if (onFailure) onFailure();
        return null;
    }
}

// Logout function
function logout() {
    clearAuthToken();
    window.location.href = '/login.html';
}

// Display user profile in header
function displayUserProfile(user) {
    const userProfile = document.getElementById('userProfile');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');

    if (userProfile && userName && userAvatar) {
        userProfile.classList.remove('hidden');
        userName.textContent = user.name || user.email;

        // Set avatar (initials or image)
        if (user.picture) {
            userAvatar.innerHTML = `<img src="${user.picture}" alt="${user.name}" class="h-10 w-10 rounded-full">`;
        } else {
            const initials = user.name ?
                user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) :
                user.email[0].toUpperCase();
            userAvatar.textContent = initials;
        }
    }
}

// Display login button (for logged-out state)
function displayLoginButton() {
    const userProfile = document.getElementById('userProfile');
    if (userProfile) {
        userProfile.innerHTML = `
            <a href="/login.html" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-white transition-all"
               style="background-color: rgb(0, 160, 235);"
               onmouseover="this.style.backgroundColor='rgb(0, 144, 211)'"
               onmouseout="this.style.backgroundColor='rgb(0, 160, 235)'">
                Sign In
            </a>
        `;
        userProfile.classList.remove('hidden');
    }
}

// Toggle user menu dropdown
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// Close user menu when clicking outside
document.addEventListener('click', function (event) {
    const userMenu = document.getElementById('userMenu');
    const userAvatar = document.getElementById('userAvatar');
    if (userMenu && userAvatar &&
        !userMenu.contains(event.target) &&
        !userAvatar.contains(event.target)) {
        userMenu.classList.add('hidden');
    }
});

// Handle authentication errors in fetch requests
async function authenticatedFetch(url, options = {}) {
    const headers = {
        ...options.headers,
        ...getAuthHeaders()
    };

    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized
    if (response.status === 401) {
        clearAuthToken();
        redirectToLogin();
        throw new Error('Authentication required');
    }

    return response;
}
