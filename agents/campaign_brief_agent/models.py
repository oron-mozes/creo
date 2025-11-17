"""Campaign brief data models."""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class CampaignBrief(BaseModel):
    """Campaign brief information model.

    This model captures all the essential information needed to create
    an influencer marketing campaign. It relates to the business card
    information through the user_id.
    """

    # Required fields
    goal: Optional[str] = None  # e.g. "more people to visit and try my new matcha tea"

    # Optional fields with defaults
    location: Optional[str] = None  # specific location (country/city) or "any"
    platform: Optional[str] = None  # Instagram/TikTok/YouTube/Facebook or "any"
    niche: Optional[str] = None  # Food/Travel/Tech/Lifestyle or "any"
    budget_per_creator: Optional[float] = None  # maximum budget per creator
    num_creators: int = 1  # number of creators (default 1)

    # Business/product info (can reference business card)
    business_name: Optional[str] = None  # business name (may come from business card)
    product_info: Optional[str] = None  # additional product details

    # Optional fields
    audience_demographics: Optional[str] = None  # target audience demographics
    audience_interests: Optional[str] = None  # target audience interests

    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: Optional[str]) -> Optional[str]:
        """Validate platform is one of the accepted values or 'any'."""
        if v is None:
            return v

        valid_platforms = ['instagram', 'tiktok', 'youtube', 'facebook', 'any']
        v_lower = v.lower()

        if v_lower not in valid_platforms:
            # Try to match partial strings
            for platform in valid_platforms:
                if platform in v_lower or v_lower in platform:
                    return platform.capitalize() if platform != 'any' else 'any'
            return v  # Return as-is if no match found

        return v_lower.capitalize() if v_lower != 'any' else 'any'

    @field_validator('niche')
    @classmethod
    def validate_niche(cls, v: Optional[str]) -> Optional[str]:
        """Validate niche is one of the accepted values or 'any'."""
        if v is None:
            return v

        valid_niches = ['food', 'travel', 'tech', 'lifestyle', 'fashion',
                       'beauty', 'fitness', 'gaming', 'any']
        v_lower = v.lower()

        if v_lower not in valid_niches:
            # Try to match partial strings
            for niche in valid_niches:
                if niche in v_lower or v_lower in niche:
                    return niche.capitalize() if niche != 'any' else 'any'
            return v  # Return as-is if no match found

        return v_lower.capitalize() if v_lower != 'any' else 'any'

    @field_validator('budget_per_creator')
    @classmethod
    def validate_budget(cls, v: Optional[float]) -> Optional[float]:
        """Validate budget is positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Budget must be positive")
        return v

    @field_validator('num_creators')
    @classmethod
    def validate_num_creators(cls, v: int) -> int:
        """Validate number of creators is positive."""
        if v < 1:
            raise ValueError("Number of creators must be at least 1")
        return v

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/display.

        Returns a dictionary with all fields, showing "Not provided" for
        optional fields that are None.
        """
        return {
            "goal": self.goal or "Not provided",
            "location": self.location or "Not provided",
            "platform": self.platform or "Not provided",
            "niche": self.niche or "Not provided",
            "budget_per_creator": self.budget_per_creator if self.budget_per_creator is not None else "Not provided",
            "num_creators": self.num_creators,
            "business_name": self.business_name or "Not provided",
            "product_info": self.product_info or "Not provided",
            "audience_demographics": self.audience_demographics or "Not provided",
            "audience_interests": self.audience_interests or "Not provided",
        }

    def is_complete(self) -> bool:
        """Check if all required fields are filled.

        At minimum, we need:
        - goal (the campaign objective)

        All other fields are optional and can default to "any" or be inferred
        from the business card.
        """
        return self.goal is not None and len(self.goal.strip()) > 0

    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields."""
        missing = []

        if not self.goal or len(self.goal.strip()) == 0:
            missing.append("goal")

        return missing

    def merge_with_business_card(self, business_card: dict) -> None:
        """Merge campaign brief with business card information.

        This allows the campaign brief to inherit relevant information
        from the business card if not explicitly provided.

        Args:
            business_card: Dictionary containing business card data
        """
        # Use business name from card if not provided in brief
        if not self.business_name and business_card.get("name"):
            self.business_name = business_card["name"]

        # Use location from card if not provided in brief
        if not self.location and business_card.get("location"):
            self.location = business_card["location"]

        # Infer niche from service_type if not provided
        if not self.niche and business_card.get("service_type"):
            service_type = business_card["service_type"].lower()

            # Map service types to niches
            niche_mapping = {
                'food': 'Food',
                'restaurant': 'Food',
                'cafe': 'Food',
                'coffee': 'Food',
                'travel': 'Travel',
                'hotel': 'Travel',
                'tourism': 'Travel',
                'tech': 'Tech',
                'software': 'Tech',
                'app': 'Tech',
                'lifestyle': 'Lifestyle',
                'fashion': 'Fashion',
                'clothing': 'Fashion',
                'beauty': 'Beauty',
                'cosmetics': 'Beauty',
                'fitness': 'Fitness',
                'gym': 'Fitness',
                'gaming': 'Gaming',
                'esports': 'Gaming',
            }

            for keyword, niche in niche_mapping.items():
                if keyword in service_type:
                    self.niche = niche
                    break
