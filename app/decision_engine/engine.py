import structlog
from typing import Dict, Any
from jinja2 import Template
from app.llm_gateway.client import llm_gateway
from app.core.utils import extract_json
from app.core.exceptions import ModelTimeoutError

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
        
        policy_config = constraints.get("policy") or {}
        shadow_config = policy_config.get("asymmetric_shadow", {})
        conf_config = policy_config.get("confidence_thresholds", {})
        
        primary_model = shadow_config.get("primary_model", "claude-3-5-sonnet-20240620")
        shadow_model = shadow_config.get("shadow_model", "claude-3-5-haiku-20241022")
        shadow_enabled = shadow_config.get("enabled", True)
        
        act_min = conf_config.get("act_minimum", 0.8)

        try:
            # 1. Primary Model Call
            primary_result = await llm_gateway.get_structured_decision(
                prompt=prompt,
                system_prompt="You are a safety-first Decision Engine.",
                model=primary_model
            )
            
            primary_decision = extract_json(primary_result.get("raw_response", ""))
            if not primary_decision:
                return self._fail_abstain(primary_result, "Primary model failed to produce structured JSON.")

            # 2. Confidence Threshold Check
            confidence = primary_decision.get("confidence", 0.0)
            if primary_decision.get("decision") == "ACT" and confidence < act_min:
                logger.warning("confidence_below_threshold", confidence=confidence, threshold=act_min)
                primary_decision["decision"] = "ABSTAIN"
                primary_decision["rationale"] += f" (Downgraded: Confidence {confidence} below policy threshold {act_min}.)"
                primary_decision["risk_factors"].append("low_confidence_override")

            # 3. Asymmetric Safety Shadow Model Call
            total_tokens = primary_result.get("input_tokens", 0) + primary_result.get("output_tokens", 0)
            total_latency = primary_result.get("latency_ms", 0)

            if shadow_enabled:
                shadow_result = await llm_gateway.get_structured_decision(
                    prompt=prompt,
                    system_prompt="You are a safety shadow validator. Your goal is to find reasons NOT to act.",
                    model=shadow_model
                )
                shadow_decision = extract_json(shadow_result.get("raw_response", ""))
                
                total_tokens += shadow_result.get("input_tokens", 0) + shadow_result.get("output_tokens", 0)
                total_latency += shadow_result.get("latency_ms", 0)

                # Shadow Veto Logic
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

        except ModelTimeoutError as e:
            logger.error("decision_engine_timeout", error=str(e))
            return {
                "decision": "ABSTAIN",
                "confidence": 0.0,
                "risk_factors": ["model_timeout"],
                "missing_information": [],
                "failure_modes": ["system_timeout"],
                "cost_estimate": {"tokens": 0, "latency_ms": 0},
                "rationale": f"System timeout / LLM failure: {str(e)}"
            }

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
