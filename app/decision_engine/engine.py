import structlog
from typing import Dict, Any
from jinja2 import Template
from app.llm_gateway.client import llm_gateway
from app.core.utils import extract_json

logger = structlog.get_logger()

class DecisionEngine:
    def __init__(self):
        with open("prompts/decision_engine.jinja", "r") as f:
            self.template = Template(f.read())

    async def decide(
        self, 
        input_data: Dict[str, Any], 
        evidence_assessment: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = self.template.render(
            input_data=input_data,
            evidence_assessment=evidence_assessment,
            constraints=constraints
        )
        
        logger.info("decision_engine_start")
        
        # 1. Primary Model Call
        primary_result = await llm_gateway.get_structured_decision(
            prompt=prompt,
            system_prompt="You are a safety-first Decision Engine.",
            model="claude-3-5-sonnet-20240620"
        )
        
        primary_decision = extract_json(primary_result.get("raw_response", ""))
        
        # 2. Safety Shadow Model Call (Ensemble/Voter)
        # We use a smaller, faster model (Haiku) as a shadow validator.
        shadow_result = await llm_gateway.get_structured_decision(
            prompt=prompt,
            system_prompt="You are a safety shadow validator. Your goal is to find reasons NOT to act.",
            model="claude-3-5-haiku-20241022"
        )
        shadow_decision = extract_json(shadow_result.get("raw_response", ""))

        if not primary_decision:
            return self._fail_abstain(primary_result, "Primary model failed to produce structured JSON.")

        # Aggregate Costs
        total_tokens = (
            primary_result.get("input_tokens", 0) + primary_result.get("output_tokens", 0) +
            shadow_result.get("input_tokens", 0) + shadow_result.get("output_tokens", 0)
        )
        total_latency = primary_result.get("latency_ms", 0) + shadow_result.get("latency_ms", 0)

        # 3. Asymmetric Safety Shadow: Unilateral veto on high-risk actions
        if primary_decision.get("decision") == "ACT":
            if not shadow_decision or shadow_decision.get("decision") != "ACT":
                logger.warning("shadow_veto_triggered", primary=primary_decision.get("decision"), shadow=shadow_decision.get("decision") if shadow_decision else "FAIL")
                primary_decision["decision"] = "ABSTAIN"
                primary_decision["rationale"] += " (Overridden by Asymmetric Safety Shadow: Unilateral veto triggered.)"
                primary_decision["risk_factors"].append("shadow_veto")

        primary_decision["cost_estimate"] = {
            "tokens": total_tokens,
            "latency_ms": total_latency
        }
        
        return primary_decision

    def _fail_abstain(self, result: Dict[str, Any], message: str) -> Dict[str, Any]:
        return {
            "decision": "ABSTAIN",
            "confidence": 0.0,
            "rationale": message,
            "cost_estimate": {
                "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
                "latency_ms": result.get("latency_ms", 0)
            }
        }

decision_engine = DecisionEngine()
