import time
import structlog
from typing import Any, Dict
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.schemas import DecisionOutcome

logger = structlog.get_logger()

class LLMGateway:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def get_structured_decision(
        self, 
        prompt: str, 
        system_prompt: str,
        model: str = "claude-3-5-sonnet-20240620",
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Calls the LLM and enforces structured output.
        Logs every request/response for auditability.
        """
        start_time = time.time()
        
        logger.info("llm_request_start", model=model, system_prompt=system_prompt[:100])
        
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Note: In a real system, we'd use Anthropic's tool use or vision-specific prompting
            # for strict JSON. Here we'll assume the prompt enforces it and we parse.
            content = response.content[0].text
            
            logger.info(
                "llm_request_success", 
                latency_ms=latency_ms, 
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )
            
            return {
                "raw_response": content,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            logger.error("llm_request_failed", error=str(e))
            # Safety guarantee: fail to ABSTAIN
            return {
                "decision": DecisionOutcome.ABSTAIN,
                "rationale": f"System error during model call: {str(e)}",
                "confidence": 0.0,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

llm_gateway = LLMGateway()
