"""
Unit tests for ResearchService.
"""
import pytest
from unittest.mock import patch, Mock
from domain.services.research_svc import ResearchService
from domain.models.plan import ResearchPlan, ResearchSubTask
from domain.models.evidence import Evidence, EvidenceSource
from datetime import datetime


@pytest.mark.unit
class TestResearchService:
    """Test cases for ResearchService."""

    @patch("domain.services.research_svc.TavilySearchAdapter")
    @patch("domain.services.research_svc.WeaviateVectorAdapter")
    def test_init_success(self, mock_vector, mock_search):
        """Test ResearchService initialization."""
        # Arrange
        mock_search_instance = Mock()
        mock_search.return_value = mock_search_instance

        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = True
        mock_vector.return_value = mock_vector_instance

        # Act
        service = ResearchService()

        # Assert
        assert service.search_enabled is True
        assert service.vector_store is not None
        mock_vector_instance.health_check.assert_called_once()

    @patch("domain.services.research_svc.TavilySearchAdapter")
    @patch("domain.services.research_svc.WeaviateVectorAdapter")
    def test_init_search_disabled(self, mock_vector, mock_search):
        """Test ResearchService initialization with search disabled."""
        # Arrange
        mock_search.side_effect = ValueError("API key missing")

        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = False
        mock_vector.return_value = mock_vector_instance

        # Act
        service = ResearchService()

        # Assert
        assert service.search_enabled is False

    @patch("domain.services.research_svc.TavilySearchAdapter")
    @patch("domain.services.research_svc.WeaviateVectorAdapter")
    def test_execute_plan_success(self, mock_vector, mock_search, sample_research_plan):
        """Test successful plan execution."""
        # Arrange
        mock_search_instance = Mock()
        mock_evidence = Evidence(
            id="test_evidence",
            source=EvidenceSource(url="https://example.com", title="Test Result", fetched_at=datetime.utcnow()),
            excerpt="Test content",
            hash="test_hash",
            tool_call_id="test_call",
            score=0.9,
            tags=["test"],
        )
        mock_search_instance.search.return_value = [mock_evidence]
        mock_search.return_value = mock_search_instance

        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = True
        mock_vector_instance.store_evidence.return_value = True
        mock_vector.return_value = mock_vector_instance

        service = ResearchService()

        # Act
        result = service.execute_plan(sample_research_plan)

        # Assert
        assert len(result) == 2  # Two tasks with web sources
        assert all(isinstance(evidence, Evidence) for evidence in result)
        mock_vector_instance.create_collection.assert_called_once()
        mock_vector_instance.store_evidence.assert_called()

    @patch("domain.services.research_svc.TavilySearchAdapter")
    @patch("domain.services.research_svc.WeaviateVectorAdapter")
    def test_execute_plan_search_disabled(self, mock_vector, mock_search, sample_research_plan):
        """Test plan execution when search is disabled."""
        # Arrange
        mock_search.side_effect = ValueError("API key missing")
        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = True
        mock_vector.return_value = mock_vector_instance

        service = ResearchService()

        # Act
        result = service.execute_plan(sample_research_plan)

        # Assert
        assert result == []
        assert service.search_enabled is False

    @patch("domain.services.research_svc.TavilySearchAdapter")
    @patch("domain.services.research_svc.WeaviateVectorAdapter")
    def test_search_existing_evidence(self, mock_vector, mock_search):
        """Test searching existing evidence."""
        # Arrange
        mock_search_instance = Mock()
        mock_search.return_value = mock_search_instance

        mock_evidence = Evidence(
            id="existing_evidence",
            source=EvidenceSource(url="https://example.com/existing", title="Existing Result", fetched_at=datetime.utcnow()),
            excerpt="Existing content",
            hash="existing_hash",
            tool_call_id="existing_call",
            score=0.8,
            tags=["existing"],
        )

        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = True
        mock_vector_instance.search_similar.return_value = [mock_evidence]
        mock_vector.return_value = mock_vector_instance

        service = ResearchService()

        # Act
        result = service.search_existing_evidence("test query", "test_collection", limit=3)

        # Assert
        assert len(result) == 1
        assert result[0].id == "existing_evidence"
        mock_vector_instance.search_similar.assert_called_once_with("test query", "test_collection", 3)

    def test_generate_collection_id(self):
        """Test collection ID generation."""
        service = ResearchService.__new__(ResearchService)  # Create instance without __init__

        # Act
        result = service._generate_collection_id("test query")

        # Assert
        assert isinstance(result, str)
        assert len(result) == 8  # MD5 hash truncated to 8 chars

        # Same query should generate same ID
        result2 = service._generate_collection_id("test query")
        assert result == result2

    def test_generate_hash(self):
        """Test content hash generation."""
        service = ResearchService.__new__(ResearchService)  # Create instance without __init__

        # Act
        result = service._generate_hash("test content")

        # Assert
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hash is 64 chars

        # Same content should generate same hash
        result2 = service._generate_hash("test content")
        assert result == result2

        # Different content should generate different hash
        result3 = service._generate_hash("different content")
        assert result != result3
