"""Discovery tools - Finding open data sources."""

from typing import Optional
from pydantic import BaseModel, Field
from agents import function_tool


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class DatasetSearchResponse(BaseModel):
    """Response from open dataset search."""
    found: bool
    jurisdiction: Optional[str] = None
    portal: Optional[str] = None
    search_url: Optional[str] = None
    api_base: Optional[str] = None
    suggested_keywords: list[str] = Field(default_factory=list)
    suggestion: Optional[str] = None
    common_portals: list[str] = Field(default_factory=list)
    note: Optional[str] = None


# ============================================================================
# CONSTANTS
# ============================================================================

KNOWN_PORTALS = {
    "austin": "data.austintexas.gov",
    "houston": "data.houstontx.gov",
    "dallas": "data.dallasopendata.com",
    "san antonio": "data.sanantonio.gov",
    "chicago": "data.cityofchicago.org",
    "los angeles": "data.lacity.org",
    "new york": "data.cityofnewyork.us",
    "denver": "data.denvergov.org",
    "seattle": "data.seattle.gov",
    "portland": "data.portlandoregon.gov",
    "phoenix": "www.phoenixopendata.com",
    "san diego": "data.sandiego.gov",
    "philadelphia": "www.opendataphilly.org",
    "atlanta": "opendata.atlantaga.gov",
}

DATASET_KEYWORDS = {
    "building_permits": ["building permit", "construction permit", "permit"],
    "assessor": ["assessor", "property", "parcel", "tax", "appraisal"],
    "parcels": ["parcel", "property", "land use", "zoning"],
}


# ============================================================================
# IMPLEMENTATION FUNCTIONS (can be called directly)
# ============================================================================

def find_open_dataset_impl(jurisdiction: str, dataset_type: str) -> DatasetSearchResponse:
    """
    Search for Socrata open data portals for a city/county.
    Use this to find building permits, assessor data, or parcel information.
    
    Args:
        jurisdiction: City or county (e.g., 'Austin, TX', 'Harris County')
        dataset_type: Type of dataset - one of: building_permits, assessor, parcels
    
    Returns:
        DatasetSearchResponse with portal info or suggestions
    """
    jurisdiction_lower = jurisdiction.lower()
    
    # Find matching portal
    portal = None
    for city, domain in KNOWN_PORTALS.items():
        if city in jurisdiction_lower:
            portal = domain
            break
    
    keywords = DATASET_KEYWORDS.get(dataset_type, [dataset_type])
    
    if portal:
        return DatasetSearchResponse(
            found=True,
            jurisdiction=jurisdiction,
            portal=portal,
            search_url=f"https://{portal}/browse?q={'+'.join(keywords)}",
            api_base=f"https://{portal}/resource/",
            suggested_keywords=keywords,
            note="Use web search to find specific dataset IDs, then query_socrata to fetch data"
        )
    
    return DatasetSearchResponse(
        found=False,
        jurisdiction=jurisdiction,
        suggestion=f"Web search for '{jurisdiction} open data portal' or '{jurisdiction} Socrata'",
        common_portals=list(KNOWN_PORTALS.keys())[:10]
    )


# ============================================================================
# TOOLS (for Agent)
# ============================================================================

find_open_dataset = function_tool(find_open_dataset_impl)
