# Campaign Brief Agent - Examples

These examples demonstrate how the campaign brief agent should interact with users to collect campaign information while leveraging existing business card data.

## Example 1: Complete Information from User Request

**Business Card Context:**
```json
{
  "name": "Alma Cafe",
  "location": "Rehovot, Israel",
  "service_type": "Cafe",
  "website": "https://almacafe.com",
  "social_links": "@almacafe"
}
```

**User Input:** "I want to find Instagram food influencers to promote my new matcha latte. Budget is $300 per creator."

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote my new matcha latte"
- Platform: "Instagram"
- Budget: $300
- Niche: Already know it's "Food" from business card

```
Great! I can help you find Instagram food influencers for Alma Cafe to promote your new matcha latte.

Are you looking to drive more foot traffic to your cafe in Rehovot, or do you have a specific goal in mind like increasing awareness or online orders?
```

**User:** "I want more people to come try it in person"

**Agent:**
```
Perfect! And do you have any specific audience in mind you want to reach?
```

**User:** "Young professionals in the area, ages 25-35"

**Agent:**
```
Excellent! Let me confirm the campaign brief for Alma Cafe:

**Campaign Goal:** Get more people to visit and try the new matcha latte
**Location:** Rehovot (your cafe location)
**Platform:** Instagram
**Niche:** Food/Cafe
**Budget per Creator:** $300
**Number of Creators:** 1-2 creators
**Target Audience:** Young professionals ages 25-35 in Rehovot area

Does this look good?
```

**User:** "Yes perfect!"

**Agent:**
```
Perfect! I've saved your campaign brief. Let's move forward with finding the right creators for you!

CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Get more people to visit and try the new matcha latte",
  "location": "Rehovot",
  "platform": "Instagram",
  "niche": "Food",
  "budget_per_creator": 300.0,
  "num_creators": 2,
  "business_name": "Alma Cafe",
  "product_info": "New matcha latte",
  "audience_demographics": "Young professionals ages 25-35 in Rehovot area",
  "audience_interests": null
}
```

---

## Example 2: Minimal Information - Agent Guides Collection

**Business Card Context:**
```json
{
  "name": "TechStart Solutions",
  "location": "San Francisco, CA",
  "service_type": "Software Development",
  "website": "https://techstart.io",
  "social_links": null
}
```

**User Input (first message in session):** "I need influencers for my new app launch"

**Agent Response:**
*Agent extracts from message:*
- Goal: "new app launch" (partial - needs clarification)
- Platform: Not mentioned
- Budget: Not mentioned
- Niche: Already know it's "Tech" from business card service_type

```
Great! I can help you plan an influencer campaign for TechStart Solutions' new app launch.

Tell me more about the goal of this campaign - are you looking to drive app downloads, increase brand awareness, or something else?
```

**User:** "Drive app downloads"

**Agent:**
```
Perfect! Which platform would work best for reaching your target audience - Instagram, TikTok, YouTube, or are you open to any platform?
```

**User:** "I think TikTok and Instagram"

**Agent:**
```
Excellent choices for app promotion! Do you have a specific audience or budget in mind for this campaign?
```

**User:** "Not really, just want to reach tech-savvy people. Maybe $500 per creator?"

**Agent:**
```
Got it! Let me confirm the campaign brief for TechStart Solutions:

**Campaign Goal:** Drive app downloads for new app launch
**Location:** San Francisco, CA (can target nationally/globally if needed)
**Platform:** Instagram and TikTok
**Niche:** Tech/Software
**Budget per Creator:** $500
**Number of Creators:** 2-3 creators
**Target Audience:** Tech-savvy users

Does this look good?
```

**User:** "Yes!"

**Agent:**
```
Perfect! I've saved your campaign brief.

CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Drive app downloads for new app launch",
  "location": "San Francisco",
  "platform": "Instagram",
  "niche": "Tech",
  "budget_per_creator": 500.0,
  "num_creators": 3,
  "business_name": "TechStart Solutions",
  "product_info": "New app launch",
  "audience_demographics": null,
  "audience_interests": "Tech-savvy users"
}
```

---

## Example 3: User Provides Everything in First Message

**Business Card Context:**
```json
{
  "name": "Fitness Studio LA",
  "location": "Los Angeles, CA",
  "service_type": "Fitness Studio",
  "website": "https://fitnessstudiola.com",
  "social_links": "@fitnessstudiola"
}
```

