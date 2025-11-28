"""Simple script to test database connection and query creators."""
import logging
import sys
import os
from pathlib import Path
import pytest

# Skip this integration-heavy test in local/offline runs
pytest.skip("Skipping database connection integration test (network/service required).", allow_module_level=True)
import pytest

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_db_connection():
    """Test database connection and basic queries."""
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("Skipping DB connection test: required API keys are not set.")

    if os.environ.get("CI") or os.environ.get("NO_NETWORK"):
        pytest.skip("Skipping DB connection test in offline/CI environment.")

    logger.info("="*80)
    logger.info("Testing Database Connection")
    logger.info("="*80)

    try:
        # Test 0: Check environment variables
        logger.info("Test 0: Checking environment variables...")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        if pinecone_key:
            logger.info(f"✓ PINECONE_API_KEY is set (length: {len(pinecone_key)})")
        else:
            logger.error("✗ PINECONE_API_KEY is not set!")

        if google_key:
            logger.info(f"✓ GOOGLE_API_KEY is set (length: {len(google_key)})")
        else:
            logger.error("✗ GOOGLE_API_KEY is not set!")

        if not pinecone_key or not google_key:
            logger.error("Missing required environment variables. Please check your .env file.")
            sys.exit(1)

        # Test 1: Import vector_db
        logger.info("Test 1: Importing VectorDB...")
        from vector_db import VectorDB
        logger.info("✓ VectorDB imported successfully")

        # Test 2: Initialize VectorDB
        logger.info("\nTest 2: Initializing VectorDB...")
        vector_db = VectorDB("creo-influencers")
        logger.info("✓ VectorDB initialized successfully")

        # Test 3: Get database stats
        logger.info("\nTest 3: Getting database stats...")
        stats = vector_db.get_stats()
        logger.info(f"✓ Database stats retrieved: {stats}")

        # Test 4: Check namespaces
        logger.info("\nTest 4: Checking namespaces...")
        namespaces = stats.get('namespaces', {})
        logger.info(f"Available namespaces: {list(namespaces.keys())}")

        # Test 5: Check creators namespace
        if '' in namespaces:
            creators_count = namespaces[''].get('vector_count', 0)
            logger.info(f"✓ Creators namespace found with {creators_count} vectors")

            if creators_count == 0:
                logger.warning("⚠ Creators namespace exists but is empty!")
        else:
            logger.warning("⚠ Creators namespace not found!")

        # Test 6: Try a simple search without filters
        logger.info("\nTest 6: Testing simple search (no filters)...")
        try:
            results = vector_db.search(
                query="creator",
                top_k=5,
                namespace="",
                filter=None
            )
            logger.info(f"✓ Search completed, returned {len(results)} results")

            if results:
                logger.info("\nSample result:")
                sample = results[0]
                logger.info(f"  ID: {sample.get('id')}")
                logger.info(f"  Score: {sample.get('score')}")
                logger.info(f"  Metadata keys: {list(sample.get('metadata', {}).keys())}")
                logger.info(f"  Sample metadata: {sample.get('metadata', {})}")
            else:
                logger.warning("⚠ Search returned no results")

        except Exception as e:
            logger.error(f"✗ Search failed: {e}")

        # Test 7: Import and test the agent tool
        logger.info("\nTest 7: Testing agent tool directly...")
        sys.path.insert(0, str(Path(__file__).parent))
        from agents.creator_finder_agent.tools import find_creators_helper

        # Test 7a: No filters (baseline)
        logger.info("\nTest 7a: Calling find_creators_helper with NO filters...")
        result = find_creators_helper()
        logger.info("Result from find_creators_helper:")
        logger.info(result)

        # Test 7b: With lifestyle + UK filters
        logger.info("\nTest 7b: Calling find_creators_helper with category=lifestyle, location=UK...")
        result = find_creators_helper(
            category="lifestyle",
            location="UK",
            min_price=0,
            max_price=100000
        )
        logger.info("Result from find_creators_helper:")
        logger.info(result)

        logger.info("\n" + "="*80)
        logger.info("Database connection test completed!")
        logger.info("="*80)

    except Exception as e:
        import traceback
        logger.error("✗ Test failed with error:")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_db_connection()
