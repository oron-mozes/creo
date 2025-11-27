"""
Creator Finder Agent Tools.

Provides influencer discovery, ranking, and search capabilities.
"""
# Legacy Pinecone-based components (deprecated - now using YouTube API)
# from .embedding_generator import EmbeddingGenerator
# from .pinecone_client import PineconeClient
# from .ranker import InfluencerRanker
# from .influencer_search import InfluencerSearch, search_influencers

# Import find_creators from parent tools.py module
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from tools.py (the file, not the directory)
import importlib.util
spec = importlib.util.spec_from_file_location("creator_finder_tools_module", Path(__file__).parent.parent / "tools.py")
if spec and spec.loader:
    creator_finder_tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(creator_finder_tools_module)
    find_creators = creator_finder_tools_module.find_creators
else:
    find_creators = None

__all__ = [
    # Legacy exports (deprecated - now using YouTube API)
    # "EmbeddingGenerator",
    # "PineconeClient",
    # "InfluencerRanker",
    # "InfluencerSearch",
    # "search_influencers",
    "find_creators",
]