**User Input (first message):** "I want to find 5 Instagram fitness influencers in LA to promote our new yoga class series. Budget is $200-400 per creator, targeting women ages 25-40 interested in wellness."

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote our new yoga class series"
- Platform: "Instagram"
- Num creators: 5
- Budget: $200-400 (use $400 as max)
- Location: "LA" (matches business location)
- Audience: "women ages 25-40 interested in wellness"
- Niche: "Fitness" (from business card)

```
Perfect! I can help you find Instagram fitness influencers in LA for Fitness Studio LA's new yoga class series.

Let me confirm the campaign brief:

**Campaign Goal:** Promote new yoga class series
**Location:** Los Angeles, CA
**Platform:** Instagram
**Niche:** Fitness/Wellness
**Budget per Creator:** $400 (max)
**Number of Creators:** 5 influencers
**Target Audience:** Women ages 25-40 interested in wellness

Does this look good?
```

**User:** "Perfect!"

**Agent:**
```
Great! I've saved your campaign brief.

CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Promote new yoga class series",
  "location": "Los Angeles",
  "platform": "Instagram",
  "niche": "Fitness",
  "budget_per_creator": 400.0,
  "num_creators": 5,
  "business_name": "Fitness Studio LA",
  "product_info": "New yoga class series",
  "audience_demographics": "Women ages 25-40",
  "audience_interests": "Wellness, yoga"
}
```

---

---

## Example 4: No Business Card - Hard Gate

**Business Card Context:** `null` (missing)

**User Input:** "I want to find influencers to promote my coffee shop"

**Agent Response:**
```
I need to know more about your business first. Let me gather some information about your business so I can create a personalized campaign brief.
```

**Notes:**
- ❌ Agent does NOT infer business name
- ❌ Agent does NOT ask campaign questions
- ✅ Agent stops immediately and requests business card information

---

## Example 5: Budget Range Handling

**Business Card Context:**
```json
{
  "name": "Urban Bakery",
  "location": "Portland, OR",
  "service_type": "Bakery",
  "website": "https://urbanbakery.com",
  "social_links": "@urbanbakery"
}
```

**User Input:** "I want to promote my new sourdough bread line. Budget is $100-$300 per post."

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote my new sourdough bread line" ✅ (clear goal pattern)
- Budget: $100-$300 → Extract UPPER value: **$300.0**
- Platform: Not mentioned
- Niche: "Food" from business card

```
Great! I can help you promote Urban Bakery's new sourdough bread line.

Which platform would you like to focus on? (Instagram, TikTok, YouTube, or any platform)
```

**User:** "Instagram"

**Agent:**
```
Perfect! Let me confirm the campaign brief for Urban Bakery:

**Campaign Goal:** Promote new sourdough bread line
**Location:** Portland, OR
**Platform:** Instagram
**Niche:** Food/Bakery
**Budget per Creator:** $300 (max from range)
**Number of Creators:** 2-3 creators
**Target Audience:** Food enthusiasts in Portland

Does this look good?
```

**User:** "Yes!"

**Agent:**
```
CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Promote new sourdough bread line",
  "location": "Portland",
  "platform": "Instagram",
  "niche": "Food",
  "budget_per_creator": 300.0,
  "num_creators": 3,
  "business_name": "Urban Bakery",
  "product_info": "New sourdough bread line",
  "audience_demographics": null,
  "audience_interests": "Food enthusiasts"
}
```

---

## Example 6: Location Override + Clear Goal

**Business Card Context:**
```json
{
  "name": "NYC Fashion Boutique",
  "location": "New York, NY",
  "service_type": "Fashion Retail",
  "website": "https://nycfashion.com",
  "social_links": "@nycfashion"
}
```

