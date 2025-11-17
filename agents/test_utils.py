"""Utilities for generating synthetic test data for agents."""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Union

try:
    from agents.utils import AgentName
except ModuleNotFoundError:
    # Allow running as a standalone script by adding the project root to sys.path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from agents.utils import AgentName

TESTABLE_AGENT_ENUMS = (
    AgentName.ONBOARDING_AGENT,
    AgentName.FRONTDESK_AGENT,
    AgentName.CREATOR_FINDER_AGENT,
    AgentName.CAMPAIGN_BRIEF_AGENT,
    AgentName.OUTREACH_MESSAGE_AGENT,
    AgentName.CAMPAIGN_BUILDER_AGENT,
)


def generate_creator_finder_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for creator finder agent."""
    return [
        {
            "name": "fashion_influencers_instagram_tiktok",
            "description": "Find fashion influencers on Instagram and TikTok targeting Gen Z and young professionals",
            "user_message": "I need fashion influencers on Instagram and TikTok for Gen Z and young professionals, 50K-500K followers, min 3% engagement",
            "session_context": {
                "business_card": {
                    "name": "Fashion Brand Co",
                    "service_type": "Fashion retail"
                }
            },
            "expected_behavior": {
                "should_search_creators": True,
                "should_filter_by_platform": True,
                "should_return_creator_list": True
            }
        },
        {
            "name": "tech_reviewers_youtube",
            "description": "Find tech review YouTubers for gaming audience",
            "user_message": "Find tech review YouTubers with 100K-1M subscribers who create video reviews for tech enthusiasts and gamers",
            "session_context": {
                "business_card": {
                    "name": "Tech Gadgets Inc",
                    "service_type": "Technology products"
                }
            },
            "expected_behavior": {
                "should_search_creators": True,
                "should_filter_by_niche": True,
                "should_return_creator_list": True
            }
        },
        {
            "name": "linkedin_thought_leaders_b2b",
            "description": "Find LinkedIn thought leaders for B2B audience",
            "user_message": "I want LinkedIn thought leaders with 10K-100K followers focused on business strategy for B2B decision makers",
            "session_context": {
                "business_card": {
                    "name": "B2B Solutions Corp",
                    "service_type": "Business consulting"
                }
            },
            "expected_behavior": {
                "should_search_creators": True,
                "should_filter_by_audience": True,
                "should_return_creator_list": True
            }
        }
    ]


def generate_campaign_brief_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for campaign brief agent."""
    return [
        {
            "name": "summer_fashion_launch",
            "description": "Create a campaign brief for summer fashion launch",
            "user_message": "I need a campaign brief for Summer Fashion Launch 2024 targeting fashion-conscious millennials (25-40), budget $50k, 3 months timeline. Focus on sustainable fashion, summer collection, limited edition.",
            "session_context": {
                "business_card": {
                    "name": "Fashion Brand Co",
                    "service_type": "Fashion retail",
                    "location": "New York, NY"
                }
            },
            "expected_behavior": {
                "should_create_campaign_brief": True,
                "should_include_objectives": True,
                "should_define_target_audience": True,
                "should_include_budget": True
            }
        },
        {
            "name": "tech_product_launch",
            "description": "Create a campaign brief for tech product launch",
            "user_message": "Create a campaign brief for Tech Product Launch targeting tech early adopters, $100k budget, 2 months. Focus on product education, pre-orders, reviews. Key messages: innovation, performance, early access.",
            "session_context": {
                "business_card": {
                    "name": "Tech Gadgets Inc",
                    "service_type": "Technology products",
                    "location": "San Francisco, CA"
                }
            },
            "expected_behavior": {
                "should_create_campaign_brief": True,
                "should_include_timeline": True,
                "should_define_key_messages": True,
                "should_include_objectives": True
            }
        }
    ]


