"""
Unit tests for TavilySearchAdapter.
"""
import pytest
import os
from unittest.mock import patch, Mock
from adapters.tavily_search.tavily_client import TavilySearchAdapter
from domain.models.evidence import Evidence, EvidenceSource
from datetime import datetime


@pytest.mark.unit
class TestTavilySearchAdapter:
    """Test cases for TavilySearchAdapter."""

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_init_success(self, mock_tavily_client):
        """Test successful initialization with valid API key."""
        # Arrange
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance

        # Act
        adapter = TavilySearchAdapter()

        # Assert
        assert adapter.api_key == "test_api_key"
        assert adapter.client == mock_client_instance
        mock_tavily_client.assert_called_once_with(api_key="test_api_key")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_api_key(self):
        """Test initialization fails without API key."""
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            TavilySearchAdapter()
        assert "TAVILY_API_KEY environment variable not set" in str(excinfo.value)

    @patch.dict(os.environ, {"TAVILY_API_KEY": "pon_tu_api_key_aqui"})
    def test_init_placeholder_api_key(self):
        """Test initialization fails with placeholder API key."""
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            TavilySearchAdapter()
        assert "TAVILY_API_KEY environment variable not set" in str(excinfo.value)

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_success(self, mock_tavily_client):
        """Test successful web search."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = {
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "content": "Test content 1", "score": 0.95},
                {"title": "Test Result 2", "url": "https://example.com/2", "content": "Test content 2", "score": 0.85},
            ]
        }
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search("test query", max_results=5)

        # Assert
        assert len(results) == 2
        assert all(isinstance(evidence, Evidence) for evidence in results)

        # Check first result
        assert results[0].source.title == "Test Result 1"
        assert results[0].source.url == "https://example.com/1"
        assert results[0].excerpt == "Test content 1"
        assert results[0].score == 0.95

        # Verify API call
        mock_client_instance.search.assert_called_once_with(query="test query", search_depth="advanced", max_results=5)

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_with_custom_depth(self, mock_tavily_client):
        """Test search with custom search depth."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = {"results": []}
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        adapter.search("test query", search_depth="basic")

        # Assert
        mock_client_instance.search.assert_called_once_with(query="test query", search_depth="basic", max_results=10)

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_error_handling(self, mock_tavily_client):
        """Test search error handling."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.side_effect = Exception("API Error")
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search("test query")

        # Assert
        assert results == []

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_news_success(self, mock_tavily_client):
        """Test successful news search."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = {
            "results": [{"title": "News Article 1", "url": "https://news.com/1", "content": "News content 1", "score": 0.9}]
        }
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search_news("test news query", max_results=5, days=7)

        # Assert
        assert len(results) == 1
        assert results[0].source.title == "News Article 1"

        # Verify API call
        mock_client_instance.search.assert_called_once_with(query="test news query", search_depth="advanced", max_results=5, topic="news")

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_news_error_handling(self, mock_tavily_client):
        """Test news search error handling."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.side_effect = Exception("News API Error")
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search_news("test query")

        # Assert
        assert results == []

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_academic_success(self, mock_tavily_client):
        """Test successful academic search."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = {
            "results": [{"title": "Academic Paper 1", "url": "https://academic.com/1", "content": "Academic content 1", "score": 0.88}]
        }
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search_academic("research query")

        # Assert
        assert len(results) == 1
        assert results[0].source.title == "Academic Paper 1"

        # Verify API call includes academic sites in query
        mock_client_instance.search.assert_called_once_with(
            query="research query site:arxiv.org OR site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov", search_depth="advanced", max_results=10
        )

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_search_academic_error_handling(self, mock_tavily_client):
        """Test academic search error handling."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.search.side_effect = Exception("Academic API Error")
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act
        results = adapter.search_academic("research query")

        # Assert
        assert results == []

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_convert_to_evidence(self, mock_tavily_client):
        """Test conversion of search results to Evidence objects."""
        # Arrange
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        search_results = [
            {"title": "Test Title", "url": "https://example.com", "content": "Test content excerpt", "score": 0.92},
            {"title": "Another Title", "url": "https://another.com", "content": "Another content excerpt", "score": 0.78},
        ]

        # Act
        evidence_list = adapter._convert_to_evidence(search_results, "original query")

        # Assert
        assert len(evidence_list) == 2

        # Check first evidence
        ev1 = evidence_list[0]
        assert isinstance(ev1, Evidence)
        assert ev1.source.title == "Test Title"
        assert ev1.source.url == "https://example.com"
        assert ev1.excerpt == "Test content excerpt"
        assert ev1.score == 0.92
        assert ev1.tool_call_id.startswith("tavily:search:tavily_")
        assert isinstance(ev1.source.fetched_at, datetime)

        # Hash is not set by Tavily adapter
        assert ev1.hash is None

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_convert_to_evidence_missing_fields(self, mock_tavily_client):
        """Test conversion handles missing fields gracefully."""
        # Arrange
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        search_results = [
            {
                "url": "https://example.com",
                "content": "Content without title",
                # Missing title and score
            }
        ]

        # Act
        evidence_list = adapter._convert_to_evidence(search_results, "test query")

        # Assert
        assert len(evidence_list) == 1
        ev = evidence_list[0]
        assert ev.source.title == ""  # Empty title from result
        assert ev.score == 0.8  # Default score
        assert ev.source.url == "https://example.com"
        assert ev.excerpt == "Content without title"

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_api_key"})
    @patch("adapters.tavily_search.tavily_client.TavilyClient")
    def test_evidence_id_generation(self, mock_tavily_client):
        """Test evidence ID generation method."""
        # Arrange
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance

        adapter = TavilySearchAdapter()

        # Act - Test evidence ID generation using the actual implementation pattern
        evidence_list = adapter._convert_to_evidence([{"title": "Test", "url": "https://example.com", "content": "test", "score": 0.9}], "test query")

        # Assert
        assert len(evidence_list) == 1
        evidence_id = evidence_list[0].id
        assert evidence_id.startswith("tavily_")
        assert len(evidence_id) == 15  # "tavily_" + 8 char MD5 hash
