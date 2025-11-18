"""Tools for the creator finder agent to search for creators in Pinecone vector database."""
from typing import List, Dict, Optional
from google.adk.tools import FunctionTool
from vector_db import VectorDB


def find_creators_helper(
    category: str,
    location: Optional[str] = None,
    min_price: float = 0,
    max_price: float = 10000,
    max_results: int = 10,
    target_audience: Optional[str] = None,
    platform: Optional[str] = None
) -> str:
    """Find creators based on campaign criteria using semantic search in Pinecone.

    This helper function searches the creator database (Pinecone) for influencers that match
    the specified criteria using semantic search and metadata filtering.

    Args:
        category: Content category (e.g., 'food', 'travel', 'tech', 'lifestyle', 'fashion', 'beauty', 'fitness', 'gaming')
        location: Geographic location at any level - country (e.g., 'US', 'UK'), region/state (e.g., 'California', 'Texas'),
                 city (e.g., 'New York', 'London'), or neighborhood (e.g., 'Queens NY', 'Brooklyn'). Optional.
        min_price: Minimum price per creator based on budget calculation
        max_price: Maximum price per creator based on budget
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
    try:
        # Initialize Pinecone vector database
        vector_db = VectorDB()

        # Build semantic search query
        query_parts = [category, "creator"]
        if platform:
            query_parts.append(platform)
        if location:
            query_parts.append(f"in {location}")
        if target_audience:
            query_parts.append(f"for {target_audience}")

        search_query = " ".join(query_parts)

        # Build metadata filter for Pinecone
        metadata_filter = {}
        if category:
            metadata_filter["category"] = category.lower()
        if platform:
            metadata_filter["platform"] = platform

        # Search in Pinecone (creators namespace)
        # Fetch more results for filtering by price and location
        search_results = vector_db.search(
            query=search_query,
            top_k=min(max_results * 3, 50),  # Fetch extra for filtering
            namespace="creators",
            filter=metadata_filter if metadata_filter else None
        )

        if not search_results:
            return f"No creators found matching the criteria: category='{category}', location='{location or 'any'}', platform='{platform or 'any'}', price range=${min_price}-${max_price}"

        # Filter results by price range and location
        filtered_creators = []
        for result in search_results:
            creator = result["metadata"]

            # Filter by price range
            price_min = creator.get("estimated_price_min", 0)
            price_max = creator.get("estimated_price_max", 0)

            # Skip if creator is too expensive or too cheap
            if price_min > max_price or price_max < min_price:
                continue

            # Filter by location (case-insensitive partial match)
            if location:
                creator_location = creator.get("location", "")
                if not creator_location or location.lower() not in creator_location.lower():
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
            result += f"{i}. {creator.get('name', 'Unknown')}\n"
            result += f"   Platform: {creator.get('platform', 'N/A')}\n"

            # Display follower/subscriber count
            if creator.get('subscriber_count'):
                result += f"   Subscribers: {creator.get('subscriber_count'):,}\n"
            elif creator.get('follower_count'):
                result += f"   Followers: {creator.get('follower_count'):,}\n"

            # Display engagement and other metrics
            if creator.get('engagement_rate'):
                result += f"   Engagement Rate: {creator.get('engagement_rate')}%\n"

            if creator.get('view_count'):
                result += f"   Total Views: {creator.get('view_count'):,}\n"

            if creator.get('video_count'):
                result += f"   Videos/Posts: {creator.get('video_count'):,}\n"

            # Price range
            price_min = creator.get('estimated_price_min', 0)
            price_max = creator.get('estimated_price_max', 0)
            result += f"   Estimated Price: ${price_min:,.2f} - ${price_max:,.2f}\n"

            # Profile URL
            url = creator.get('channel_url') or creator.get('profile_url', 'N/A')
            result += f"   URL: {url}\n"

            # Description
            description = creator.get('description', 'No description available')
            if len(description) > 200:
                description = description[:200] + '...'
            result += f"   Description: {description}\n"

            # Location
            if creator.get('location'):
                result += f"   Location: {creator.get('location')}\n"

            result += "-" * 80 + "\n\n"

        return result

    except Exception as e:
        return f"Error searching for creators in database: {str(e)}\n\nPlease ensure the database is properly configured and populated with creator data."


# Create the tool instance
find_creators = FunctionTool(find_creators_helper)