def generate_outreach_message_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for outreach message agent."""
    return [
        {
            "name": "tech_reviewer_outreach",
            "description": "Create outreach message for tech reviewer",
            "user_message": "Write an outreach message to @techreviewer (Tech YouTuber, 500K subscribers) for a product review of our new smartphone. Tone should be professional but friendly. Key points: early access, honest review, creative freedom.",
            "session_context": {
                "business_card": {
                    "name": "Tech Gadgets Inc",
                    "service_type": "Technology products"
                }
            },
            "expected_behavior": {
                "should_create_personalized_message": True,
                "should_include_value_proposition": True,
                "should_maintain_professional_tone": True
            }
        },
        {
            "name": "fashion_influencer_outreach",
            "description": "Create outreach message for fashion influencer",
            "user_message": "Draft an outreach message to @fashionista (Fashion Instagram Influencer, 200K followers) for sponsored posts about our sustainable clothing brand. Casual and approachable tone. Focus on sustainability and long-term partnership.",
            "session_context": {
                "business_card": {
                    "name": "Fashion Brand Co",
                    "service_type": "Fashion retail"
                }
            },
            "expected_behavior": {
                "should_create_personalized_message": True,
                "should_align_with_brand_values": True,
                "should_propose_partnership": True
            }
        },
        {
            "name": "fitness_creator_outreach",
            "description": "Create outreach message for fitness creator",
            "user_message": "Create outreach for @fitnessguru (Fitness Content Creator, 150K followers) for brand ambassadorship of our fitness app. Motivational and authentic tone. Emphasize authentic partnership and user testimonials.",
            "session_context": {
                "business_card": {
                    "name": "FitLife App",
                    "service_type": "Fitness technology"
                }
            },
            "expected_behavior": {
                "should_create_personalized_message": True,
                "should_propose_ambassadorship": True,
                "should_emphasize_authenticity": True
            }
        }
    ]


def generate_campaign_builder_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for campaign builder agent."""
    return [
        {
            "name": "eco_skincare_launch_campaign",
            "description": "Build comprehensive campaign for eco-friendly skincare launch",
            "user_message": "Build a full campaign to launch our new eco-friendly skincare product targeting environmentally conscious millennials (25-40), primarily female. Budget is $50k, 3 months timeline. Use Instagram, TikTok, YouTube, and influencer partnerships.",
            "session_context": {
                "business_card": {
                    "name": "EcoBeauty Co",
                    "service_type": "Skincare products",
                    "location": "Los Angeles, CA"
                }
            },
            "expected_behavior": {
                "should_create_comprehensive_plan": True,
                "should_define_channels": True,
                "should_include_budget_allocation": True,
                "should_include_timeline": True
            }
        },
        {
            "name": "b2b_saas_lead_generation",
            "description": "Build B2B SaaS lead generation campaign",
            "user_message": "Create a campaign to increase B2B SaaS product sign-ups targeting small business owners and marketing managers. Budget $30k, 2 months. Use LinkedIn, email, webinars, and content marketing.",
            "session_context": {
                "business_card": {
                    "name": "MarketingTech SaaS",
                    "service_type": "B2B Software",
                    "location": "Austin, TX"
                }
            },
            "expected_behavior": {
                "should_create_comprehensive_plan": True,
                "should_target_b2b_audience": True,
                "should_include_lead_generation_strategy": True,
                "should_allocate_budget_per_channel": True
            }
        }
    ]


