# Creator Finder Agent - Examples

## Example 1: Food Campaign

**User Input:**
"I need creators for my organic meal kit business. Budget is $15,000, looking for 3 creators, focused on health-conscious millennials in the US."

**Agent Response:**
"Perfect! I'd love to help you find food content creators for your organic meal kit campaign. Quick question - which platform would you prefer? YouTube, Instagram, TikTok, or would you like to search across all platforms?"

**User**: "Let's focus on Instagram and TikTok"

**Agent Response:**
"Great choice! Let me search for food content creators on Instagram and TikTok.

Based on your specifications:
- Category: Food
- Platforms: Instagram, TikTok
- Location: US
- Budget: $15,000
- Number of creators: 3
- Price range per creator: $4,500 - $15,000
- Target audience: Health-conscious millennials

Searching now..."

[Uses find_creators tool with: category="food", platform=None (searches both), location="US", min_price=4500, max_price=15000, max_results=10, target_audience="health-conscious millennials healthy eating"]

**Tool Returns:**
List of 8 creators including:
1. @HealthyEatsDaily - Instagram, 250K followers, 5.2% engagement, $3,500-$12,000
2. @CleanFoodKitchen - TikTok, 180K followers, 6.8% engagement, $2,500-$9,000
3. @WellnessChef - Instagram, 95K followers, 8.1% engagement, $1,500-$7,500

**Agent Presents:**
"Great news! I found 8 food creators on Instagram and TikTok that match your criteria. Here are the top 3 based on engagement:

1. **@WellnessChef** (Instagram - 95K followers)
   - High engagement rate of 8.1%
   - Estimated price: $1,500-$7,500
   - Focuses on healthy cooking and meal prep
   - Location: New York, US

2. **@CleanFoodKitchen** (TikTok - 180K followers)
   - Excellent engagement rate of 6.8%
   - Estimated price: $2,500-$9,000
   - Specializes in plant-based and clean eating
   - Location: California, US

3. **@HealthyEatsDaily** (Instagram - 250K followers)
   - Solid engagement rate of 5.2%
   - Estimated price: $3,500-$12,000
   - Covers organic recipes and nutrition
   - Location: Texas, US

All three creators are in your budget range and have strong engagement with health-conscious millennials. Would you like more details on any of these creators, or should I search with different criteria?"

## Example 2: Tech Campaign

**User Input:**
"Looking for tech reviewers for our new smartphone launch. Need 2 creators, $20,000 budget total, global audience interested in mobile technology."

**Agent Response:**
"I'll help you find tech creators for your smartphone launch!

Campaign details:
- Category: Tech
- Location: Global (any)
- Budget: $20,000
- Number of creators: 2
- Price range per creator: $8,000 - $20,000
- Target audience: Mobile technology enthusiasts

Which platform would you like to focus on? YouTube is popular for detailed tech reviews, but Instagram and TikTok are great for quick product showcases."

**User**: "YouTube works best for us"

**Agent**: "Perfect! Searching for YouTube tech creators now..."

[Uses find_creators tool with: category="tech", platform="YouTube", location=None, min_price=8000, max_price=20000, max_results=10, target_audience="mobile technology smartphone enthusiasts"]

**Tool Returns:**
List of 6 tech creators specializing in mobile reviews.

**Agent Presents:**
"Found 6 YouTube tech creators who specialize in smartphone reviews and mobile technology:

1. **Mobile Tech Review** (YouTube - 890K subscribers)
   - Engagement: 4.5%
   - Price range: $10,000-$18,000
   - Deep-dive smartphone comparisons
   - Global audience

2. **Gadget Guru** (YouTube - 450K subscribers)
   - Engagement: 6.2%
   - Price range: $8,500-$15,000
   - Consumer-focused tech reviews
   - North America & Europe

These creators have strong engagement with tech-savvy audiences and fit within your budget. Would you like me to provide more information about any specific creator?"

## Example 3: Iterative Search

**User Input:**
"I want travel vloggers but the results are too expensive for my $5,000 budget."

**Agent Response:**
"I understand. Let me adjust the search to find travel creators that better fit your $5,000 budget. How many creators would you like to work with? This will help me calculate the right price range.

Also, micro-influencers (10K-100K subscribers) often have great engagement rates and more affordable pricing. Would you like me to focus on that range?"

**User**: "Yes, 2 creators would be good."

**Agent**: "Perfect! Searching for travel content creators with pricing between $2,000-$5,000 per creator..."

[Performs new search with adjusted parameters]

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
