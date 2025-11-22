"""Tools for the creator finder agent to search for creators in Pinecone vector database."""

from typing import Optional
import logging
import re

from google.adk.tools import FunctionTool  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def find_creators_helper(
    category: Optional[str] = None,
    location: Optional[str] = None,
    budget: Optional[float] = None,
    min_price: float = 0.0,
    max_price: Optional[float] = 100000.0,
    max_results: int = 10,
    target_audience: Optional[str] = None,
    platform: Optional[str] = None
) -> str:
    """Find creators based on campaign criteria using semantic search in Pinecone.

    This helper function searches the creator database (Pinecone) for influencers that match
    the specified criteria using semantic search and metadata filtering.

    Args:
        category: Content category/niche/topic (e.g., 'food', 'travel', 'tech', 'lifestyle', 'fashion', 'beauty', 'fitness', 'gaming').
                 A creator is deemed relevant if the topic/niche appears in ANY of these fields: 'subcategory', 'content_themes',
                 'category', or 'audience_interests'. Optional.
        location: Geographic location at any level - country (e.g., 'US', 'UK'), region/state (e.g., 'California', 'Texas'),
                 city (e.g., 'New York', 'London'), or neighborhood (e.g., 'Queens NY', 'Brooklyn'). Optional.
        budget: Total budget for the campaign. Used to calculate follower range:
                - If single value: min_followers = budget*3, max_followers = budget*20
                - If range (min_price/max_price): min_followers = min_price*6, max_followers = max_price*20
        min_price: Minimum price per creator based on budget calculation (default: 0.0)
        max_price: Maximum price per creator based on budget (default: 100000.0)
        max_results: Maximum number of creators to return (default: 10, max: 50)
        target_audience: Description of target audience. Age ranges (e.g., "18-24", "25-34") and age keywords
                        (e.g., "millennials" → 28-43, "gen z" → 18-27, "teens" → 13-19) are converted to numeric ranges
                        and matched against the creator's 'audience_age_range' field. A match occurs if ANY part of the
                        creator's age range falls within the target range (e.g., target "18-50" matches creator "20-25").
                        Interest keywords (e.g., "fitness", "gaming", "food") are matched against 'audience_interests' field.
        platform: Platform filter (e.g., 'YouTube', 'Instagram', 'TikTok'). Optional, defaults to all platforms.

    Returns:
        A formatted string containing the list of creators with their details:
        - Creator name
        - Platform
        - Subscriber/follower count
        - Engagement rate
        - Description
        - Estimated price range
        - Profile/Channel URL
    """
    logger.info("="*80)
    logger.info(f"find_creators_helper called with: category={category}, location={location}, budget={budget}, min_price={min_price}, max_price={max_price}, platform={platform}, target_audience={target_audience}")
    logger.info("="*80)

    # Calculate follower range based on budget
    min_followers = None
    max_followers = None

    # TODO: when budget become a must, adjust this if to fit.
    if budget is not None:
        # Single budget value provided
        min_followers = budget * 3
        max_followers = budget * 20
        logger.info(f"Budget-based follower range: {min_followers:,.0f} - {max_followers:,.0f}")
    elif min_price > 0 or max_price < 100000.0:
        # Budget range provided via min_price/max_price
        min_followers = min_price * 6
        max_followers = max_price * 20
        logger.info(f"Price range-based follower range: {min_followers:,.0f} - {max_followers:,.0f}")

    try:
        # Initialize Pinecone vector database (lazy initialization)
        import sys
        import os
        # Add parent directory to path to import vector_db
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
        from vector_db import VectorDB  # type: ignore[import-not-found]

        vector_db = VectorDB()
        logger.info("VectorDB initialized successfully")

        # Build semantic search query
        query_parts = ["creator"]
        if category:
            query_parts.insert(0, category)
        if platform:
            query_parts.append(platform)
        if location:
            query_parts.append(f"in {location}")

        # Note: target_audience is handled via metadata filtering (audience_age_range, audience_interests)
        # rather than semantic search to ensure precise matching
        search_query = " ".join(query_parts)
        logger.info(f"Search query: '{search_query}'")

        # Build metadata filter for Pinecone
        # NOTE: We do NOT filter by category or platform in metadata because:
        # 1. Semantic search already handles category matching
        # 2. Category values in DB may be different from user input (e.g., "diy" vs "home_and_garden")
        # 3. Platform filtering with OR logic (multiple platforms) is handled in post-filtering
        metadata_filter = {}

        logger.info(f"Metadata filter: {metadata_filter if metadata_filter else 'None'}")
        if category:
            logger.info(f"Category '{category}' will be matched via post-filtering")
        if platform:
            logger.info(f"Platform '{platform}' will be matched via post-filtering")

        # Search in Pinecone (creators namespace)
        # Fetch more results for filtering by price and location
        search_results = vector_db.search(
            query=search_query,
            top_k=min(max_results * 3, 50),  # Fetch extra for filtering
            namespace="",
            filter=metadata_filter if metadata_filter else None
        )

        if not search_results:
            return f"No creators found matching the criteria: category='{category}', location='{location or 'any'}', platform='{platform or 'any'}'"

        logger.info(f"Pinecone returned {len(search_results)} results before filtering")

        # Filter results by location, followers, platform, category/niche, and target audience
        filtered_creators = []
        filter_stats = {"follower_count": 0, "platform": 0, "location": 0, "category": 0, "target_audience": 0, "passed": 0}

        for result in search_results:
            creator = result["metadata"]
            creator_name = creator.get("display_name", "Unknown")

            # Filter by follower count if budget-based range is set
            if min_followers is not None and max_followers is not None:
                creator_followers = creator.get("followers", 0)

                # Skip if creator's followers are outside the calculated range
                if creator_followers < min_followers or creator_followers > max_followers:
                    logger.info(f"Filtered out {creator_name}: followers {creator_followers} outside range {min_followers}-{max_followers}")
                    filter_stats["follower_count"] += 1
                    continue

            # Filter by platform (case-insensitive partial match)
            # Supports multiple platforms separated by commas (e.g., "YouTube, Instagram")
            # Comma-separated values are treated as OR (match ANY), unless user explicitly uses "and"/"&"
            if platform:
                creator_platform = (creator.get("platform", "") or "").lower()

                # Check if user wants ALL platforms (uses "and" or "&")
                if " and " in platform.lower() or " & " in platform:
                    # AND logic: creator must match all platforms (impossible for a single creator, so this will likely filter all)
                    platform_parts = [plat.strip().lower() for plat in platform.replace(" and ", ",").replace(" & ", ",").split(',')]
                    all_platform_match = all(plat in creator_platform for plat in platform_parts)
                    if not all_platform_match:
                        logger.info(f"Filtered out {creator_name}: platform '{creator_platform}' doesn't match all of '{platform}'")
                        filter_stats["platform"] += 1
                        continue
                else:
                    # OR logic: creator must match ANY of the platforms (default)
                    platform_parts = [plat.strip().lower() for plat in platform.split(',')]

                    platform_match = False
                    for plat in platform_parts:
                        if plat in creator_platform:
                            platform_match = True
                            break

                    if not platform_match:
                        logger.info(f"Filtered out {creator_name}: platform '{creator_platform}' doesn't match any of '{platform}'")
                        filter_stats["platform"] += 1
                        continue

            # Filter by location (case-insensitive partial match)
            # Supports multiple locations separated by commas (e.g., "UK, Germany, France")
            # Comma-separated values are treated as OR (match ANY), unless user explicitly uses "and"/"&"
            if location:
                creator_city = creator.get("location_city", "")
                creator_country = creator.get("location_country", "")

                # Map common country code aliases
                country_aliases = {
                    'gb': 'uk',
                    'usa': 'us',
                    'united states': 'us',
                    'united kingdom': 'uk',
                    'deutschland': 'germany',
                    'de': 'germany',
                    'fr': 'france',
                }

                # Helper function to normalize location (apply aliases)
                def normalize_location(loc):
                    loc_lower = loc.strip().lower()
                    return country_aliases.get(loc_lower, loc_lower)

                # Check if user wants ALL locations (uses "and" or "&")
                if " and " in location.lower() or " & " in location:
                    # AND logic: creator must match all locations (rare case)
                    location_parts = [normalize_location(loc) for loc in location.replace(" and ", ",").replace(" & ", ",").split(',')]
                    all_match = all(
                        (creator_city and loc in creator_city.lower()) or (creator_country and loc in creator_country.lower())
                        for loc in location_parts
                    )
                    if not all_match:
                        logger.info(f"Filtered out {creator_name}: location '{creator_city}, {creator_country}' doesn't match all of '{location}'")
                        filter_stats["location"] += 1
                        continue
                else:
                    # OR logic: creator must match ANY of the locations (default)
                    location_parts = [normalize_location(loc) for loc in location.split(',')]

                    location_match = False
                    for location_part in location_parts:
                        # Check if this location part matches either city or country
                        city_match = creator_city and location_part in creator_city.lower()
                        country_match = creator_country and location_part in creator_country.lower()

                        if city_match or country_match:
                            location_match = True
                            break

                    if not location_match:
                        logger.info(f"Filtered out {creator_name}: location '{creator_city}, {creator_country}' doesn't match any of '{location}'")
                        filter_stats["location"] += 1
                        continue

            # Filter by category/niche/topic (check subcategory, content_themes, category, and audience_interests)
            # A creator is deemed relevant if the topic appears in ANY of these fields (case-insensitive)
            # Supports multiple categories separated by commas (e.g., "lifestyle, fashion")
            # Comma-separated values are treated as OR (match ANY), unless user explicitly uses "and"/"&"
            if category:
                # Helper function to convert field to lowercase string (handles both strings and lists)
                def to_lower_string(field):
                    if isinstance(field, list):
                        return " ".join(str(item).lower() for item in field)
                    elif field:
                        return str(field).lower()
                    return ""

                # Get all relevant fields for category matching (convert to lowercase for case-insensitive comparison)
                creator_category = to_lower_string(creator.get("category", ""))
                creator_subcategory = to_lower_string(creator.get("subcategory", ""))
                creator_content_themes = to_lower_string(creator.get("content_themes", ""))
                creator_audience_interests = to_lower_string(creator.get("audience_interests", ""))

                # Combine all fields for keyword matching
                category_combined = f"{creator_category} {creator_subcategory} {creator_content_themes} {creator_audience_interests}"

                # Check if user wants ALL categories (uses "and" or "&")
                if " and " in category.lower() or " & " in category:
                    # AND logic: creator must match all categories (rare case)
                    category_parts = [cat.strip().lower() for cat in category.replace(" and ", ",").replace(" & ", ",").split(',')]
                    all_category_match = all(
                        cat in category_combined or any(len(word) > 2 and word in category_combined for word in cat.split())
                        for cat in category_parts
                    )
                    if not all_category_match:
                        logger.info(f"Filtered out {creator_name}: doesn't match all categories '{category}'")
                        filter_stats["category"] += 1
                        continue
                else:
                    # OR logic: creator must match ANY of the categories (default)
                    category_parts = [cat.strip().lower() for cat in category.split(',')]

                    category_match = False
                    for cat in category_parts:
                        # Check if this category is found in any of the fields
                        # Match if the entire category OR any word (>2 chars) is found
                        if cat in category_combined or any(len(word) > 2 and word in category_combined for word in cat.split()):
                            category_match = True
                            break

                    if not category_match:
                        logger.info(f"Filtered out {creator_name}: category '{category}' not found in category: '{creator.get('category', '')}', subcategory: '{creator.get('subcategory', '')}', content_themes: '{creator.get('content_themes', '')}', audience_interests: '{creator.get('audience_interests', '')}'")
                        filter_stats["category"] += 1
                        continue

            # Filter by target audience (check audience_age_range and audience_interests)
            # Supports multiple age groups/keywords separated by commas (e.g., "millennials, gen z")
            # Comma-separated values are treated as OR (match ANY), unless user explicitly uses "and"/"&"
            if target_audience:
                target_audience_lower = target_audience.lower()

                # Check audience_age_range field for age-related keywords
                audience_age_range = creator.get("audience_age_range", "")
                # Check audience_interests field for interest/topic keywords (can be string or list)
                audience_interests_raw = creator.get("audience_interests", "")
                # Convert to string if it's a list
                if isinstance(audience_interests_raw, list):
                    audience_interests = " ".join(str(item) for item in audience_interests_raw)
                else:
                    audience_interests = str(audience_interests_raw) if audience_interests_raw else ""

                audience_match = False

                # Map age-related keywords to age ranges
                age_keyword_map = {
                    'gen z': (18, 27),
                    'genz': (18, 27),
                    'millennials': (28, 43),
                    'millennial': (28, 43),
                    'gen x': (44, 59),
                    'genx': (44, 59),
                    'baby boomers': (60, 78),
                    'boomers': (60, 78),
                    'teens': (13, 19),
                    'teenagers': (13, 19),
                    'young adults': (18, 35),
                    'adults': (18, 65),
                }

                # Extract creator's age range once
                creator_min_age = None
                creator_max_age = None
                if audience_age_range:
                    age_range_pattern = r'(\d+)\s*-\s*(\d+)'
                    creator_age_match = re.search(age_range_pattern, audience_age_range)
                    if creator_age_match:
                        creator_min_age = int(creator_age_match.group(1))
                        creator_max_age = int(creator_age_match.group(2))

                # Helper function to check if a target age range matches creator's age range
                def age_ranges_overlap(target_min, target_max, creator_min, creator_max):
                    if creator_min is None or creator_max is None:
                        return False
                    return (target_min <= creator_min <= target_max or
                            target_min <= creator_max <= target_max or
                            (creator_min <= target_min and creator_max >= target_max))

                # Check for multiple age groups (comma-separated)
                # Split by comma, but preserve "and"/"&" for AND logic detection
                age_check_performed = False

                # Try to match age keywords or numeric ranges
                for keyword, (min_age, max_age) in age_keyword_map.items():
                    if keyword in target_audience_lower:
                        age_check_performed = True
                        if age_ranges_overlap(min_age, max_age, creator_min_age, creator_max_age):
                            audience_match = True
                            logger.info(f"Age match: keyword '{keyword}' ({min_age}-{max_age}) overlaps with creator {creator_min_age}-{creator_max_age}")
                            break

                # If no keyword found, try to extract numeric age range (e.g., "18-24", "25-34")
                if not age_check_performed:
                    age_range_pattern = r'(\d+)\s*-\s*(\d+)'
                    target_age_match = re.search(age_range_pattern, target_audience)
                    if target_age_match:
                        age_check_performed = True
                        target_min_age = int(target_age_match.group(1))
                        target_max_age = int(target_age_match.group(2))

                        if age_ranges_overlap(target_min_age, target_max_age, creator_min_age, creator_max_age):
                            audience_match = True
                            logger.info(f"Age range match: target {target_min_age}-{target_max_age} overlaps with creator {creator_min_age}-{creator_max_age}")

                # If no age range match found, fall back to keyword matching for interests
                if not audience_match:
                    # Combine both fields for keyword matching
                    audience_combined = f"{audience_age_range} {audience_interests}".lower()

                    # Check if any part of target_audience is mentioned in the creator's audience fields
                    # Split target_audience into words/phrases to check individually
                    for word in target_audience_lower.split():
                        if len(word) > 2 and word in audience_combined:  # Skip very short words
                            audience_match = True
                            break

                if not audience_match:
                    logger.info(f"Filtered out {creator_name}: target audience '{target_audience}' not found in age_range: '{audience_age_range}' or interests: '{audience_interests}'")
                    filter_stats["target_audience"] += 1
                    continue

            # Creator passed all filters
            filter_stats["passed"] += 1
            filtered_creators.append(creator)

        # Log filter statistics
        logger.info("="*80)
        logger.info("FILTER STATISTICS:")
        logger.info(f"  Total from Pinecone: {len(search_results)}")
        logger.info(f"  Filtered by follower count: {filter_stats['follower_count']}")
        logger.info(f"  Filtered by platform: {filter_stats['platform']}")
        logger.info(f"  Filtered by location: {filter_stats['location']}")
        logger.info(f"  Filtered by category/niche: {filter_stats['category']}")
        logger.info(f"  Filtered by target audience: {filter_stats['target_audience']}")
        logger.info(f"  PASSED all filters: {filter_stats['passed']}")
        logger.info("="*80)

        if not filtered_creators:
            follower_msg = ""
            if min_followers is not None and max_followers is not None:
                follower_msg = f" with follower range {min_followers:,.0f}-{max_followers:,.0f}"
            return f"Found creators but none match the specified criteria{follower_msg} for location '{location or 'any'}'"

        # Sort by engagement rate (best match first)
        creators_sorted = sorted(
            filtered_creators,
            key=lambda x: x.get('engagement_rate', 0),
            reverse=True
        )[:max_results]

        # Format results with greeting and budget explanation
        result = "Hello! I'd be happy to help you find creators for your campaign.\n\n"

        # Explain budget-to-follower calculation
        if budget is not None:
            result += f"Based on your budget of ${budget:,.0f}, I searched for creators with follower counts between {min_followers:,.0f}-{max_followers:,.0f} (calculated as budget × 3 for minimum and budget × 20 for maximum).\n\n"
        elif min_followers is not None and max_followers is not None:
            result += f"Based on your budget range, I searched for creators with follower counts between {min_followers:,.0f}-{max_followers:,.0f} (calculated as min budget × 6 for minimum and max budget × 20 for maximum).\n\n"

        result += f"Found {len(creators_sorted)} creator(s) matching your criteria:\n\n"
        result += f"Category: {category}\n"
        result += f"Location: {location or 'Any'}\n"
        result += f"Platform: {platform or 'Any'}\n"
        if min_followers is not None and max_followers is not None:
            result += f"Follower Range: {min_followers:,.0f} - {max_followers:,.0f}\n"
        result += f"Target Audience: {target_audience or 'Not specified'}\n\n"
        result += "=" * 80 + "\n\n"

        for i, creator in enumerate(creators_sorted, 1):
            result += f"{i}. {creator.get('display_name', 'Unknown')}\n"
            result += f"   Platform: {creator.get('platform', 'N/A')}\n"

            # Display follower/subscriber count
            if creator.get('followers'):
                result += f"   Followers: {creator.get('followers'):,.0f}\n"

            # Display engagement and other metrics
            if creator.get('engagement_rate'):
                result += f"   Engagement Rate: {creator.get('engagement_rate')}%\n"

            if creator.get('posts_count'):
                result += f"   Posts: {creator.get('posts_count'):,.0f}\n"

            # Price
            creator_price = creator.get('price', 0)
            if creator_price:
                result += f"   Price: ${creator_price:,.2f}\n"

            # Profile URL
            url = creator.get('profile_url', 'N/A')
            result += f"   URL: {url}\n"

            # Description
            description = creator.get('bio', 'No description available')
            if len(description) > 200:
                description = description[:200] + '...'
            result += f"   Bio: {description}\n"

            # Location
            location_parts = []
            if creator.get('location_city'):
                location_parts.append(creator.get('location_city'))
            if creator.get('location_country'):
                location_parts.append(creator.get('location_country'))
            if location_parts:
                result += f"   Location: {', '.join(location_parts)}\n"

            result += "-" * 80 + "\n\n"

        return result

    except Exception as e:
        return f"Error searching for creators in database: {str(e)}\n\nPlease ensure the database is properly configured and populated with creator data."


# Create the tool instance
find_creators = FunctionTool(find_creators_helper)
