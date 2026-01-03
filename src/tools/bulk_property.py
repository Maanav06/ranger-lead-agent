"""
Bulk Property Search - Get 100-1000+ property leads directly.

This tool queries Socrata APIs directly and optionally runs batch skip trace,
bypassing the LLM context window limitations.
"""

import json
import os
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import httpx

from .skip_trace import skip_trace_impl
from .discovery import KNOWN_PORTALS


# ============================================================================
# MODELS
# ============================================================================

class PropertyLead(BaseModel):
    """A property lead."""
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    year_built: Optional[int] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    property_type: Optional[str] = None
    sqft: Optional[int] = None
    source: Optional[str] = None


class BulkPropertyResponse(BaseModel):
    """Response from bulk property search."""
    success: bool
    location: str
    total_found: int
    with_phones: int
    leads: list[PropertyLead] = Field(default_factory=list)
    csv_path: Optional[str] = None
    data_source: Optional[str] = None
    error: Optional[str] = None
    note: Optional[str] = None


# ============================================================================
# KNOWN PROPERTY DATASETS
# ============================================================================

# These are actual Socrata dataset IDs for property data
PROPERTY_DATASETS = {
    "austin": {
        "portal": "data.austintexas.gov",
        "dataset": "5bx7-5kqc",  # Residential property data
        "address_field": "address",
        "year_field": "year_built",
        "city_field": "city",
    },
    "houston": {
        "portal": "data.houstontx.gov",
        "dataset": "properties",  # Placeholder
        "address_field": "situs_address",
        "year_field": "year_built",
    },
    "dallas": {
        "portal": "www.dallasopendata.com",
        "dataset": "properties",  # Placeholder
        "address_field": "address",
        "year_field": "year_built",
    },
}


# ============================================================================
# IMPLEMENTATION
# ============================================================================

def bulk_property_search_impl(
    city: str,
    state: str = "TX",
    year_before: int = 2005,
    limit: int = 100,
    skip_trace_enabled: bool = False
) -> BulkPropertyResponse:
    """
    Search for bulk property leads from open data sources.
    
    Args:
        city: City to search
        state: State code (default: TX)
        year_before: Find properties built before this year
        limit: Max properties to return (up to 1000)
        skip_trace_enabled: If True, attempt to get owner phones
    
    Returns:
        BulkPropertyResponse with property leads
    """
    city_lower = city.lower().strip()
    
    # Check if we have a known dataset for this city
    dataset_info = PROPERTY_DATASETS.get(city_lower)
    
    if not dataset_info:
        # Try to find via discovery
        return BulkPropertyResponse(
            success=False,
            location=f"{city}, {state}",
            total_found=0,
            with_phones=0,
            error=f"No known property dataset for {city}. Available cities: {list(PROPERTY_DATASETS.keys())}",
            note="Use find_open_dataset to search for property data in this area"
        )
    
    # Build Socrata query
    portal = dataset_info["portal"]
    dataset = dataset_info["dataset"]
    address_field = dataset_info.get("address_field", "address")
    year_field = dataset_info.get("year_field", "year_built")
    
    endpoint = f"https://{portal}/resource/{dataset}.json"
    
    # Query parameters
    params = {
        "$limit": min(limit, 1000),
        "$where": f"{year_field} < {year_before}",
        "$order": f"{year_field} ASC",  # Oldest first (most likely to need roof)
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        
        leads = []
        for record in data:
            lead = PropertyLead(
                address=record.get(address_field, ""),
                city=record.get("city", city),
                state=record.get("state", state),
                zip_code=record.get("zip", record.get("zip_code", "")),
                year_built=_safe_int(record.get(year_field)),
                property_type=record.get("property_type", record.get("land_use", "")),
                sqft=_safe_int(record.get("sqft", record.get("living_area", 0))),
                source=endpoint
            )
            leads.append(lead)
        
        # Optional: Run skip trace for phones
        with_phones = 0
        if skip_trace_enabled and leads:
            for lead in leads[:50]:  # Limit to 50 for cost
                if lead.address and lead.city:
                    result = skip_trace_impl(
                        lead.address,
                        lead.city,
                        lead.state or state,
                        lead.zip_code or ""
                    )
                    if result.success and result.phone:
                        lead.phone = result.phone
                        lead.owner_name = result.owner_name
                        lead.email = result.email
                        with_phones += 1
        
        # Save to CSV
        csv_path = _save_leads_csv(leads, city, state)
        
        return BulkPropertyResponse(
            success=True,
            location=f"{city}, {state}",
            total_found=len(leads),
            with_phones=with_phones,
            leads=leads,
            csv_path=csv_path,
            data_source=endpoint,
            note=f"Found {len(leads)} properties built before {year_before}"
        )
        
    except httpx.HTTPStatusError as e:
        return BulkPropertyResponse(
            success=False,
            location=f"{city}, {state}",
            total_found=0,
            with_phones=0,
            error=f"API error: {e.response.status_code}",
            note="The dataset ID may need to be updated"
        )
    except Exception as e:
        return BulkPropertyResponse(
            success=False,
            location=f"{city}, {state}",
            total_found=0,
            with_phones=0,
            error=str(e)
        )


def _safe_int(val) -> Optional[int]:
    """Safely convert to int."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _save_leads_csv(leads: list[PropertyLead], city: str, state: str) -> str:
    """Save leads to CSV and return path."""
    import csv
    
    output_dir = os.getenv("OUTPUT_DIR", "output")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"property_leads_{city}_{state}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    fieldnames = ["address", "city", "state", "zip_code", "year_built", 
                  "owner_name", "phone", "email", "property_type", "sqft"]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead.model_dump(include=set(fieldnames)))
    
    return filepath


# ============================================================================
# DIRECT FUNCTION (not a tool - call directly for bulk operations)
# ============================================================================

def get_bulk_properties(
    city: str,
    state: str = "TX",
    year_before: int = 2005,
    limit: int = 100,
    skip_trace: bool = False
) -> BulkPropertyResponse:
    """
    Direct function to get bulk property leads.
    Call this directly from CLI for large batches.
    """
    return bulk_property_search_impl(city, state, year_before, limit, skip_trace)

