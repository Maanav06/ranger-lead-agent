"""Ranger Lead Agent - Roofing lead generation using OpenAI Agents SDK."""

from .agent import (
    run_agent,
    find_leads,
    find_storm_leads,
    find_middlemen,
    LeadAgent,
    LeadsResponse,
    StormResponse,
    Lead,
)

__version__ = "2.0.0"
__all__ = [
    "run_agent",
    "find_leads",
    "find_storm_leads",
    "find_middlemen",
    "LeadAgent",
    "LeadsResponse",
    "StormResponse",
    "Lead",
]
