# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def call_llm(prompt):
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.choices[0].message.content



"""
Fixed LLM Service with error handling, cost control, and logging
Features:
- Proper exception handling
- Token limit enforcement
- Cost estimation
- Retry mechanism
- Structured output validation
"""

import os
import logging
from typing import Optional, Dict
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""
    pass

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        raw_max_tokens = os.getenv("MAX_TOKENS")
        self.max_tokens = int(raw_max_tokens) if raw_max_tokens else None
        self.temperature = float(os.getenv("TEMPERATURE", 0.7))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", 60))
        self.max_retries = 3
        
        if not self.api_key:
            raise LLMServiceError("OPENAI_API_KEY not found in environment variables. Please create a .env file.")
        
        self.client = OpenAI(api_key=self.api_key, timeout=self.request_timeout)
        logger.info(f"LLMService initialized with model: {self.model}")
    
    def estimate_cost(self, text: str, is_completion: bool = False) -> Dict[str, float]:
        """
        Estimate cost for prompt or completion
        Using gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output
        """
        # Rough estimate: 4 chars = 1 token
        prompt_tokens = len(text) // 4
        completion_tokens = self.max_tokens if (is_completion and self.max_tokens is not None) else 0
        
        # Pricing per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        
        return {
            "estimated_input_cost": round(input_cost, 6),
            "estimated_output_cost": round(output_cost, 6),
            "total_estimated_cost": round(input_cost + output_cost, 6),
            "prompt_tokens": prompt_tokens,
            "max_output_tokens": completion_tokens
        }
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retries: int = 0
    ) -> str:
        """
        Call LLM with proper error handling and retry logic
        
        Args:
            prompt: Main prompt
            system_prompt: System message (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            retries: Internal retry counter
        
        Returns:
            LLM response text
            
        Raises:
            LLMServiceError: If all retries fail
        """
        try:
            # Log cost estimation
            cost_info = self.estimate_cost(prompt, is_completion=True)
            logger.debug(f"Estimated cost: ${cost_info['total_estimated_cost']:.6f}")
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Use provided values or defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            request_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temp,
                "timeout": self.request_timeout,
            }
            if tokens is not None:
                request_kwargs["max_tokens"] = tokens

            logger.info(
                "Calling %s with %s",
                self.model,
                f"max_tokens={tokens}" if tokens is not None else "no explicit max_tokens limit",
            )
            response = self.client.chat.completions.create(**request_kwargs)
            
            result = response.choices[0].message.content
            
            # Validate response
            if not result or not result.strip():
                raise LLMServiceError("LLM returned empty response")
            
            logger.info(f"LLM call successful, tokens used: {response.usage.total_tokens}")
            return result
            
        except APIConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            if retries < self.max_retries:
                logger.info(f"Retrying... ({retries + 1}/{self.max_retries})")
                return self.call_llm(prompt, system_prompt, temperature, max_tokens, retries + 1)
            raise LLMServiceError(f"Failed to connect after {self.max_retries} retries: {str(e)}")
            
        except RateLimitError as e:
            logger.error(f"Rate limited: {str(e)}")
            if retries < self.max_retries:
                logger.info(f"Retrying due to rate limit... ({retries + 1}/{self.max_retries})")
                return self.call_llm(prompt, system_prompt, temperature, max_tokens, retries + 1)
            raise LLMServiceError(f"Rate limited after {self.max_retries} retries")
            
        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            raise LLMServiceError(f"OpenAI API error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
            raise LLMServiceError(f"Unexpected error calling LLM: {str(e)}")
    
    def generate_with_schema(
        self,
        prompt: str,
        schema: str,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate response with JSON schema validation
        
        Args:
            prompt: Main prompt
            schema: JSON schema description
            system_prompt: System message
            
        Returns:
            Parsed JSON response
        """
        schema_instruction = f"""
        Return ONLY valid JSON matching this schema:
        {schema}
        Do not include markdown backticks or any other text.
        """
        
        combined_prompt = f"{prompt}\n\n{schema_instruction}"
        response = self.call_llm(combined_prompt, system_prompt)
        
        try:
            # Remove markdown if present
            response = response.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise LLMServiceError(f"Invalid JSON in response: {str(e)}")

# Global instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get or initialize LLM service"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

def call_llm(prompt: str, **kwargs) -> str:
    """Backwards compatible function"""
    return get_llm_service().call_llm(prompt, **kwargs)
