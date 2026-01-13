import uuid
import structlog
from fastapi import APIRouter, HTTPException
from app.core.schemas import DecisionRequest, DecisionTraceResponse
from app.evidence_planner.planner import evidence_planner
from app.decision_engine.engine import decision_engine
from app.trace_store.store import trace_store
from app.core.policies import policy_manager
from app.core.hard_constraints import hard_constraints

router = APIRouter()
logger = structlog.get_logger()

@router.post("/decide", response_model=DecisionTraceResponse)
async def create_decision(request: DecisionRequest):
    """
    Core entrypoint for the DecisionTrace pipeline.
    """
    trace_id = str(uuid.uuid4())
    
    # Resolve policy
    policy_id = request.policy_id or "default"
    policy = policy_manager.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    logger.info("decision_requested", trace_id=trace_id, policy_id=policy_id)

    # 0. Deterministic Hard Constraints (Shadow Policy)
    is_safe, constraint_rationale = hard_constraints.check(request.context, request.signals)
    if not is_safe:
        logger.warning("hard_constraint_violated", trace_id=trace_id, rationale=constraint_rationale)
        return {
            "decision": "ABSTAIN",
            "confidence": 1.0,
            "risk_factors": ["hard_constraint_violation"],
            "missing_information": [],
            "failure_modes": ["deterministic_block"],
            "cost_estimate": {"tokens": 0, "latency_ms": 0},
            "trace_id": trace_id,
            "rationale": constraint_rationale
        }

    # 1. Evidence Planning
    evidence_result = await evidence_planner.plan(
        input_data={"context": request.context, "signals": request.signals},
        constraints={"policy": policy}
    )
    
    # 2. Decision Making
    decision_result = await decision_engine.decide(
        input_data={"context": request.context, "signals": request.signals},
        evidence_assessment=evidence_result,
        constraints={"policy": policy}
    )

    # 3. Trace Logging (Immutable)
    try:
        await trace_store.log_trace(trace_id, {
            "request": request.model_dump(),
            "evidence_planning": evidence_result,
            "decision": decision_result
        })
    except Exception as e:
        logger.error("trace_logging_failed", error=str(e))
        if decision_result.get("decision") == "ACT":
             decision_result["decision"] = "ABSTAIN"
             decision_result["rationale"] += " (Trace logging failed, action revoked for safety)"

    # Include trace_id in response
    decision_result["trace_id"] = trace_id
    
    return decision_result
