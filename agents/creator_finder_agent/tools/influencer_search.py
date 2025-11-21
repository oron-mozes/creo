"""
High-Level Influencer Search Interface.

Provides a simple API for the creator_finder_agent to search for influencers
using natural language queries with optional filters.
"""
from typing import List, Dict, Any, Optional
from .embedding_generator import EmbeddingGenerator
from .pinecone_client import PineconeClient
from .ranker import InfluencerRanker


class InfluencerSearch:
    """High-level interface for influencer discovery."""

    def __init__(self):
        """Initialize search components."""
        self.embedding_gen = EmbeddingGenerator()
        self.pinecone_client = PineconeClient()
        self.ranker = InfluencerRanker()

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        rank_results: bool = True,
        ranking_preferences: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for influencers using natural language query.

        Args:
            query: Natural language search query
                Examples:
                - "coffee influencers in Israel"
                - "fitness creators with female audiences"
                - "tech reviewers who speak Korean"

            filters: Optional metadata filters
                Examples:
                - {"followers": {"$gte": 10000, "$lte": 100000}}
                - {"engagement_rate": {"$gte": 3.0}}
                - {"location_country": {"$eq": "USA"}}
                - {"category": {"$eq": "food_and_beverage"}}

            top_k: Number of results to return (default: 10)

            rank_results: Whether to re-rank by performance (default: True)

            ranking_preferences: Custom ranking weights
                Example: {"semantic_weight": 0.5, "campaign_performance_weight": 0.3}

        Returns:
            List of influencer results with scores and metadata
        """
        # Step 1: Generate query embedding
        query_embedding = self.embedding_gen.generate_query_embedding(query)

        # Step 2: Search Pinecone
        if filters:
            # Hybrid search (semantic + filters)
            results = self.pinecone_client.hybrid_search(
                query_embedding=query_embedding,
                filters=filters,
                top_k=top_k * 2  # Get more results for re-ranking
            )
        else:
            # Pure semantic search
            results = self.pinecone_client.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,
                include_metadata=True
            )

        # Step 3: Re-rank by performance
        if rank_results and results:
            results = self.ranker.rank_influencers(
                search_results=results,
                preferences=ranking_preferences
            )

        # Step 4: Return top K
        return results[:top_k]

    def format_results(
        self,
        results: List[Dict[str, Any]],
        include_scores: bool = False
    ) -> str:
        """
        Format search results for display.

        Args:
            results: Search results
            include_scores: Whether to include score breakdown

        Returns:
            Formatted string
        """
        if not results:
            return "No influencers found matching your criteria."

        output = []
        output.append(f"Found {len(results)} influencers:\n")

        for i, result in enumerate(results, 1):
            metadata = result['metadata']

            # Basic info
            output.append(f"{i}. @{metadata['username']}")
            output.append(f"   Platform: {metadata['platform'].title()}")
            output.append(f"   Category: {metadata['category'].replace('_', ' ').title()} / {metadata['subcategory'].replace('_', ' ').title()}")
            output.append(f"   Location: {metadata['location_city']}, {metadata['location_country']}")
            output.append(f"   Followers: {int(metadata['followers']):,}")
            output.append(f"   Engagement: {metadata['engagement_rate']:.1f}%")
            output.append(f"   Performance Tier: {metadata['performance_tier'].title()}")

            # Campaign stats
            if metadata.get('campaign_count', 0) > 0:
                output.append(f"   Campaigns: {metadata['campaign_count']} (Avg ROI: {metadata['avg_campaign_roi']:.1f}x)")

            # Audience
            aud_female = metadata.get('audience_gender_female', 0)
            aud_male = metadata.get('audience_gender_male', 0)
            output.append(f"   Audience: {aud_female}% women, {aud_male}% men, ages {metadata.get('audience_age_range', 'N/A')}")

            # Contact
            output.append(f"   Email: {metadata['email']}")

            # Scores (optional)
            if include_scores and 'final_score' in result:
                output.append(f"   Final Score: {result['final_score']:.3f}")

            output.append("")  # Blank line

        return "\n".join(output)


# Initialize singleton instance for agent use
_search = InfluencerSearch()


def search_influencers(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5
) -> str:
    """
    Search for influencers using natural language query with optional filters.

    Args:
        query: Natural language search query (e.g., "coffee influencers in Israel")
        filters: Optional metadata filters as a dictionary
        top_k: Number of results to return (default: 5)

    Returns:
        Formatted string with influencer results

    Example:
        search_influencers("coffee influencers", filters={"location_country": {"$eq": "Israel"}}, top_k=3)
    """
    results = _search.search(query=query, filters=filters, top_k=top_k)
    return _search.format_results(results, include_scores=False)


# Example usage
if __name__ == "__main__":
    # Initialize search
    search = InfluencerSearch()

    print("=== Example 1: Natural Language Search ===")
    results = search.search("coffee influencers in Israel", top_k=3)
    print(search.format_results(results, include_scores=True))

    print("\n=== Example 2: Search with Filters (Category) ===")
    results = search.search(
        query="gaming influencers",
        filters={
            "category": {"$eq": "tech_and_gaming"},
            "subcategory": {"$eq": "gaming"},
            "followers": {"$gte": 50000}
        },
        top_k=3
    )
    print(search.format_results(results))

    print("\n=== Example 3: Search with Filters (Audience) ===")
    results = search.search(
        query="fitness influencers",
        filters={
            "audience_gender_female": {"$gte": 60},
            "audience_age_range": {"$eq": "25-34"}
        },
        top_k=3
    )
    print(search.format_results(results))

    print("\n=== Example 4: Search with Filters (High Performers) ===")
    results = search.search(
        query="fashion influencers",
        filters={
            "avg_campaign_roi": {"$gte": 2.5},
            "campaign_count": {"$gte": 5},
            "performance_tier": {"$eq": "gold"}
        },
        top_k=3
    )
    print(search.format_results(results))
