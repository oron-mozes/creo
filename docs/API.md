# API Documentation

> **HTTP and Socket.IO API reference for the Creo platform**

This document covers all API endpoints, Socket.IO events, and API contracts.

## Table of Contents

1. [Getting Started](#getting-started)
2. [HTTP API](#http-api)
3. [Socket.IO Events](#socketio-events)
4. [API Contract](#api-contract)
5. [Testing](#testing)

---

## Getting Started

### Start the Server

```bash
make install  # Install dependencies including FastAPI
make server   # Start the server on http://localhost:8000
```

The server starts on `http://localhost:8000` with automatic reload enabled.

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## HTTP API

### Health Check

**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "agent": "orchestrator"
}
```

### Create Session

**POST** `/api/sessions`

Create a new chat session with an initial message.

**Request:**
```json
{
  "message": "I need help finding influencers",
  "user_id": "user123"  // Optional, auto-generated if not provided
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "user_id": "user123"
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error

### Get Session Messages

**GET** `/api/sessions/{session_id}/messages`

Get all messages for a session.

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "role": "user",
      "content": "I need help with influencer marketing",
      "timestamp": "2025-01-16T10:00:00",
      "user_id": "user_abc"
    },
    {
      "id": "msg_124",
      "role": "assistant",
      "content": "I'd be happy to help...",
      "timestamp": "2025-01-16T10:00:05",
      "user_id": "assistant"
    }
  ],
  "session_id": "session_xyz"
}
```

**Status Codes:**
- `200` - Success
- `404` - Session not found

### Clear User Session

**DELETE** `/api/session/{user_id}`

Clear all sessions for a specific user.

**Response:**
```json
{
  "status": "success",
  "message": "Session cleared for user: user123"
}
```

**Status Codes:**
- `200` - Success

### Chat with Orchestrator (Legacy)

**POST** `/api/chat`

Send a message to the orchestrator agent. The orchestrator analyzes and routes to appropriate sub-agents.

**Request:**
```json
{
  "message": "I need to find fashion influencers for my brand",
  "user_id": "user123",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "I'll help you find fashion influencers...",
  "session_id": "session_abc123",
  "user_id": "user123"
}
```

---

## Socket.IO Events

### Client → Server Events

#### join_session

Join a session and start processing initial message (if exists).

**Payload:**
```typescript
{
  session_id: string;
  user_id: string;
  token?: string;  // Optional, for authenticated users
}
```

**Response Sequence:**
1. `chat_history` (with existing messages)
2. `agent_thinking` (if initial message needs processing)
3. `message_chunk` (0+ times, optional)
4. `message_complete`

**Example:**
```javascript
socket.emit('join_session', {
  session_id: 'session_xyz',
  user_id: 'user_abc'
});
```

#### send_message

Send a new message to the agent.

**Payload:**
```typescript
{
  message: string;
  session_id: string;
  user_id: string;
  token?: string;  // Optional, for authenticated users
}
```

**Response Sequence:**
1. `agent_thinking`
2. `message_chunk` (0+ times, optional)
3. `message_complete`

**Example:**
```javascript
socket.emit('send_message', {
  message: 'I have a local coffee shop',
  session_id: 'session_xyz',
  user_id: 'user_abc'
});
```

### Server → Client Events

#### chat_history

Emitted when a client joins a session. Contains all previous messages.

**Payload:**
```typescript
{
  messages: Array<{
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;  // ISO 8601 format
    user_id: string;
  }>;
  session_id: string;
}
```

**When Emitted:**
- When client joins a session via `join_session` event

**Example:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "role": "user",
      "content": "I need help with influencer marketing",
      "timestamp": "2025-01-16T10:00:00",
      "user_id": "user_abc"
    }
  ],
  "session_id": "session_xyz"
}
```

#### agent_thinking

Emitted when the agent starts processing. Triggers loading indicator in UI.

**Payload:**
```typescript
{
  session_id: string;
}
```

**When Emitted:**
- When processing initial message in `join_session`
- When processing new message in `send_message`

**Example:**
```javascript
socket.on('agent_thinking', (data) => {
  console.log('Agent is thinking...');
  showLoadingIndicator();
});
```

#### message_chunk (Optional)

Emitted during streaming responses. May be emitted 0+ times.

**Payload:**
```typescript
{
  chunk: string;
  session_id: string;
  message_id: string;
}
```

**When Emitted:**
- During streaming responses from frontdesk_agent
- **NOT emitted** for non-streaming responses

**Example:**
```javascript
socket.on('message_chunk', (data) => {
  appendTextToMessage(data.chunk);
});
```

#### message_complete (Required)

Emitted when agent finishes processing. Contains the complete response.

**Payload:**
```typescript
{
  message: string;          // Full response text (required)
  session_id: string;
  message_id: string;
  business_card: BusinessCard | null;  // MUST be present (even if null)
}

interface BusinessCard {
  name: string | "Not provided";
  website: string | "Not provided";
  social_links: string | "Not provided";  // Comma-separated URLs
  location: string | "Not provided";
  service_type: string | "Not provided";
}
```

**When Emitted:**
- Always emitted at end of agent processing
- Contains full message text even if `message_chunk` events were sent

**Example (no business card):**
```json
{
  "message": "Hi there! How can I help you today?",
  "session_id": "session_xyz",
  "message_id": "msg_456",
  "business_card": null
}
```

**Example (with business card):**
```json
{
  "message": "Great! Let me confirm I have this right...",
  "session_id": "session_xyz",
  "message_id": "msg_456",
  "business_card": {
    "name": "Alma Cafe",
    "website": "https://almacafe.co.il",
    "social_links": "Not provided",
    "location": "Rehovot, Israel",
    "service_type": "Coffee shop"
  }
}
```

#### error

Emitted when an error occurs during processing.

**Payload:**
```typescript
{
  error: string;
}
```

**When Emitted:**
- When an exception occurs during message processing
- When authentication fails

**Example:**
```javascript
socket.on('error', (data) => {
  console.error('Error:', data.error);
  if (data.error.includes('Authentication')) {
    redirectToLogin();
  }
});
```

---

## API Contract

### Event Sequence Diagrams

#### Joining a Session with Initial Message

```
Client                          Server
  |                               |
  |--- join_session ----------->  |
  |                               |
  |<-- chat_history ------------- |  (existing messages)
  |                               |
  |<-- agent_thinking ----------- |  (start processing)
  |                               |
  |<-- message_chunk ------------ |  (optional, 0+ times)
  |<-- message_chunk ------------ |
  |                               |
  |<-- message_complete --------- |  (final response)
  |                               |
```

#### Sending a New Message

```
Client                          Server
  |                               |
  |--- send_message ----------->  |
  |                               |
  |<-- agent_thinking ----------- |  (start processing)
  |                               |
  |<-- message_chunk ------------ |  (optional, 0+ times)
  |<-- message_chunk ------------ |
  |                               |
  |<-- message_complete --------- |  (final response)
  |                               |
```

### Backwards Compatibility

#### ✅ Safe Changes (Non-Breaking)

1. **Adding new optional fields** to existing events
   - Old clients will ignore unknown fields
   - Example: Adding `metadata` field to `message_complete`

2. **Adding new events**
   - Old clients will ignore unknown events
   - Example: Adding `agent_progress` event

3. **Increasing event frequency**
   - Example: Emitting more `message_chunk` events

#### ❌ Breaking Changes (Require Client Update)

1. **Removing required fields** from events
   - Example: Removing `session_id` from `message_complete`

2. **Changing field types**
   - Example: Changing `business_card` from object to string

3. **Changing event names**
   - Example: Renaming `message_complete` to `response_done`

4. **Removing events**
   - Example: Removing `agent_thinking` event

5. **Changing event sequence**
   - Example: Emitting `message_complete` before `agent_thinking`

### Making Contract Changes

⚠️ **CRITICAL**: Changes to this contract are **BREAKING CHANGES** and require client updates!

If you need to make changes:

1. **Discuss with team first** - Breaking changes affect all clients
2. **Update this document** - Document the new contract
3. **Update tests** - Add tests for new contract
4. **Version the API** - Consider versioning if breaking changes required
5. **Update clients** - Coordinate client updates before deploying

**Remember**: The contract is a promise to our clients. Breaking it breaks their applications!

---

## Testing

### Run Contract Tests

Verify API stability:

```bash
make test
```

Contract tests are located in:
- `tests/test_socketio_contract.py` - Socket.IO event contracts
- `tests/test_http_contract.py` - HTTP API contracts

### Example Requests

#### Find Influencers
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to find fashion influencers for my sustainable clothing brand",
    "user_id": "demo_user"
  }'
```

#### Create Campaign Brief
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to create a campaign brief for launching a new skincare product",
    "user_id": "demo_user"
  }'
```

#### Generate Outreach Message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me write an outreach message to a fitness influencer",
    "user_id": "demo_user"
  }'
```

---

## Error Handling

All errors return appropriate HTTP status codes:

**500 Internal Server Error:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found:**
```json
{
  "detail": "Session not found"
}
```

---

## Version History

### v1.0.0 (Current)
- Initial Socket.IO event contract
- HTTP session management API
- Business card collection via onboarding agent
- Authentication support (Google OAuth + anonymous users)

---

## Summary

The Creo API provides:

✅ **HTTP endpoints** for session management
✅ **Socket.IO events** for real-time chat
✅ **Stable contract** with backwards compatibility guarantees
✅ **Business card collection** via onboarding agent
✅ **Authentication** support (OAuth + anonymous)
✅ **Streaming responses** via message chunks
✅ **Error handling** with clear error messages

For questions or issues, check the interactive documentation at `/docs` or review the contract tests.
