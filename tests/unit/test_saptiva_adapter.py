"""
Unit tests for SaptivaModelAdapter.
"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
import requests
from adapters.saptiva_model.saptiva_client import SaptivaModelAdapter


@pytest.mark.unit
class TestSaptivaModelAdapter:
    """Test cases for SaptivaModelAdapter."""

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        # Act
        adapter = SaptivaModelAdapter()

        # Assert
        assert adapter.api_key == "test_api_key"
        assert adapter.base_url == "https://api.saptiva.com/v1"
        assert adapter.max_retries == 3
        assert adapter.retry_delay == 1.0
        assert adapter.connect_timeout == 15  # default value
        assert adapter.read_timeout == 90  # default value
        assert adapter.mock_mode is False

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_api_key(self):
        """Test initialization without API key (mock mode)."""
        # Act
        adapter = SaptivaModelAdapter()

        # Assert
        assert adapter.mock_mode is True

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "pon_tu_api_key_aqui"})
    def test_init_with_placeholder_api_key(self):
        """Test initialization with placeholder API key (mock mode)."""
        # Act
        adapter = SaptivaModelAdapter()

        # Assert
        assert adapter.mock_mode is True

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_key", "SAPTIVA_CONNECT_TIMEOUT": "20", "SAPTIVA_READ_TIMEOUT": "120"})
    def test_init_with_custom_timeouts(self):
        """Test initialization with custom timeout values."""
        # Act
        adapter = SaptivaModelAdapter()

        # Assert
        assert adapter.connect_timeout == 20
        assert adapter.read_timeout == 120

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    def test_generate_mock_mode(self):
        """Test generate method in mock mode."""
        # Arrange
        adapter = SaptivaModelAdapter()
        adapter.mock_mode = True

        # Act
        result = adapter.generate("Saptiva Cortex", "Test prompt")

        # Assert
        assert isinstance(result, dict)
        assert "content" in result
        # Mock response doesn't include model field

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    def test_generate_api_mode_success(self, mock_post):
        """Test generate method with successful API call."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}], "model": "Saptiva Cortex", "usage": {"total_tokens": 100}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        adapter = SaptivaModelAdapter()

        # Act
        result = adapter.generate("Saptiva Cortex", "Test prompt", max_tokens=500, temperature=0.5)

        # Assert
        assert result["content"] == "Test response"
        assert "raw" in result
        assert result["raw"]["model"] == "Saptiva Cortex"
        assert result["raw"]["usage"]["total_tokens"] == 100

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "chat/completions" in call_args[0][0]
        assert call_args[1]["json"]["max_tokens"] == 500
        assert call_args[1]["json"]["temperature"] == 0.5

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    def test_chat_completion_success(self, mock_post):
        """Test chat_completion method with successful API call."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Chat response"}}], "model": "Saptiva Cortex", "usage": {"total_tokens": 150}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        adapter = SaptivaModelAdapter()
        messages = [{"role": "user", "content": "Hello"}]

        # Act
        result = adapter.chat_completion("Saptiva Cortex", messages)

        # Assert
        assert result["content"] == "Chat response"
        assert "raw" in result
        assert result["raw"]["model"] == "Saptiva Cortex"

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    def test_api_call_with_retries_success_on_second_try(self, mock_post):
        """Test API call that succeeds on retry."""
        # Arrange
        # First call fails, second call succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")

        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success on retry"}}],
            "model": "Saptiva Cortex",
            "usage": {"total_tokens": 75},
        }
        mock_response_success.raise_for_status.return_value = None

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        adapter = SaptivaModelAdapter()

        # Act
        result = adapter.generate("Saptiva Cortex", "Test prompt")

        # Assert
        assert result["content"] == "Success on retry"
        assert mock_post.call_count == 2

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    @patch("adapters.saptiva_model.saptiva_client.time.sleep")  # Mock sleep to speed up test
    def test_api_call_max_retries_exceeded(self, mock_sleep, mock_post):
        """Test API call that fails after max retries."""
        # Arrange
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Persistent API Error")
        mock_post.return_value = mock_response_fail

        adapter = SaptivaModelAdapter()

        # Act
        result = adapter.generate("Saptiva Cortex", "Test prompt")

        # Assert - Should fallback to mock response
        assert "content" in result
        # Mock fallback doesn't include model field
        assert mock_post.call_count == 3  # max_retries
        assert mock_sleep.call_count == 2  # sleep called between retries

    def test_get_mock_response_structure(self):
        """Test mock response structure."""
        adapter = SaptivaModelAdapter()

        # Act
        result = adapter._get_mock_response("Test Model", "Test prompt")

        # Assert
        assert isinstance(result, dict)
        assert "content" in result
        # Mock response doesn't include model or usage fields

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    def test_get_model_info(self):
        """Test get_model_info method."""
        adapter = SaptivaModelAdapter()

        # Act
        info = adapter.get_model_info("Saptiva Cortex")

        # Assert
        assert isinstance(info, dict)
        assert "base" in info
        assert "use_case" in info
        assert info["use_case"] == "analysis"

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    def test_api_call_timeout_configuration(self, mock_post):
        """Test that API calls use configured timeouts."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}], "model": "Saptiva Cortex", "usage": {"total_tokens": 50}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        adapter = SaptivaModelAdapter()

        # Act
        adapter.generate("Saptiva Cortex", "Test prompt")

        # Assert
        call_args = mock_post.call_args
        timeout_arg = call_args[1]["timeout"]
        assert timeout_arg == (15, 90)  # (connect_timeout, read_timeout)

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    @patch("adapters.saptiva_model.saptiva_client.requests.post")
    def test_api_call_headers_configuration(self, mock_post):
        """Test that API calls use correct headers."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}], "model": "Saptiva Cortex", "usage": {"total_tokens": 50}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        adapter = SaptivaModelAdapter()

        # Act
        adapter.generate("Saptiva Cortex", "Test prompt")

        # Assert
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"

    @patch.dict(os.environ, {"SAPTIVA_API_KEY": "test_api_key"})
    def test_chat_completion_mock_mode(self):
        """Test chat_completion in mock mode."""
        # Arrange
        adapter = SaptivaModelAdapter()
        adapter.mock_mode = True
        messages = [{"role": "user", "content": "Test message"}]

        # Act
        result = adapter.chat_completion("Saptiva Cortex", messages)

        # Assert
        assert isinstance(result, dict)
        assert "content" in result
        # Mock response doesn't include model field
