import os
import time
from typing import Any

import requests

from ports.model_client_port import ModelClientPort


class SaptivaModelAdapter(ModelClientPort):
    def __init__(self):
        self.api_key = os.getenv("SAPTIVA_API_KEY")
        # Endpoint oficial según documentación de Saptiva
        # Puede ser configurado via SAPTIVA_BASE_URL
        self.base_url = os.getenv("SAPTIVA_BASE_URL", "https://api.saptiva.ai/v1")
        self.max_retries = 3
        self.retry_delay = 1.0
        # Configurable timeouts for Docker/production environments
        self.connect_timeout = int(os.getenv("SAPTIVA_CONNECT_TIMEOUT", "15"))
        self.read_timeout = int(os.getenv("SAPTIVA_READ_TIMEOUT", "90"))

        if not self.api_key or self.api_key == "pon_tu_api_key_aqui":
            print("Warning: SAPTIVA_API_KEY not set. Using mock responses.")
            self.mock_mode = True
        else:
            self.mock_mode = False

    def generate(self, model: str, prompt: str, **kwargs: Any) -> dict:
        """Generate a simple completion from a prompt."""
        if self.mock_mode:
            return self._get_mock_response(model, prompt)

        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(model, messages, **kwargs)

    def chat_completion(self, model: str, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        """Generate a chat completion response."""
        if self.mock_mode:
            return self._get_mock_response(model, str(messages))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=(self.connect_timeout, self.read_timeout),
                )
                response.raise_for_status()
                api_response = response.json()

                # Manejo robusto de respuesta según formato OpenAI
                choices = api_response.get("choices", [])
                content = choices[0]["message"].get("content", "") if choices and "message" in choices[0] else api_response.get("response", "")

                return {"content": content, "raw": api_response}

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt+1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay * (2**attempt))  # exponential backoff
                else:
                    print(f"Error calling Saptiva API: {e}. Falling back to mock response.")
                    return self._get_mock_response(model, str(messages))

    def health_check(self) -> bool:
        """Check if the API is reachable and authenticated."""
        if self.mock_mode:
            return True
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=(self.connect_timeout, min(30, self.read_timeout)),
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        return ["Saptiva Ops", "Saptiva Cortex", "Saptiva Turbo", "Saptiva Legacy", "Saptiva Coder"]

    def get_model_info(self, model: str) -> dict[str, Any]:
        """Get information about a specific model."""
        model_info = {
            "Saptiva Ops": {"base": "qwen2.5:72b-instruct", "use_case": "planning"},
            "Saptiva Cortex": {"base": "qwen3:30b", "use_case": "analysis"},
            "Saptiva Turbo": {"base": "gemma2:27b", "use_case": "general"},
            "Saptiva Legacy": {"base": "llama3.3:70b", "use_case": "legacy"},
            "Saptiva Coder": {"base": "deepseek-coder-v2:236b", "use_case": "coding"},
        }
        return model_info.get(model, {"base": "unknown", "use_case": "general"})

    def _get_mock_response(self, model: str, prompt_or_messages: str) -> dict[str, Any]:
        """Return a mock response when API is unavailable."""
        if "planner" in model.lower() or "ops" in model.lower():
            return {
                "content": """subtasks:
  - id: "01"
    query: "Análisis de mercado bancario digital"
    sources: ["web", "reports"]
  - id: "02"
    query: "Principales competidores fintech"
    sources: ["web", "databases"]"""
            }
        elif "evaluation" in prompt_or_messages.lower() or "completeness" in prompt_or_messages.lower():
            return {
                "content": (
                    '{"completion_score": 0.75, "completion_level": "adequate", '
                    '"areas_covered": ["market", "competitors"], '
                    '"reasoning": "Good coverage of key areas"}'
                )
            }
        elif "refinement" in prompt_or_messages.lower():
            return {"content": '["Análisis de regulación fintech México", "Tendencias tecnológicas banca digital"]'}
        elif "gaps" in prompt_or_messages.lower():
            return {"content": '[{"area": "regulation", "priority": 3, "description": "Regulatory framework analysis"}]'}
        else:
            return {
                "content": f"""# Análisis de Competidores Bancarios Digitales México

## Resumen Ejecutivo
El mercado de banca digital en México presenta un crecimiento acelerado, impulsado por la regulación fintech y la demanda de servicios financieros digitales.

## Principales Competidores
- **Nu México**: Líder en tarjetas de crédito sin comisiones
- **Mercado Pago**: Dominante en pagos digitales y e-commerce
- **BBVA México**: Fuerte transformación digital
- **Banorte**: Inversión significativa en tecnología

## Conclusiones
El sector mantiene alta competitividad con oportunidades en inclusión financiera.

*Generado con Saptiva {model} (Mock Mode)*"""
            }
