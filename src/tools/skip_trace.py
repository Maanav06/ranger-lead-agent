"""
Skip Tracing Tool - Get phone numbers from property addresses.

This is a placeholder that supports multiple providers.
Configure your provider in .env - if not configured, returns graceful failure.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
import httpx
from agents import function_tool


# ============================================================================
# INPUT & RESPONSE MODELS
# ============================================================================

class PropertyAddress(BaseModel):
    """A property address for skip tracing."""
    address: str
    city: str
    state: str
    zip_code: str


class SkipTraceResult(BaseModel):
    """Result from skip tracing a property."""
    success: bool
    address: str
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    phone_type: Optional[str] = None  # mobile, landline, voip
    email: Optional[str] = None
    confidence: Optional[float] = None  # 0-1 confidence score
    provider: Optional[str] = None
    error: Optional[str] = None
    configured: bool = Field(default=True, description="Whether skip trace is configured")


class BatchSkipTraceResult(BaseModel):
    """Result from batch skip tracing."""
    success: bool
    total_requested: int
    total_found: int
    results: list[SkipTraceResult]
    error: Optional[str] = None
    configured: bool = True


# ============================================================================
# PROVIDER IMPLEMENTATIONS
# ============================================================================

def _skip_trace_batch_skip_tracing(address: str, city: str, state: str, zip_code: str) -> SkipTraceResult:
    """BatchSkipTracing.com API implementation."""
    api_key = os.getenv("BATCH_SKIP_TRACING_API_KEY")
    
    if not api_key:
        return SkipTraceResult(
            success=False,
            address=f"{address}, {city}, {state} {zip_code}",
            error="BATCH_SKIP_TRACING_API_KEY not configured",
            configured=False
        )
    
    # BatchSkipTracing API endpoint
    url = "https://api.batchskiptracing.com/api/v1/skip-trace"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        return SkipTraceResult(
            success=True,
            address=f"{address}, {city}, {state} {zip_code}",
            owner_name=data.get("owner_name"),
            phone=data.get("phone"),
            phone_type=data.get("phone_type"),
            email=data.get("email"),
            confidence=data.get("confidence"),
            provider="BatchSkipTracing"
        )
    except Exception as e:
        return SkipTraceResult(
            success=False,
            address=f"{address}, {city}, {state} {zip_code}",
            error=str(e),
            provider="BatchSkipTracing"
        )


def _skip_trace_reiskip(address: str, city: str, state: str, zip_code: str) -> SkipTraceResult:
    """REISkip API implementation."""
    api_key = os.getenv("REISKIP_API_KEY")
    
    if not api_key:
        return SkipTraceResult(
            success=False,
            address=f"{address}, {city}, {state} {zip_code}",
            error="REISKIP_API_KEY not configured",
            configured=False
        )
    
    # REISkip API endpoint (placeholder - check actual docs)
    url = "https://api.reiskip.com/v1/lookup"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    payload = {
        "street": address,
        "city": city,
        "state": state,
        "zip": zip_code
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        return SkipTraceResult(
            success=True,
            address=f"{address}, {city}, {state} {zip_code}",
            owner_name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
            provider="REISkip"
        )
    except Exception as e:
        return SkipTraceResult(
            success=False,
            address=f"{address}, {city}, {state} {zip_code}",
            error=str(e),
            provider="REISkip"
        )


# ============================================================================
# IMPLEMENTATION FUNCTIONS (can be called directly)
# ============================================================================

def skip_trace_impl(
    address: str,
    city: str,
    state: str,
    zip_code: str
) -> SkipTraceResult:
    """
    Get owner name and phone number from a property address using skip tracing.
    
    Args:
        address: Street address (e.g., '123 Oak Street')
        city: City name (e.g., 'Austin')
        state: State code (e.g., 'TX')
        zip_code: ZIP code (e.g., '78701')
    
    Returns:
        SkipTraceResult with owner name, phone, email if found.
        If not configured, returns success=False with configured=False.
    """
    # Check which provider is configured (in priority order)
    provider = os.getenv("SKIP_TRACE_PROVIDER", "").lower().strip()
    batch_key = os.getenv("BATCH_SKIP_TRACING_API_KEY", "").strip()
    reiskip_key = os.getenv("REISKIP_API_KEY", "").strip()
    
    # Ignore placeholder values
    placeholder_values = {"", "your-key-here", "your-api-key", "your_api_key", "xxx", "placeholder"}
    batch_key = "" if batch_key.lower() in placeholder_values else batch_key
    reiskip_key = "" if reiskip_key.lower() in placeholder_values else reiskip_key
    
    if provider == "batchskiptracing" and batch_key:
        return _skip_trace_batch_skip_tracing(address, city, state, zip_code)
    
    if provider == "reiskip" and reiskip_key:
        return _skip_trace_reiskip(address, city, state, zip_code)
    
    # Try any configured key regardless of provider setting
    if batch_key:
        return _skip_trace_batch_skip_tracing(address, city, state, zip_code)
    if reiskip_key:
        return _skip_trace_reiskip(address, city, state, zip_code)
    
    # No provider configured - return graceful failure
    return SkipTraceResult(
        success=False,
        address=f"{address}, {city}, {state} {zip_code}",
        phone=None,
        owner_name=None,
        error="No skip trace provider configured. Set SKIP_TRACE_PROVIDER and API key in .env",
        configured=False
    )


def batch_skip_trace_impl(properties: list[PropertyAddress]) -> BatchSkipTraceResult:
    """
    Skip trace multiple properties at once.
    
    Args:
        properties: List of PropertyAddress objects with address, city, state, zip_code
    
    Returns:
        BatchSkipTraceResult with results for each property.
        Gracefully handles unconfigured state.
    """
    if not properties:
        return BatchSkipTraceResult(
            success=False,
            total_requested=0,
            total_found=0,
            results=[],
            error="No properties provided"
        )
    
    results = []
    found_count = 0
    configured = True
    
    for prop in properties:
        result = skip_trace_impl(
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code
        )
        results.append(result)
        
        if result.success and result.phone:
            found_count += 1
        
        if not result.configured:
            configured = False
    
    return BatchSkipTraceResult(
        success=configured,
        total_requested=len(properties),
        total_found=found_count,
        results=results,
        configured=configured,
        error=None if configured else "Skip trace provider not configured"
    )


# ============================================================================
# TOOLS (for Agent)
# ============================================================================

skip_trace = function_tool(skip_trace_impl)
batch_skip_trace = function_tool(batch_skip_trace_impl)

