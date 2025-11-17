# Creator Finder Agent - Examples

## Example 1: Local Coffee Shop Campaign

**User Input:**
"I need influencers to promote my coffee shop in Tel Aviv. Looking for local creators who talk about food and coffee culture."

**Agent Response:**
I'll help you find local coffee and food influencers in Tel Aviv!

```python
search_influencers(
    query="coffee food beverage cafe lifestyle local",
    filters={
        "location_country": {"$eq": "Israel"},
        "location_city": {"$eq": "Tel Aviv"},
        "followers": {"$gte": 10000}
    },
    top_k=5
)
```

Found 5 influencers in Tel Aviv:

1. **@anthony.coffee**
   - Platform: YouTube
   - Followers: 261,263
   - Engagement: 5.66%
   - Category: Food & Beverage / Coffee
   - Audience: 47% women, 53% men, ages 25-34
   - Performance: Bronze tier
   - Email: oronmozes+anthonycoffee@gmail.com

2. **@gadget_amelia**
   - Platform: Instagram
   - Followers: 155,563
   - Engagement: 6.56%
   - Category: Tech & Gaming / Gadgets
   - Audience: 52% women, 48% men, ages 18-24
   - Performance: Bronze tier
   - Email: oronmozes+gadgetamelia@gmail.com

These influencers have strong local presence and engaged audiences in your target demographic!

---

## Example 2: Fitness Brand with Female Audience

**User Input:**
"I'm launching a women's fitness apparel line. Need influencers with primarily female audiences interested in fitness and wellness."

**Agent Response:**
Perfect! I'll search for fitness influencers with female-dominant audiences.

```python
search_influencers(
    query="fitness gym workout wellness women health",
    filters={
        "audience_gender_female": {"$gte": 65},
        "audience_age_range": {"$eq": "25-34"}
    },
    top_k=5
)
```

Found 5 fitness influencers with 65%+ female audiences:

1. **@yoga_instructor_isabella**
   - Platform: Instagram
   - Followers: 89,421
   - Engagement: 7.2%
   - Category: Fitness & Wellness / Yoga
   - Audience: 78% women, 22% men, ages 25-34
   - Interested in: yoga, wellness, meditation
   - Performance: Silver tier, 4 campaigns, 2.1x avg ROI
   - Email: oronmozes+yogainstructorisabella@gmail.com

These creators have highly engaged female audiences perfect for your apparel launch!

---

## Example 3: Tech Product Launch - High Performers

**User Input:**
"We're launching a new gadget and need proven influencers who drive conversions. Budget allows for mid-tier creators (50K-200K followers)."

**Agent Response:**
I'll find proven tech influencers with strong ROI history.

```python
search_influencers(
    query="tech gadgets product reviews unboxing technology",
    filters={
        "followers": {"$gte": 50000, "$lte": 200000},
        "avg_campaign_roi": {"$gte": 2.5},
        "campaign_count": {"$gte": 5},
        "performance_tier": {"$eq": "gold"}
    },
    top_k=5
)
```

Found 3 proven tech influencers in your budget range:

1. **@tech_reviewer_lucas**
   - Platform: YouTube
   - Followers: 156,000
   - Engagement: 5.8%
   - Category: Tech & Gaming / Tech Reviews
   - Performance: Gold tier, 12 campaigns, 3.2x avg ROI, 4.5% conversion
   - Audience: 65% men, 35% women, ages 25-34
   - Email: oronmozes+techreviewerlucas@gmail.com

These influencers have proven track records driving conversions for tech products!

---

## Example 4: Broad Category Search

**User Input:**
"Show me top gaming influencers with good engagement"

**Agent Response:**
```python
search_influencers(
    query="gaming esports gameplay video games",
    filters={
        "category": {"$eq": "tech_and_gaming"},
        "subcategory": {"$eq": "gaming"},
        "followers": {"$gte": 30000},
        "engagement_rate": {"$gte": 4.0}
    },
    top_k=5
)
```

Found 5 gaming influencers with 4%+ engagement:

1. **@esports_champion_noah**
   - Platform: TikTok
   - Followers: 187,450
   - Engagement: 6.8%
   - Specializes in: esports, FPS games, gameplay
   - Audience: 72% men, 28% women, ages 18-24
   - Performance: Silver tier
   - Email: oronmozes+esportschampionnoah@gmail.com

---

## Example 5: No Results - Refining Search

**User Input:**
"Find vegan food influencers in Japan with 500K+ followers"

**Agent Response:**
```python
search_influencers(
    query="vegan food plant-based vegetarian healthy eating",
    filters={
        "location_country": {"$eq": "Japan"},
        "followers": {"$gte": 500000}
    },
    top_k=5
)
```

I couldn't find influencers matching all criteria (vegan + Japan + 500K+ followers). Let me try a broader search:

**Option 1: Remove follower requirement**
```python
search_influencers(
    query="vegan food plant-based vegetarian healthy eating",
    filters={
        "location_country": {"$eq": "Japan"},
        "followers": {"$gte": 10000}
    },
    top_k=5
)
```

**Option 2: Expand location to Asia**
```python
search_influencers(
    query="vegan food plant-based Asia vegetarian",
    filters={"followers": {"$gte": 500000}},
    top_k=5
)
```

Which approach would you prefer?

---

## Example 6: Multi-Criteria Complex Search

**User Input:**
"Need fashion influencers in NYC, female audience 60%+, engagement over 5%, who've done at least 3 campaigns"

**Agent Response:**
```python
search_influencers(
    query="fashion style outfit NYC New York clothing trends",
    filters={
        "location_country": {"$eq": "USA"},
        "location_city": {"$eq": "New York"},
        "engagement_rate": {"$gte": 5.0},
        "audience_gender_female": {"$gte": 60},
        "campaign_count": {"$gte": 3}
    },
    top_k=5
)
```

Found 2 fashion influencers matching all criteria:

1. **@fashionista_sophia**
   - Platform: Instagram
   - Followers: 125,890
   - Engagement: 5.9%
   - Location: New York, USA
   - Audience: 73% women, 27% men, ages 18-24
   - Performance: Gold tier, 8 campaigns, 2.8x avg ROI
   - Email: oronmozes+fashionistasophia@gmail.com

These creators meet your strict criteria and have proven campaign success!

---

## Example 7: Explaining Why an Influencer is a Good Match

**User Input:**
"Why is @anthony.coffee a good fit for my Tel Aviv cafe?"

**Agent Response:**
@anthony.coffee is an excellent match for several reasons:

**Location Alignment** ✅
- Based in Milan, Italy (European coffee culture similar to Tel Aviv)
- Audience from Italy (coffee-loving demographic)

**Niche Expertise** ✅
- Specializes in: Food & Beverage / Coffee
- Content themes: Coffee culture, recipes, brewing techniques
- Creates content in Italian and English

**Strong Engagement** ✅
- 5.66% engagement rate (above 3% industry standard)
- 261K+ followers (good reach without mega-influencer pricing)
- Authenticity score: 0.89 (mostly real followers)

**Audience Demographics** ✅
- 47% women, 53% men (balanced, coffee appeals to all)
- Ages 25-34 (prime coffee-drinking demographic)
- Interested in: food, lifestyle, dining

**Considerations** ⚠️
- Bronze tier (newer to campaigns, lower rates but less proven)
- No campaign history yet (could negotiate better rates)
- Italy-based (may need to discuss travel or remote collaboration)

**Recommendation**: Great for brand awareness and reaching European coffee enthusiasts. Consider pairing with a local Tel Aviv micro-influencer for local reach.
