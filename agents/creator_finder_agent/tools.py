"""Tools for the Creator Finder Agent - YouTube Data API v3 integration."""

import os
import logging
import json
import pycountry
from typing import Optional
from datetime import datetime, timedelta
from collections import OrderedDict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def _language_to_iso639(language: Optional[str]) -> Optional[str]:
    """
    Convert language name to ISO 639-1 code.
    
    Args:
        language: Language name (e.g., 'English', 'Spanish') or None
        
    Returns:
        ISO 639-1 code (e.g., 'en', 'es') or None if not found/not specified
    """
    if not language:
        return None
    
    language_lower = language.lower().strip()
    return _LANGUAGE_TO_ISO639.get(language_lower)


def _iso639_to_language(iso_code: Optional[str]) -> Optional[str]:
    """
    Convert ISO 639-1 code to readable language name.
    
    Args:
        iso_code: ISO 639-1 code (e.g., 'en', 'es') or None
        
    Returns:
        Language name (e.g., 'English', 'Spanish') or None if not found/not specified
    """
    if not iso_code:
        return None
    
    return _ISO639_TO_LANGUAGE.get(iso_code.lower())


def _get_cache_key(params: dict) -> str:
    """Generate cache key from search parameters."""
    # Create sorted JSON string for consistent keys
    sorted_params = json.dumps(sorted(params.items()), sort_keys=True)
    return sorted_params


def _check_cache(cache_key: str) -> Optional[dict]:
    """Check if result exists in cache and is still valid."""
    global _cache_stats, _search_cache
    
    # Reset stats every hour
    if datetime.now() - _cache_stats['last_reset'] > timedelta(hours=1):
        logger.info(f"Cache stats (before reset): {_cache_stats}")
        _cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': len(_search_cache),
            'last_reset': datetime.now()
        }
    
    if cache_key in _search_cache:
        entry = _search_cache[cache_key]
        # Check if entry is still valid (within TTL)
        if datetime.now() - entry['timestamp'] < timedelta(seconds=CACHE_TTL_SECONDS):
            # Move to end for LRU
            _search_cache.move_to_end(cache_key)
            _cache_stats['hits'] += 1
            _cache_stats['size'] = len(_search_cache)
            logger.info(f"Cache HIT. Stats: hits={_cache_stats['hits']}, misses={_cache_stats['misses']}, size={_cache_stats['size']}")
            return entry['data']
        else:
            # Entry expired, remove it
            del _search_cache[cache_key]
    
    _cache_stats['misses'] += 1
    _cache_stats['size'] = len(_search_cache)
    logger.info(f"Cache MISS. Stats: hits={_cache_stats['hits']}, misses={_cache_stats['misses']}, size={_cache_stats['size']}")
    return None


def _store_cache(cache_key: str, data: dict):
    """Store result in cache with LRU eviction."""
    global _cache_stats, _search_cache
    
    # Evict oldest entries if cache is full
    while len(_search_cache) >= MAX_CACHE_SIZE:
        oldest_key, _ = _search_cache.popitem(last=False)
        _cache_stats['evictions'] += 1
        logger.info(f"Cache EVICTION. Removed oldest entry. Total evictions: {_cache_stats['evictions']}")
    
    _search_cache[cache_key] = {
        'timestamp': datetime.now(),
        'data': data
    }
    _cache_stats['size'] = len(_search_cache)


# Budget calculation multipliers - easily adjustable
BUDGET_EXPANSION_MIN = 0.8  # Search 80% of budget minimum
BUDGET_EXPANSION_MAX = 1.2  # Search 120% of budget maximum
BUDGET_THRESHOLD_MIN = 0.9  # Flag results below 90% of budget
MIN_SUBSCRIBER_MULTIPLIER = 3  # Min subscribers = budget * 3
MAX_SUBSCRIBER_MULTIPLIER = 20  # Max subscribers = budget * 20
MIN_PRICE_SUBSCRIBER_MULTIPLIER = 6  # For price ranges: min subscribers = min_price * 6
MIN_BUDGET = 0  # Minimum allowed budget

# Cache configuration
MAX_CACHE_SIZE = 1000
CACHE_TTL_SECONDS = 3600  # 1 hour

# Module-level cache using OrderedDict for LRU
_search_cache = OrderedDict()
_cache_stats = {
    'hits': 0,
    'misses': 0,
    'evictions': 0,
    'size': 0,
    'last_reset': datetime.now()
}

