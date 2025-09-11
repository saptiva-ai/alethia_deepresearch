import os
import requests
import time
import logging
from typing import Dict, Any, Optional, List
from ports.model_client_port import ModelClientPort
class SaptivaModelAdapter(ModelClientPort):
    def __init__(self):
        self.api_key = os.getenv("SAPTIVA_API_KEY")
        # Endpoint oficial según docs de Saptiva
        self.base_url = "https://api.saptiva.com/v1"
        self.max_retries = 3
        self.retry_delay = 1.0

        if not self.api_key or self.api_key == "pon_tu_api_key_aqui":
            print("Warning: SAPTIVA_API_KEY not set. Using mock responses.")
            self.mock_mode = True
        else:
            self.mock_mode = False

    def generate(self, model: str, prompt: str, **kwargs: Any) -> Dict:
        if self.mock_mode:
            return self._get_mock_response(model, prompt)

        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(model, messages, **kwargs)

    def chat_completion(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
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
                    timeout=30,
                )
                response.raise_for_status()
                api_response = response.json()

                # Manejo robusto de respuesta
                choices = api_response.get("choices", [])
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", "")
                else:
                    # fallback si el formato cambia
                    content = api_response.get("response", "")

                return {"content": content, "raw": api_response}

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt+1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay * (2**attempt))  # exponential backoff
                else:
                    print(f"Error calling Saptiva API: {e}. Falling back to mock response.")
                    return self._get_mock_response(model, str(messages))

    def health_check(self) -> bool:
        """
        Check if the API is reachable and authenticated.
        """
        if self.mock_mode:
            return True
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False


    def _call_real_api(self, model: str, prompt: str, **kwargs: Any) -> Dict:
        """
        Makes the actual API call to Saptiva with retry logic.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                response.raise_for_status()
                api_response = response.json()
                
                # Extract content from the API response
                content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {"content": content}
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise e


    def chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
        """
        Generate a chat completion response.
        """
        # Convert messages to a single prompt for the generate method
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
        
        return self.generate(model, prompt.strip(), **kwargs)
    
    def list_models(self) -> List[str]:
        """
        List available models.
        """
        return ["SAPTIVA_OPS", "SAPTIVA_CORTEX", "SAPTIVA_TURBO"]
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        """
        model_info = {
            "SAPTIVA_OPS": {
                "name": "SAPTIVA_OPS",
                "description": "Optimal model for planning and operational tasks",
                "max_tokens": 4096,
                "context_window": 16384
            },
            "SAPTIVA_CORTEX": {
                "name": "SAPTIVA_CORTEX", 
                "description": "Advanced model for analysis and writing tasks",
                "max_tokens": 4096,
                "context_window": 32768
            },
            "SAPTIVA_TURBO": {
                "name": "SAPTIVA_TURBO",
                "description": "Fast model for quick tasks and research",
                "max_tokens": 2048,
                "context_window": 8192
            }
        }
        return model_info.get(model, {"name": model, "description": "Unknown model"})
    
    def _get_mock_response(self, model: str, prompt: str) -> Dict:
        model_name = model.lower()
        if "planner" in model_name or "ops" in model_name:
            return {
                "content": """
- id: T01
  query: "Historia y evolución de la banca abierta en México"
  sources: ["web"]
- id: T02
  query: "Principales competidores y jugadores en el ecosistema de banca abierta en México"
  sources: ["web"]
- id: T03
  query: "Regulación y marco normativo de la banca abierta en México (Ley Fintech)"
  sources: ["web"]
"""
            }
        elif "writer" in model_name or "cortex" in model_name:
            return {
                "content": "# Reporte de Investigación: Banca Abierta en México\n\n## Introducción\nLa banca abierta en México ha emergido como una fuerza transformadora en el sector financiero... (Este es un reporte mockeado)"
            }
        else:
            return {"content": "Respuesta mockeada."}
