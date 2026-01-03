"""
Business Search Tool - Aggregated multi-search for finding businesses.

Does multiple web searches internally to gather enough leads,
then returns aggregated results for the agent to score.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field
from agents import function_tool, WebSearchTool


# ============================================================================
# MODELS
# ============================================================================

class BusinessResult(BaseModel):
    """A business found from search."""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None


class BusinessSearchResponse(BaseModel):
    """Response from business search."""
    success: bool
    profession: str
    location: str
    requested_count: int
    found_count: int
    businesses: list[BusinessResult] = Field(default_factory=list)
    search_queries_used: list[str] = Field(default_factory=list)
    note: Optional[str] = None


# ============================================================================
# SEARCH PATTERNS
# ============================================================================

SEARCH_PATTERNS = [
    "{profession} in {city}",
    "{profession} near {city}",
    "best {profession} {city}",
    "{profession} {city} phone number",
    "{city} {profession} directory",
    "{profession} {city} yelp",
    "{profession} {city} reviews",
    "top rated {profession} {city}",
    "{profession} companies {city}",
    "licensed {profession} {city}",
]


# ============================================================================
# PHONE/EMAIL EXTRACTION
# ============================================================================

PHONE_PATTERN = re.compile(
    r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
)

EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

URL_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+'
)


def extract_phone(text: str) -> Optional[str]:
    """Extract first phone number from text."""
    matches = PHONE_PATTERN.findall(text)
    for match in matches:
        # Filter out numbers that are too short or look like years
        cleaned = re.sub(r'[^\d]', '', match)
        if 10 <= len(cleaned) <= 15:
            return match.strip()
    return None


def extract_email(text: str) -> Optional[str]:
    """Extract first email from text."""
    matches = EMAIL_PATTERN.findall(text)
    return matches[0] if matches else None


def extract_url(text: str) -> Optional[str]:
    """Extract first URL from text."""
    matches = URL_PATTERN.findall(text)
    return matches[0] if matches else None


# ============================================================================
# IMPLEMENTATION
# ============================================================================

def find_businesses_impl(
    profession: str,
    city: str,
    state: str = "",
    count: int = 10
) -> BusinessSearchResponse:
    """
    Find businesses by doing multiple web searches.
    
    This is a placeholder that describes what the tool SHOULD do.
    The actual implementation requires the agent to call web_search multiple times.
    
    Args:
        profession: Type of business (e.g., "home inspector", "realtor")
        city: City to search in
        state: State code (optional)
        count: Number of businesses to find
    
    Returns:
        BusinessSearchResponse with search patterns to use
    """
    location = f"{city}, {state}" if state else city
    
    # Calculate how many search patterns we need
    # Assume ~3-5 results per search
    num_searches = min(max(count // 3, 3), len(SEARCH_PATTERNS))
    
    queries_to_use = []
    for pattern in SEARCH_PATTERNS[:num_searches]:
        query = pattern.format(profession=profession, city=location)
        queries_to_use.append(query)
    
    return BusinessSearchResponse(
        success=True,
        profession=profession,
        location=location,
        requested_count=count,
        found_count=0,
        businesses=[],
        search_queries_used=queries_to_use,
        note=f"Use web_search for EACH of these {len(queries_to_use)} queries to find {count} businesses: {queries_to_use}"
    )


# ============================================================================
# TOOL
# ============================================================================

find_businesses = function_tool(find_businesses_impl)

