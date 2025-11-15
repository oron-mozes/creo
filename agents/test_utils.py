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
    AgentName.CREATOR_FINDER_AGENT,
    AgentName.CAMPAING_BRIEF_AGENT,
    AgentName.OUTREACH_MESSAGE_AGENT,
    AgentName.CAMPAIGN_BUILDER_AGENT,
)


def generate_creator_finder_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for creator finder agent."""
    return [
        {
            "input": {
                "platforms": ["Instagram", "TikTok"],
                "target_audiences": ["Gen Z (18-24)", "Young Professionals (25-35)"],
                "niche": "Fashion and Lifestyle",
                "follower_range": "50K-500K",
                "engagement_rate_min": 3.0
            },
            "expected_output_type": "list_of_creators",
            "description": "Find fashion influencers on Instagram and TikTok targeting Gen Z and young professionals"
        },
        {
            "input": {
                "platforms": ["YouTube"],
                "target_audiences": ["Tech Enthusiasts", "Gamers"],
                "niche": "Technology Reviews",
                "follower_range": "100K-1M",
                "content_type": "Video Reviews"
            },
            "expected_output_type": "list_of_creators",
            "description": "Find tech review YouTubers for gaming audience"
        },
        {
            "input": {
                "platforms": ["LinkedIn"],
                "target_audiences": ["B2B Decision Makers"],
                "niche": "Business Strategy",
                "follower_range": "10K-100K",
                "content_focus": "Thought Leadership"
            },
            "expected_output_type": "list_of_creators",
            "description": "Find LinkedIn thought leaders for B2B audience"
        }
    ]


def generate_campaign_brief_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for campaign brief agent."""
    return [
        {
            "input": {
                "campaign_name": "Summer Fashion Launch 2024",
                "objectives": ["Brand awareness", "Product launch", "Engagement"],
                "target_audience": "Fashion-conscious millennials (25-40)",
                "budget": "$50,000",
                "timeline": "3 months",
                "key_messages": ["Sustainable fashion", "Summer collection", "Limited edition"]
            },
            "expected_output_type": "campaign_brief",
            "description": "Create a campaign brief for summer fashion launch"
        },
        {
            "input": {
                "campaign_name": "Tech Product Launch",
                "objectives": ["Product education", "Pre-orders", "Reviews"],
                "target_audience": "Tech early adopters",
                "budget": "$100,000",
                "timeline": "2 months",
                "key_messages": ["Innovation", "Performance", "Early access"]
            },
            "expected_output_type": "campaign_brief",
            "description": "Create a campaign brief for tech product launch"
        }
    ]


def generate_outreach_message_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for outreach message agent."""
    return [
        {
            "input": {
                "creator_name": "@techreviewer",
                "creator_type": "Tech YouTuber",
                "subscriber_count": "500K",
                "campaign_type": "Product Review",
                "product": "New smartphone",
                "key_points": ["Early access", "Honest review", "Creative freedom"],
                "tone": "Professional but friendly"
            },
            "expected_output_type": "outreach_message",
            "description": "Create outreach message for tech reviewer"
        },
        {
            "input": {
                "creator_name": "@fashionista",
                "creator_type": "Fashion Instagram Influencer",
                "subscriber_count": "200K",
                "campaign_type": "Sponsored Post",
                "product": "Sustainable clothing brand",
                "key_points": ["Sustainability focus", "Long-term partnership"],
                "tone": "Casual and approachable"
            },
            "expected_output_type": "outreach_message",
            "description": "Create outreach message for fashion influencer"
        },
        {
            "input": {
                "creator_name": "@fitnessguru",
                "creator_type": "Fitness Content Creator",
                "subscriber_count": "150K",
                "campaign_type": "Brand Ambassadorship",
                "product": "Fitness app",
                "key_points": ["Authentic partnership", "User testimonials"],
                "tone": "Motivational and authentic"
            },
            "expected_output_type": "outreach_message",
            "description": "Create outreach message for fitness creator"
        }
    ]


def generate_campaign_builder_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for campaign builder agent."""
    return [
        {
            "input": {
                "objective": "Launch new eco-friendly skincare product",
                "target_audience": "Environmentally conscious millennials (25-40), primarily female",
                "budget": "$50,000",
                "timeline": "3 months",
                "channels": ["Instagram", "TikTok", "YouTube", "Influencer partnerships"]
            },
            "expected_output_type": "campaign_plan",
            "description": "Build comprehensive campaign for eco-friendly skincare launch"
        },
        {
            "input": {
                "objective": "Increase B2B SaaS product sign-ups",
                "target_audience": "Small business owners, marketing managers",
                "budget": "$30,000",
                "timeline": "2 months",
                "channels": ["LinkedIn", "Email", "Webinars", "Content marketing"]
            },
            "expected_output_type": "campaign_plan",
            "description": "Build B2B SaaS lead generation campaign"
        }
    ]


def generate_orchestrator_tests() -> List[Dict[str, Any]]:
    """Generate synthetic test data for orchestrator agent."""
    return [
        {
            "input": {
                "user_request": "I need to find fashion influencers for my brand"
            },
            "expected_redirect": "creator_finder_agent",
            "description": "Should redirect to creator finder agent"
        },
        {
            "input": {
                "user_request": "I want to create a campaign brief for a product launch"
            },
            "expected_redirect": "campaing_brief_agent",
            "description": "Should redirect to campaign brief agent"
        },
        {
            "input": {
                "user_request": "Help me write an outreach message to a creator"
            },
            "expected_redirect": "outreach_message_agent",
            "description": "Should redirect to outreach message agent"
        },
        {
            "input": {
                "user_request": "I need a complete marketing campaign strategy"
            },
            "expected_redirect": "campaign_builder_agent",
            "description": "Should redirect to campaign builder agent"
        },
        {
            "input": {
                "user_request": "I need to find creators, then create outreach messages, then build a campaign"
            },
            "expected_redirect": ["creator_finder_agent", "outreach_message_agent", "campaign_builder_agent"],
            "description": "Should suggest workflow sequence with multiple agents"
        }
    ]


# Map agent names to their test generators
AGENT_TEST_GENERATORS = {
    AgentName.CREATOR_FINDER_AGENT.value: generate_creator_finder_tests,
    AgentName.CAMPAING_BRIEF_AGENT.value: generate_campaign_brief_tests,
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