# Language mappings
_LANGUAGE_TO_ISO639 = {
    'english': 'en',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'italian': 'it',
    'portuguese': 'pt',
    'japanese': 'ja',
    'korean': 'ko',
    'chinese': 'zh',
    'russian': 'ru',
    'arabic': 'ar',
    'hindi': 'hi',
    'dutch': 'nl',
    'polish': 'pl',
    'turkish': 'tr',
    'swedish': 'sv',
    'norwegian': 'no',
    'danish': 'da',
    'finnish': 'fi',
    'greek': 'el',
}

_ISO639_TO_LANGUAGE = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'el': 'Greek',
}

def find_creators(
    category: str,
    platform: Optional[str] = None,
    location: Optional[str] = None,
    budget: Optional[float] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    max_results: int = 10,
    target_audience: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    """
    Search for YouTube creators/channels based on campaign criteria.
    
    Args:
        category: Content category/niche (e.g., 'food', 'tech', 'fitness')
        platform: Platform filter - only 'YouTube' is supported (others ignored)
        location: Geographic location (country or region)
        budget: Single budget value (calculates follower range with 80-120% expansion)
        min_price: Minimum budget for range (calculates min followers with 80-120% expansion)
        max_price: Maximum budget for range (calculates max followers with 80-120% expansion)
        max_results: Maximum number of results to return (default: 10, max: 50)
        target_audience: Description of target audience (used in search query)
        language: Content language (e.g., 'English', 'Spanish') - converted to ISO 639-1
    
    Returns:
        dict: Search results with budget status flags and content language
    """
    # Always cache all results for the query, not just the first page
    cache_params = {
        'category': category,
        'platform': platform,
        'location': location,
        'budget': budget,
        'min_price': min_price,
        'max_price': max_price,
        'target_audience': target_audience,
        'language': language,
    }
    cache_key = _get_cache_key(cache_params)
    cached_result = _check_cache(cache_key)
    if cached_result is not None:
        # Present only up to 10 results at a time
        results = cached_result.get('all_results', [])
        show_count = min(10, len(results))
        response = dict(cached_result)
        response['results'] = results[:show_count]
        response['more_results_available'] = len(results) > show_count
        if response['more_results_available']:
            response['message'] = (response.get('message', '') +
                f" Showing {show_count} of {len(results)} results. Would you like to see more?")
        return response
    # Get YouTube API key from environment
    api_key = os.getenv('YOUTUBE_DATA_API_KEY')
    if not api_key:
        result = {
            'error': 'YOUTUBE_DATA_API_KEY not found in environment variables',
            'all_results': [],
            'results': [],
            'more_results_available': False
        }
        _store_cache(cache_key, result)
        return result
    
    # Only YouTube is supported
    if platform and platform.lower() != 'youtube':
        result = {
            'message': f'Only YouTube is supported. Platform "{platform}" was ignored.',
            'all_results': [],
            'results': [],
            'more_results_available': False
        }
        _store_cache(cache_key, result)
        return result
    
    # Validate budget
    if budget is not None and budget < MIN_BUDGET:
        result = {
            'error': f'Budget must be at least ${MIN_BUDGET}',
            'all_results': [],
            'results': [],
            'more_results_available': False
        }
        _store_cache(cache_key, result)
        return result
    
    # Calculate follower (subscriber) range from budget with expansion for search
    # Store original budget for status comparison
    original_min_budget = None
    original_max_budget = None
    min_followers = None
    max_followers = None
    search_min_followers = None
    search_max_followers = None
    
    if budget:
        # Original range (for flagging)
        original_min_budget = budget
        original_max_budget = budget
        min_followers = int(budget * MIN_SUBSCRIBER_MULTIPLIER)
        max_followers = int(budget * MAX_SUBSCRIBER_MULTIPLIER)
        # Expanded range for search (80%-120%)
        search_min_followers = int(budget * MIN_SUBSCRIBER_MULTIPLIER * BUDGET_EXPANSION_MIN)
        search_max_followers = int(budget * MAX_SUBSCRIBER_MULTIPLIER * BUDGET_EXPANSION_MAX)
    elif min_price and max_price:
        # Original range (for flagging)
        original_min_budget = min_price
        original_max_budget = max_price
        min_followers = int(min_price * MIN_PRICE_SUBSCRIBER_MULTIPLIER)
        max_followers = int(max_price * MAX_SUBSCRIBER_MULTIPLIER)
        # Expanded range for search (80%-120%)
        search_min_followers = int(min_price * MIN_PRICE_SUBSCRIBER_MULTIPLIER * BUDGET_EXPANSION_MIN)
        search_max_followers = int(max_price * MAX_SUBSCRIBER_MULTIPLIER * BUDGET_EXPANSION_MAX)
    
    try:
        # Build YouTube API client
        youtube = build('youtube', 'v3', developerKey=api_key)
        # Build search query
        search_terms = [category]
        if target_audience:
            search_terms.append(target_audience)
        search_query = ' '.join(search_terms)
        
        # Convert location to country code for filtering
        required_country_code = _get_region_code(location) if location else None
        
        # Convert language to ISO 639-1 code if provided
        language_code = _language_to_iso639(language) if language else None
        
        # Search for channels
        search_request = youtube.search().list(
            part='snippet',
            q=search_query,
            type='channel',
            maxResults=50,  # Always get max results for caching
            regionCode=required_country_code,
            relevanceLanguage=language_code,
            order='relevance'
        )
        search_response = search_request.execute()
        
        # Get detailed channel statistics
        channel_ids = [item['id']['channelId'] for item in search_response.get('items', [])]
        if not channel_ids:
            result = {
                'message': f'No YouTube channels found for query: {search_query}',
                'search_query': search_query,
                'all_results': [],
                'results': [],
                'more_results_available': False
            }
            _store_cache(cache_key, result)
            return result
        channels_request = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=','.join(channel_ids)
        )
        channels_response = channels_request.execute()
        # Process and filter results
        all_results = []
        filtered_out = 0
        filtered_by_country = 0
        for channel in channels_response.get('items', []):
            stats = channel.get('statistics', {})
            snippet = channel.get('snippet', {})
            
            # Soft filter by country: only filter out if channel HAS a country set AND it doesn't match
            # Many channels don't set their country, but regionCode in search already biases toward the region
            channel_country = snippet.get('country', '').upper()
            if required_country_code and channel_country and channel_country != required_country_code:
                filtered_by_country += 1
                continue
            subscriber_count = int(stats.get('subscriberCount', 0))
            view_count = int(stats.get('viewCount', 0))
            video_count = int(stats.get('videoCount', 1))
            
            # Filter by subscriber count (expanded range)
            if search_min_followers is not None and subscriber_count < search_min_followers:
                filtered_out += 1
                continue
            if search_max_followers is not None and subscriber_count > search_max_followers:
                filtered_out += 1
                continue
            
            # Calculate approximate engagement rate (views per video / subscribers)
            avg_views_per_video = view_count / video_count if video_count > 0 else 0
            engagement_rate = (avg_views_per_video / subscriber_count * 100) if subscriber_count > 0 else 0
            
            # Calculate estimated price range
            estimated_min, estimated_max = _calculate_price_range_values(subscriber_count)
            
            # Determine budget status
            budget_status = 'within_budget'
            budget_note = None
            if original_min_budget is not None and original_max_budget is not None:
                # Calculate thresholds
                min_threshold = original_min_budget * BUDGET_THRESHOLD_MIN
                max_threshold = original_max_budget
                if estimated_min > max_threshold:
                    budget_status = 'above_budget'
                    budget_note = f"Estimated price (${estimated_min:,}-${estimated_max:,}) exceeds your budget of ${original_max_budget:,}"
                elif estimated_max < min_threshold:
                    budget_status = 'below_budget_threshold'
                    budget_note = f"Estimated price (${estimated_min:,}-${estimated_max:,}) is significantly below your budget range (less than 90% of ${original_min_budget:,})"
            
            # Build result object
            channel_data = {
                'username': snippet.get('title', 'Unknown'),
                'channel_id': channel['id'],
                'platform': 'YouTube',
                'followers': subscriber_count,
                'subscribers': subscriber_count,
                'video_count': video_count,
                'total_views': view_count,
                'engagement_rate': round(engagement_rate, 2),
                'description': snippet.get('description', ''),
                'category': category,
                'location': snippet.get('country', 'Unknown'),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'url': f"https://www.youtube.com/channel/{channel['id']}",
                'estimated_price_range': f"${estimated_min:,} - ${estimated_max:,}",
                'budget_status': budget_status,
            }
            
            # Add budget note if status is not within budget
            if budget_note:
                channel_data['budget_note'] = budget_note
            all_results.append(channel_data)
        # Sort by subscribers (highest first)
        all_results.sort(key=lambda x: x['subscribers'], reverse=True)
        # Log filtering stats
        if filtered_out > 0:
            logger.info(f"Filtered out {filtered_out} channels outside subscriber range {search_min_followers:,}-{search_max_followers:,}")
        if filtered_by_country > 0:
            logger.info(f"Filtered out {filtered_by_country} channels not in country: {required_country_code}")
        
        # Build message with filtering info
        filter_messages = []
        if filtered_out > 0:
            filter_messages.append(f'{filtered_out} outside budget range')
        if filtered_by_country > 0:
            filter_messages.append(f'{filtered_by_country} not in {location}')
        message = f'Found {len(all_results)} YouTube channels matching criteria'
        if filter_messages:
            message += f' (filtered out: {", ".join(filter_messages)})'
        show_count = min(10, len(all_results))
        result = {
            'message': message + (f" Showing {show_count} of {len(all_results)} results. Would you like to see more?" if len(all_results) > show_count else ""),
            'search_query': search_query,
            'location_filter': location if location else None,
            'country_code': required_country_code if required_country_code else None,
            'original_budget_range': {
                'min': original_min_budget,
                'max': original_max_budget
            } if (original_min_budget or original_max_budget) else None,
            'expanded_search_range': {
                'min_subscribers': search_min_followers,
                'max_subscribers': search_max_followers
            } if (search_min_followers or search_max_followers) else None,
            'all_results': all_results,
            'results': all_results[:show_count],
            'more_results_available': len(all_results) > show_count
        }
        
        # Store in cache
        _store_cache(cache_key, result)
        
        # Save to Firestore if session context is available
        try:
            from session_manager import get_current_session_context
            from db import FoundCreatorsDB
            
            session_context = get_current_session_context()
            if session_context:
                session_id = session_context['session_id']
                user_id = session_context['user_id']
                
                # Prepare search params
                search_params = {
                    'category': category,
                    'platform': platform,
                    'location': location,
                    'budget': budget,
                    'min_price': min_price,
                    'max_price': max_price,
                    'max_results': max_results,
                    'target_audience': target_audience,
                    'language': language,
                }
                
                # Prepare metadata
                metadata = {
                    'search_query': search_query,
                    'country_code': required_country_code,
                    'cache_hit': False,
                }
                
                # Save to Firestore
                found_creators_db = FoundCreatorsDB()
                found_creators_db.save_search_results(
                    session_id=session_id,
                    user_id=user_id,
                    search_params=search_params,
                    results=all_results,
                    metadata=metadata
                )
                logger.info(f"Saved {len(all_results)} creator results to Firestore for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to save creator search results to Firestore: {e}")
        
        return result
        
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        result = {
            'error': f'YouTube API error: {str(e)}',
            'all_results': [],
            'results': [],
            'more_results_available': False
        }
        _store_cache(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        result = {
            'error': f'Unexpected error: {str(e)}',
            'all_results': [],
            'results': [],
            'more_results_available': False
        }
        _store_cache(cache_key, result)
        return result

def _get_region_code(location: str) -> Optional[str]:
    """Convert location string to ISO 3166-1 alpha-2 country code using pycountry."""
    if not location:
        return None
    
    location_clean = location.strip()
    
    # Try exact match by name
    try:
        country = pycountry.countries.search_fuzzy(location_clean)
        if country:
            return country[0].alpha_2
    except LookupError:
        pass
    
    # Try as alpha-2 code (e.g., "US", "GB")
    if len(location_clean) == 2:
        try:
            country = pycountry.countries.get(alpha_2=location_clean.upper())
            if country:
                return country.alpha_2
        except KeyError:
            pass
    
    # Try as alpha-3 code (e.g., "USA", "GBR")
    if len(location_clean) == 3:
        try:
            country = pycountry.countries.get(alpha_3=location_clean.upper())
            if country:
                return country.alpha_2
        except KeyError:
            pass
    
    return None

def _calculate_price_range(subscribers: int) -> str:
    """Calculate estimated price range based on subscriber count."""
    # Industry standard: $10-$50 per 1000 subscribers for sponsored content
    min_price = int((subscribers / 1000) * 10)
    max_price = int((subscribers / 1000) * 50)
    
    return f"${min_price:,} - ${max_price:,}"


def _calculate_price_range_values(subscribers: int) -> tuple:
    """Calculate estimated price range values based on subscriber count."""
    # Industry standard: $10-$50 per 1000 subscribers for sponsored content
    min_price = int((subscribers / 1000) * 10)
    max_price = int((subscribers / 1000) * 50)
    
    return min_price, max_price