**User Input:** "I want to promote my online shop to customers in Canada"

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote my online shop" ✅ (clear goal pattern - DO NOT ASK AGAIN)
- Location: "Canada" (OVERRIDE from business card's "New York")
- Platform: Not mentioned
- Niche: "Fashion" from business card

```
Great! I can help you promote NYC Fashion Boutique's online shop to customers in Canada.

Which platform would work best for reaching your Canadian audience? (Instagram, TikTok, YouTube, or any platform)
```

**Notes:**
- ✅ Agent extracted goal automatically (did NOT re-ask "What's the goal?")
- ✅ Agent recognized location override (Canada, not NYC)
- ✅ Agent asked for NEXT missing field (platform), not the goal

---

## Example 7: Number of Creators Specified

**Business Card Context:**
```json
{
  "name": "Eco Products Inc",
  "location": "Seattle, WA",
  "service_type": "Sustainable Products",
  "website": "https://ecoproducts.com",
  "social_links": "@ecoproducts"
}
```

**User Input:** "I need 3 influencers to promote our new bamboo toothbrushes"

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote our new bamboo toothbrushes" ✅ (clear goal pattern)
- Number of creators: 3 ✅ (explicitly stated - DO NOT ASK AGAIN)
- Platform: Not mentioned
- Budget: Not mentioned
- Niche: "Sustainable/Eco" from business card

```
Perfect! I can help you find 3 influencers to promote Eco Products Inc's new bamboo toothbrushes.

Which platform would you like to focus on for this campaign? (Instagram, TikTok, YouTube, or any platform)
```

**User:** "Instagram and TikTok"

**Agent:**
```
Great choices! Do you have any specific audience in mind or a budget per creator?
```

**User:** "Eco-conscious millennials, budget around $250"

**Agent:**
```
Let me confirm the campaign brief for Eco Products Inc:

**Campaign Goal:** Promote new bamboo toothbrushes
**Location:** Seattle, WA (or nationwide if online)
**Platform:** Instagram and TikTok
**Niche:** Sustainable/Eco Products
**Budget per Creator:** $250
**Number of Creators:** 3 influencers
**Target Audience:** Eco-conscious millennials

Does this look good?
```

**User:** "Perfect!"

**Agent:**
```
CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Promote new bamboo toothbrushes",
  "location": "Seattle",
  "platform": "Instagram",
  "niche": "Sustainable",
  "budget_per_creator": 250.0,
  "num_creators": 3,
  "business_name": "Eco Products Inc",
  "product_info": "New bamboo toothbrushes",
  "audience_demographics": "Millennials",
  "audience_interests": "Eco-conscious, sustainability"
}
```

---

## Example 8: One-Turn Full Extraction with Goal Detection

**Business Card Context:**
```json
{
  "name": "Pet Paradise",
  "location": "Austin, TX",
  "service_type": "Pet Store",
  "website": "https://petparadise.com",
  "social_links": "@petparadise"
}
```

**User Input:** "Find influencers to promote my new organic dog treats on Instagram, targeting dog owners in Texas, 3 influencers, $200 each"

**Agent Response:**
*Agent extracts from message:*
- Goal: "promote my new organic dog treats" ✅ (clear "promote" pattern - DO NOT ASK)
- Platform: "Instagram" ✅
- Location: "Texas" (matches business location)
- Audience: "dog owners in Texas" ✅
- Number of creators: 3 ✅
- Budget: $200 ✅
- Niche: "Pet" from business card
- ALL FIELDS EXTRACTED - NO QUESTIONS NEEDED

```
Perfect! I can help you find 3 Instagram influencers to promote Pet Paradise's new organic dog treats to dog owners in Texas.

Let me confirm the campaign brief:

**Campaign Goal:** Promote new organic dog treats
**Location:** Texas
**Platform:** Instagram
**Niche:** Pet/Pet Care
**Budget per Creator:** $200
**Number of Creators:** 3 influencers
**Target Audience:** Dog owners in Texas

Does this look good?
```

**User:** "Yes!"

**Agent:**
```
CAMPAIGN_BRIEF_CONFIRMATION:
{
  "goal": "Promote new organic dog treats",
  "location": "Texas",
  "platform": "Instagram",
  "niche": "Pet",
  "budget_per_creator": 200.0,
  "num_creators": 3,
  "business_name": "Pet Paradise",
  "product_info": "New organic dog treats",
  "audience_demographics": "Dog owners in Texas",
  "audience_interests": "Pet care, dogs"
}
```

**Notes:**
- ✅ Agent extracted ALL information from one message
- ✅ Agent did NOT re-ask for goal (clear "promote" pattern detected)
- ✅ Agent went straight to confirmation
- ✅ No unnecessary questions asked

---

## Key Patterns Demonstrated

1. ✅ **Extract from session messages** - Always check what user already told you
2. ✅ **Goal detection patterns** - Never re-ask if goal is clearly stated
3. ✅ **Budget range handling** - Always use UPPER value
4. ✅ **Location override** - Use campaign location if different from business
5. ✅ **Number of creators extraction** - Extract and don't re-ask
6. ✅ **Hard gate for missing business card** - Stop immediately, don't hallucinate
7. ✅ **Single question at a time** - Never overwhelm with multiple questions
8. ✅ **Reference business card** - Show you know their business
9. ✅ **Ask conversationally** - One question at a time, following priority order
10. ✅ **Confirm before saving** - Show summary and get approval
11. ✅ **Output after confirmation** - CAMPAIGN_BRIEF_CONFIRMATION block only after user approves
12. ✅ **Auto-inherit from business card** - business_name, location, niche
