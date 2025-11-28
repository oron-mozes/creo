"""
Pinecone Client for Influencer Vector Search.

Manages Pinecone index initialization, vector upsert, and semantic search.
"""
import os
from typing import Dict, List, Any, Optional
from pinecone import Pinecone, ServerlessSpec


class PineconeClient:
    """Client for managing influencer vectors in Pinecone."""

    def __init__(
        self,
        index_name: str = "creo-influencers",
        dimension: int = 768,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1"
    ):
        """
        Initialize Pinecone client.

        Args:
            index_name: Name of the Pinecone index
            dimension: Vector dimension (768 for text-embedding-004)
            metric: Distance metric (cosine, euclidean, dotproduct)
            cloud: Cloud provider (gcp, aws, azure)
            region: Cloud region
        """
        # Get API key from environment
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "PINECONE_API_KEY environment variable not set.\n"
                "Get your API key from: https://app.pinecone.io/"
            )

        # Initialize Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.index: Optional[Any] = None

    def create_index(self) -> None:
        """
        Create Pinecone index if it doesn't exist.

        Creates a serverless index optimized for influencer search.
        """
        # Check if index already exists
        existing_indexes = self.pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]

        if self.index_name in index_names:
            print(f"✓ Index '{self.index_name}' already exists")
            self.index = self.pc.Index(self.index_name)
            return

        # Create new index
        print(f"Creating index '{self.index_name}'...")
        self.pc.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric=self.metric,
            spec=ServerlessSpec(
                cloud=self.cloud,
                region=self.region
            )
        )

        print(f"✓ Index '{self.index_name}' created successfully")
        self.index = self.pc.Index(self.index_name)

    def get_index(self) -> Any:
        """
        Get reference to Pinecone index.

        Returns:
            Pinecone index object
        """
        if self.index is None:
            self.index = self.pc.Index(self.index_name)
        return self.index

    def upsert_influencer(
        self,
        influencer_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Upsert a single influencer vector to Pinecone.

        Args:
            influencer_id: Unique influencer ID (e.g., "instagram_12345")
            embedding: 768-dimensional embedding vector
            metadata: Influencer metadata for filtering
        """
        index = self.get_index()

        # Prepare vector for upsert
        vector = {
            "id": influencer_id,
            "values": embedding,
            "metadata": metadata
        }

        # Upsert to Pinecone
        index.upsert(vectors=[vector])

    def upsert_batch(
        self,
        influencer_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Upsert multiple influencer vectors in batches.

        Args:
            influencer_ids: List of influencer IDs
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            batch_size: Number of vectors per batch
        """
        index = self.get_index()
        total = len(influencer_ids)

        print(f"Upserting {total} influencers to Pinecone...")

        for i in range(0, total, batch_size):
            batch_end = min(i + batch_size, total)

            # Prepare batch
            vectors = [
                {
                    "id": influencer_ids[j],
                    "values": embeddings[j],
                    "metadata": metadatas[j]
                }
                for j in range(i, batch_end)
            ]

            # Upsert batch
            index.upsert(vectors=vectors)

            print(f"Progress: {batch_end}/{total} influencers upserted")

        print("✓ All influencers upserted to Pinecone")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for influencers using query embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter (e.g., {"followers": {"$gte": 10000}})
            include_metadata: Include metadata in results

        Returns:
            List of search results with scores and metadata
        """
        index = self.get_index()

        # Execute search
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )

        # Format results
        matches = []
        for match in results.matches:
            matches.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata if include_metadata else None
            })

        return matches

    def hybrid_search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: semantic search + metadata filtering.

        Example filters:
        {
            "followers": {"$gte": 10000, "$lte": 100000},
            "engagement_rate": {"$gte": 3.0},
            "location_country": {"$eq": "Israel"},
            "category": {"$eq": "food_and_beverage"}
        }

        Args:
            query_embedding: Query embedding vector
            filters: Metadata filters
            top_k: Number of results to return

        Returns:
            List of search results
        """
        return self.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )

    def get_influencer(self, influencer_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific influencer by ID.

        Args:
            influencer_id: Influencer ID

        Returns:
            Influencer data or None if not found
        """
        index = self.get_index()

        result = index.fetch(ids=[influencer_id])

        if influencer_id in result.vectors:
            vector = result.vectors[influencer_id]
            return {
                "id": vector.id,
                "metadata": vector.metadata
            }

        return None

    def update_metadata(
        self,
        influencer_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update metadata for an influencer (e.g., after campaign completion).

        Args:
            influencer_id: Influencer ID
            metadata: New metadata to merge with existing
        """
        index = self.get_index()

        # Update metadata (keeps embedding unchanged)
        index.update(
            id=influencer_id,
            set_metadata=metadata
        )

        print(f"✓ Updated metadata for {influencer_id}")

    def delete_influencer(self, influencer_id: str) -> None:
        """
        Delete an influencer from the index.

        Args:
            influencer_id: Influencer ID to delete
        """
        index = self.get_index()
        index.delete(ids=[influencer_id])
        print(f"✓ Deleted {influencer_id} from index")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with index stats
        """
        index = self.get_index()
        stats = index.describe_index_stats()

        return {
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness
        }

    def delete_all(self) -> None:
        """
        Delete all vectors from the index (use with caution!).
        """
        index = self.get_index()
        index.delete(delete_all=True)
        print("⚠️  All vectors deleted from index")


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = PineconeClient()

    # Create index
    client.create_index()

    # Get stats
    stats = client.get_stats()
    print(f"\nIndex Stats: {stats}")

    # Example: Upsert a test vector
    test_embedding = [0.1] * 768  # Mock embedding
    test_metadata = {
        "platform": "instagram",
        "username": "test_user",
        "category": "food_and_beverage",
        "followers": 50000,
        "engagement_rate": 4.5,
        "location_country": "USA"
    }

    client.upsert_influencer(
        influencer_id="test_001",
        embedding=test_embedding,
        metadata=test_metadata
    )

    print("\n✓ Test influencer upserted")

    # Search example
    results = client.search(
        query_embedding=test_embedding,
        top_k=5
    )

    print(f"\nSearch Results: {len(results)} matches")
    for result in results:
        print(f"  - {result['id']}: score={result['score']:.4f}")
