"""
Ranger Lead Agent - Single Agent with Chained Reasoning

The agent follows a reasoning chain:
1. Identify target area (storms, city, etc.)
2. Find properties in that area
3. Get contact info via skip trace
4. Score and output leads
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from agents import Agent, Runner, WebSearchTool, RunConfig, ModelSettings

from .config import config
from .tools import ALL_TOOLS, write_leads_impl, LeadRow


# Model settings optimized for speed
MODEL_SETTINGS = ModelSettings(
    parallel_tool_calls=True,  # Enable parallel tool execution
    temperature=0.3,  # Lower = faster, more deterministic
)

# Run configuration for speed
RUN_CONFIG = RunConfig(
    model=config.OPENAI_MODEL,  # gpt-4o-mini by default for speed
    model_settings=MODEL_SETTINGS,
    tracing_disabled=True,  # Disable tracing for speed
)


def _lead_to_row(lead: "Lead") -> LeadRow:
    """Convert a Lead model to LeadRow for CSV export."""
    data = lead.model_dump()
    # Convert list to pipe-separated string for CSV
    if isinstance(data.get("evidence_urls"), list):
        data["evidence_urls"] = "|".join(data["evidence_urls"])
    # Map 'zip' to 'zip_code' if present
    if "zip" in data and "zip_code" not in data:
        data["zip_code"] = data.pop("zip")
    return LeadRow(**data)


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class Lead(BaseModel):
    """A qualified lead with contact info."""
    name: Optional[str] = Field(default=None, description="Owner or business name")
    address: Optional[str] = Field(default=None, description="Property address")
    city: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    zip: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, description="Phone number (from skip trace or web)")
    phone_available: bool = Field(default=False, description="Whether phone was found")
    email: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    
    # Qualification
    type: str = Field(description="Lead type: middleman, storm, or homeowner")
    score: int = Field(ge=0, le=100, description="Qualification score 0-100")
    qualified: bool = Field(description="Whether lead is qualified")
    reason: str = Field(description="Why qualified or not")
    
    # Evidence
    evidence_urls: list[str] = Field(default_factory=list)
    storm_context: Optional[str] = Field(default=None, description="Related storm event if any")
    year_built: Optional[int] = Field(default=None)
    
    # Metadata
    role: Optional[str] = Field(default=None, description="Professional role for middlemen")
    notes: Optional[str] = Field(default=None)


class LeadsResponse(BaseModel):
    """Structured response with leads."""
    leads: list[Lead] = Field(description="List of qualified leads")
    summary: str = Field(description="Brief summary of findings")
    total_found: int = Field(description="Total leads found")
    qualified_count: int = Field(description="Number qualified")
    phones_found: int = Field(default=0, description="Number with phone numbers")
    data_sources_used: list[str] = Field(default_factory=list)
    storm_events: list[str] = Field(default_factory=list, description="Storm events that informed search")
    skip_trace_configured: bool = Field(default=True, description="Whether skip tracing is available")


class StormAlertInfo(BaseModel):
    """A storm alert for response."""
    event: str
    severity: str
    affected_area: str
    affected_zones: list[str] = Field(default_factory=list)
    roofing_relevant: bool
    headline: Optional[str] = None


class StormResponse(BaseModel):
    """Structured storm analysis."""
    alerts: list[StormAlertInfo] = Field(description="Storm alerts found")
    target_areas: list[str] = Field(description="Recommended areas for outreach")
    summary: str
    recommended_message_type: str = Field(description="storm or homeowner")


# ============================================================================
# DIRECT PROMPT (optimized for speed + complete data)
# ============================================================================

SYSTEM_PROMPT = """You are a roofing lead generation expert for Lone Ranger Roofing.

## YOU CAN ANSWER TWO TYPES OF QUERIES:

### 1. STRATEGY QUESTIONS (no leads needed)
If asked "who can help find leads?" or "how do I get referrals?" etc:
- Explain lead generation strategies for roofers
- Key referral sources: home inspectors, realtors, insurance adjusters, property managers
- Storm chasing: monitor weather, contact homeowners in affected areas
- Property data: target older homes (pre-2005) likely needing roof replacement

### 2. LEAD SEARCHES (find actual contacts)
If asked to "find" or "get" leads:

For MIDDLEMEN (inspectors, realtors, contractors):
1. Use web_search to find businesses
2. Extract: name, phone, address, website
3. Every lead MUST have a phone number

For STORM/HOMEOWNER leads:
1. get_nws_alerts(state) for affected areas
2. find_open_dataset + query_socrata for properties
3. skip_trace for owner phones

## LEAD DATA REQUIRED:
- name, phone (REQUIRED), type ("middleman"|"homeowner"|"storm")
- address, email, website (if available)

## SCORING:
Phone: 40 | Email: 10 | Address: 10 | Website: 10 | Licensed: 15 | Reviews: 15
Qualified if >= 50

