"""
Tools package - All tools use function_tool() wrapper.
Each tool has both:
  - *_impl: The raw function (can be called directly)
  - *: The FunctionTool wrapper (for Agent)
"""

from .discovery import find_open_dataset, find_open_dataset_impl, DatasetSearchResponse
from .weather import (
    get_nws_alerts, get_nws_alerts_impl,
    get_noaa_storm_events, get_noaa_storm_events_impl,
    NWSAlertsResponse, NOAAStormResponse, Alert
)
from .data import (
    geocode, geocode_impl,
    query_socrata, query_socrata_impl,
    GeocodeResponse, SocrataResponse
)
from .output import (
    write_leads, write_leads_impl,
    generate_message, generate_message_impl,
    WriteLeadsResponse, GeneratedMessage, LeadRow, LeadData
)
from .skip_trace import (
    skip_trace, skip_trace_impl,
    batch_skip_trace, batch_skip_trace_impl,
    SkipTraceResult, BatchSkipTraceResult, PropertyAddress
)
from .business_search import (
    find_businesses, find_businesses_impl,
    BusinessSearchResponse, BusinessResult
)

# All tools for the Agent
ALL_TOOLS = [
    find_open_dataset,
    find_businesses,  # Multi-search aggregator
    geocode,
    query_socrata,
    get_nws_alerts,
    get_noaa_storm_events,
    write_leads,
    generate_message,
    skip_trace,
    batch_skip_trace,
]

__all__ = [
    # Tools (FunctionTool for Agent)
    "find_open_dataset",
    "geocode",
    "query_socrata",
    "get_nws_alerts",
    "get_noaa_storm_events",
    "write_leads",
    "generate_message",
    "skip_trace",
    "batch_skip_trace",
    # Implementation functions (can be called directly)
    "find_open_dataset_impl",
    "geocode_impl",
    "query_socrata_impl",
    "get_nws_alerts_impl",
    "get_noaa_storm_events_impl",
    "write_leads_impl",
    "generate_message_impl",
    "skip_trace_impl",
    "batch_skip_trace_impl",
    # Response models
    "DatasetSearchResponse",
    "GeocodeResponse",
    "SocrataResponse",
    "NWSAlertsResponse",
    "NOAAStormResponse",
    "Alert",
    "WriteLeadsResponse",
    "GeneratedMessage",
    "LeadRow",
    "LeadData",
    "SkipTraceResult",
    "BatchSkipTraceResult",
    "PropertyAddress",
    # For Agent
    "ALL_TOOLS",
]
