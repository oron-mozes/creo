# Authentication

> **User authentication, anonymous users, and OAuth integration**

This document covers all authentication aspects of the Creo platform, including Google OAuth setup, anonymous user support, and authentication flows.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Google OAuth Setup](#google-oauth-setup)
3. [Authentication Flows](#authentication-flows)
4. [Anonymous Users](#anonymous-users)
5. [API Reference](#api-reference)
6. [Security](#security)

---

## Quick Start

### Test Without Google OAuth (Development)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python server.py
   ```

3. **Open browser:**
   ```
   http://localhost:8000
   ```

4. **Click "Dev Login (No OAuth)"** (only visible on localhost)

5. **You're authenticated!** Test with a development user account.

### What You Can Test

✅ User profile display in header
✅ Protected API endpoints
✅ Session management tied to user ID
✅ Business card storage per user
✅ Personalized suggestions
✅ Logout functionality

---

## Google OAuth Setup

### 1. Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create new)
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure consent screen:
   - User Type: External (for testing) or Internal (for workspace)
   - App name: Creo
   - User support email: Your email
6. Application type: **Web application**
7. Name: Creo Web Client
8. Authorized redirect URIs:
   - Local: `http://localhost:8000/api/auth/google/callback`
   - Production: `https://your-domain.com/api/auth/google/callback`
9. Copy **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Update `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# JWT Secret Key (generate secure random string)
SESSION_SECRET_KEY=your-secret-key-change-in-production
```

**Generate secure secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Test with Google OAuth

1. Update `.env` with real credentials
2. Restart server: `python server.py`
3. Visit `http://localhost:8000`
4. Click **"Continue with Google"**
5. Complete OAuth flow
6. Redirected back authenticated

---

## Authentication Flows

### Flow 1: Browse Without Login

```
User visits homepage
  ↓
See homepage (no redirect)
  ↓
See "Sign In" button in header
  ↓
Browse features, read about Creo
```

**Pages affected:** `index.html`
**Authentication:** Optional

### Flow 2: Try to Chat Without Login

```
User visits homepage (not logged in)
  ↓
Types message: "I have a coffee shop"
  ↓
Clicks "Send"
  ↓
→ Message saved to localStorage
→ Redirected to: /login.html?return_url=%2F
  ↓
User logs in (Google or Dev)
  ↓
→ Redirected back to homepage
→ Message restored in input field
→ Scroll to chat section
  ↓
User clicks "Send" again
  ↓
Chat starts!
```

**Data preserved:** Pending message

### Flow 3: Direct Chat URL Without Login

```
User visits /chat/session_abc123 (not logged in)
  ↓
→ Redirected to: /login.html?return_url=%2Fchat%2Fsession_abc123
  ↓
User logs in
  ↓
→ Redirected back to: /chat/session_abc123
  ↓
Chat loads with session history
```

**Data preserved:** Session ID in URL

### Flow 4: Token Expires During Session

```
User is chatting (logged in)
  ↓
Token expires (7 days default)
  ↓
User sends a message
  ↓
→ Socket.IO error: "Invalid or expired token"
→ Token cleared from localStorage
→ Redirected to: /login.html?return_url=%2Fchat%2Fsession_abc123
  ↓
User logs in again
  ↓
→ Redirected back to chat session
→ Session continues
```

**Data preserved:** Session ID, chat history in Firestore

### Implementation: Return URL Handling

**Homepage (index.html):**
```javascript
// When redirecting to login, save current location
localStorage.setItem('pending_message', message);
window.location.href = '/login.html?return_url=' + encodeURIComponent('/');

// After login, restore message
const pendingMessage = localStorage.getItem('pending_message');
if (pendingMessage) {
    input.value = pendingMessage;
    localStorage.removeItem('pending_message');
    scrollToChat();
}
```

**Chat Page (chat.html):**
```javascript
function redirectToLogin() {
    const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login.html?return_url=${returnUrl}`;
}
```

**Login Page (login.html):**
```javascript
function getReturnUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('return_url') || '/';
}

// After successful login
const returnUrl = getReturnUrl();
window.location.href = returnUrl;
```

---

## Anonymous Users

Creo supports **anonymous users** who can explore the platform before signing up.

### User Journey

#### Phase 1: Anonymous Exploration (No Login)

```
User visits Creo
  ↓
Anonymous user ID automatically generated (anon_abc123xyz)
  ↓
User can:
  ✓ Search for influencers
  ✓ Create campaign briefs
  ✓ Get recommendations
  ✓ Have multiple chat sessions
  ✓ See all their session history
  ↓
Data stored with anonymous user ID
```

#### Phase 2: Value Demonstration

```
User finds perfect influencers
  ↓
User wants to reach out
  ↓
System prompts: "Sign in to contact influencers"
  ↓
User sees value before commitment
```

#### Phase 3: Registration & Migration

```
User signs in with Google
  ↓
System migrates anonymous data:
  ✓ Business card → Authenticated user
  ✓ Chat sessions → Linked (but hidden initially)
  ✓ Preferences → Transferred
  ↓
User marked as "registered"
  ↓
Old anonymous sessions hidden (contain sensitive pre-auth data)
  ↓
User can create new authenticated sessions
```

### Technical Implementation

#### Anonymous User IDs

**Format:** `anon_<random12chars>`

**Generated:**
- Automatically on first visit
- Stored in localStorage: `creo_anon_user_id`
- Persists across browser sessions
- Unique per browser/device

**Code:**
```javascript
function getAnonymousUserId() {
    let anonId = localStorage.getItem('creo_anon_user_id');
    if (!anonId) {
        anonId = 'anon_' + generateRandomId();
        localStorage.setItem('creo_anon_user_id', anonId);
    }
    return anonId;
}
```

#### User ID Resolution

**Priority:**
1. Authenticated user ID (from JWT token) - `google_123456`
2. Anonymous user ID (from localStorage) - `anon_abc123`

```javascript
function getCurrentUserId() {
    const token = getAuthToken();
    if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub;  // google_123456
    }
    return getAnonymousUserId();  // anon_abc123
}
```

#### API Support for Both User Types

| Endpoint | Anonymous | Authenticated | Notes |
|----------|-----------|---------------|-------|
| `POST /api/sessions` | ✅ | ✅ | Create chat session |
| `POST /api/chat` | ✅ | ✅ | Send message |
| `POST /api/suggestions` | ✅ | ✅ | Generic vs personalized |
| `POST /api/users/migrate` | ❌ | ✅ | Migrate anon → auth |

#### Data Migration

**Client-side:**
```javascript
async function migrateAnonymousUser() {
    const anonId = localStorage.getItem('creo_anon_user_id');
    const authToken = getAuthToken();

    if (!anonId || !authToken) return;

    const response = await fetch('/api/users/migrate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
            anonymous_user_id: anonId
        })
    });

    if (response.ok) {
        markAnonymousUserRegistered();
    }
}
```

**Server-side:**
```python
@app.post("/api/users/migrate")
def migrate_anonymous_user(request, current_user):
    anon_user_id = request.anonymous_user_id
    auth_user_id = current_user.user_id

    # In Firestore:
    # 1. Find all sessions with anon_user_id
    # 2. Update to auth_user_id
    # 3. Merge business cards
    # 4. Transfer preferences
