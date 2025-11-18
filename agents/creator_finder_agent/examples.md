# Examples

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

