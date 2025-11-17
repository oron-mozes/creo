# Pinecone Schema for Influencer Search

## Index Configuration

**Index Name**: `creo-influencers`
**Dimension**: 768 (Google's text-embedding-004 model)
**Metric**: cosine (for semantic similarity)
**Cloud**: GCP (to match your Google Cloud setup)

## Vector Metadata Schema

Each influencer vector in Pinecone contains:

### Required Fields

```json
{
  "id": "instagram_12345678",           // Format: {platform}_{user_id}
  "platform": "instagram",               // instagram, tiktok, youtube
  "username": "coffee_lover_jane",
  "display_name": "Jane's Coffee Corner",

  // Profile Information
  "bio": "☕ Coffee enthusiast | Latte art | Tel Aviv",
  "category": "food_and_beverage",       // See categories below
  "subcategory": "coffee",
  "location_country": "Israel",
  "location_city": "Tel Aviv",
  "languages": ["en", "he"],

  // Metrics (for filtering)
  "followers": 45000,
  "engagement_rate": 4.2,                // Percentage
  "avg_likes": 1890,
  "avg_comments": 42,
  "posts_count": 324,

  // Quality Scores
  "authenticity_score": 0.92,            // 0-1, fake follower detection
  "brand_safety_score": 0.88,            // 0-1, content appropriateness
  "
_score": 0.85,            // 0-1, overall quality

  // Campaign Performance (updated after campaigns)
  "campaign_count": 3,                   // Number of campaigns completed
  "avg_campaign_roi": 2.4,               // Average ROI from past campaigns
  "avg_conversion_rate": 0.034,          // Average conversion rate
  "last_campaign_date": "2025-01-10",
  "performance_tier": "gold",            // bronze, silver, gold, platinum

  // Contact & Links
  "email": "jane@coffeecorner.com",
  "website": "https://janescoffeecorner.com",
  "profile_url": "https://instagram.com/coffee_lover_jane",

  // Indexing Metadata
  "indexed_at": "2025-01-17T10:00:00Z",
  "data_source": "mock",                 // mock, modash, custom_scraper
  "last_updated": "2025-01-17T10:00:00Z"
}
```

## Categories & Subcategories

### Food & Beverage
- coffee, restaurants, baking, healthy_eating, vegan, wine, cocktails

### Fashion & Beauty
- fashion, makeup, skincare, haircare, streetwear, luxury_fashion, sustainable_fashion

### Fitness & Wellness
- gym, yoga, running, nutrition, mental_health, meditation

### Travel & Lifestyle
- travel, luxury_travel, budget_travel, van_life, photography

### Tech & Gaming
- tech_reviews, gaming, coding, gadgets, ai, crypto

### Business & Finance
- entrepreneurship, investing, real_estate, productivity, saas

### Parenting & Family
- parenting, pregnancy, baby_products, family_travel

### Home & DIY
- interior_design, gardening, diy, organization, home_improvement

### Entertainment
- comedy, music, dance, art, books

## Embedding Strategy

The vector embedding is generated from a **composite text** combining:

1. **Bio** (70% weight) - Primary content describing the influencer
2. **Category + Subcategory** (15% weight) - Niche classification
3. **Location** (10% weight) - Geographic context
4. **Content themes** (5% weight) - Common topics/hashtags

**Example composite text:**
```
Coffee enthusiast sharing latte art and cafe reviews in Tel Aviv.
Niche: food and beverage, coffee.
Location: Tel Aviv, Israel.
Themes: coffee culture, cafe lifestyle, barista tips, food photography.
```

## Search Query Types

### 1. Semantic Search
**User query**: "I need influencers who love coffee and live in Israel"
**Process**: Embed query → Find similar vectors → Filter by metadata

### 2. Hybrid Search (Semantic + Filters)
**Filters**:
- `followers >= 10000 AND followers <= 100000`
- `engagement_rate >= 3.0`
- `location_country = "Israel"`
- `category = "food_and_beverage"`
- `authenticity_score >= 0.8`

### 3. Lookalike Search
**Input**: Existing influencer ID
**Process**: Use their vector to find similar influencers

## Performance Ranking Algorithm

After retrieving candidates from Pinecone, rank them by:

```python
final_score = (
    semantic_similarity * 0.40 +      # How well they match the query
    engagement_rate * 0.20 +          # Audience engagement
    authenticity_score * 0.15 +       # Follower quality
    campaign_performance * 0.15 +     # Past campaign success
    brand_safety_score * 0.10         # Content appropriateness
)
```

## Campaign Performance Updates

After a campaign completes, update the influencer metadata:

```python
# Calculate new performance metrics
new_roi = calculate_roi(campaign_results)
new_conversion_rate = calculate_conversion_rate(campaign_results)

# Update metadata in Pinecone
update_metadata(
    influencer_id,
    {
        "campaign_count": campaign_count + 1,
        "avg_campaign_roi": (avg_campaign_roi * campaign_count + new_roi) / (campaign_count + 1),
        "avg_conversion_rate": (avg_conversion_rate * campaign_count + new_conversion_rate) / (campaign_count + 1),
        "last_campaign_date": today,
        "performance_tier": calculate_tier(new_avg_roi)
    }
)
```

## Sync Strategy

### Initial Seed (Mock Data)
- Load 100-200 mock influencers
- Generate embeddings for all
- Upsert to Pinecone

### Future: API Sync
- Fetch new influencers from Modash/API daily
- Generate embeddings
- Upsert to Pinecone (upsert = update if exists, insert if new)

### Campaign-Based Updates
- After campaign completion: Update performance metrics
- Weekly: Refresh engagement rates for active influencers
- Monthly: Re-embed all influencers (in case bio/category changed)

## Tools to Build

1. **`embedding_generator.py`** - Generate embeddings from influencer data
2. **`pinecone_client.py`** - Initialize Pinecone, upsert, search
3. **`influencer_search.py`** - High-level search interface for agent
4. **`ranker.py`** - Rank search results by performance
5. **`seed_data_loader.py`** - Load mock data and populate Pinecone
