"""
Service to fetch data from Lexa internal API.

Domains and domain groups are cached at application startup for performance.
Use init_lexa_cache() to initialize the cache, typically called from AppConfig.ready().
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Lexa internal API base URL (via Docker network)
LEXA_INTERNAL_URL = getattr(settings, 'LEXA_INTERNAL_URL', 'http://legal230-latest-runserver-1:8099')

# Default color for domains not in any group
DEFAULT_DOMAIN_COLOR = '#B0BEC5'

# Base colors for each domain group - domains within a group will have nuances of this color
DOMAIN_GROUP_COLORS = {
    'Tax law': '#9575CD',        # Purple
    'Corporate': '#BC8F8F',      # Rosy brown
    'Criminal law': '#E57373',   # Red/coral
    'Litigation': '#FFB74D',     # Orange
    'IP/IT': '#4DB6AC',          # Teal
    'Maritime law': '#64B5F6',   # Blue
    'Real-estate': '#FF8A65',    # Deep orange/peach
    'Public law': '#81C784',     # Green
    'Business law': '#BA68C8',   # Lavender/purple
    'Finance law': '#FFD54F',    # Amber/gold
    'Social law': '#F06292',     # Pink
    'Other': '#90A4AE',          # Blue grey
}


def _hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    """Convert RGB tuple to hex color."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def _adjust_color_lightness(hex_color, factor):
    """
    Adjust color lightness. factor > 1 lightens, factor < 1 darkens.
    Returns a pastel version of the color.
    """
    r, g, b = _hex_to_rgb(hex_color)

    # Blend with white to create pastel effect
    white_blend = 0.3 + (factor * 0.15)  # 30-60% white blend for pastel
    r = int(r + (255 - r) * white_blend)
    g = int(g + (255 - g) * white_blend)
    b = int(b + (255 - b) * white_blend)

    # Clamp values
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))

    return _rgb_to_hex((r, g, b))

# Caches for Lexa data - populated at application startup or lazily
_domains_cache = None
_domain_groups_cache = None
_users_cache = None  # Dict mapping UUID to user info
_memories_by_domain_group_cache = None  # Dict mapping domain_group name to list of memories


def init_lexa_cache():
    """
    Initialize the Lexa cache at application startup.
    Call this from AppConfig.ready() to load domains and domain groups.
    """
    global _domains_cache, _domain_groups_cache, _memories_by_domain_group_cache

    logger.info("[LEXA_CACHE] Initializing Lexa cache...")

    # Load domain groups first (domains depend on them)
    try:
        _domain_groups_cache = _fetch_domain_groups_from_api()
        logger.info(f"[LEXA_CACHE] Loaded {len(_domain_groups_cache)} domain groups")
    except Exception as e:
        logger.warning(f"[LEXA_CACHE] Failed to load domain groups: {e}")
        _domain_groups_cache = []

    # Build memories cache grouped by domain_group
    try:
        _memories_by_domain_group_cache = _build_memories_by_domain_group()
        logger.info(f"[LEXA_CACHE] Loaded memories for {len(_memories_by_domain_group_cache)} domain groups")
    except Exception as e:
        logger.warning(f"[LEXA_CACHE] Failed to build memories cache: {e}")
        _memories_by_domain_group_cache = {}

    # Build domains cache from domain groups (includes memory associations)
    try:
        _domains_cache = _build_domains_from_groups(_domain_groups_cache)
        logger.info(f"[LEXA_CACHE] Loaded {len(_domains_cache)} unique domains")
    except Exception as e:
        logger.warning(f"[LEXA_CACHE] Failed to build domains cache: {e}")
        _domains_cache = {}

    logger.info("[LEXA_CACHE] Cache initialization complete")


