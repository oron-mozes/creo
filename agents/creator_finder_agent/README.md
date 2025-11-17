# Creator Finder Agent - Technical Documentation

## Overview

The Creator Finder Agent uses **semantic search with Pinecone** to find influencers that match campaign requirements. It combines:
- **Vector embeddings** (Google's text-embedding-004) for semantic matching
- **Metadata filtering** for precise criteria (followers, location, etc.)
- **Performance ranking** based on past campaign success

---

## Architecture

```
User Query
    ↓
[Embedding Generator] → Query embedding (768-dim vector)
    ↓
[Pinecone Search] → Semantic search + metadata filters
    ↓
[Ranker] → Re-rank by campaign performance
    ↓
Top N Influencers (with full details)
```

---

## Data Pipeline

### 1. Mock Data (100 Influencers)
**Location**: `data/seed_influencers.json`

**Platforms**: Instagram (29), TikTok (45), YouTube (26)

**Categories**:
- Food & Beverage (coffee, restaurants, etc.)
- Fashion & Beauty (makeup, skincare, etc.)
- Tech & Gaming (reviews, gaming, etc.)
- Fitness & Wellness (gym, yoga, etc.)
- Travel & Lifestyle
- Business & Finance
- And more...

**Key Fields**:
```json
{
  "id": "instagram_1000",
  "platform": "instagram",
  "username": "coffee_lover_jane",
  "bio": "☕ Coffee enthusiast...",
  "category": "food_and_beverage",
  "subcategory": "coffee",
  "location_country": "Israel",
  "location_city": "Tel Aviv",
  "followers": 45000,
  "engagement_rate": 4.2,
  "authenticity_score": 0.92,
  "performance_tier": "gold",
  "email": "oronmozes+coffeeloverjane@gmail.com",
  "content_themes": ["coffee culture", "cafe lifestyle"],
  "audience_demographics": {
    "gender": {"female": 60, "male": 40},
    "age_range": "25-34",
    "interests": ["coffee", "food", "lifestyle"],
    "location": "Israel"
  }
}
```

### 2. Embedding Generation
**Module**: `tools/embedding_generator.py`

**Composite Text Format**:
```
{bio}
Creates content about {content_themes}.
Specializes in {category}, particularly {subcategory}.
Based in {location}.
Creates content in {languages}.
Audience: {gender}, ages {age_range}, interested in {interests}, from {location}.
```

**Example**:
```
☕ Coffee enthusiast sharing latte art & cafe reviews in Tel Aviv
Creates content about coffee culture, cafe lifestyle, barista tips, food photography.
Specializes in food and beverage, particularly coffee.
Based in Tel Aviv, Israel.
Creates content in EN and HE.
Audience: 60% women, 40% men, ages 25-34, interested in coffee, food, lifestyle, from Israel.
```

### 3. Pinecone Index
**Module**: `tools/pinecone_client.py`

**Index Config**:
- Name: `creo-influencers`
- Dimension: 768 (text-embedding-004)
- Metric: cosine similarity
- Cloud: GCP (us-central1)

**Metadata Stored**:
- Profile: platform, username, bio, category, location, languages
- Metrics: followers, engagement_rate, quality scores
- Campaign performance: ROI, conversion rate, tier
- Audience: gender, age, interests, location
- Contact: email (oronmozes+{username}@gmail.com)

---

## Tools

### `embedding_generator.py`
Generates 768-dim embeddings from influencer profiles.

```python
from agents.creator_finder_agent.tools.embedding_generator import EmbeddingGenerator

gen = EmbeddingGenerator()

# Generate influencer embedding
embedding = gen.generate_influencer_embedding(influencer_data)

# Generate query embedding
query_embedding = gen.generate_query_embedding("coffee influencers in Israel")
```

### `pinecone_client.py`
Manages Pinecone index and search operations.

```python
from agents.creator_finder_agent.tools.pinecone_client import PineconeClient

client = PineconeClient()
client.create_index()

# Upsert influencer
client.upsert_influencer(
    influencer_id="instagram_12345",
    embedding=embedding_vector,
    metadata=metadata_dict
)

# Semantic search
results = client.search(
    query_embedding=query_vector,
    top_k=10
)

# Hybrid search (semantic + filters)
results = client.hybrid_search(
    query_embedding=query_vector,
    filters={
        "followers": {"$gte": 10000, "$lte": 100000},
        "engagement_rate": {"$gte": 3.0},
        "location_country": {"$eq": "Israel"}
    },
    top_k=10
)
```

---

## Setup & Usage

### 1. Generate Mock Data
```bash
python3 scripts/generate_mock_influencers.py
```

Generates 100 influencers with realistic data.

### 2. Seed Pinecone
```bash
# Ensure GOOGLE_API_KEY and PINECONE_API_KEY are set
export GOOGLE_API_KEY=your-key
export PINECONE_API_KEY=your-key

# Run seed script
python3 scripts/seed_pinecone.py
```

This will:
1. Load 100 influencers
2. Generate embeddings (takes ~5-10 minutes)
3. Upsert to Pinecone
4. Run a test search

### 3. Search for Influencers
```python
from agents.creator_finder_agent.tools.embedding_generator import EmbeddingGenerator
from agents.creator_finder_agent.tools.pinecone_client import PineconeClient

# Initialize
gen = EmbeddingGenerator()
client = PineconeClient()

# Search
query = "tech influencers with highly engaged audiences"
query_embedding = gen.generate_query_embedding(query)

results = client.hybrid_search(
    query_embedding=query_embedding,
    filters={"engagement_rate": {"$gte": 5.0}},
    top_k=5
)

for result in results:
    print(f"@{result['metadata']['username']}: {result['score']}")
```

---

## Search Examples

### Semantic Search
```python
# Natural language queries
"coffee influencers in Tel Aviv"
"fitness creators with female audiences"
"tech reviewers who create content in Korean"
"travel bloggers with audiences interested in photography"
```

### Hybrid Search (Semantic + Filters)
```python
client.hybrid_search(
    query_embedding=gen.generate_query_embedding("fashion influencers"),
    filters={
        "followers": {"$gte": 50000},
        "engagement_rate": {"$gte": 4.0},
        "audience_gender_female": {"$gte": 60},
        "location_country": {"$eq": "USA"}
    },
    top_k=10
)
```

---

## Performance Tiers

Influencers are ranked into tiers based on:
- Engagement rate (40% weight)
- Authenticity score (30% weight)
- Campaign ROI (30% weight)

**Tiers**:
- **Platinum** (score ≥ 0.85): Top performers, proven ROI
- **Gold** (score ≥ 0.75): Strong performers
- **Silver** (score ≥ 0.65): Solid performers
- **Bronze** (score < 0.65): New or lower performers

---

## Next Steps

1. **Search Tool** - High-level search interface for the agent
2. **Ranker** - Re-rank results by campaign performance
3. **Update Agent** - Integrate tools into creator_finder_agent
4. **Real API Integration** - Replace mock data with Modash/real API

---

## Files

```
agents/creator_finder_agent/
├── README.md                        # This file
├── PINECONE_SCHEMA.md              # Detailed schema documentation
├── agent.py                         # Agent definition
├── instruction.md                   # Agent instructions
├── examples.md                      # Agent examples
├── data/
│   └── seed_influencers.json       # 100 mock influencers
└── tools/
    ├── embedding_generator.py      # Generate embeddings
    ├── pinecone_client.py          # Pinecone integration
    ├── influencer_search.py        # High-level search (TODO)
    └── ranker.py                   # Performance ranking (TODO)

scripts/
├── generate_mock_influencers.py    # Generate seed data
└── seed_pinecone.py                # Populate Pinecone
```

---

## Contact Emails

All mock influencers use Gmail + aliasing for testing:
- Format: `oronmozes+{username}@gmail.com`
- Example: `oronmozes+coffeeloverjane@gmail.com`

This allows you to:
- Receive all test emails at `oronmozes@gmail.com`
- Filter by influencer using Gmail filters
- Test outreach campaign integration