```

### Authentication Gates

#### ❌ Don't Require Login For:
- Browsing homepage
- Finding influencers
- Creating campaign briefs
- Getting recommendations
- Chatting with AI

#### ✅ Require Login For:
- **Contacting influencers (outreach)**
- Saving payment information
- Accessing premium features
- Viewing analytics/reports

#### Outreach Gate Example

```javascript
if (response.action === 'outreach' && isAnonymous()) {
    showAuthGate({
        title: "Sign in to Contact Influencers",
        message: "Create a free account to reach out to the influencers you've found",
        ctaText: "Sign in with Google",
        onAuth: () => {
            sendOutreachMessage();
        }
    });
    return;
}
```

### localStorage Keys

| Key | Purpose | Example Value |
|-----|---------|---------------|
| `creo_anon_user_id` | Anonymous user identifier | `anon_abc123xyz` |
| `creo_auth_token` | JWT authentication token | `eyJhbGciOiJIUzI1NiIs...` |
| `creo_anon_user_registered` | Flag: anonymous user registered | `"true"` |
| `pending_message` | Message typed before login | `"I have a coffee shop"` |

---

## API Reference

### Authentication Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/google` | GET | Start OAuth flow |
| `/api/auth/google/callback` | GET | OAuth callback (automatic) |
| `/api/auth/me` | GET | Get current user (requires auth) |
| `/api/auth/check` | GET | Check authentication status |
| `/api/auth/logout` | POST | Logout (client deletes token) |
| `/api/auth/dev/login` | POST | Dev login (development only) |

