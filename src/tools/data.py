"""Data tools - Geocoding and Socrata queries."""

import json
from typing import Optional
from pydantic import BaseModel, Field
import httpx
from agents import function_tool


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class GeocodeResponse(BaseModel):
    """Response from geocoding request."""
    success: bool
    input: Optional[str] = None
    matched_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    tiger_line_id: Optional[str] = None
    error: Optional[str] = None


class SocrataResponse(BaseModel):
    """Response from Socrata query."""
    success: bool
    endpoint: Optional[str] = None
    count: int = 0
    total_fetched: int = 0
    records_json: str = Field(default="[]", description="JSON string of records")
    note: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# IMPLEMENTATION FUNCTIONS (can be called directly)
# ============================================================================

def geocode_impl(address: str) -> GeocodeResponse:
    """
    Convert a street address to lat/long using US Census geocoder (free).
    
    Args:
        address: Full street address (e.g., '1600 Pennsylvania Ave NW, Washington, DC')
    
    Returns:
        GeocodeResponse with coordinates and normalized address
    """
    base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        matches = data.get("result", {}).get("addressMatches", [])
        
        if matches:
            match = matches[0]
            coords = match.get("coordinates", {})
            components = match.get("addressComponents", {})
            
            return GeocodeResponse(
                success=True,
                input=address,
                matched_address=match.get("matchedAddress"),
                latitude=coords.get("y"),
                longitude=coords.get("x"),
                city=components.get("city"),
                state=components.get("state"),
                zip=components.get("zip"),
                tiger_line_id=match.get("tigerLine", {}).get("tigerLineId")
            )
        
        return GeocodeResponse(
            success=False,
            input=address,
            error="No address matches found"
        )
        
    except Exception as e:
        return GeocodeResponse(
            success=False,
            input=address,
            error=str(e)
        )


def query_socrata_impl(endpoint: str, where: str = "", limit: int = 100) -> SocrataResponse:
    """
    Query a Socrata open data endpoint for property/permit records.
    
    Args:
        endpoint: Full Socrata URL (e.g., 'https://data.austintexas.gov/resource/abc123.json')
        where: SoQL WHERE clause (e.g., 'year_built < 2000')
        limit: Max records to return (default: 100)
    
    Returns:
        SocrataResponse with query results
    """
    params = {"$limit": limit}
    if where:
        params["$where"] = where
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        
        return SocrataResponse(
            success=True,
            endpoint=endpoint,
            count=len(data),
            total_fetched=len(data),
            records_json=json.dumps(data[:20]),  # Limit for context window
            note=f"Showing first 20 of {len(data)} records" if len(data) > 20 else None
        )
        
    except Exception as e:
        return SocrataResponse(
            success=False,
            endpoint=endpoint,
            error=str(e)
        )


# ============================================================================
# TOOLS (for Agent)
# ============================================================================

geocode = function_tool(geocode_impl)
query_socrata = function_tool(query_socrata_impl)