def _fetch_domain_groups_from_api():
    """Fetch domain groups directly from Lexa API."""
    url = f"{LEXA_INTERNAL_URL}/api/internal/domain-groups/"
    response = requests.get(
        url,
        headers={'Host': 'api.portail.lexamt.fr'},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def _build_memories_by_domain_group():
    """
    Build a dict mapping domain_group names to their associated memories.
    Queries the Memory model to get all memories grouped by domain_group.
    """
    from apps.memories.models import Memory

    memories_by_group = {}

    # Get all memories with their language info
    memories = Memory.objects.select_related('source_language', 'target_language').all()

    for memory in memories:
        domain_group = memory.domain_group
        if not domain_group:
            continue

        if domain_group not in memories_by_group:
            memories_by_group[domain_group] = []

        memories_by_group[domain_group].append({
            'memory_id': memory.memory_id,
            'name': memory.name,
            'source_language': memory.source_language.abbreviation if memory.source_language else None,
            'target_language': memory.target_language.abbreviation if memory.target_language else None,
        })

    return memories_by_group


def _build_domains_from_groups(domain_groups):
    """Build a dict of unique domains from domain groups with colors and memories."""
    global _memories_by_domain_group_cache

    domains = {}
    for group in domain_groups:
        group_name = group.get('name', '')
        group_domains = group.get('domains', [])
        base_color = DOMAIN_GROUP_COLORS.get(group_name, DEFAULT_DOMAIN_COLOR)

        # Get memories associated with this domain group
        group_memories = []
        if _memories_by_domain_group_cache:
            group_memories = _memories_by_domain_group_cache.get(group_name, [])

        for idx, domain in enumerate(group_domains):
            domain_name = domain.get('name')
            if domain_name and domain_name not in domains:
                # Generate color variation based on position in group
                # factor: 0=darker, 1=base, 2=lighter
                num_domains = len(group_domains)
                if num_domains == 1:
                    factor = 1.0
                else:
                    factor = idx / (num_domains - 1) * 2  # Range 0-2
                color = _adjust_color_lightness(base_color, factor)

                domains[domain_name] = {
                    'id': domain.get('id'),
                    'name': domain_name,
                    'french_name': domain.get('french_name'),
                    'icon': domain.get('icon'),
                    'color': color,
                    'featured': domain.get('featured', False),
                    'domain_group': group_name,
                    'translation_memories': group_memories,  # All memories for this domain's group
                }
    return domains


def get_lexa_users():
    """
    Fetch users from Lexa internal API.
    Returns list of user dictionaries.
    """
    try:
        url = f"{LEXA_INTERNAL_URL}/api/internal/users/"
        response = requests.get(
            url,
            headers={'Host': 'api.portail.lexamt.fr'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch users from Lexa: {e}")
        return []


def get_lexa_domain_groups():
    """
    Get domain groups from cache or fetch from Lexa API.
    Returns list of domain group dictionaries with nested domains.
    """
    global _domain_groups_cache

    # Return from cache if available
    if _domain_groups_cache is not None:
        return _domain_groups_cache

    # Lazy initialization if cache wasn't populated at startup
    try:
        _domain_groups_cache = _fetch_domain_groups_from_api()
        # Also build domains cache
        global _domains_cache
        _domains_cache = _build_domains_from_groups(_domain_groups_cache)
        return _domain_groups_cache
    except requests.RequestException as e:
        logger.error(f"Failed to fetch domain groups from Lexa: {e}")
        return []


def get_lexa_user_by_customer_id(customer_id):
    """
    Fetch a specific user by Stripe customer_id from Lexa.
    """
    try:
        url = f"{LEXA_INTERNAL_URL}/api/internal/users/"
        response = requests.get(
            url,
            params={'customer_id': customer_id},
            headers={'Host': 'api.portail.lexamt.fr'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch user {customer_id} from Lexa: {e}")
        return None


def get_lexa_domains():
    """
    Get all unique domains from cache.
    Returns a dict mapping domain name to domain info (icon, french_name, etc.).
    Cache is populated at startup or lazily on first access.
    """
    global _domains_cache

    # Return from cache if available
    if _domains_cache is not None:
        return _domains_cache

    # Lazy initialization - trigger domain groups fetch which populates domains cache
    get_lexa_domain_groups()

    return _domains_cache or {}


def get_lexa_domain(domain_name):
    """
    Get a specific domain's info by name.
    Returns dict with id, name, french_name, icon, featured, domain_group or None.
    """
    domains = get_lexa_domains()
    return domains.get(domain_name)


def get_lexa_user_by_uuid(uuid):
    """
    Get a user by UUID from cache.
    Cache is populated lazily on first access.
    Returns dict with id, uuid, username, email, etc. or None.
    """
    global _users_cache

    if not uuid:
        return None

    # Initialize cache if needed
    if _users_cache is None:
        _users_cache = {}
        try:
            users = get_lexa_users()
            for user in users:
                user_uuid = user.get('uuid')
                if user_uuid:
                    _users_cache[user_uuid] = user
            logger.info(f"[LEXA_CACHE] Loaded {len(_users_cache)} users into cache")
        except Exception as e:
            logger.warning(f"[LEXA_CACHE] Failed to load users: {e}")

    return _users_cache.get(uuid)


def get_memories_for_domain_group(domain_group_name):
    """
    Get all memories associated with a domain group.
    Returns list of memory dicts with memory_id, name, source_language, target_language.
    """
    global _memories_by_domain_group_cache

    # Lazy initialization if cache wasn't populated at startup
    if _memories_by_domain_group_cache is None:
        try:
            _memories_by_domain_group_cache = _build_memories_by_domain_group()
        except Exception as e:
            logger.warning(f"[LEXA_CACHE] Failed to build memories cache: {e}")
            _memories_by_domain_group_cache = {}

    return _memories_by_domain_group_cache.get(domain_group_name, [])


def clear_lexa_cache():
    """Clear all Lexa caches to force a refresh."""
    global _domains_cache, _domain_groups_cache, _users_cache, _memories_by_domain_group_cache
    _domains_cache = None
    _domain_groups_cache = None
    _users_cache = None
    _memories_by_domain_group_cache = None
    logger.info("[LEXA_CACHE] Cache cleared")
