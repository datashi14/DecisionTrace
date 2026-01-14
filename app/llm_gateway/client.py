import time
import structlog
from typing import Any, Dict
from anthropic import AsyncAnthropic
from app.core.config import settings
import anthropic
from app.core.exceptions import ModelTimeoutError
from app.observability.metrics import tokens_consumed_total, llm_latency_seconds

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
                timeout=10.0  # Set explicit timeout
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.content[0].text
            
            logger.info(
                "llm_request_success", 
                latency_ms=latency_ms, 
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )
            
            # Record Metrics
            tokens_consumed_total.labels(model=model, type="input").inc(response.usage.input_tokens)
            tokens_consumed_total.labels(model=model, type="output").inc(response.usage.output_tokens)
            llm_latency_seconds.labels(model=model).observe(latency_ms / 1000.0)

            return {
                "raw_response": content,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": latency_ms
            }
            
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            logger.error("llm_request_timeout", error=str(e))
            raise ModelTimeoutError(f"LLM provider timeout or connection issue: {str(e)}")
        except Exception as e:
            logger.error("llm_request_failed", error=str(e))
            raise ModelTimeoutError(f"Unexpected LLM error: {str(e)}")

llm_gateway = LLMGateway()
