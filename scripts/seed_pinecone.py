"""
Seed Pinecone with Mock Influencer Data.

This script:
1. Loads 100 mock influencers from seed_influencers.json
2. Generates embeddings for each influencer
3. Upserts vectors + metadata to Pinecone

Run this once to populate the Pinecone index with test data.
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.creator_finder_agent.tools.embedding_generator import EmbeddingGenerator
from agents.creator_finder_agent.tools.pinecone_client import PineconeClient


def prepare_metadata(influencer: dict) -> dict:
    """
    Extract metadata for Pinecone from influencer data.

    Only include fields that will be used for filtering or display.
    Exclude fields that are too large or not useful.

    Args:
        influencer: Full influencer data

    Returns:
        Metadata dictionary for Pinecone
    """
    # Pinecone metadata restrictions:
    # - Max 40KB per vector
    # - Nested objects allowed
    # - Arrays allowed

    metadata = {
        # Identifiers
        "platform": influencer["platform"],
        "username": influencer["username"],
        "display_name": influencer["display_name"],

        # Profile
        "bio": influencer["bio"][:500],  # Truncate if too long
        "category": influencer["category"],
        "subcategory": influencer["subcategory"],

        # Location
        "location_country": influencer["location_country"],
        "location_city": influencer.get("location_city", ""),
        "languages": influencer["languages"],

        # Metrics (for filtering)
        "followers": influencer["followers"],
        "engagement_rate": influencer["engagement_rate"],
        "avg_likes": influencer["avg_likes"],
        "avg_comments": influencer["avg_comments"],
        "posts_count": influencer["posts_count"],

        # Quality scores
        "authenticity_score": influencer["authenticity_score"],
        "brand_safety_score": influencer["brand_safety_score"],
        "quality_score": influencer["quality_score"],

        # Campaign performance
        "campaign_count": influencer["campaign_count"],
        "avg_campaign_roi": influencer["avg_campaign_roi"],
        "avg_conversion_rate": influencer["avg_conversion_rate"],
        "performance_tier": influencer["performance_tier"],

        # Contact
        "email": influencer["email"],
        "website": influencer.get("website", ""),
        "profile_url": influencer["profile_url"],

        # Pricing
        "price": influencer.get("price", 0),
        "currency": influencer.get("currency", "USD"),

        # Content themes (limited to first 5)
        "content_themes": influencer.get("content_themes", [])[:5],

        # Audience demographics
        "audience_gender_female": influencer.get("audience_demographics", {}).get("gender", {}).get("female", 0),
        "audience_gender_male": influencer.get("audience_demographics", {}).get("gender", {}).get("male", 0),
        "audience_age_range": influencer.get("audience_demographics", {}).get("age_range", ""),
        "audience_interests": influencer.get("audience_demographics", {}).get("interests", [])[:5],
        "audience_location": influencer.get("audience_demographics", {}).get("location", ""),

        # Indexing metadata
        "data_source": "mock",
        "last_updated": influencer.get("last_updated", "2025-01-17T00:00:00Z")
    }

    return metadata


def seed_pinecone(
    data_file: Path,
    batch_size: int = 100,
    create_index: bool = True
) -> None:
    """
    Seed Pinecone with influencer data.

    Args:
        data_file: Path to seed_influencers.json
        batch_size: Batch size for upserting
        create_index: Whether to create index if it doesn't exist
    """
    print("=" * 60)
    print("  SEEDING PINECONE WITH MOCK INFLUENCER DATA")
    print("=" * 60)
    print()

    # Step 1: Load influencer data
    print(f"[1/5] Loading influencer data from {data_file}...")
    with open(data_file, 'r') as f:
        influencers = json.load(f)
    print(f"✓ Loaded {len(influencers)} influencers")
    print()

    # Step 2: Initialize Pinecone client
    print("[2/5] Initializing Pinecone client...")
    pinecone_client = PineconeClient()

    if create_index:
        pinecone_client.create_index()

    # Get current stats
    stats = pinecone_client.get_stats()
    print(f"✓ Current index has {stats['total_vectors']} vectors")
    print()

    # Step 3: Initialize embedding generator
    print("[3/5] Initializing embedding generator...")
    embedding_gen = EmbeddingGenerator()
    print("✓ Embedding generator ready")
    print()

    # Step 4: Generate embeddings
    print(f"[4/5] Generating embeddings for {len(influencers)} influencers...")
    print("(This may take a few minutes...)")
    print()

    embeddings = []
    for i, influencer in enumerate(influencers):
        try:
            embedding = embedding_gen.generate_influencer_embedding(influencer)
            embeddings.append(embedding)

            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{len(influencers)} embeddings...")

        except Exception as e:
            print(f"  ⚠️  Error generating embedding for {influencer['id']}: {e}")
            # Use zero vector as fallback
            embeddings.append([0.0] * 768)

    print(f"✓ Generated {len(embeddings)} embeddings")
    print()

    # Step 5: Prepare metadata and upsert to Pinecone
    print(f"[5/5] Upserting {len(influencers)} influencers to Pinecone...")

    influencer_ids = [inf["id"] for inf in influencers]
    metadatas = [prepare_metadata(inf) for inf in influencers]

    pinecone_client.upsert_batch(
        influencer_ids=influencer_ids,
        embeddings=embeddings,
        metadatas=metadatas,
        batch_size=batch_size
    )

    print()

    # Final stats
    final_stats = pinecone_client.get_stats()
    print("=" * 60)
    print("  SEEDING COMPLETE")
    print("=" * 60)
    print(f"  Total vectors in index: {final_stats['total_vectors']}")
    print(f"  Index dimension: {final_stats['dimension']}")
    print(f"  Index fullness: {final_stats['index_fullness']:.2%}")
    print("=" * 60)
    print()

    # Test search
    print("Testing search...")
    test_query = "coffee influencers in Israel"
    query_embedding = embedding_gen.generate_query_embedding(test_query)

    results = pinecone_client.search(
        query_embedding=query_embedding,
        top_k=3
    )

    print(f"\nTest Query: \"{test_query}\"")
    print(f"Top 3 Results:")
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        print(f"\n{i}. @{metadata['username']} (Score: {result['score']:.4f})")
        print(f"   Platform: {metadata['platform']}")
        print(f"   Category: {metadata['category']} / {metadata['subcategory']}")
        print(f"   Location: {metadata['location_city']}, {metadata['location_country']}")
        print(f"   Followers: {metadata['followers']:,}")
        print(f"   Engagement: {metadata['engagement_rate']}%")

    print("\n✓ Pinecone is ready for influencer search!")


if __name__ == "__main__":
    # Path to seed data
    data_file = PROJECT_ROOT / "agents/creator_finder_agent/data/seed_influencers.json"

    if not data_file.exists():
        print(f"Error: {data_file} not found")
        print("Run: python3 scripts/generate_mock_influencers.py")
        sys.exit(1)

    # Seed Pinecone
    seed_pinecone(
        data_file=data_file,
        batch_size=100,
        create_index=True
    )