## CRITICAL FOR LEAD SEARCHES:
- Return the requested number of leads
- Every lead needs a phone number
- Use real URLs (not "turn0search1")
"""


# ============================================================================
# SINGLE AGENT
# ============================================================================

agent = Agent(
    name="Ranger Lead Agent",
    instructions=SYSTEM_PROMPT,
    tools=[
        WebSearchTool(),
        *ALL_TOOLS,
    ],
)


# ============================================================================
# RUNNER FUNCTIONS
# ============================================================================

def run_agent(
    query: str,
    output_type: Type[BaseModel] | None = None
) -> BaseModel | str:
    """
    Run the agent with optional structured output.
    Uses agent.clone() to set the output_type dynamically.
    Uses gpt-4o-mini by default for 3-5x faster responses.
    """
    # Use higher max_turns for larger lead requests
    max_turns = config.MAX_TURNS
    
    if output_type:
        # Clone the agent with the desired output type
        typed_agent = agent.clone(output_type=output_type)
        result = Runner.run_sync(typed_agent, query, run_config=RUN_CONFIG, max_turns=max_turns)
    else:
        result = Runner.run_sync(agent, query, run_config=RUN_CONFIG, max_turns=max_turns)
    return result.final_output


def find_leads(
    location: str,
    lead_type: str = "homeowner",
    year_before: int = 2005,
    check_storms: bool = True,
    save_csv: bool = True
) -> LeadsResponse:
    """
    Main workflow: Find leads with full reasoning chain.
    
    This chains together:
    1. Storm check (if state provided)
    2. Property search
    3. Skip tracing for phones
    4. Scoring and output
    """
    # Build query based on parameters
    storm_clause = ""
    if check_storms and len(location) == 2:  # State code
        storm_clause = f"""
First, check for active storm alerts in {location} using get_nws_alerts.
Identify storm-affected areas and prioritize those for lead search.
"""
    
    if lead_type == "middleman":
        query = f"""{storm_clause}
Find and qualify roofing-related professionals (inspectors, realtors, property managers) in {location}.

1. Web search for professionals in the area
2. Verify their licenses via web search
3. Check reviews and online presence
4. Extract phone numbers from business listings
5. Score each 0-100 based on verified facts

Return structured leads with contact info and evidence URLs."""
    else:
        query = f"""{storm_clause}
Find homeowner leads in {location} - properties likely needing roof work.

1. Use find_open_dataset to locate property data for {location}
2. Query for properties built before {year_before}
3. For each property, use skip_trace to get owner contact info
4. If skip_trace is not configured, still include leads with phone_available=False
5. Score based on: property age, storm exposure, data quality

Return structured leads with addresses and any available contact info."""

    output: LeadsResponse = run_agent(query, output_type=LeadsResponse)
    
    if save_csv and output.leads:
        rows = [_lead_to_row(lead) for lead in output.leads]
        location_clean = location.replace(' ', '_').replace(',', '')
        write_leads_impl(rows, f"{lead_type}_leads_{location_clean}")
    
    return output


def find_storm_leads(state: str, save_csv: bool = True) -> LeadsResponse:
    """
    Find leads based on storm activity.
    Chains: Storm alerts → Property search → Skip trace → Output
    """
    query = f"""Find roofing leads in {state} based on storm activity.

FOLLOW THE FULL REASONING CHAIN:

1. STORM CHECK: Use get_nws_alerts("{state}") to find active storm alerts
   - Identify areas with hail, wind, severe weather
   - Note the affected counties/zones

2. PROPERTY SEARCH: For storm-affected areas:
   - Use find_open_dataset to locate property data
   - Query for older homes in those areas
   - If no open data, use web search for property info

3. CONTACT INFO: For each property found:
   - Use skip_trace(address, city, state, zip) to get owner phone
   - If skip_trace not configured, mark phone_available=False
   - Still include the lead

4. SCORE & OUTPUT:
   - Score based on storm exposure + property age + phone availability
   - Include storm_context for each lead
   - Return structured leads

Even if some steps fail (no open data, no skip trace), continue with available data."""

    output: LeadsResponse = run_agent(query, output_type=LeadsResponse)
    
    if save_csv and output.leads:
        rows = [_lead_to_row(lead) for lead in output.leads]
        write_leads_impl(rows, f"storm_leads_{state}")
    
    return output


def find_middlemen(
    role: str,
    location: str,
    radius: int = 25,
    save_csv: bool = True
) -> LeadsResponse:
    """Find middlemen (inspectors, realtors, PMs) with contact info."""
    query = f"""Find and qualify {role}s in {location} (within {radius} miles).

1. Web search for "{role} near {location}"
2. Verify licenses via web search
3. Extract phone numbers from business listings (Google, Yelp, websites)
4. Check reviews and online presence
5. Score each 0-100 based on verified facts

Return structured leads with phone numbers and evidence URLs."""

    output: LeadsResponse = run_agent(query, output_type=LeadsResponse)
    
    if save_csv and output.leads:
        rows = [_lead_to_row(lead) for lead in output.leads]
        location_clean = location.replace(' ', '_').replace(',', '')
        write_leads_impl(rows, f"middlemen_{role.replace(' ', '_')}_{location_clean}")
    
    return output


# ============================================================================
# CONVENIENCE CLASS
# ============================================================================

class LeadAgent:
    """High-level interface."""
    
    def __init__(self):
        config.validate()
    
    def find_leads(self, location: str, lead_type: str = "homeowner", **kwargs) -> LeadsResponse:
        """Main method - finds leads with full reasoning chain."""
        return find_leads(location, lead_type, **kwargs)
    
    def find_storm_leads(self, state: str) -> LeadsResponse:
        """Find leads based on storm activity."""
        return find_storm_leads(state)
    
    def find_middlemen(self, role: str, location: str, radius: int = 25) -> LeadsResponse:
        """Find middlemen (inspectors, realtors, PMs)."""
        return find_middlemen(role, location, radius)
    
    def custom_query(self, query: str, structured: bool = False) -> LeadsResponse | str:
        """Run a custom query."""
        if structured:
            return run_agent(query, output_type=LeadsResponse)
        return run_agent(query)
