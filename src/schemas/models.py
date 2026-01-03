"""Pydantic models for leads and data structures."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LeadType(str, Enum):
    """Types of leads we generate."""
    MIDDLEMAN = "middleman"
    STORM = "storm"
    HOMEOWNER = "homeowner"


class ContactInfo(BaseModel):
    """Contact information."""
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class Location(BaseModel):
    """Location data."""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zip")
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class QualifiedLead(BaseModel):
    """A qualified lead ready for outreach."""
    
    name: str
    type: LeadType
    score: int = Field(..., ge=0, le=100, description="0-100 qualification score")
    qualified: bool = True
    reason: str = Field(..., description="Why qualified/not")
    evidence_urls: list[str] = Field(default_factory=list)
    
    contact: Optional[ContactInfo] = None
    location: Optional[Location] = None
    role: Optional[str] = None  # For middlemen
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_row(self) -> dict:
        """Flatten to dict for CSV/Excel export."""
        return {
            "name": self.name,
            "type": self.type.value,
            "score": self.score,
            "qualified": self.qualified,
            "reason": self.reason,
            "evidence_urls": "|".join(self.evidence_urls),
            "phone": self.contact.phone if self.contact else None,
            "email": self.contact.email if self.contact else None,
            "website": self.contact.website if self.contact else None,
            "city": self.location.city if self.location else None,
            "state": self.location.state if self.location else None,
            "zip": self.location.zip_code if self.location else None,
            "role": self.role,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class StormAlert(BaseModel):
    """Weather alert from NWS."""
    
    alert_id: str
    event_type: str
    severity: str
    headline: str
    description: Optional[str] = None
    affected_zones: list[str] = Field(default_factory=list)
    effective: Optional[datetime] = None
    expires: Optional[datetime] = None
    
    @property
    def is_roofing_relevant(self) -> bool:
        """Check if relevant to roofing damage."""
        keywords = ["hail", "wind", "tornado", "thunderstorm", "hurricane"]
        return any(kw in self.event_type.lower() for kw in keywords)


class PropertyRecord(BaseModel):
    """Property record from open data."""
    
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    year_built: Optional[int] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    last_permit_date: Optional[str] = None
    last_permit_type: Optional[str] = None
    data_source: str
    
    @property
    def roof_age_estimate(self) -> Optional[int]:
        """Estimate roof age (assumes original roof)."""
        if self.year_built:
            return datetime.now().year - self.year_built
        return None
    
    @property
    def priority_score(self) -> int:
        """Score 0-100 based on roof replacement likelihood."""
        score = 50
        
        if self.year_built:
            age = datetime.now().year - self.year_built
            if age > 25:
                score += 30
            elif age > 20:
                score += 20
            elif age > 15:
                score += 10
            elif age < 5:
                score -= 20
        
        if self.last_permit_type and "roof" in self.last_permit_type.lower():
            score -= 30
        
        return max(0, min(100, score))

