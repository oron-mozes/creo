"""
Influencer Performance Ranker.

Re-ranks influencer search results based on multiple factors:
- Semantic similarity (from Pinecone)
- Engagement rate
- Authenticity score
- Campaign performance (ROI, conversion rate)
- Brand safety
"""
from typing import List, Dict, Any, Optional


class InfluencerRanker:
    """Ranks influencers based on campaign suitability."""

    def __init__(
        self,
        semantic_weight: float = 0.40,
        engagement_weight: float = 0.20,
        authenticity_weight: float = 0.15,
        campaign_performance_weight: float = 0.15,
        brand_safety_weight: float = 0.10
    ):
        """
        Initialize ranker with configurable weights.

        Args:
            semantic_weight: Weight for semantic similarity (0-1)
            engagement_weight: Weight for engagement rate (0-1)
            authenticity_weight: Weight for follower authenticity (0-1)
            campaign_performance_weight: Weight for past campaign success (0-1)
            brand_safety_weight: Weight for content safety (0-1)

        Note: Weights should sum to 1.0
        """
        self.semantic_weight = semantic_weight
        self.engagement_weight = engagement_weight
        self.authenticity_weight = authenticity_weight
        self.campaign_performance_weight = campaign_performance_weight
        self.brand_safety_weight = brand_safety_weight

        # Validate weights sum to 1.0
        total = sum([
            semantic_weight,
            engagement_weight,
            authenticity_weight,
            campaign_performance_weight,
            brand_safety_weight
        ])

        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 range.

        Args:
            value: Value to normalize
            min_val: Minimum possible value
            max_val: Maximum possible value

        Returns:
            Normalized value between 0 and 1
        """
        if max_val == min_val:
            return 0.5

        return (value - min_val) / (max_val - min_val)

    def calculate_engagement_score(self, engagement_rate: float) -> float:
        """
        Calculate normalized engagement score.

        Typical engagement rates:
        - Excellent: 6%+
        - Good: 3-6%
        - Average: 1-3%
        - Poor: <1%

        Args:
            engagement_rate: Engagement rate percentage (0-100)

        Returns:
            Normalized score (0-1)
        """
        # Normalize to 0-10% range (cap at 10%)
        capped_rate = min(engagement_rate, 10.0)
        return self.normalize_score(capped_rate, 0.0, 10.0)

    def calculate_campaign_score(
        self,
        campaign_count: int,
        avg_campaign_roi: float,
        avg_conversion_rate: float
    ) -> float:
        """
        Calculate campaign performance score.

        Args:
            campaign_count: Number of campaigns completed
            avg_campaign_roi: Average ROI (e.g., 2.5 means 250% return)
            avg_conversion_rate: Average conversion rate (0-1)

        Returns:
            Normalized score (0-1)
        """
        # No campaigns = neutral score
        if campaign_count == 0:
            return 0.5

        # ROI score (normalize 0-5 range)
        roi_score = self.normalize_score(min(avg_campaign_roi, 5.0), 0.0, 5.0)

        # Conversion score (normalize 0-10% range)
        conversion_score = self.normalize_score(
            min(avg_conversion_rate * 100, 10.0),
            0.0,
            10.0
        )

        # Experience bonus (more campaigns = more reliable data)
        experience_multiplier = min(1.0, campaign_count / 10.0)

        # Combined score
        campaign_score = (roi_score * 0.6 + conversion_score * 0.4) * experience_multiplier

        return campaign_score

    def rank_influencers(
        self,
        search_results: List[Dict[str, Any]],
        preferences: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank influencers by calculating composite scores.

        Args:
            search_results: List of Pinecone search results with metadata
            preferences: Optional weight overrides for this search

        Returns:
            Ranked list of influencers with final scores
        """
        # Use custom weights if provided
        weights = {
            'semantic': preferences.get('semantic_weight', self.semantic_weight) if preferences else self.semantic_weight,
            'engagement': preferences.get('engagement_weight', self.engagement_weight) if preferences else self.engagement_weight,
            'authenticity': preferences.get('authenticity_weight', self.authenticity_weight) if preferences else self.authenticity_weight,
            'campaign': preferences.get('campaign_performance_weight', self.campaign_performance_weight) if preferences else self.campaign_performance_weight,
            'brand_safety': preferences.get('brand_safety_weight', self.brand_safety_weight) if preferences else self.brand_safety_weight,
        }

        ranked_results = []

        for result in search_results:
            metadata = result['metadata']
            semantic_score = result['score']  # From Pinecone (0-1)

            # Extract metrics
            engagement_rate = metadata.get('engagement_rate', 0.0)
            authenticity_score = metadata.get('authenticity_score', 0.0)
            brand_safety_score = metadata.get('brand_safety_score', 0.0)
            campaign_count = metadata.get('campaign_count', 0)
            avg_roi = metadata.get('avg_campaign_roi', 0.0)
            avg_conversion = metadata.get('avg_conversion_rate', 0.0)

            # Calculate component scores
            engagement_score = self.calculate_engagement_score(engagement_rate)
            campaign_score = self.calculate_campaign_score(
                campaign_count,
                avg_roi,
                avg_conversion
            )

            # Calculate final weighted score
            final_score = (
                semantic_score * weights['semantic'] +
                engagement_score * weights['engagement'] +
                authenticity_score * weights['authenticity'] +
                campaign_score * weights['campaign'] +
                brand_safety_score * weights['brand_safety']
            )

            # Add scores to result
            ranked_result = result.copy()
            ranked_result['final_score'] = final_score
            ranked_result['component_scores'] = {
                'semantic': semantic_score,
                'engagement': engagement_score,
                'authenticity': authenticity_score,
                'campaign': campaign_score,
                'brand_safety': brand_safety_score
            }

            ranked_results.append(ranked_result)

        # Sort by final score (descending)
        ranked_results.sort(key=lambda x: x['final_score'], reverse=True)

        return ranked_results

    def explain_ranking(self, influencer: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of an influencer's ranking.

        Args:
            influencer: Ranked influencer result

        Returns:
            Explanation string
        """
        final_score = influencer['final_score']
        components = influencer['component_scores']
        metadata = influencer['metadata']

        explanation = f"""
Influencer: @{metadata['username']}
Final Score: {final_score:.3f}

Component Breakdown:
- Semantic Match: {components['semantic']:.3f} (How well they match your query)
- Engagement: {components['engagement']:.3f} (Engagement rate: {metadata['engagement_rate']:.1f}%)
- Authenticity: {components['authenticity']:.3f} (Follower quality: {metadata['authenticity_score']:.2f})
- Campaign Performance: {components['campaign']:.3f} ({metadata['campaign_count']} campaigns, {metadata['avg_campaign_roi']:.1f}x ROI)
- Brand Safety: {components['brand_safety']:.3f} (Content safety: {metadata['brand_safety_score']:.2f})

Performance Tier: {metadata['performance_tier']}
        """.strip()

        return explanation


# Example usage
if __name__ == "__main__":
    # Mock search results from Pinecone
    mock_results = [
        {
            "id": "instagram_1001",
            "score": 0.85,  # High semantic similarity
            "metadata": {
                "username": "coffee_jane",
                "engagement_rate": 4.2,
                "authenticity_score": 0.92,
                "brand_safety_score": 0.88,
                "campaign_count": 3,
                "avg_campaign_roi": 2.4,
                "avg_conversion_rate": 0.034,
                "performance_tier": "gold"
            }
        },
        {
            "id": "instagram_1002",
            "score": 0.75,  # Lower semantic similarity
            "metadata": {
                "username": "mega_influencer",
                "engagement_rate": 8.5,  # But amazing engagement!
                "authenticity_score": 0.95,
                "brand_safety_score": 0.96,
                "campaign_count": 15,
                "avg_campaign_roi": 3.8,
                "avg_conversion_rate": 0.048,
                "performance_tier": "platinum"
            }
        },
        {
            "id": "instagram_1003",
            "score": 0.90,  # Highest semantic match
            "metadata": {
                "username": "new_creator",
                "engagement_rate": 2.1,  # But low engagement
                "authenticity_score": 0.78,
                "brand_safety_score": 0.82,
                "campaign_count": 0,  # No campaign history
                "avg_campaign_roi": 0.0,
                "avg_conversion_rate": 0.0,
                "performance_tier": "bronze"
            }
        }
    ]

    # Initialize ranker
    ranker = InfluencerRanker()

    # Rank results
    ranked = ranker.rank_influencers(mock_results)

    print("=== RANKED INFLUENCERS ===\n")
    for i, influencer in enumerate(ranked, 1):
        print(f"{i}. @{influencer['metadata']['username']}")
        print(f"   Final Score: {influencer['final_score']:.3f}")
        print(f"   Tier: {influencer['metadata']['performance_tier']}")
        print()

    # Show detailed explanation for top influencer
    print("\n=== TOP INFLUENCER EXPLANATION ===")
    print(ranker.explain_ranking(ranked[0]))