def generate_onboarding_agent_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for onboarding agent."""
    return [
        {
            "name": "user_provides_website_url",
            "description": "User provides a website URL, agent should search and extract business info",
            "user_message": "Yes, here is my website: https://www.almacafe.co.il/ourplaces/rehovot",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_extract_business_info": True,
                "should_generate_confirmation_block": True,
                "should_ask_for_confirmation": True
            },
            "expected_business_card": {
                "name": "Alma Cafe",
                "website": "https://www.almacafe.co.il/ourplaces/rehovot",
                "location": "Rehovot, Israel",
                "service_type": "Coffee shop",
                "social_links": "Not provided"
            }
        },
        {
            "name": "user_provides_business_name_and_location",
            "description": "User provides business name and location, agent should search for details",
            "user_message": "My business is called TechStart and we're located in San Francisco",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_extract_business_info": True,
                "should_generate_confirmation_block": True,
                "should_ask_for_confirmation": True
            }
        },
        {
            "name": "business_card_already_exists",
            "description": "Business card already exists in session, should skip onboarding",
            "user_message": "I want to find influencers for my brand",
            "session_context": {
                "business_card": {
                    "name": "Alma Cafe",
                    "website": "https://www.almacafe.co.il",
                    "location": "Rehovot, Israel",
                    "service_type": "Coffee shop",
                    "social_links": "Not provided"
                }
            },
            "expected_behavior": {
                "should_use_google_search": False,
                "should_extract_business_info": False,
                "should_generate_confirmation_block": False,
                "should_acknowledge_existing_business": True,
                "should_confirm_onboarding_complete": True
            },
            "expected_response_contains": [
                "Alma Cafe",
                "already have your details",
                "Let's move forward"
            ]
        },
        {
            "name": "user_confirms_business_details",
            "description": "User confirms the business details presented",
            "user_message": "Yes, that's correct!",
            "session_context": {
                "business_card": None,
                "last_agent_message": "Business Name: Alma Cafe\\nLocation: Rehovot, Israel\\nService Type: Coffee shop\\n\\nDoes everything look correct?"
            },
            "expected_behavior": {
                "should_generate_confirmation_block": True,
                "should_thank_user": True
            }
        },
        {
            "name": "new_user_with_minimal_info",
            "description": "New user provides minimal information, agent should ask for more",
            "user_message": "I have a local coffee shop",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_ask_for_business_name": True,
                "should_ask_for_location": True,
                "should_not_generate_confirmation_block": True
            }
        },
        {
            "name": "user_provides_social_media_handle",
            "description": "User provides Instagram handle, agent should search for business info",
            "user_message": "My Instagram is @almacafe_rehovot",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_extract_business_info": True
            }
        },
        {
            "name": "vague_generic_question_no_context",
            "description": "User asks vague question with no business context clues",
            "user_message": "Can you help me with marketing?",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_ask_for_business_name": True,
                "should_ask_for_industry_or_service_type": True,
                "should_not_generate_confirmation_block": True,
                "should_be_conversational_and_welcoming": True
            },
            "expected_response_contains": [
                "business",
                "brand"
            ]
        },
        {
            "name": "user_provides_comprehensive_info_upfront",
            "description": "User volunteers multiple pieces of info in one sentence",
            "user_message": "I run a sustainable fashion brand in LA called EcoWear",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_extract_name": True,
                "should_extract_location": True,
                "should_extract_service_type": True,
                "should_use_google_search": True,
                "should_generate_confirmation_block": True
            },
            "expected_business_card_contains": {
                "name": "EcoWear",
                "location": "LA",
                "service_type": "sustainable fashion"
            }
        },
        {
            "name": "user_asks_clarifying_question",
            "description": "User confused about what agent is asking, seeks clarification",
            "user_message": "What do you mean by location?",
            "session_context": {
                "business_card": None,
                "last_agent_message": "What's your brand name and where is your business located?"
            },
            "expected_behavior": {
                "should_provide_clarification": True,
                "should_give_location_examples": True,
                "should_not_generate_confirmation_block": True,
                "should_remain_patient_and_helpful": True
            },
            "expected_response_contains": [
                "city",
                "example"
            ]
        },
        {
            "name": "user_provides_business_name_only",
            "description": "User provides only business name, no location or other context",
            "user_message": "My business is called StyleHub",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_ask_for_location_if_search_fails": True,
                "should_not_generate_confirmation_block_yet": True
            }
        },
        {
            "name": "user_provides_tiktok_handle",
            "description": "User provides TikTok handle, agent should search for business info",
            "user_message": "Check out our TikTok @ecowear_official",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_extract_business_info": True,
                "should_mention_searching_tiktok": True
            }
        },
        {
            "name": "user_corrects_information_during_confirmation",
            "description": "User corrects details when asked for confirmation",
            "user_message": "No, the location is wrong - we're actually in San Jose, not San Francisco",
            "session_context": {
                "business_card": None,
                "last_agent_message": "Business Name: TechStart\\nLocation: San Francisco, CA\\nService Type: Tech startup\\n\\nDoes everything look correct?"
            },
            "expected_behavior": {
                "should_acknowledge_correction": True,
                "should_update_location": True,
                "should_present_updated_info_for_confirmation": True,
                "should_not_generate_confirmation_block_yet": True
            },
            "expected_response_contains": [
                "San Jose"
            ]
        },
        {
            "name": "user_provides_linkedin_profile",
            "description": "User provides LinkedIn company profile URL",
            "user_message": "Here's our LinkedIn: linkedin.com/company/techstart-inc",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_extract_business_info": True,
                "should_include_linkedin_in_social_links": True
            }
        },
        {
            "name": "user_provides_partial_url",
            "description": "User provides domain without https protocol",
            "user_message": "Our site is almacafe.co.il",
            "session_context": {
                "business_card": None
            },
            "expected_behavior": {
                "should_use_google_search": True,
                "should_construct_full_url": True,
                "should_extract_business_info": True
            }
        },
        {
            "name": "user_gives_address_instead_of_location",
            "description": "User provides full street address instead of city",
            "user_message": "We're at 123 Main Street, Suite 400, New York, NY 10001",
            "session_context": {
                "business_card": None,
                "last_agent_message": "What's your brand name and where is your business located?"
            },
            "expected_behavior": {
                "should_extract_city_and_state": True,
                "should_simplify_location_format": True,
                "should_not_include_full_street_address": True
            },
            "expected_business_card_contains": {
                "location": "New York, NY"
            }
        }
    ]


def generate_frontdesk_agent_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for frontdesk agent."""
    return [
        {
            "name": "transform_technical_creator_results",
            "description": "Transform technical creator finder results into warm message",
            "user_message": "Found 15 creators matching criteria: Fashion niche, 50K-500K followers, 3%+ engagement on Instagram and TikTok",
            "session_context": {
                "business_card": {
                    "name": "StyleHub Boutique",
                    "location": "Los Angeles, CA",
                    "service_type": "Fashion retail"
                },
                "context": "User asked to find fashion influencers"
            },
            "expected_behavior": {
                "should_be_conversational": True,
                "should_use_business_name": True,
                "should_avoid_markdown": True,
                "should_include_key_info": True
            },
            "expected_response_contains": [
                "StyleHub Boutique",
                "15 creators",
                "fashion"
            ]
        },
        {
            "name": "handle_error_empathetically",
            "description": "Transform error message into empathetic response",
            "user_message": "Error: Unable to connect to creator database",
            "session_context": {
                "business_card": None,
                "context": "User tried to search for creators"
            },
            "expected_behavior": {
                "should_be_empathetic": True,
                "should_explain_simply": True,
                "should_provide_next_steps": True,
                "should_avoid_technical_jargon": True
            },
            "forbidden_patterns": [
                "database",
                "connection failed",
                "error code"
            ]
        },
        {
            "name": "personalize_with_business_card",
            "description": "Use business card to personalize greeting",
            "user_message": "Campaign brief created successfully",
            "session_context": {
                "business_card": {
                    "name": "Alma Cafe",
                    "location": "Rehovot, Israel",
                    "service_type": "Coffee shop"
                },
                "context": "User just completed onboarding"
            },
            "expected_behavior": {
                "should_use_business_name": True,
                "should_be_warm": True,
                "should_guide_next_steps": True
            },
            "expected_response_contains": [
                "Alma Cafe"
            ]
        },
        {
            "name": "generic_greeting_without_business_card",
            "description": "Use generic friendly greeting when business card unavailable",
            "user_message": "Ready to help you find creators",
            "session_context": {
                "business_card": None,
                "context": "New user, no business card yet"
            },
            "expected_behavior": {
                "should_be_friendly": True,
                "should_not_assume_business_details": True
            },
            "forbidden_patterns": [
                "[Business Name]",
                "[location]",
                "[service type]"
            ]
        },
        {
            "name": "no_markdown_in_output",
            "description": "Ensure no markdown symbols in response",
            "user_message": "Campaign includes: 1. Instagram posts 2. TikTok videos 3. YouTube reviews",
            "session_context": {
                "business_card": None,
                "context": "User asked about campaign plan"
            },
            "expected_behavior": {
                "should_avoid_markdown": True,
                "should_use_plain_text": True
            },
            "forbidden_patterns": [
                "**",
                "*   ",
                "# ",
                "## ",
                "___",
                "---"
            ]
        },
        {
            "name": "hide_internal_agent_names",
            "description": "Never expose internal agent names to user",
            "user_message": "creator_finder_agent found 10 results",
            "session_context": {
                "business_card": None,
                "context": "User asked to find creators"
            },
            "expected_behavior": {
                "should_hide_agent_names": True,
                "should_use_first_person": True
            },
            "forbidden_patterns": [
                "agent",
                "creator_finder",
                "campaign_builder",
                "orchestrator",
                "forwarding",
                "redirecting"
            ],
            "expected_response_contains": [
                "I found",
                "we found",
                "10 results"
            ]
        }
    ]


