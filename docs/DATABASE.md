# Database Setup Guide

This project uses two databases:

1. **Firestore** - For storing structured data (conversations, sessions, campaigns)
2. **Pinecone** - For vector embeddings and semantic search

## Overview

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│Firestore│ │ Pinecone │
│(NoSQL)  │ │ (Vector) │
└─────────┘ └──────────┘
```

---

## Firestore Setup

### What is Firestore?

Firestore is Google's NoSQL document database. We use it to store:
- **Conversations**: Chat messages between users and agents
- **Sessions**: User session data
- **Campaigns**: Marketing campaign information
- **Analytics**: Usage events and metrics

### Free Tier

- ✅ **1GB storage FREE**
- ✅ **50,000 reads/day FREE**
- ✅ **20,000 writes/day FREE**
- ✅ **20,000 deletes/day FREE**

### Setup Steps

#### 1. Enable Firestore

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create Firestore database (choose Native mode)
gcloud firestore databases create \
  --location=nam5 \
  --project=gen-lang-client-0751221742
```

Or via Console:
1. Go to: https://console.cloud.google.com/firestore
2. Click "Create Database"
3. Choose "Native mode"
4. Select location: `nam5` (US multi-region) or your preferred location

#### 2. Local Testing with Firestore Emulator

```bash
# Using docker-compose (recommended)
docker-compose up firestore

# Or install and run locally
gcloud components install cloud-firestore-emulator
gcloud emulators firestore start --host-port=localhost:8080
```

Set environment variable for local testing:
```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
export GCP_PROJECT_ID=demo-creo
```

#### 3. Authentication

**Local Development:**
```bash
# Use your gcloud credentials
gcloud auth application-default login
```

**Cloud Run (Production):**
- Automatically uses the service account
- No additional configuration needed

### Usage Examples

```python
from db import ConversationDB, SessionDB, CampaignDB

# Store a conversation message
conv_db = ConversationDB()
conv_db.save_message(
    session_id="session_123",
    user_id="user_456",
    role="user",
    message="I need help finding influencers"
)

# Get conversation history
history = conv_db.get_conversation_history("session_123")

# Create a session
session_db = SessionDB()
session_db.create_session("session_123", "user_456")

# Save a campaign
campaign_db = CampaignDB()
campaign_db.save_campaign(
    user_id="user_456",
    campaign_data={"name": "Summer Campaign", "budget": 50000}
)
```

---

## Pinecone Setup

### What is Pinecone?

Pinecone is a vector database for storing and searching embeddings. We use it for:
- **Semantic Search**: Find similar conversations/campaigns
- **RAG (Retrieval Augmented Generation)**: Provide context to agents
- **Conversation Memory**: Remember relevant past interactions

### Free Tier

- ✅ **100,000 vectors FREE forever**
- ✅ **1 index**
- ✅ **2GB storage**
- ✅ Perfect for competitions!

### Setup Steps

#### 1. Create Pinecone Account

1. Sign up at: https://www.pinecone.io/
2. No credit card required for free tier
3. Verify your email

#### 2. Get API Key

1. Go to: https://app.pinecone.io/
2. Navigate to "API Keys"
3. Copy your API key

#### 3. Add to Environment

**Local (.env file):**
```bash
PINECONE_API_KEY=your-pinecone-api-key-here
```

**Cloud Run:**
```bash
gcloud run services update creo \
  --region us-central1 \
  --set-env-vars PINECONE_API_KEY=your-key
```

**GitHub Actions (for CI/CD):**
Add `PINECONE_API_KEY` to GitHub Secrets:
https://github.com/oron-mozes/creo/settings/secrets/actions

#### 4. Create Index (Automatic)

The first time you use the vector database, it will automatically create an index named `creo-embeddings`.

Or manually:
```python
from vector_db import get_or_create_index

index = get_or_create_index(
    index_name="creo-embeddings",
    dimension=768,  # Gemini embedding size
    metric="cosine"
)
```

### Usage Examples

```python
from vector_db import VectorDB, store_campaign_knowledge, search_campaign_knowledge

# Store campaign knowledge
texts = [
    "Target audience: Millennials interested in sustainable fashion",
    "Budget: $50,000 for influencer partnerships",
    "Timeline: 3-month campaign starting in June"
]
store_campaign_knowledge(
    campaign_id="camp_123",
    texts=texts,
    user_id="user_456"
)

# Search for relevant information
results = search_campaign_knowledge(
    query="What is the target audience?",
    campaign_id="camp_123",
    user_id="user_456",
    top_k=3
)

# Direct usage
vdb = VectorDB()

# Store text with embedding
vdb.upsert_text(
    id="unique_id_1",
    text="This is some text to embed and store",
    metadata={"source": "user_input", "campaign_id": "camp_123"},
    namespace="user_456"
)

# Semantic search
matches = vdb.search(
    query="find similar text",
    top_k=5,
    namespace="user_456",
    filter={"campaign_id": "camp_123"}
)
```

