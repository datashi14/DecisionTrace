from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DecisionOutcome(str, Enum):
    ACT = "ACT"
    ASK = "ASK"
    ABSTAIN = "ABSTAIN"

class CostEstimate(BaseModel):
    tokens: int = 0
    latency_ms: int = 0

class DecisionTraceResponse(BaseModel):
    decision: DecisionOutcome
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    cost_estimate: CostEstimate = Field(default_factory=CostEstimate)
    trace_id: str
    rationale: str

class DecisionRequest(BaseModel):
    context: Dict[str, Any]
    signals: Dict[str, Any]
    policy_id: Optional[str] = "default"
