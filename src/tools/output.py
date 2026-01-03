"""Output tools - Writing leads and generating messages."""

import csv
import os
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from agents import function_tool

# Try pandas for Excel support
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ============================================================================
# INPUT MODELS (for strict JSON schema compatibility)
# ============================================================================

class LeadRow(BaseModel):
    """A single lead row for writing to file."""
    name: Optional[str] = None
    type: Optional[str] = None
    score: Optional[int] = None
    qualified: Optional[bool] = None
    reason: Optional[str] = None
    evidence_urls: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    owner_name: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None
    year_built: Optional[int] = None
    created_at: Optional[str] = None


class LeadData(BaseModel):
    """Lead data for message generation."""
    name: Optional[str] = None
    role: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class WriteLeadsResponse(BaseModel):
    """Response from writing leads to file."""
    success: bool
    filepath: Optional[str] = None
    format: Optional[str] = None
    rows_written: int = 0
    columns: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    fallback: Optional[str] = None


class GeneratedMessage(BaseModel):
    """A generated outreach message."""
    success: bool
    lead_type: str
    message: str
    context_used: Optional[str] = None
    note: str = "Review and personalize before sending"


# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================

MESSAGE_TEMPLATES = {
    "middleman": """Hi {name},

I'm reaching out from Lone Ranger Roofing. We're connecting with {role}s in the {area} area for referral partnerships.

We offer competitive referral fees and prioritize quality work. Would you be open to a quick call?

Best,
Lone Ranger Roofing""",

    "storm": """Hello,

We noticed recent storm activity in your area and wanted to offer our services. Lone Ranger Roofing provides free roof inspections to help assess any potential damage.

If you'd like to schedule a no-obligation inspection, please reply or call.

Stay safe,
Lone Ranger Roofing""",

    "homeowner": """Hello,

Lone Ranger Roofing is offering free roof inspections in your neighborhood. A professional inspection can help identify issues before they become costly repairs.

Would you be interested in scheduling a free assessment?

Best,
Lone Ranger Roofing"""
}


# ============================================================================
# IMPLEMENTATION FUNCTIONS (can be called directly)
# ============================================================================

def write_leads_impl(
    rows: list[LeadRow],
    filename: str,
    format: Literal["csv", "xlsx"] = "csv"
) -> WriteLeadsResponse:
    """
    Write lead data to CSV or Excel file.
    
    Args:
        rows: List of LeadRow objects with lead information
        filename: Output filename (saved to ./output/)
        format: Output format - 'csv' or 'xlsx' (xlsx requires pandas)
    
    Returns:
        WriteLeadsResponse with file path and stats
    """
    if not rows:
        return WriteLeadsResponse(success=False, error="No rows to write")
    
    output_dir = os.getenv("OUTPUT_DIR", "output")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = filename.replace(".csv", "").replace(".xlsx", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Convert Pydantic models to dicts, excluding None values
    dict_rows = [row.model_dump(exclude_none=True) for row in rows]
    
    try:
        if format == "xlsx":
            if not HAS_PANDAS:
                return WriteLeadsResponse(
                    success=False,
                    error="Excel requires pandas: pip install pandas openpyxl",
                    fallback="Use format='csv' instead"
                )
            
            filepath = os.path.join(output_dir, f"{filename}_{timestamp}.xlsx")
            df = pd.DataFrame(dict_rows)
            df.to_excel(filepath, index=False, engine="openpyxl")
        
        else:
            filepath = os.path.join(output_dir, f"{filename}_{timestamp}.csv")
            
            fieldnames = []
            for row in dict_rows:
                for key in row.keys():
                    if key not in fieldnames:
                        fieldnames.append(key)
            
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dict_rows)
        
        return WriteLeadsResponse(
            success=True,
            filepath=filepath,
            format=format,
            rows_written=len(dict_rows),
            columns=list(dict_rows[0].keys()) if dict_rows else []
        )
        
    except Exception as e:
        return WriteLeadsResponse(success=False, error=str(e))


def generate_message_impl(
    lead_type: Literal["middleman", "storm", "homeowner"],
    lead_data: LeadData,
    context: str = ""
) -> GeneratedMessage:
    """
    Generate an outreach message template for a lead.
    
    Args:
        lead_type: Type of lead - one of: middleman, storm, homeowner
        lead_data: LeadData with name, role, city, area fields
        context: Additional context like storm details
    
    Returns:
        GeneratedMessage with the message text
    """
    template = MESSAGE_TEMPLATES.get(lead_type, MESSAGE_TEMPLATES["homeowner"])
    
    message = template.format(
        name=lead_data.name or "there",
        role=lead_data.role or "professional",
        area=lead_data.city or lead_data.area or "your"
    )
    
    return GeneratedMessage(
        success=True,
        lead_type=lead_type,
        message=message,
        context_used=context if context else None
    )


# ============================================================================
# TOOLS (for Agent)
# ============================================================================

write_leads = function_tool(write_leads_impl)
generate_message = function_tool(generate_message_impl)
