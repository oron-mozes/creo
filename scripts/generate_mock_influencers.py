"""
Generate mock influencer data for testing the creator_finder_agent.

This script creates 100 realistic influencer profiles across different:
- Platforms (Instagram, TikTok, YouTube)
- Categories (Food, Fashion, Tech, Travel, Fitness, etc.)
- Locations (Global coverage)
- Follower ranges (10K - 500K)
- Performance tiers (Bronze, Silver, Gold, Platinum)
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
TOTAL_INFLUENCERS = 100
OUTPUT_FILE = Path(__file__).parent.parent / "agents/creator_finder_agent/data/seed_influencers.json"

# Templates
PLATFORMS = ["instagram", "tiktok", "youtube"]

CATEGORIES = {
    "food_and_beverage": ["coffee", "restaurants", "baking", "healthy_eating", "vegan", "wine"],
    "fashion_and_beauty": ["fashion", "makeup", "skincare", "streetwear", "sustainable_fashion"],
    "fitness_and_wellness": ["gym", "yoga", "running", "nutrition", "mental_health"],
    "travel_and_lifestyle": ["travel", "luxury_travel", "budget_travel", "van_life", "photography"],
    "tech_and_gaming": ["tech_reviews", "gaming", "coding", "gadgets", "ai"],
    "business_and_finance": ["entrepreneurship", "investing", "real_estate", "productivity"],
    "parenting_and_family": ["parenting", "pregnancy", "baby_products", "family_travel"],
    "home_and_diy": ["interior_design", "gardening", "diy", "organization"],
    "entertainment": ["comedy", "music", "dance", "art", "books"]
}

LOCATIONS = [
    ("USA", "New York"), ("USA", "Los Angeles"), ("USA", "Miami"), ("USA", "Austin"), ("USA", "San Francisco"),
    ("UK", "London"), ("UK", "Manchester"),
    ("Israel", "Tel Aviv"), ("Israel", "Jerusalem"),
    ("Italy", "Rome"), ("Italy", "Milan"),
    ("France", "Paris"), ("France", "Lyon"),
    ("Spain", "Barcelona"), ("Spain", "Madrid"),
    ("Germany", "Berlin"), ("Germany", "Munich"),
    ("Japan", "Tokyo"), ("Japan", "Osaka"),
    ("Australia", "Sydney"), ("Australia", "Melbourne"),
    ("Canada", "Toronto"), ("Canada", "Vancouver"),
    ("Brazil", "São Paulo"), ("Brazil", "Rio de Janeiro"),
    ("India", "Mumbai"), ("India", "Bangalore"),
    ("Mexico", "Mexico City"), ("Mexico", "Guadalajara"),
    ("Thailand", "Bangkok"), ("Thailand", "Chiang Mai"),
    ("UAE", "Dubai"),
    ("Singapore", "Singapore"),
    ("South Korea", "Seoul"),
    ("Netherlands", "Amsterdam"),
    ("Indonesia", "Bali"),
]

LANGUAGE_MAP = {
    "USA": ["en"], "UK": ["en"], "Australia": ["en"], "Canada": ["en", "fr"],
    "Israel": ["en", "he"], "Italy": ["it", "en"], "France": ["fr", "en"],
    "Spain": ["es", "en"], "Germany": ["de", "en"], "Japan": ["ja", "en"],
    "Brazil": ["pt", "en"], "India": ["en", "hi"], "Mexico": ["es", "en"],
    "Thailand": ["th", "en"], "UAE": ["ar", "en"], "Singapore": ["en", "zh"],
    "South Korea": ["ko", "en"], "Netherlands": ["nl", "en"], "Indonesia": ["id", "en"]
}

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason", "Isabella", "Lucas",
    "Mia", "Alexander", "Charlotte", "James", "Amelia", "Benjamin", "Harper", "Elijah", "Evelyn",
    "Logan", "Abigail", "Michael", "Emily", "Daniel", "Elizabeth", "Matthew", "Sofia", "Jackson",
    "Avery", "David", "Ella", "Joseph", "Scarlett", "Carter", "Grace", "Owen", "Chloe", "Samuel",
    "Victoria", "Wyatt", "Riley", "John", "Aria", "Jack", "Lily", "Luke", "Aubrey", "Jayden",
    "Zoey", "Dylan", "Penelope", "Grayson", "Layla", "Levi", "Nora", "Isaac", "Lillian", "Gabriel",
    "Hannah", "Julian", "Addison", "Mateo", "Eleanor", "Anthony", "Natalie", "Jaxon", "Luna",
    "Lincoln", "Savannah", "Joshua", "Brooklyn", "Christopher", "Leah", "Andrew", "Zoe", "Theodore",
    "Stella", "Caleb", "Hazel", "Ryan", "Ellie", "Asher", "Paisley", "Nathan", "Audrey", "Thomas",
    "Skylar", "Leo", "Violet", "Isaiah", "Claire", "Charles", "Bella", "Josiah", "Aurora", "Hudson"
]

BIO_TEMPLATES = {
    "coffee": "☕ Coffee enthusiast | {specialty} | {location} | {cta}",
    "restaurants": "👨‍🍳 {specialty} chef | Food lover | {location} | {cta}",
    "fashion": "👗 Fashion {specialty} | Style tips | {location} | {cta}",
    "makeup": "💄 Makeup artist | {specialty} tutorials | {location} | {cta}",
    "gym": "💪 {specialty} trainer | Fitness coach | {location} | {cta}",
    "yoga": "🧘‍♀️ Yoga instructor | {specialty} | {location} | {cta}",
    "travel": "🌍 {specialty} traveler | {countries} countries | {location} | {cta}",
    "tech_reviews": "🚀 Tech reviewer | {specialty} | {location} | {cta}",
    "gaming": "🎮 {specialty} gamer | Esports | {location} | {cta}",
    "entrepreneurship": "💼 {specialty} | Business coach | {location} | {cta}",
}

SPECIALTIES = {
    "coffee": ["Specialty coffee", "Latte art", "Coffee roasting", "Barista skills"],
    "restaurants": ["Italian cuisine", "Vegan cooking", "Fine dining", "Street food"],
    "fashion": ["Sustainable fashion", "Streetwear", "Luxury brands", "Thrift shopping"],
    "makeup": ["Cruelty-free beauty", "Glam looks", "Natural makeup", "Special effects"],
    "gym": ["Personal training", "Bodybuilding", "HIIT workouts", "Strength training"],
    "yoga": ["Mindfulness", "Vinyasa flow", "Meditation", "Breathwork"],
    "travel": ["Budget travel", "Luxury travel", "Solo travel", "Van life"],
    "tech_reviews": ["Gadget unboxing", "AI & ML", "Smart home", "Mobile tech"],
    "gaming": ["FPS", "RPG", "Esports", "Game reviews"],
    "entrepreneurship": ["Startups", "E-commerce", "SaaS", "Digital marketing"],
}

CTAS = [
    "DM for collabs",
    "Link in bio",
    "Check my latest post",
    "Join my community",
    "Shop my recommendations",
    "Book a session",
    "Subscribe for more",
    "Follow my journey"
]

# Audience demographics by category
AUDIENCE_PROFILES = {
    "coffee": {
        "interests": ["coffee", "food", "lifestyle", "travel", "photography"],
        "age_ranges": ["18-24", "25-34", "35-44"],
        "gender_bias": "balanced"  # 45-55% female
    },
    "restaurants": {
        "interests": ["food", "dining", "cooking", "travel", "lifestyle"],
        "age_ranges": ["25-34", "35-44", "45-54"],
        "gender_bias": "balanced"
    },
    "fashion": {
        "interests": ["fashion", "beauty", "shopping", "lifestyle", "travel"],
        "age_ranges": ["18-24", "25-34"],
        "gender_bias": "female"  # 60-80% female
    },
    "makeup": {
        "interests": ["beauty", "makeup", "skincare", "fashion", "lifestyle"],
        "age_ranges": ["18-24", "25-34"],
        "gender_bias": "female"  # 70-90% female
    },
    "gym": {
        "interests": ["fitness", "health", "sports", "nutrition", "lifestyle"],
        "age_ranges": ["18-24", "25-34", "35-44"],
        "gender_bias": "male"  # 55-70% male
    },
    "yoga": {
        "interests": ["yoga", "wellness", "meditation", "fitness", "health"],
        "age_ranges": ["25-34", "35-44", "45-54"],
        "gender_bias": "female"  # 65-85% female
    },
    "travel": {
        "interests": ["travel", "adventure", "photography", "culture", "food"],
        "age_ranges": ["25-34", "35-44"],
        "gender_bias": "balanced"
    },
    "tech_reviews": {
        "interests": ["technology", "gadgets", "innovation", "gaming", "science"],
        "age_ranges": ["18-24", "25-34", "35-44"],
        "gender_bias": "male"  # 60-75% male
    },
    "gaming": {
        "interests": ["gaming", "esports", "technology", "entertainment", "streaming"],
        "age_ranges": ["13-17", "18-24", "25-34"],
        "gender_bias": "male"  # 65-80% male
    },
    "entrepreneurship": {
        "interests": ["business", "entrepreneurship", "finance", "productivity", "leadership"],
        "age_ranges": ["25-34", "35-44", "45-54"],
        "gender_bias": "male"  # 55-65% male
    },
}


def generate_username(name, subcategory, platform):
    """Generate a realistic username."""
    name_lower = name.lower()
    category_short = subcategory.replace("_", "")[:6]

    patterns = [
        f"{category_short}_{name_lower}",
        f"{name_lower}_{category_short}",
        f"{name_lower}.{category_short}",
        f"the_{name_lower}_{category_short}",
    ]

    return random.choice(patterns)


def generate_bio(subcategory, location_city, location_country):
    """Generate a realistic bio."""
    template = BIO_TEMPLATES.get(subcategory, "✨ Content creator | {specialty} | {location} | {cta}")
    specialty = random.choice(SPECIALTIES.get(subcategory, ["Passionate creator"]))
    cta = random.choice(CTAS)
    location = location_city if location_city else location_country

    countries_visited = random.randint(15, 85) if "travel" in subcategory else None

    bio = template.format(
        specialty=specialty,
        location=location,
        cta=cta,
        countries=countries_visited if countries_visited else ""
    )

    return bio


def generate_content_themes(subcategory):
    """Generate content themes based on subcategory."""
    theme_map = {
        "coffee": ["coffee culture", "cafe reviews", "barista tips", "coffee brewing"],
        "restaurants": ["recipes", "cooking tips", "food photography", "restaurant reviews"],
        "fashion": ["outfit ideas", "fashion trends", "styling tips", "brand reviews"],
        "makeup": ["makeup tutorials", "product reviews", "beauty hacks", "skincare routines"],
        "gym": ["workout routines", "fitness tips", "nutrition advice", "transformation stories"],
        "yoga": ["yoga flows", "mindfulness", "meditation", "wellness tips"],
        "travel": ["travel guides", "destination reviews", "travel hacks", "cultural experiences"],
        "tech_reviews": ["product reviews", "tech news", "unboxing videos", "tutorials"],
        "gaming": ["game reviews", "gameplay", "esports", "gaming tips"],
        "entrepreneurship": ["business tips", "startup advice", "productivity hacks", "success stories"],
    }

    return theme_map.get(subcategory, ["lifestyle content", "daily vlogs", "tips and tricks", "inspiration"])


def generate_audience_demographics(subcategory, location_country):
    """Generate realistic audience demographics based on influencer niche."""
    profile = AUDIENCE_PROFILES.get(subcategory, {
        "interests": ["lifestyle", "entertainment", "social media"],
        "age_ranges": ["18-24", "25-34"],
        "gender_bias": "balanced"
    })

    # Generate gender distribution
    gender_bias = profile["gender_bias"]
    if gender_bias == "female":
        female = random.randint(60, 85)
        male = 100 - female
    elif gender_bias == "male":
        male = random.randint(55, 75)
        female = 100 - male
    else:  # balanced
        female = random.randint(45, 55)
        male = 100 - female

    # Pick primary age range
    age_range = random.choice(profile["age_ranges"])

    # Get interests
    interests = profile["interests"]

    # Audience location (usually same country or nearby)
    audience_location = location_country

    return {
        "gender": {
            "female": female,
            "male": male
        },
        "age_range": age_range,
        "interests": interests,
        "location": audience_location
    }


def generate_performance_tier(engagement_rate, authenticity_score, campaign_roi):
    """Calculate performance tier based on metrics."""
    score = (engagement_rate / 10) * 0.4 + authenticity_score * 0.3 + (campaign_roi / 5) * 0.3

    if score >= 0.85:
        return "platinum"
    elif score >= 0.75:
        return "gold"
    elif score >= 0.65:
        return "silver"
    else:
        return "bronze"


def generate_influencer(idx):
    """Generate a single influencer profile."""
    # Basic info
    platform = random.choice(PLATFORMS)
    category = random.choice(list(CATEGORIES.keys()))
    subcategory = random.choice(CATEGORIES[category])
    location_country, location_city = random.choice(LOCATIONS)
    languages = LANGUAGE_MAP.get(location_country, ["en"])
    name = random.choice(FIRST_NAMES)

    # Generate username and display name
    username = generate_username(name, subcategory, platform)
    display_name = f"{name}'s {subcategory.replace('_', ' ').title()}"

    # Metrics (realistic distribution)
    followers = random.randint(10000, 500000)
    engagement_rate = round(random.uniform(2.0, 8.0), 2)
    avg_likes = int(followers * (engagement_rate / 100))
    avg_comments = int(avg_likes * random.uniform(0.02, 0.08))
    posts_count = random.randint(50, 800)

    # Quality scores
    authenticity_score = round(random.uniform(0.75, 0.98), 2)
    brand_safety_score = round(random.uniform(0.80, 0.98), 2)
    quality_score = round((authenticity_score + brand_safety_score) / 2, 2)

    # Campaign performance
    campaign_count = random.randint(0, 20)
    if campaign_count > 0:
        avg_campaign_roi = round(random.uniform(1.5, 4.5), 1)
        avg_conversion_rate = round(random.uniform(0.015, 0.065), 3)
        days_ago = random.randint(1, 90)
        last_campaign_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    else:
        avg_campaign_roi = 0
        avg_conversion_rate = 0
        last_campaign_date = None

    performance_tier = generate_performance_tier(engagement_rate, authenticity_score, avg_campaign_roi)

    # Generate ID
    platform_prefix = platform
    influencer_id = f"{platform_prefix}_{1000 + idx}"

    # Bio and themes
    bio = generate_bio(subcategory, location_city, location_country)
    content_themes = generate_content_themes(subcategory)

    # Audience demographics
    audience_demographics = generate_audience_demographics(subcategory, location_country)

    # Pricing (based on followers and performance tier)
    # Price per 1k followers: $1 to $10
    base_price = (followers / 1000) * random.uniform(1.0, 10.0)

    # Adjust by performance tier
    tier_multipliers = {
        "platinum": random.uniform(1.8, 2.5),
        "gold": random.uniform(1.4, 1.8),
        "silver": random.uniform(1.0, 1.4),
        "bronze": random.uniform(0.6, 1.0)
    }
    price = int(base_price * tier_multipliers[performance_tier])

    # Ensure price is within range 100-5000
    price = max(100, min(5000, price))

    # Currency (80% USD, 20% EUR)
    currency = random.choices(["USD", "EUR"], weights=[80, 20])[0]

    # Contact info (use demo email with + aliasing for testing)
    clean_username = username.replace('.', '').replace('_', '')
    email = f"oronmozes+{clean_username}@gmail.com"  # Gmail + aliasing for tracking
    website = f"https://{clean_username}.com"
    profile_url = f"https://{platform}.com/{'@' if platform == 'tiktok' or platform == 'youtube' else ''}{username}"

    return {
        "id": influencer_id,
        "platform": platform,
        "username": username,
        "display_name": display_name,
        "bio": bio,
        "category": category,
        "subcategory": subcategory,
        "location_country": location_country,
        "location_city": location_city,
        "languages": languages,
        "followers": followers,
        "engagement_rate": engagement_rate,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "posts_count": posts_count,
        "authenticity_score": authenticity_score,
        "brand_safety_score": brand_safety_score,
        "quality_score": quality_score,
        "campaign_count": campaign_count,
        "avg_campaign_roi": avg_campaign_roi,
        "avg_conversion_rate": avg_conversion_rate,
        "last_campaign_date": last_campaign_date,
        "performance_tier": performance_tier,
        "email": email,
        "website": website,
        "profile_url": profile_url,
        "content_themes": content_themes,
        "audience_demographics": audience_demographics,
        "price": price,
        "currency": currency
    }


def main():
    """Generate 100 influencers and save to JSON."""
    print(f"Generating {TOTAL_INFLUENCERS} mock influencers...")

    # Load existing seed data (first 10)
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r') as f:
            existing = json.load(f)
        print(f"Found {len(existing)} existing influencers")
        start_idx = len(existing)
    else:
        existing = []
        start_idx = 0

    # Generate remaining influencers
    influencers = existing.copy()
    for i in range(start_idx, TOTAL_INFLUENCERS):
        influencer = generate_influencer(i)
        influencers.append(influencer)

        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{TOTAL_INFLUENCERS} influencers...")

    # Save to file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(influencers, f, indent=2)

    print(f"\n✓ Successfully generated {len(influencers)} influencers")
    print(f"✓ Saved to: {OUTPUT_FILE}")

    # Print statistics
    print("\n=== Statistics ===")
    platforms = {}
    categories = {}
    tiers = {}

    for inf in influencers:
        platforms[inf['platform']] = platforms.get(inf['platform'], 0) + 1
        categories[inf['category']] = categories.get(inf['category'], 0) + 1
        tiers[inf['performance_tier']] = tiers.get(inf['performance_tier'], 0) + 1

    print(f"\nPlatforms: {platforms}")
    print(f"Categories: {categories}")
    print(f"Performance Tiers: {tiers}")

    # Calculate averages
    avg_followers = sum(inf['followers'] for inf in influencers) / len(influencers)
    avg_engagement = sum(inf['engagement_rate'] for inf in influencers) / len(influencers)

    print(f"\nAverage Followers: {avg_followers:,.0f}")
    print(f"Average Engagement Rate: {avg_engagement:.2f}%")


if __name__ == "__main__":
    main()
