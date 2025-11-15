# Creo Agent API Documentation

FastAPI server that exposes the orchestrator agent, which routes requests to specialized sub-agents.

## Starting the Server

```bash
make install  # Install dependencies including FastAPI
make server   # Start the server on http://localhost:8000
```

The server will start on `http://localhost:8000` with automatic reload enabled.

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "agent": "orchestrator"
}
```

---

### 2. Chat with Orchestrator Agent
**POST** `/api/chat`

Send a message to the orchestrator agent. The orchestrator analyzes your request and routes it to the appropriate sub-agent.

**Request Body:**
```json
{
  "message": "I need to find fashion influencers for my brand",
  "user_id": "user123",
  "session_id": "optional-session-id"
}
```

**Fields:**
- `message` (required): Your request message
- `user_id` (optional): Unique user identifier (default: "default_user")
- `session_id` (optional): Session ID for conversation continuity (auto-generated if not provided)

**Response:**
```json
{
  "response": "I'll help you find fashion influencers. Let me redirect you to the creator finder agent...",
  "session_id": "session_abc123",
  "user_id": "user123"
}
```

---

### 3. Clear User Session
**DELETE** `/api/session/{user_id}`

Clear the conversation session for a specific user.

**Response:**
```json
{
  "status": "success",
  "message": "Session cleared for user: user123"
}
```

---

## Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Postman Example Requests

### Example 1: Find Influencers
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "I need to find fashion influencers for my sustainable clothing brand",
  "user_id": "demo_user"
}
```

### Example 2: Create Campaign Brief
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "I want to create a campaign brief for launching a new skincare product",
  "user_id": "demo_user"
}
```

### Example 3: Generate Outreach Message
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Help me write an outreach message to a fitness influencer for a protein powder campaign",
  "user_id": "demo_user"
}
```

### Example 4: Build Complete Campaign
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "I need a complete marketing campaign strategy for a B2B SaaS product launch",
  "user_id": "demo_user"
}
```

### Example 5: Multi-step Workflow
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "I need to find creators, then create outreach messages, then build a campaign for my eco-friendly water bottle brand",
  "user_id": "demo_user"
}
```

---

## How the Orchestrator Routes Requests

The orchestrator agent automatically routes your request to the appropriate sub-agent based on your message:

| Intent | Routed To | Description |
|--------|-----------|-------------|
| Find influencers/creators | `creator_finder_agent` | Searches for relevant influencers |
| Create campaign brief | `campaing_brief_agent` | Generates campaign briefs |
| Write outreach messages | `outreach_message_agent` | Crafts personalized outreach |
| Build campaign strategy | `campaign_builder_agent` | Creates complete campaign plans |
| Multi-step workflows | Multiple agents | Coordinates across agents |

---

## Session Management

- Each `user_id` maintains its own conversation context
- Sessions persist across requests using the same `user_id` and `session_id`
- Clear a session with `DELETE /api/session/{user_id}` to start fresh

---

## Error Handling

All errors return appropriate HTTP status codes:

**500 Internal Server Error:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Development

The server runs with auto-reload enabled when started with `make server`. Any changes to `server.py` or agent files will automatically restart the server.
