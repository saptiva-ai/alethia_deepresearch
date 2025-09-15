"""
Unit tests for EvaluationService - Together AI Pattern.
"""
import json
from unittest.mock import Mock, patch

import pytest

from domain.models.evaluation import CompletionLevel, CompletionScore, InformationGap, RefinementQuery
from domain.services.evaluation_svc import EvaluationService


@pytest.mark.unit
class TestEvaluationService:
    """Test cases for EvaluationService implementing Together AI pattern."""

    def test_init(self):
        """Test EvaluationService initialization."""
        evaluator = EvaluationService()
        assert evaluator is not None
        assert hasattr(evaluator, "model_adapter")
        assert hasattr(evaluator, "evaluation_model")

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_evaluate_research_completeness_success(self, mock_adapter, sample_evidence_list):
        """Test successful research completeness evaluation."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": json.dumps(
                {
                    "overall_score": 0.75,
                    "completion_level": "adequate",
                    "coverage_areas": {"competitors": 0.8, "market_analysis": 0.7, "regulations": 0.9},
                    "confidence": 0.85,
                    "reasoning": "Good coverage across most areas",
                }
            ),
            "model": "SAPTIVA_CORTEX",
        }
        mock_adapter.return_value = mock_instance

        evaluator = EvaluationService()
        query = "Banking analysis Mexico"

        # Act
        result = evaluator.evaluate_research_completeness(query, sample_evidence_list)

        # Assert
        assert isinstance(result, CompletionScore)
        assert result.overall_score == 0.75
        assert result.completion_level == CompletionLevel.ADEQUATE
        assert result.coverage_areas["competitors"] == 0.8
        assert result.confidence == 0.85
        assert "Good coverage" in result.reasoning

        # Verify adapter was called with correct parameters
        mock_instance.generate.assert_called_once()
        call_args = mock_instance.generate.call_args
        assert call_args[1]["temperature"] == 0.3  # Lower temp for analytical tasks

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_identify_information_gaps_success(self, mock_adapter, sample_evidence_list):
        """Test successful information gap identification."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": json.dumps(
                [
                    {
                        "gap_type": "missing_competitor_analysis",
                        "description": "Lack of detailed competitive positioning data",
                        "priority": 4,
                        "suggested_query": "Competitive analysis and market positioning",
                    },
                    {
                        "gap_type": "missing_financial_data",
                        "description": "No recent financial performance metrics",
                        "priority": 5,
                        "suggested_query": "Financial performance Q3 2024",
                    },
                ]
            ),
            "model": "SAPTIVA_CORTEX",
        }
        mock_adapter.return_value = mock_instance

        evaluator = EvaluationService()
        query = "Banking analysis Mexico"

        # Act
        result = evaluator.identify_information_gaps(query, sample_evidence_list)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(gap, InformationGap) for gap in result)

        gap1 = result[0]
        assert gap1.gap_type == "missing_competitor_analysis"
        assert gap1.priority == 4
        assert "competitive positioning" in gap1.description.lower()

        gap2 = result[1]
        assert gap2.gap_type == "missing_financial_data"
        assert gap2.priority == 5

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_generate_refinement_queries_success(self, mock_adapter):
        """Test successful refinement query generation."""
        # Arrange
        gaps = [
            InformationGap(gap_type="missing_competitor", description="Need competitor data", priority=4, suggested_query="Competitor analysis"),
            InformationGap(gap_type="missing_regulations", description="Need regulatory info", priority=5, suggested_query="Banking regulations"),
        ]

        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": json.dumps(
                [
                    {
                        "query": "Banking competitors Mexico market share 2024",
                        "gap_addressed": "missing_competitor",
                        "priority": 4,
                        "expected_sources": ["web", "financial_reports"],
                    },
                    {
                        "query": "Mexican banking regulations CNBV 2024",
                        "gap_addressed": "missing_regulations",
                        "priority": 5,
                        "expected_sources": ["web", "government"],
                    },
                ]
            ),
            "model": "SAPTIVA_CORTEX",
        }
        mock_adapter.return_value = mock_instance

        evaluator = EvaluationService()
        original_query = "Banking analysis Mexico"

        # Act
        result = evaluator.generate_refinement_queries(gaps, original_query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(query, RefinementQuery) for query in result)

        query1 = result[0]
        assert "market share 2024" in query1.query
        assert query1.gap_addressed == "missing_competitor"
        assert "financial_reports" in query1.expected_sources

        query2 = result[1]
        assert "CNBV 2024" in query2.query
        assert query2.gap_addressed == "missing_regulations"

    def test_build_evaluation_prompt(self, sample_evidence_list):
        """Test evaluation prompt construction."""
        evaluator = EvaluationService()
        query = "Banking analysis Mexico"

        # Act
        prompt = evaluator._build_evaluation_prompt(query, sample_evidence_list)

        # Assert
        assert isinstance(prompt, str)
        assert query in prompt
        assert "overall_score" in prompt
        assert "completion_level" in prompt
        assert "coverage_areas" in prompt
        assert len(prompt) > 500  # Should be substantial

    def test_build_gap_analysis_prompt(self, sample_evidence_list):
        """Test gap analysis prompt construction."""
        evaluator = EvaluationService()
        query = "Banking analysis Mexico"

        # Act
        prompt = evaluator._build_gap_analysis_prompt(query, sample_evidence_list)

        # Assert
        assert isinstance(prompt, str)
        assert query in prompt
        assert "gap_type" in prompt
        assert "priority" in prompt
        assert "competitor" in prompt.lower()
        assert len(prompt) > 300

    def test_build_refinement_prompt(self):
        """Test refinement prompt construction."""
        evaluator = EvaluationService()
        gaps = [InformationGap(gap_type="missing_data", description="Missing market data", priority=4, suggested_query="Market analysis")]
        original_query = "Banking analysis Mexico"

        # Act
        prompt = evaluator._build_refinement_prompt(gaps, original_query)

        # Assert
        assert isinstance(prompt, str)
        assert original_query in prompt
        assert "missing_data" in prompt
        assert "priority" in prompt
        assert "expected_sources" in prompt

    def test_summarize_evidence(self, sample_evidence_list):
        """Test evidence summarization."""
        evaluator = EvaluationService()

        # Act
        summary = evaluator._summarize_evidence(sample_evidence_list)

        # Assert
        assert isinstance(summary, str)
        assert "Test Source 1" in summary
        assert "Test Source 2" in summary
        assert "example.com" in summary
        assert len(summary) > 100

    def test_summarize_evidence_empty(self):
        """Test evidence summarization with empty list."""
        evaluator = EvaluationService()

        # Act
        summary = evaluator._summarize_evidence([])

        # Assert
        assert summary == "No evidence collected yet."

    def test_summarize_evidence_large_list(self):
        """Test evidence summarization with >10 items."""
        evaluator = EvaluationService()
        from datetime import datetime

        from domain.models.evidence import Evidence, EvidenceSource

        # Create 15 evidence items
        evidence_list = []
        for i in range(15):
            evidence = Evidence(
                id=f"evidence_{i}",
                source=EvidenceSource(url=f"https://example.com/{i}", title=f"Test Source {i}", fetched_at=datetime.utcnow()),
                excerpt=f"Sample excerpt {i}",
                hash=f"hash_{i}",
                tool_call_id=f"call_{i}",
                score=0.8,
                tags=["test"],
            )
            evidence_list.append(evidence)

        # Act
        summary = evaluator._summarize_evidence(evidence_list)

        # Assert
        assert "and 5 more evidence items" in summary
        assert "Test Source 9" in summary  # Should include first 10
        assert "Test Source 14" not in summary  # Should not include >10

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_parse_evaluation_response_invalid_json(self, mock_adapter):
        """Test parsing invalid JSON evaluation response."""
        evaluator = EvaluationService()
        invalid_response = "This is not valid JSON {["

        # Act
        result = evaluator._parse_evaluation_response(invalid_response)

        # Assert - Should return fallback score
        assert isinstance(result, CompletionScore)
        assert result.overall_score == 0.5
        assert result.completion_level == CompletionLevel.PARTIAL
        assert result.confidence == 0.5
        assert "Could not parse" in result.reasoning

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_parse_gaps_response_invalid_json(self, mock_adapter):
        """Test parsing invalid JSON gaps response."""
        evaluator = EvaluationService()
        invalid_response = "Not valid JSON"

        # Act
        result = evaluator._parse_gaps_response(invalid_response)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_parse_refinement_response_invalid_json(self, mock_adapter):
        """Test parsing invalid JSON refinement response."""
        evaluator = EvaluationService()
        invalid_response = "Invalid JSON"

        # Act
        result = evaluator._parse_refinement_response(invalid_response)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.parametrize(
        "score,expected_level",
        [
            (0.3, CompletionLevel.INSUFFICIENT),
            (0.6, CompletionLevel.PARTIAL),
            (0.8, CompletionLevel.ADEQUATE),
            (0.95, CompletionLevel.COMPREHENSIVE),
        ],
    )
    @patch("domain.services.evaluation_svc.SaptivaModelAdapter")
    def test_completion_levels(self, mock_adapter, score, expected_level, sample_evidence_list):
        """Test different completion score levels."""
        # Create a fresh mock instance for this test
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": json.dumps(
                {"overall_score": score, "completion_level": expected_level.value, "coverage_areas": {}, "confidence": 0.8, "reasoning": f"Test score {score}"}
            ),
            "model": "SAPTIVA_CORTEX",
        }
        mock_adapter.return_value = mock_instance

        evaluator = EvaluationService()
        result = evaluator.evaluate_research_completeness("test", sample_evidence_list)

        assert result.overall_score == score
        assert result.completion_level == expected_level