---

## Environment Variables

Required environment variables:

```bash
# .env file
GEMINI_API_KEY=your-gemini-api-key
PINECONE_API_KEY=your-pinecone-api-key
GCP_PROJECT_ID=gen-lang-client-0751221742  # Optional, defaults to this

# For local Firestore emulator (optional)
FIRESTORE_EMULATOR_HOST=localhost:8080
```

---

## Testing Databases Locally

### Test with Docker Compose

```bash
# Start Firestore emulator + app
docker-compose up

# App will be at: http://localhost:8000
# Firestore emulator at: http://localhost:8080
```

### Test Firestore

```python
# Test script
from db import ConversationDB, SessionDB

# Will use emulator if FIRESTORE_EMULATOR_HOST is set
conv_db = ConversationDB()
conv_db.save_message("test_session", "test_user", "user", "Hello!")

messages = conv_db.get_conversation_history("test_session")
print(messages)
```

### Test Pinecone

```python
# Test script
from vector_db import VectorDB

vdb = VectorDB()

# Store test data
vdb.upsert_text(
    id="test_1",
    text="Influencer marketing for fashion brands",
    namespace="test"
)

# Search
results = vdb.search("fashion marketing", namespace="test")
print(results)
```

---

## Database Models (Pydantic)

We use Pydantic for type safety and validation:

```python
from db import Message, Session, Campaign, AnalyticsEvent

# Create a message with validation
message = Message(
    session_id="session_123",
    user_id="user_456",
    role="user",
    message="Hello, agent!",
    metadata={"source": "web"}
)

# Create a campaign with validation
campaign = Campaign(
    user_id="user_456",
    name="Summer Campaign",
    budget=50000.0,
    channels=["Instagram", "TikTok"]
)
```

---

## Production Considerations

### Firestore

1. **Indexes**: Create composite indexes for complex queries
   ```bash
   # Indexes defined in firestore.indexes.json
   gcloud firestore indexes create --composite-indexes=firestore.indexes.json
   ```

2. **Security Rules**: Set up security rules in production
   ```javascript
   // firestore.rules
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /conversations/{document} {
         allow read, write: if request.auth != null
           && request.auth.uid == resource.data.user_id;
       }
     }
   }
   ```

3. **Backups**: Enable automated backups

### Pinecone

1. **Namespaces**: Use user_id as namespace for data isolation
2. **Metadata Filters**: Use for efficient filtering
3. **Batch Operations**: Upsert in batches of 100 for best performance
4. **Monitor Usage**: Check dashboard at https://app.pinecone.io/

---

## Cost Monitoring

### Firestore

Monitor usage:
```bash
# View Firestore metrics
gcloud firestore operations list
```

Dashboard: https://console.cloud.google.com/firestore/usage

### Pinecone

Dashboard: https://app.pinecone.io/organizations/-/projects

Watch for:
- Vector count (max 100K on free tier)
- Storage usage (max 2GB on free tier)
- Request rate

---

## Troubleshooting

### Firestore Issues

**Error: Permission denied**
```bash
# Re-authenticate
gcloud auth application-default login
```

**Error: Database not found**
```bash
# Create database
gcloud firestore databases create --region=us-central
```

**Emulator connection refused**
```bash
# Check if emulator is running
docker-compose ps

# Restart emulator
docker-compose restart firestore
```

### Pinecone Issues

**Error: API key invalid**
- Check your API key at https://app.pinecone.io/
- Verify environment variable is set

**Error: Index not found**
- Index is created automatically on first use
- Or create manually via dashboard

**Error: Quota exceeded**
- Free tier limit: 100K vectors
- Delete old vectors or upgrade plan

---

## Quick Reference

```bash
# Install dependencies
make install

# Test databases locally with Docker
docker-compose up

# Run server (will connect to real databases)
make server

# Environment variables needed
export GEMINI_API_KEY=your-key
export PINECONE_API_KEY=your-key
export FIRESTORE_EMULATOR_HOST=localhost:8080  # Optional, for local testing
```

---

## Next Steps

- [ ] Set up Firestore security rules
- [ ] Create Firestore indexes for common queries
- [ ] Implement data backup strategy
- [ ] Monitor database usage
- [ ] Set up alerts for quota limits
