"""Vector database utilities using Pinecone for embeddings and similarity search."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

# Initialize Pinecone client
_pc: Optional[Pinecone] = None
_index = None


def get_pinecone_client() -> Pinecone:
    """Get or create Pinecone client."""
    global _pc
    if _pc is None:
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY environment variable is required")
        _pc = Pinecone(api_key=api_key)
    return _pc


def get_or_create_index(
    index_name: str = "creo-embeddings",
    dimension: int = 768,  # Gemini embedding dimension
    metric: str = "cosine"
):
    """Get or create a Pinecone index."""
    global _index
    if _index is not None:
        return _index

    pc = get_pinecone_client()

    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_names = [idx.name for idx in existing_indexes]

    if index_name not in index_names:
        # Create new index
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(
                cloud="aws",  # Free tier is on AWS
                region="us-east-1"  # Free tier region
            )
        )

    _index = pc.Index(index_name)
    return _index


class EmbeddingGenerator:
    """Generate embeddings using Google Gemini."""

    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is required")
        genai.configure(api_key=api_key)

    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding for text using Gemini.

        Args:
            text: Text to embed
            task_type: One of: retrieval_query, retrieval_document, semantic_similarity,
                      classification, clustering

        Returns:
            List of floats representing the embedding vector
        """
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type,
        )
        return result['embedding']

    def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text, task_type)
            embeddings.append(embedding)
        return embeddings


class VectorDB:
    """Vector database operations using Pinecone."""

    def __init__(self, index_name: str = "creo-influencers"):
        self.index = get_or_create_index(index_name)
        self.embedding_gen = EmbeddingGenerator()

    def upsert_text(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: str = ""
    ) -> None:
        """
        Store text with its embedding in the vector database.

        Args:
            id: Unique identifier for the text
            text: The text content to embed and store
            metadata: Additional metadata to store with the vector
            namespace: Namespace for organizing vectors (e.g., by user_id)
        """
        # Generate embedding
        embedding = self.embedding_gen.generate_embedding(text, task_type="retrieval_document")

        # Prepare metadata
        meta = metadata or {}
        meta["text"] = text  # Store original text in metadata

        # Upsert to Pinecone
        self.index.upsert(
            vectors=[(id, embedding, meta)],
            namespace=namespace
        )

    def upsert_texts_batch(
        self,
        items: List[Tuple[str, str, Optional[Dict[str, Any]]]],  # (id, text, metadata)
        namespace: str = "",
        batch_size: int = 100
    ) -> None:
        """
        Store multiple texts with their embeddings.

        Args:
            items: List of (id, text, metadata) tuples
            namespace: Namespace for organizing vectors
            batch_size: Number of vectors to upsert at once
        """
        vectors = []
        for id, text, metadata in items:
            embedding = self.embedding_gen.generate_embedding(text, task_type="retrieval_document")
            meta = metadata or {}
            meta["text"] = text
            vectors.append((id, embedding, meta))

            # Upsert in batches
            if len(vectors) >= batch_size:
                self.index.upsert(vectors=vectors, namespace=namespace)
                vectors = []

        # Upsert remaining vectors
        if vectors:
            self.index.upsert(vectors=vectors, namespace=namespace)

    def search(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "",
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts using semantic search.

        Args:
            query: The search query text
            top_k: Number of results to return
            namespace: Namespace to search in
            filter: Metadata filter (e.g., {"user_id": "123"})

        Returns:
            List of matches with id, score, and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_gen.generate_embedding(query, task_type="retrieval_query")

        # Search in Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_metadata=True
        )

        # Format results
        matches = []
        for match in results.matches:
            matches.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
            })

        return matches

    def delete(self, ids: List[str], namespace: str = "") -> None:
        """Delete vectors by IDs."""
        self.index.delete(ids=ids, namespace=namespace)

    def delete_namespace(self, namespace: str) -> None:
        """Delete all vectors in a namespace."""
        self.index.delete(delete_all=True, namespace=namespace)

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self.index.describe_index_stats()


# Convenience functions for common use cases

def store_campaign_knowledge(
    campaign_id: str,
    texts: List[str],
    user_id: str
) -> None:
    """Store campaign-related knowledge for RAG."""
    vdb = VectorDB()
    items = [
        (f"{campaign_id}_{i}", text, {"campaign_id": campaign_id, "user_id": user_id})
        for i, text in enumerate(texts)
    ]
    vdb.upsert_texts_batch(items, namespace=user_id)


def search_campaign_knowledge(
    query: str,
    campaign_id: str,
    user_id: str,
    top_k: int = 3
) -> List[str]:
    """Search for relevant campaign knowledge."""
    vdb = VectorDB()
    results = vdb.search(
        query=query,
        top_k=top_k,
        namespace=user_id,
        filter={"campaign_id": campaign_id}
    )
    return [match["text"] for match in results]


def store_conversation_context(
    session_id: str,
    message: str,
    user_id: str,
    role: str
) -> None:
    """Store conversation message for semantic search."""
    vdb = VectorDB()
    message_id = f"{session_id}_{role}_{hash(message)}"
    vdb.upsert_text(
        id=message_id,
        text=message,
        metadata={
            "session_id": session_id,
            "user_id": user_id,
            "role": role
        },
        namespace=user_id
    )


def search_conversation_context(
    query: str,
    session_id: str,
    user_id: str,
    top_k: int = 5
) -> List[str]:
    """Search conversation history semantically."""
    vdb = VectorDB()
    results = vdb.search(
        query=query,
        top_k=top_k,
        namespace=user_id,
        filter={"session_id": session_id}
    )
    return [match["text"] for match in results]
