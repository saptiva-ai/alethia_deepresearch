"""
Tests for the WriterService.
"""
from unittest.mock import MagicMock, patch

from domain.services.writer_svc import WriterService
from domain.models.evidence import Evidence, EvidenceSource


@patch("domain.services.writer_svc.SaptivaModelAdapter")
@patch("domain.services.writer_svc.WeaviateVectorAdapter")
def test_write_report(mock_weaviate_adapter, mock_saptiva_adapter):
    """Test the write_report method."""
    # Arrange
    mock_saptiva_adapter.return_value.generate.return_value = {"content": "# Test Report"}
    mock_weaviate_adapter.return_value.search_similar.return_value = []

    writer_service = WriterService()
    writer_service.model_adapter = mock_saptiva_adapter()
    writer_service.vector_store = mock_weaviate_adapter()

    query = "Test query"
    evidence_list = [
        Evidence(
            id="1",
            source=EvidenceSource(url="http://example.com", title="Example"),
            excerpt="This is an excerpt.",
        )
    ]

    # Act
    report = writer_service.write_report(query, evidence_list)

    # Assert
    assert report == "# Test Report"
    mock_saptiva_adapter.return_value.generate.assert_called_once()
    mock_weaviate_adapter.return_value.search_similar.assert_called_once()


@patch("domain.services.writer_svc.SaptivaModelAdapter")
@patch("domain.services.writer_svc.WeaviateVectorAdapter")
def test_enhance_with_rag(mock_weaviate_adapter, mock_saptiva_adapter):
    """Test the _enhance_with_rag method."""
    # Arrange
    mock_weaviate_adapter.return_value.search_similar.return_value = [
        Evidence(
            id="2",
            source=EvidenceSource(url="http://example2.com", title="Example 2"),
            excerpt="This is another excerpt.",
        )
    ]

    writer_service = WriterService()
    writer_service.vector_store = mock_weaviate_adapter()

    query = "Test query"
    evidence_list = [
        Evidence(
            id="1",
            source=EvidenceSource(url="http://example.com", title="Example"),
            excerpt="This is an excerpt.",
        )
    ]

    # Act
    enhanced_list = writer_service._enhance_with_rag(query, evidence_list, "collection_name")

    # Assert
    assert len(enhanced_list) == 2
    mock_weaviate_adapter.return_value.search_similar.assert_called_once_with(query, "collection_name", limit=10)
