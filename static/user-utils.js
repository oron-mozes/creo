/**
 * User management utilities for Creo
 * Handles both anonymous and authenticated users
 */

// Generate or retrieve anonymous user ID
function getAnonymousUserId() {
    let anonId = localStorage.getItem('creo_anon_user_id');
    if (!anonId) {
        anonId = 'anon_' + generateRandomId();
        localStorage.setItem('creo_anon_user_id', anonId);
        console.log('[USER] Created new anonymous user ID:', anonId);
    }
    return anonId;
}

function getStoredAuthUser() {
    const raw = localStorage.getItem('creo_user_info');
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        console.error('[USER] Failed to parse stored auth user:', e);
        return null;
    }
}

function clearStoredAuthUser() {
    localStorage.removeItem('creo_user_info');
}

// Get current user ID (authenticated or anonymous)
function getCurrentUserId() {
    const storedUser = getStoredAuthUser();
    if (storedUser?.user_id) {
        console.log('[USER] Using authenticated user ID from cache:', storedUser.user_id);
        return storedUser.user_id;
    }

    // First check if user is authenticated
    const token = getAuthToken();
    if (token) {
        try {
            // Decode JWT to get user ID (without verification, just for display)
            const payload = JSON.parse(atob(token.split('.')[1]));
            const userId = payload.sub;
            console.log('[USER] Using authenticated user ID:', userId);
            return userId;
        } catch (e) {
            console.error('[USER] Failed to decode token:', e);
        }
    }

    // Fall back to anonymous user ID
    const anonId = getAnonymousUserId();
    console.log('[USER] Using anonymous user ID:', anonId);
    return anonId;
}

// Check if user is authenticated (vs anonymous)
function isAuthenticated() {
    const storedUser = getStoredAuthUser();
    if (storedUser?.user_id) return true;
    const token = getAuthToken();
    return !!token;
}

// Check if user is anonymous
function isAnonymous() {
    return !isAuthenticated();
}

// Generate random ID
function generateRandomId() {
    return Math.random().toString(36).substring(2, 15) +
           Math.random().toString(36).substring(2, 15);
}

// Mark that anonymous user has registered
function markAnonymousUserRegistered() {
    const anonId = localStorage.getItem('creo_anon_user_id');
    if (anonId) {
        localStorage.setItem('creo_anon_user_registered', 'true');
        console.log('[USER] Marked anonymous user as registered:', anonId);
    }
}

// Check if anonymous user has registered
function hasAnonymousUserRegistered() {
    return localStorage.getItem('creo_anon_user_registered') === 'true';
}

// Clear anonymous user registration flag
function clearAnonymousUserRegistration() {
    localStorage.removeItem('creo_anon_user_registered');
}

// Get user sessions (filtered based on registration status)
function getUserSessions() {
    const sessions = JSON.parse(localStorage.getItem('creo_sessions') || '[]');

    // If user is authenticated
    if (isAuthenticated()) {
        // If they were previously anonymous and just registered
        if (hasAnonymousUserRegistered()) {
            // Hide old anonymous sessions (they contain sensitive data)
            console.log('[USER] Hiding anonymous sessions after registration');
            return [];
        }
        // Show all sessions for fully authenticated users
        return sessions;
    }

    // For anonymous users, show all their sessions
    return sessions;
}

// Save session
function saveUserSession(sessionId, title) {
    const sessions = JSON.parse(localStorage.getItem('creo_sessions') || '[]');
    const existingIndex = sessions.findIndex(s => s.id === sessionId);

    const session = {
        id: sessionId,
        title: title,
        timestamp: new Date().toISOString(),
        userId: getCurrentUserId()
    };

    if (existingIndex >= 0) {
        sessions[existingIndex] = session;
    } else {
        sessions.unshift(session);
    }

    // Keep only last 10 sessions
    if (sessions.length > 10) {
        sessions.splice(10);
    }

    localStorage.setItem('creo_sessions', JSON.stringify(sessions));
}

// Migration: Connect anonymous user to authenticated user
async function migrateAnonymousUser() {
    const anonId = localStorage.getItem('creo_anon_user_id');
    const authToken = getAuthToken();

    if (!anonId) {
        console.log('[USER] No migration needed');
        return;
    }

    try {
        // Call backend to migrate anonymous user data
        const response = await fetch('/api/users/migrate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
            },
            credentials: 'include',
            body: JSON.stringify({
                anonymous_user_id: anonId
            })
        });

        if (response.ok) {
            console.log('[USER] Successfully migrated anonymous user:', anonId);
            markAnonymousUserRegistered();
            return true;
        } else {
            console.error('[USER] Migration failed:', await response.text());
            return false;
        }
    } catch (error) {
        console.error('[USER] Migration error:', error);
        return false;
    }
}

// User info for display
function getUserDisplayInfo() {
    const storedUser = getStoredAuthUser();
    if (storedUser?.user_id) {
        return {
            authenticated: true,
            userId: storedUser.user_id,
            email: storedUser.email,
            name: storedUser.name,
            picture: storedUser.picture
        };
    }

    if (isAuthenticated()) {
        const token = getAuthToken();
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return {
                authenticated: true,
                userId: payload.sub,
                email: payload.email,
                name: payload.name,
                picture: payload.picture
            };
        } catch (e) {
            console.error('[USER] Failed to decode token:', e);
        }
    }

    return {
        authenticated: false,
        userId: getAnonymousUserId(),
        email: null,
        name: 'Guest',
        picture: null
    };
}
