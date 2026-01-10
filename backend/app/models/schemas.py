from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    INTAKE = "intake"
    CODER = "coder"
    REBUTTAL = "rebuttal"
    SCRIBE = "scribe"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class Urgency(str, Enum):
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"


class ClinicalEntity(BaseModel):
    type: str
    value: str
    unit: Optional[str] = None


class DenialExtraction(BaseModel):
    document_type: str
    patient_name: Optional[str] = None
    account_number: Optional[str] = None
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    appeal_deadline_days: Optional[int] = None
    peer_to_peer_available: bool = False
    key_missing_criteria: List[str] = []
    urgency: Urgency = Urgency.P2_MEDIUM


class RebuttalOutput(BaseModel):
    letter: str
    talking_points: List[str]
    confidence_score: float


class AgentUpdate(BaseModel):
    agent: AgentType
    status: AgentStatus
    message: str
    data: Optional[dict] = None
    timestamp: datetime = datetime.now()


class CaseCreate(BaseModel):
    patient_name: str
    account_number: Optional[str] = None


class CaseResponse(BaseModel):
    case_id: str
    patient_name: str
    status: str
    denial_detected: bool = False
    denial_reason: Optional[str] = None
    peer_to_peer_deadline: Optional[str] = None
    rebuttal_letter: Optional[str] = None
    talking_points: List[str] = []
    agent_logs: List[AgentUpdate] = []
