/**
 * Authentication Gate Component
 *
 * Displays an inline authentication prompt when anonymous users
 * try to perform actions that require authentication (like outreach)
 */

// Show authentication gate in the chat
function showAuthGateInChat(options = {}) {
    const {
        title = "Sign in to Continue",
        message = "Please sign in to contact influencers and complete your outreach.",
        ctaText = "Sign in with Google",
        secondaryText = "Why do I need to sign in?",
        reason = "We need to verify your identity before allowing outreach to protect both you and the influencers."
    } = options;

    const messagesDiv = document.getElementById('messages');
    if (!messagesDiv) {
        console.error('[AUTH_GATE] Messages container not found');
        return;
    }

    // Create auth gate message
    const authGateDiv = document.createElement('div');
    authGateDiv.className = 'auth-gate-message animate-fade-in';
    authGateDiv.innerHTML = `
        <div class="flex gap-4 max-w-2xl mx-auto my-6">
            <div class="flex-1 p-6 rounded-3xl" style="background: linear-gradient(135deg, rgba(0, 160, 235, 0.1), rgba(147, 51, 234, 0.1)); border: 2px solid rgba(0, 160, 235, 0.3);">
                <!-- Icon -->
                <div class="flex items-center justify-center w-14 h-14 mx-auto mb-4 rounded-full" style="background: linear-gradient(135deg, rgb(0, 160, 235), rgb(0, 144, 211));">
                    <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                </div>

                <!-- Title -->
                <h3 class="text-xl font-bold text-center text-gray-900 mb-2">
                    ${escapeHtml(title)}
                </h3>

                <!-- Message -->
                <p class="text-center text-gray-700 mb-6">
                    ${escapeHtml(message)}
                </p>

                <!-- Sign In Button -->
                <div class="flex flex-col gap-3">
                    <button onclick="handleAuthGateSignIn()" class="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-2xl font-medium text-white transition-all" style="background-color: rgb(0, 160, 235);" onmouseover="this.style.backgroundColor='rgb(0, 144, 211)'" onmouseout="this.style.backgroundColor='rgb(0, 160, 235)'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        <span>${escapeHtml(ctaText)}</span>
                    </button>

                    <!-- Why link -->
                    <button onclick="toggleAuthGateReason(this)" class="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                        ${escapeHtml(secondaryText)} ▼
                    </button>

                    <!-- Reason (hidden by default) -->
                    <div class="auth-gate-reason hidden mt-2 p-4 bg-white bg-opacity-50 rounded-xl text-sm text-gray-700">
                        ${escapeHtml(reason)}
                    </div>
                </div>

                <!-- Benefits -->
                <div class="mt-6 pt-6 border-t border-gray-300">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">What you get:</p>
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="flex items-start gap-2">
                            <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span class="text-gray-700">Contact influencers</span>
                        </div>
                        <div class="flex items-start gap-2">
                            <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span class="text-gray-700">Save your progress</span>
                        </div>
                        <div class="flex items-start gap-2">
                            <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span class="text-gray-700">Track campaigns</span>
                        </div>
                        <div class="flex items-start gap-2">
                            <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span class="text-gray-700">Access history</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    messagesDiv.appendChild(authGateDiv);

    // Scroll to show the auth gate
    if (typeof scrollToBottom === 'function') {
        scrollToBottom();
    }
}

// Handle sign in button click
function handleAuthGateSignIn() {
    // Save current context
    const currentUrl = window.location.pathname + window.location.search;
    const returnUrl = encodeURIComponent(currentUrl);

    // Redirect to login
    window.location.href = `/login.html?return_url=${returnUrl}`;
}

// Toggle reason display
function toggleAuthGateReason(button) {
    const reasonDiv = button.nextElementSibling;
    if (reasonDiv && reasonDiv.classList.contains('auth-gate-reason')) {
        const isHidden = reasonDiv.classList.contains('hidden');

        if (isHidden) {
            reasonDiv.classList.remove('hidden');
            button.innerHTML = button.innerHTML.replace('▼', '▲');
        } else {
            reasonDiv.classList.add('hidden');
            button.innerHTML = button.innerHTML.replace('▲', '▼');
        }
    }
}

// Parse agent response for authentication requirement
function checkForAuthRequirement(agentResponse) {
    // Check if agent response contains authentication markers
    const authMarkers = [
        'REQUIRES_AUTH',
        'AUTH_REQUIRED',
        'AUTHENTICATION_NEEDED',
        'LOGIN_REQUIRED'
    ];

    for (const marker of authMarkers) {
        if (agentResponse.includes(marker)) {
            return true;
        }
    }

    // Check for outreach-related keywords
    const outreachKeywords = [
        'contact influencer',
        'reach out',
        'send message to',
        'email influencer',
        'start outreach'
    ];

    const lowerResponse = agentResponse.toLowerCase();
    for (const keyword of outreachKeywords) {
        if (lowerResponse.includes(keyword) && isAnonymous()) {
            return true;
        }
    }

    return false;
}

// Handle agent response that requires authentication
function handleAgentResponseWithAuthCheck(response) {
    if (checkForAuthRequirement(response)) {
        // Extract custom message if provided
        const customMatch = response.match(/AUTH_MESSAGE:\s*(.+?)(?:\n|$)/);
        const customMessage = customMatch ? customMatch[1].trim() : undefined;

        // Show auth gate
        showAuthGateInChat({
            message: customMessage || "Please sign in to contact influencers and complete your outreach."
        });

        // Remove auth markers from response
        let cleanResponse = response;
        for (const marker of ['REQUIRES_AUTH', 'AUTH_REQUIRED', 'AUTHENTICATION_NEEDED', 'LOGIN_REQUIRED']) {
            cleanResponse = cleanResponse.replace(new RegExp(marker + '\\s*', 'g'), '');
        }
        cleanResponse = cleanResponse.replace(/AUTH_MESSAGE:\s*.+?(?:\n|$)/g, '');

        return cleanResponse.trim();
    }

    return response;
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.showAuthGateInChat = showAuthGateInChat;
    window.handleAuthGateSignIn = handleAuthGateSignIn;
    window.toggleAuthGateReason = toggleAuthGateReason;
    window.checkForAuthRequirement = checkForAuthRequirement;
    window.handleAgentResponseWithAuthCheck = handleAgentResponseWithAuthCheck;
}
