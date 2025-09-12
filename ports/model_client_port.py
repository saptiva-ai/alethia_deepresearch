from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ModelClientPort(ABC):
    """Port for AI model client operations."""

    @abstractmethod
    def generate(self, model: str, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate a response from an AI model.

        Args:
            model: Model identifier (e.g., "SAPTIVA_OPS", "SAPTIVA_CORTEX")
            prompt: Input prompt text
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Dict containing the response with at least a "content" field
        """
        pass

    @abstractmethod
    def chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
        """
        Generate a chat completion response.

        Args:
            model: Model identifier
            messages: List of message dicts with "role" and "content" keys
            **kwargs: Additional parameters

        Returns:
            Dict containing the response
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """
        List available models.

        Returns:
            List of model identifiers
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the model client is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model: Model identifier

        Returns:
            Dict containing model metadata
        """
        pass
