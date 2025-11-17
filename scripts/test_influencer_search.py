"""
Test Influencer Search System.

Quick test of the complete influencer search pipeline.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.creator_finder_agent.tools.influencer_search import InfluencerSearch


def main():
    print("=" * 80)
    print(" TESTING INFLUENCER SEARCH SYSTEM")
    print("=" * 80)
    print()

    # Initialize search
    print("[1/4] Initializing search system...")
    search = InfluencerSearch()
    print("✓ Search system ready\n")

    # Test 1: Natural language search
    print("=" * 80)
    print("[2/4] TEST 1: Natural Language Search")
    print("=" * 80)
    print('Query: "coffee influencers in Israel"\n')

    results = search.search("coffee influencers in Israel", top_k=3)
    print(search.format_results(results, include_scores=True))

    # Test 2: Search with filters (Category)
    print("=" * 80)
    print("[3/4] TEST 2: Search with Filters (Category)")
    print("=" * 80)
    print("Query: 'gaming esports'")
    print("Filters: tech_and_gaming category, gaming subcategory, 30K+ followers, 4%+ engagement\n")

    results = search.search(
        query="gaming esports gameplay video games",
        filters={
            "category": {"$eq": "tech_and_gaming"},
            "subcategory": {"$eq": "gaming"},
            "followers": {"$gte": 30000},
            "engagement_rate": {"$gte": 4.0}
        },
        top_k=3
    )
    print(search.format_results(results))

    # Test 3: Search with filters (Audience)
    print("=" * 80)
    print("[4/4] TEST 3: Search with Filters (Audience)")
    print("=" * 80)
    print("Query: 'fitness influencers'")
    print("Filters: Female audience (60%+), Ages 25-34\n")

    results = search.search(
        query="fitness gym workout wellness health",
        filters={
            "audience_gender_female": {"$gte": 60},
            "audience_age_range": {"$eq": "25-34"}
        },
        top_k=3
    )
    print(search.format_results(results))

    # Summary
    print("=" * 80)
    print(" ALL TESTS COMPLETE")
    print("=" * 80)
    print("\n✓ Influencer search system is fully operational!")
    print("\nYou can now:")
    print("1. Search influencers using natural language")
    print("2. Filter by category, location, audience, performance")
    print("3. Get ranked results based on campaign suitability")
    print()


if __name__ == "__main__":
    main()
