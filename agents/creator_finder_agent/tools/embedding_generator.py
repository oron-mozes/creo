"""
Embedding Generator for Influencer Profiles.

Generates semantic embeddings from influencer data using Google's text-embedding-004 model.
These embeddings enable semantic search in Pinecone.
"""
import os
from typing import Dict, List, Any, cast
import google.generativeai as genai


class EmbeddingGenerator:
    """Generate embeddings for influencer profiles."""

    def __init__(self, model_name: str = "models/text-embedding-004"):
        """
        Initialize the embedding generator.

        Args:
            model_name: Google embedding model to use
        """
        # Configure Google AI
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model_name = model_name

    def create_composite_text(self, influencer: Dict[str, Any]) -> str:
        """
        Create composite text from influencer data for embedding.

        The composite text combines (in order of importance):
        - Bio (40% weight) - Primary description
        - Content themes (30% weight) - What they talk about
        - Category + Subcategory (20% weight) - Niche classification
        - Location (10% weight) - Geographic context
        - Languages - Content language capabilities
        - Audience demographics (if available) - Who follows them

        Args:
            influencer: Influencer data dictionary

        Returns:
            Rich narrative text optimized for semantic embedding
        """
        bio = influencer.get("bio", "")
        category = influencer.get("category", "").replace("_", " ")
        subcategory = influencer.get("subcategory", "").replace("_", " ")
        location_city = influencer.get("location_city", "")
        location_country = influencer.get("location_country", "")
        content_themes = influencer.get("content_themes", [])
        languages = influencer.get("languages", ["en"])
        audience_demographics = influencer.get("audience_demographics", None)

        # Build location string
        if location_city and location_country:
            location = f"{location_city}, {location_country}"
        elif location_country:
            location = location_country
        else:
            location = "Global"

        # Build themes string
        themes_str = ", ".join(content_themes) if content_themes else "lifestyle content"

        # Build languages string
        if len(languages) == 1:
            languages_str = languages[0].upper()
        elif len(languages) == 2:
            languages_str = f"{languages[0].upper()} and {languages[1].upper()}"
        else:
            languages_str = ", ".join([lang.upper() for lang in languages[:-1]]) + f", and {languages[-1].upper()}"

        # Build composite text as rich narrative
        parts = [
            bio,  # 40% weight - most important
            f"Creates content about {themes_str}.",  # 30% weight
            f"Specializes in {category}, particularly {subcategory}.",  # 20% weight
            f"Based in {location}.",  # 10% weight
            f"Creates content in {languages_str}."
        ]

        # Add audience demographics if available
        if audience_demographics:
            audience_parts = []

            # Gender breakdown
            if "gender" in audience_demographics:
                gender = audience_demographics["gender"]
                if gender.get("female"):
                    audience_parts.append(f"{gender['female']}% women")
                if gender.get("male"):
                    audience_parts.append(f"{gender['male']}% men")

            # Age range
            if "age_range" in audience_demographics:
                age = audience_demographics["age_range"]
                audience_parts.append(f"ages {age}")

            # Interests
            if "interests" in audience_demographics:
                interests = audience_demographics["interests"]
                if isinstance(interests, list) and interests:
                    interests_str = ", ".join(interests[:3])  # Top 3 interests
                    audience_parts.append(f"interested in {interests_str}")

            # Location of audience
            if "location" in audience_demographics:
                aud_location = audience_demographics["location"]
                if isinstance(aud_location, str):
                    audience_parts.append(f"from {aud_location}")

            if audience_parts:
                audience_desc = ", ".join(audience_parts)
                parts.append(f"Audience: {audience_desc}.")

        composite = "\n".join(parts)
        return composite

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a text string.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector
        """
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document"  # Optimized for retrieval tasks
        )

        return cast(List[float], result['embedding'])

    def generate_influencer_embedding(self, influencer: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for an influencer profile.

        Args:
            influencer: Influencer data dictionary

        Returns:
            768-dimensional embedding vector
        """
        composite_text = self.create_composite_text(influencer)
        return self.generate_embedding(composite_text)

    def generate_batch_embeddings(
        self,
        influencers: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple influencers in batches.

        Note: Google's embedding API processes requests one at a time.
        This method processes in batches for better organization but doesn't
        parallelize (to avoid rate limits).

        Args:
            influencers: List of influencer data dictionaries
            batch_size: Number of influencers per batch (for progress tracking)

        Returns:
            List of 768-dimensional embedding vectors
        """
        embeddings = []
        total = len(influencers)

        print(f"Generating embeddings for {total} influencers...")

        for i, influencer in enumerate(influencers):
            embedding = self.generate_influencer_embedding(influencer)
            embeddings.append(embedding)

            # Progress indicator
            if (i + 1) % batch_size == 0 or (i + 1) == total:
                print(f"Progress: {i + 1}/{total} embeddings generated")

        print("✓ All embeddings generated")
        return embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: User's search query (e.g., "coffee influencers in Israel")

        Returns:
            768-dimensional embedding vector
        """
        result = genai.embed_content(
            model=self.model_name,
            content=query,
            task_type="retrieval_query"  # Optimized for query embedding
        )

        return cast(List[float], result['embedding'])


# Example usage
if __name__ == "__main__":
    # Test the embedding generator
    generator = EmbeddingGenerator()

    # Sample influencer
    test_influencer = {
        "bio": "☕ Coffee enthusiast sharing latte art & cafe reviews in Tel Aviv",
        "category": "food_and_beverage",
        "subcategory": "coffee",
        "location_country": "Israel",
        "location_city": "Tel Aviv",
        "content_themes": ["coffee culture", "cafe lifestyle", "barista tips"]
    }

    # Generate composite text
    composite = generator.create_composite_text(test_influencer)
    print("Composite text:")
    print(composite)
    print()

    # Generate embedding
    embedding = generator.generate_influencer_embedding(test_influencer)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")
    print()

    # Generate query embedding
    query = "coffee influencers in Tel Aviv"
    query_embedding = generator.generate_query_embedding(query)
    print(f"Query embedding dimension: {len(query_embedding)}")
    print(f"Query first 10 values: {query_embedding[:10]}")
