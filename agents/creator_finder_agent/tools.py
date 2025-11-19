"""Tools for the creator finder agent to search for creators in Pinecone vector database."""
import sys
print("DEBUG: Starting tools.py import", file=sys.stderr, flush=True)

from typing import List, Dict, Optional
print("DEBUG: Imported typing", file=sys.stderr, flush=True)

import logging
print("DEBUG: Imported logging", file=sys.stderr, flush=True)

print("DEBUG: About to import FunctionTool from google.adk.tools", file=sys.stderr, flush=True)
from google.adk.tools import FunctionTool
print("DEBUG: Imported FunctionTool", file=sys.stderr, flush=True)

logger = logging.getLogger(__name__)
print("DEBUG: Logger created", file=sys.stderr, flush=True)


def find_creators_helper(
    category: Optional[str] = None,
    location: Optional[str] = None,
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
        category: Content category (e.g., 'food', 'travel', 'tech', 'lifestyle', 'fashion', 'beauty', 'fitness', 'gaming'). Optional.
        location: Geographic location at any level - country (e.g., 'US', 'UK'), region/state (e.g., 'California', 'Texas'),
                 city (e.g., 'New York', 'London'), or neighborhood (e.g., 'Queens NY', 'Brooklyn'). Optional.
        min_price: Minimum price per creator based on budget calculation (default: 0.0)
        max_price: Maximum price per creator based on budget (default: 100000.0)
        max_results: Maximum number of creators to return (default: 10, max: 50)
        target_audience: Description of target audience demographics or interests (optional)
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
    logger.info(f"find_creators_helper called with: category={category}, location={location}, min_price={min_price}, max_price={max_price}, platform={platform}, target_audience={target_audience}")
    logger.info("="*80)

    try:
        # Initialize Pinecone vector database (lazy initialization)
        logger.info("Importing VectorDB...")
        import sys
        import os
        # Add parent directory to path to import vector_db
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
        from vector_db import VectorDB
        logger.info("Initializing VectorDB...")
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
        if target_audience:
            query_parts.append(f"for {target_audience}")

        search_query = " ".join(query_parts)
        logger.info(f"Search query: '{search_query}'")

        # Build metadata filter for Pinecone
        # NOTE: We do NOT filter by category in metadata because:
        # 1. Semantic search already handles category matching
        # 2. Category values in DB may be different from user input (e.g., "diy" vs "home_and_garden")
        metadata_filter = {}
        if platform:
            metadata_filter["platform"] = platform

        logger.info(f"Metadata filter: {metadata_filter if metadata_filter else 'None'}")
        if category:
            logger.info(f"Category '{category}' will be matched via semantic search, not metadata filter")

        # Search in Pinecone (creators namespace)
        # Fetch more results for filtering by price and location
        search_results = vector_db.search(
            query=search_query,
            top_k=min(max_results * 3, 50),  # Fetch extra for filtering
            namespace="",
            filter=metadata_filter if metadata_filter else None
        )

        if not search_results:
            return f"No creators found matching the criteria: category='{category}', location='{location or 'any'}', platform='{platform or 'any'}', price range=${min_price}-${max_price}"

        # Filter results by price range and location
        filtered_creators = []
        for result in search_results:
            creator = result["metadata"]

            # Filter by price range
            creator_price = creator.get("price", 0)

            # Skip if creator is too expensive or too cheap
            if creator_price > max_price or creator_price < min_price:
                continue

            # Filter by location (case-insensitive partial match)
            if location:
                creator_city = creator.get("location_city", "")
                creator_country = creator.get("location_country", "")
                location_lower = location.lower()

                # Check if location matches either city or country
                city_match = creator_city and location_lower in creator_city.lower()
                country_match = creator_country and location_lower in creator_country.lower()

                if not (city_match or country_match):
                    continue

            filtered_creators.append(creator)

        if not filtered_creators:
            return f"Found creators but none match the price range ${min_price:,.2f}-${max_price:,.2f} or location '{location or 'any'}'"

        # Sort by engagement rate (best match first)
        creators_sorted = sorted(
            filtered_creators,
            key=lambda x: x.get('engagement_rate', 0),
            reverse=True
        )[:max_results]

        # Format results
        result = f"Found {len(creators_sorted)} creator(s) matching your criteria:\n\n"
        result += f"Category: {category}\n"
        result += f"Location: {location or 'Any'}\n"
        result += f"Platform: {platform or 'Any'}\n"
        result += f"Price Range: ${min_price:,.2f} - ${max_price:,.2f}\n"
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
print("DEBUG: About to create FunctionTool instance", file=sys.stderr, flush=True)
find_creators = FunctionTool(find_creators_helper)
print("DEBUG: FunctionTool instance created", file=sys.stderr, flush=True)
print("DEBUG: tools.py module load complete", file=sys.stderr, flush=True)
