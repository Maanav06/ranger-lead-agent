"""Weather tools - NWS alerts and NOAA storm data."""

from typing import Optional
from pydantic import BaseModel, Field
import httpx
from agents import function_tool


# ============================================================================
# RESPONSE MODELS (for typed returns)
# ============================================================================

class Alert(BaseModel):
    """A single weather alert."""
    id: Optional[str] = None
    event: str
    severity: str
    urgency: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    affected_zones: list[str] = Field(default_factory=list)
    effective: Optional[str] = None
    expires: Optional[str] = None
    sender: Optional[str] = None


class NWSAlertsResponse(BaseModel):
    """Response from NWS alerts query."""
    success: bool
    area: str
    total_alerts: int = 0
    alerts: list[Alert] = Field(default_factory=list)
    roofing_relevant_alerts: list[Alert] = Field(default_factory=list)
    roofing_relevant_count: int = 0
    source: str = "National Weather Service"
    error: Optional[str] = None


class NOAAStormResponse(BaseModel):
    """Response for NOAA storm events query."""
    success: bool
    note: str
    recommendation: str
    bulk_data_url: str
    state: str
    date_range: str


# ============================================================================
# CONSTANTS
# ============================================================================

ROOFING_EVENTS = [
    "Severe Thunderstorm",
    "Tornado",
    "Hail",
    "Wind",
    "Hurricane",
    "Tropical Storm",
    "High Wind",
]


# ============================================================================
# IMPLEMENTATION FUNCTIONS (can be called directly)
# ============================================================================

def get_nws_alerts_impl(area: str) -> NWSAlertsResponse:
    """
    Get active weather alerts from National Weather Service.
    Use this to find storm-affected areas for roofing leads.
    
    Args:
        area: State code (e.g., 'TX') or NWS zone ID (e.g., 'TXZ104')
    
    Returns:
        NWSAlertsResponse with alerts and roofing-relevant filtered alerts
    """
    base_url = "https://api.weather.gov/alerts/active"
    params = {"area": area.upper()} if len(area) == 2 else {"zone": area.upper()}
    headers = {
        "User-Agent": "RangerLeadAgent/1.0",
        "Accept": "application/geo+json"
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        features = data.get("features", [])
        alerts = []
        
        for feature in features[:15]:
            props = feature.get("properties", {})
            alerts.append(Alert(
                id=props.get("id"),
                event=props.get("event", "Unknown"),
                severity=props.get("severity", "Unknown"),
                urgency=props.get("urgency"),
                headline=props.get("headline"),
                description=(props.get("description") or "")[:500],
                affected_zones=props.get("affectedZones", []),
                effective=props.get("effective"),
                expires=props.get("expires"),
                sender=props.get("senderName")
            ))
        
        # Filter for roofing-relevant
        relevant = [
            a for a in alerts
            if any(evt.lower() in a.event.lower() for evt in ROOFING_EVENTS)
        ]
        
        return NWSAlertsResponse(
            success=True,
            area=area,
            total_alerts=len(features),
            alerts=alerts,
            roofing_relevant_alerts=relevant,
            roofing_relevant_count=len(relevant)
        )
        
    except Exception as e:
        return NWSAlertsResponse(
            success=False,
            area=area,
            error=str(e)
        )


def get_noaa_storm_events_impl(state: str, days_back: int = 30) -> NOAAStormResponse:
    """
    Get info about NOAA Storm Events historical data.
    Note: NCEI requires bulk downloads. Use get_nws_alerts for recent alerts.
    
    Args:
        state: Two-letter state code (e.g., 'TX')
        days_back: Days to look back (for reference)
    
    Returns:
        NOAAStormResponse with guidance on accessing historical data
    """
    return NOAAStormResponse(
        success=True,
        note="NOAA Storm Events Database requires bulk file downloads",
        recommendation="Use get_nws_alerts for active/recent alerts instead",
        bulk_data_url="https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/",
        state=state,
        date_range=f"Past {days_back} days requested"
    )


# ============================================================================
# TOOLS (for Agent)
# ============================================================================

get_nws_alerts = function_tool(get_nws_alerts_impl)
get_noaa_storm_events = function_tool(get_noaa_storm_events_impl)
