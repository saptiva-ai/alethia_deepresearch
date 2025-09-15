"""
Unit tests for PlannerService.
"""
from unittest.mock import Mock, patch

import pytest

from domain.models.plan import ResearchPlan
from domain.services.planner_svc import PlannerService


@pytest.mark.unit
class TestPlannerService:
    """Test cases for PlannerService."""

    def test_init(self):
        """Test PlannerService initialization."""
        planner = PlannerService()
        assert planner is not None
        assert hasattr(planner, "model_adapter")

    @patch("domain.services.planner_svc.SaptivaModelAdapter")
    def test_create_plan_success(self, mock_adapter):
        """Test successful plan creation."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": """
- id: "task_1"
  query: "Sub query 1"
  sources: ["web", "academic"]
- id: "task_2"
  query: "Sub query 2"
  sources: ["web", "news"]
            """,
            "model": "SAPTIVA_OPS",
        }
        mock_adapter.return_value = mock_instance

        planner = PlannerService()
        query = "Test research query"

        # Act
        result = planner.create_plan(query)

        # Assert
        assert isinstance(result, ResearchPlan)
        assert result.main_query == query
        assert len(result.sub_tasks) == 2
        assert result.sub_tasks[0].id == "task_1"
        assert result.sub_tasks[0].query == "Sub query 1"
        assert "web" in result.sub_tasks[0].sources

        # Verify adapter was called
        mock_instance.generate.assert_called_once()
        call_args = mock_instance.generate.call_args
        assert "Saptiva Ops" in str(call_args)
        assert query in str(call_args)

    @patch("domain.services.planner_svc.SaptivaModelAdapter")
    def test_create_plan_with_invalid_yaml(self, mock_adapter):
        """Test plan creation with invalid YAML response."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.return_value = {"content": "invalid yaml content {[}", "model": "SAPTIVA_OPS"}
        mock_adapter.return_value = mock_instance

        planner = PlannerService()
        query = "Test query"

        # Act
        result = planner.create_plan(query)

        # Assert - Should return fallback plan
        assert isinstance(result, ResearchPlan)
        assert result.main_query == query
        assert len(result.sub_tasks) >= 1  # Should have fallback sub-tasks

    @patch("domain.services.planner_svc.SaptivaModelAdapter")
    def test_create_plan_with_missing_fields(self, mock_adapter):
        """Test plan creation with missing required fields in YAML."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": """
- id: "task_1"
  query: "Missing id field test"
  sources: ["web"]
            """,
            "model": "SAPTIVA_OPS",
        }
        mock_adapter.return_value = mock_instance

        planner = PlannerService()
        query = "Test query"

        # Act
        result = planner.create_plan(query)

        # Assert
        assert isinstance(result, ResearchPlan)
        assert result.main_query == "Test query"
        # Should handle missing id gracefully or provide fallback

    @patch("domain.services.planner_svc.SaptivaModelAdapter")
    def test_create_plan_adapter_error(self, mock_adapter):
        """Test plan creation when adapter raises an error."""
        # Arrange
        mock_instance = Mock()
        mock_instance.generate.side_effect = Exception("API Error")
        mock_adapter.return_value = mock_instance

        planner = PlannerService()
        query = "Test query"

        # Act
        result = planner.create_plan(query)

        # Assert - Should return fallback plan
        assert isinstance(result, ResearchPlan)
        assert result.main_query == query
        assert len(result.sub_tasks) >= 1

    def test_build_planning_prompt(self):
        """Test planning prompt construction."""
        planner = PlannerService()
        query = "Test research query"

        # Act
        prompt = planner._build_prompt(query)

        # Assert
        assert isinstance(prompt, str)
        assert query in prompt
        assert "YAML" in prompt or "yaml" in prompt
        assert "sub-tasks" in prompt
        assert len(prompt) > 100  # Should be a substantial prompt

    def test_parse_plan_response_valid(self):
        """Test parsing valid plan response."""
        planner = PlannerService()
        main_query = "Banking analysis Mexico"
        valid_yaml = """
  - id: "competitors"
    query: "Competitor analysis in Mexican banking"
    sources: ["web", "financial_reports"]
  - id: "regulations"
    query: "Banking regulations Mexico 2024"
    sources: ["web", "government"]
        """

        # Act
        result = planner._parse_plan(main_query, valid_yaml)

        # Assert
        assert isinstance(result, ResearchPlan)
        assert result.main_query == main_query
        assert len(result.sub_tasks) == 2
        assert result.sub_tasks[0].id == "competitors"
        assert "financial_reports" in result.sub_tasks[0].sources

    def test_parse_plan_response_invalid(self):
        """Test parsing invalid plan response."""
        planner = PlannerService()
        invalid_yaml = "invalid: yaml: content: {["
        query = "Original query"

        # Act
        result = planner._parse_plan(query, invalid_yaml)

        # Assert
        assert isinstance(result, ResearchPlan)
        assert result.main_query == query
        assert len(result.sub_tasks) >= 1

    @pytest.mark.parametrize(
        "query,expected_tasks",
        [
            ("Banking analysis", 3),
            ("Company research Tesla", 3),
            ("Market analysis fintech", 3),
            ("", 3),  # Even empty query should return fallback
        ],
    )
    @patch("domain.services.planner_svc.SaptivaModelAdapter")
    def test_create_plan_various_queries(self, mock_adapter, query, expected_tasks):
        """Test plan creation with various query types."""
        # Setup mock for parametrized test
        mock_instance = Mock()
        mock_instance.generate.return_value = {
            "content": """
- id: "task_1"
  query: "Analysis task 1"
  sources: ["web", "news"]
- id: "task_2"
  query: "Analysis task 2"
  sources: ["web", "academic"]
- id: "task_3"
  query: "Analysis task 3"
  sources: ["web", "reports"]
            """,
            "model": "SAPTIVA_OPS",
        }
        mock_adapter.return_value = mock_instance

        planner = PlannerService()

        # Act
        result = planner.create_plan(query)

        # Assert
        assert isinstance(result, ResearchPlan)
        assert len(result.sub_tasks) >= expected_tasks
        if query:
            assert query.lower() in result.main_query.lower() or result.main_query == query