def generate_orchestrator_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for orchestrator agent."""
    return [
        {
            "name": "new_user_no_business_card",
            "description": "New user with no business card should be routed to onboarding_agent",
            "user_message": "I have a local coffee shop",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_call_campaign_brief": True,
                "should_NOT_ask_questions_directly": True,
                "should_NOT_search_google": True
            }
        },
        {
            "name": "onboarding_stage_active",
            "description": "When stage is 'onboarding', should stay with onboarding_agent",
            "user_message": "Alma cafe",
            "session_context": {
                "workflow_state": {"stage": "onboarding"},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_switch_to_campaign_brief": True,
                "should_NOT_search_google": True,
                "should_NOT_assume_location": True
            }
        },
        {
            "name": "onboarding_with_url",
            "description": "User provides URL during onboarding, should delegate to onboarding_agent",
            "user_message": "this is us https://www.almacafe.co.il/ourplaces/rehovot",
            "session_context": {
                "workflow_state": {"stage": "onboarding"},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_extract_info_itself": True,
                "should_delegate_url_to_onboarding": True
            }
        },
        {
            "name": "business_card_exists_find_influencers",
            "description": "Business card exists, user wants influencers - should route to campaign_brief_agent",
            "user_message": "I want to find influencers for my cafe",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": {
                    "name": "Alma Cafe",
                    "website": "https://www.almacafe.co.il",
                    "location": "Brooklyn, NY",
                    "service_type": "Coffee shop"
                }
            },
            "expected_behavior": {
                "should_call_campaign_brief_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_call_onboarding_agent": True,
                "should_use_existing_business_card": True
            }
        },
        {
            "name": "campaign_brief_stage_active",
            "description": "When stage is 'campaign_brief', should stay with campaign_brief_agent",
            "user_message": "I want to reach young professionals who love specialty coffee",
            "session_context": {
                "workflow_state": {"stage": "campaign_brief"},
                "business_card": {
                    "name": "Alma Cafe",
                    "location": "Brooklyn, NY",
                    "service_type": "Coffee shop"
                }
            },
            "expected_behavior": {
                "should_call_campaign_brief_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_switch_to_creator_finder": True,
                "should_stay_in_current_stage": True
            }
        },
        {
            "name": "vague_question_no_business_card",
            "description": "Vague marketing question with no business card - should start onboarding first",
            "user_message": "Can you help me with marketing?",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_answer_directly": True,
                "should_collect_business_info_first": True
            }
        },
        {
            "name": "business_card_exists_wants_campaign",
            "description": "User with business card wants to create a campaign - should route to campaign_brief_agent",
            "user_message": "I want to create a marketing campaign to promote my new menu",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": {
                    "name": "TechStart",
                    "location": "San Francisco, CA",
                    "service_type": "Tech startup"
                }
            },
            "expected_behavior": {
                "should_call_campaign_brief_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_call_onboarding_agent": True
            }
        },
        {
            "name": "business_card_exists_wants_outreach",
            "description": "User with business card wants help writing outreach message - should route to outreach_message_agent",
            "user_message": "Can you help me write a message to reach out to @fitness_guru_sarah?",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": {
                    "name": "FitLife Gym",
                    "location": "Austin, TX",
                    "service_type": "Fitness center"
                }
            },
            "expected_behavior": {
                "should_call_outreach_message_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_call_onboarding_agent": True
            }
        },
        {
            "name": "creator_finder_stage_active",
            "description": "When stage is 'creator_finder', should stay with creator_finder_agent",
            "user_message": "I want creators with at least 100K followers",
            "session_context": {
                "workflow_state": {"stage": "creator_finder"},
                "business_card": {
                    "name": "GreenEats",
                    "location": "Portland, OR",
                    "service_type": "Vegan restaurant"
                }
            },
            "expected_behavior": {
                "should_call_creator_finder_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_switch_to_different_stage": True,
                "should_stay_in_current_stage": True
            }
        },
        {
            "name": "outreach_message_stage_active",
            "description": "When stage is 'outreach_message', should stay with outreach_message_agent",
            "user_message": "Make it more personal and mention our sustainable practices",
            "session_context": {
                "workflow_state": {"stage": "outreach_message"},
                "business_card": {
                    "name": "EcoWear",
                    "location": "Seattle, WA",
                    "service_type": "Sustainable clothing"
                }
            },
            "expected_behavior": {
                "should_call_outreach_message_agent": True,
                "should_call_frontdesk_agent": True,
                "should_stay_in_current_stage": True
            }
        },
        {
            "name": "campaign_builder_stage_active",
            "description": "When stage is 'campaign_builder', should stay with campaign_builder_agent",
            "user_message": "Add more Instagram posts to the campaign",
            "session_context": {
                "workflow_state": {"stage": "campaign_builder"},
                "business_card": {
                    "name": "StyleHub",
                    "location": "Miami, FL",
                    "service_type": "Fashion boutique"
                }
            },
            "expected_behavior": {
                "should_call_campaign_builder_agent": True,
                "should_call_frontdesk_agent": True,
                "should_stay_in_current_stage": True
            }
        },
        {
            "name": "multiple_business_info_pieces_no_business_card",
            "description": "User provides multiple pieces of business info upfront - should route to onboarding_agent",
            "user_message": "I run a yoga studio called ZenFlow in Boulder, Colorado",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_ask_for_already_provided_info": True
            }
        },
        {
            "name": "general_question_with_business_card",
            "description": "User asks general question but has business card - should provide helpful response without switching stages",
            "user_message": "What's the best way to reach millennials?",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": {
                    "name": "ModernEats",
                    "location": "Chicago, IL",
                    "service_type": "Restaurant"
                }
            },
            "expected_behavior": {
                "should_call_campaign_brief_agent": True,
                "should_call_frontdesk_agent": True,
                "should_provide_helpful_response": True
            }
        },
        {
            "name": "follow_up_question_during_onboarding",
            "description": "User asks clarifying question during onboarding - should stay with onboarding_agent",
            "user_message": "What do you mean by service type?",
            "session_context": {
                "workflow_state": {"stage": "onboarding"},
                "business_card": None
            },
            "expected_behavior": {
                "should_call_onboarding_agent": True,
                "should_call_frontdesk_agent": True,
                "should_help_user_understand": True,
                "should_NOT_switch_stages": True
            }
        },
        {
            "name": "specific_creator_request_with_business_card",
            "description": "User asks to find specific type of creators with existing business card",
            "user_message": "Find me food bloggers in Los Angeles with 50K+ followers",
            "session_context": {
                "workflow_state": {"stage": None},
                "business_card": {
                    "name": "TacoTime",
                    "location": "Los Angeles, CA",
                    "service_type": "Mexican restaurant"
                }
            },
            "expected_behavior": {
                "should_call_campaign_brief_agent": True,
                "should_call_frontdesk_agent": True,
                "should_NOT_call_onboarding_agent": True
            }
        }
    ]


# Map agent names to their test generators
AGENT_TEST_GENERATORS = {
    AgentName.ONBOARDING_AGENT.value: generate_onboarding_agent_tests,
    AgentName.FRONTDESK_AGENT.value: generate_frontdesk_agent_tests,
    AgentName.CREATOR_FINDER_AGENT.value: generate_creator_finder_tests,
    AgentName.CAMPAIGN_BRIEF_AGENT.value: generate_campaign_brief_tests,
    AgentName.OUTREACH_MESSAGE_AGENT.value: generate_outreach_message_tests,
    AgentName.CAMPAIGN_BUILDER_AGENT.value: generate_campaign_builder_tests,
    'root_agent': generate_orchestrator_tests,
}


def generate_test_data_for_agent(agent_name: Union[str, AgentName], agent_dir: Path, evaluation_dir: Path) -> None:
    """
    Generate and save test data for a specific agent.
    
    Args:
        agent_name: Name of the agent (AgentName enum or string, accepts 'root_agent')
        agent_dir: Path to the agent directory
        evaluation_dir: Path to the evaluation directory where test.json will be saved
    """
    if isinstance(agent_name, AgentName):
        agent_name = agent_name.value

    if agent_name not in AGENT_TEST_GENERATORS:
        print(f"⚠ No test generator found for agent: {agent_name}")
        return
    
    generator = AGENT_TEST_GENERATORS[agent_name]
    test_data = generator()
    
    # Create evaluation directory if it doesn't exist
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    
    # Save test.json in the evaluation folder
    test_file = evaluation_dir / 'test.json'
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"✓ Generated {len(test_data)} test cases for {agent_name} at {test_file}")


def generate_all_test_data(agents_dir: Path) -> None:
    """
    Generate test data for all agents.
    
    Args:
        agents_dir: Path to the agents directory
    """
    print("Generating test data for all agents...\n")
    
    # Generate for orchestrator agent
    orchestrator_dir = agents_dir / 'orchestrator-agent'
    if orchestrator_dir.exists():
        evaluation_dir = orchestrator_dir / 'evaluation'
        generate_test_data_for_agent('root_agent', orchestrator_dir, evaluation_dir)
    
    # Generate for all other agents
    for agent_enum in TESTABLE_AGENT_ENUMS:
        agent_name = agent_enum.value
        # Convert snake_case to kebab-case for directory name
        agent_dir_name = agent_name.replace('_', '-')
        agent_dir = agents_dir / agent_dir_name
        
        if agent_dir.exists():
            evaluation_dir = agent_dir / 'evaluation'
            generate_test_data_for_agent(agent_enum, agent_dir, evaluation_dir)
        else:
            print(f"⚠ Agent directory not found: {agent_dir}")


if __name__ == '__main__':
    # When run directly, generate test data for all agents
    agents_dir = Path(__file__).parent
    generate_all_test_data(agents_dir)