### Protected Endpoints

Require `Authorization: Bearer <token>` header:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sessions` | POST | Create new chat session |
| `/api/chat` | POST | Send message to agent |

### Optional Auth Endpoints

Work with or without authentication:

| Endpoint | Method | Authenticated | Anonymous |
|----------|--------|---------------|-----------|
| `/api/suggestions` | POST | Personalized | Generic |

### Socket.IO Authentication

**Connection:**
```javascript
socket.emit('join_session', {
    session_id: sessionId,
    token: token || null,      // Optional for anonymous
    user_id: userId            // Required (anon or auth)
});
```

**Message:**
```javascript
socket.emit('send_message', {
    message: message,
    session_id: sessionId,
    token: token || null
});
```

**Error Handling:**
```javascript
socket.on('error', (data) => {
    if (data.error.includes('Authentication')) {
        clearAuthToken();
        redirectToLogin();
    }
});
```

### JWT Token Structure

```json
{
  "sub": "google_<google_user_id>",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://...",
  "exp": 1234567890
}
```

### User ID Formats

- `google_123456789` - Google OAuth user
- `anon_abc123xyz` - Anonymous user
- `dev_username` - Development user (local only)

---

## Security

### Token Management

- **Storage:** localStorage (client-side)
- **Lifetime:** 7 days (configurable in `auth.py`)
- **Format:** JWT with signature
- **Payload:** `{sub: user_id, email, name, picture, exp}`

### Return URL Security

- ✅ URLs are properly encoded
- ✅ Only internal paths allowed (no external redirects)
- ✅ Session IDs preserved but not sensitive

### What's Protected

✅ Creating new sessions
✅ Sending messages
✅ Socket.IO connections
✅ User-specific data (business cards, session history)

### What's Public

✅ Homepage viewing
✅ Generic suggestions
✅ Marketing content

### Production Deployment

**Environment Variables for Cloud Run:**

Set in Google Cloud Secret Manager:
1. `GOOGLE_CLIENT_ID` - OAuth client ID
2. `GOOGLE_CLIENT_SECRET` - OAuth client secret
3. `SESSION_SECRET_KEY` - Secure random string
4. `GOOGLE_REDIRECT_URI` - Production callback URL

**Update Authorized Redirect URIs:**

In Google Cloud Console:
- `https://your-app-name.run.app/api/auth/google/callback`

**CORS Configuration:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Security Considerations

1. **JWT Secret Key**: Use strong, randomly generated secret in production
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiration**: 7-day default, configurable
4. **CORS**: Restrict allowed origins in production
5. **Token Storage**: localStorage (consider httpOnly cookies for extra security)

---

## Troubleshooting

### "Authentication required" error
- Clear localStorage: `localStorage.removeItem('creo_auth_token')`
- Check browser console for errors
- Verify server is running

### OAuth redirect loop
- Verify redirect URI matches exactly in Google Cloud Console
- Check `GOOGLE_REDIRECT_URI` environment variable
- Clear browser cookies and localStorage

### "Invalid token" error
- Token may have expired (7 day default)
- Secret key mismatch
- User should log in again

### Dev login not showing
- Only appears on localhost/127.0.0.1
- Not available in production (`K_SERVICE` env set)

### "Lost my message after login"
- Check: `localStorage.getItem('pending_message')`
- Message should be restored after login

### Socket.IO keeps disconnecting
- Token expired or invalid
- Check: `localStorage.getItem('creo_auth_token')`
- Verify token: `fetch('/api/auth/check', {headers: {'Authorization': 'Bearer ' + token}})`

---

## Summary

The Creo authentication system provides:

✅ **Google OAuth** - Secure third-party authentication
✅ **Anonymous users** - Frictionless onboarding
✅ **Return URL preservation** - Seamless login flow
✅ **Message preservation** - No data loss during login
✅ **Token management** - 7-day JWT tokens
✅ **Data migration** - Anonymous → authenticated transition
✅ **Smart auth gates** - Login only when needed (outreach)
✅ **Development mode** - Quick testing without OAuth

This creates a superior user experience while maintaining security and privacy.
