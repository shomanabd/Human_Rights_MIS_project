from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from bson import ObjectId

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class VictimType(str, Enum):
    VICTIM = "victim"
    WITNESS = "witness"
    BOTH = "both"

class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    secure_messaging: Optional[str] = None
    preferred_contact: Optional[str] = None

class Demographics(BaseModel):
    gender: Optional[str] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    occupation: Optional[str] = None

class RiskAssessment(BaseModel):
    level: RiskLevel
    threats: List[str] = []
    protection_needed: bool = False
    notes: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None

class SupportService(BaseModel):
    type: str  # legal, medical, psychological, social
    provider: str
    status: str  # active, inactive, completed
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None

class VictimCreate(BaseModel):
    type: VictimType
    anonymous: bool = False
    pseudonym: Optional[str] = None
    demographics: Optional[Demographics] = None
    contact_info: Optional[ContactInfo] = None
    risk_assessment: RiskAssessment
    support_services: List[SupportService] = []
    notes: Optional[str] = None

class VictimUpdate(BaseModel):
    type: Optional[VictimType] = None
    anonymous: Optional[bool] = None
    pseudonym: Optional[str] = None
    demographics: Optional[Demographics] = None
    contact_info: Optional[ContactInfo] = None
    risk_assessment: Optional[RiskAssessment] = None
    support_services: Optional[List[SupportService]] = None
    notes: Optional[str] = None

class VictimResponse(BaseModel):
    id: str = Field(alias="_id")
    type: VictimType
    anonymous: bool
    pseudonym: Optional[str] = None
    demographics: Optional[Demographics] = None
    contact_info: Optional[ContactInfo] = None
    cases_involved: List[str] = []
    risk_assessment: RiskAssessment
    support_services: List[SupportService] = []
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True