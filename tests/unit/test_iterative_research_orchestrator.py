"""
Tests for IterativeResearchOrchestrator - the main orchestrator for deep research.
"""
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.models.evaluation import CompletionLevel, CompletionScore
from domain.models.evidence import Evidence, EvidenceSource
from domain.models.plan import ResearchPlan, ResearchSubTask
from domain.services.iterative_research_svc import DeepResearchResult, IterativeResearchOrchestrator, ResearchIteration


class TestResearchIteration:
    """Test suite for ResearchIteration dataclass."""

    def test_init(self):
        """Test ResearchIteration initialization."""
        iteration = ResearchIteration(iteration_number=1, queries_executed=["query1", "query2"], evidence_collected=[])

        assert iteration.iteration_number == 1
        assert iteration.queries_executed == ["query1", "query2"]
        assert iteration.evidence_collected == []
        assert iteration.timestamp is not None
        assert iteration.completion_score is None
        assert iteration.gaps_identified is None
        assert iteration.refinement_queries is None

    def test_init_with_optional_fields(self):
        """Test ResearchIteration with all optional fields."""
        timestamp = datetime.utcnow()
        completion_score = CompletionScore(
            overall_score=0.8,
            completion_level=CompletionLevel.ADEQUATE,
            coverage_areas={"market": 0.8},
            identified_gaps=[],
            confidence=0.9,
            reasoning="Test score",
        )

        iteration = ResearchIteration(
            iteration_number=2,
            queries_executed=["query3"],
            evidence_collected=[],
            completion_score=completion_score,
            gaps_identified=[],
            refinement_queries=[],
            timestamp=timestamp,
        )

        assert iteration.timestamp == timestamp
        assert iteration.completion_score == completion_score


class TestDeepResearchResult:
    """Test suite for DeepResearchResult dataclass."""

    def test_init(self):
        """Test DeepResearchResult initialization."""
        iterations = [ResearchIteration(iteration_number=1, queries_executed=["query1"], evidence_collected=[])]

        result = DeepResearchResult(
            original_query="test query",
            iterations=iterations,
            final_evidence=[],
            final_report="Test report",
            total_evidence_count=0,
            completion_level=CompletionLevel.ADEQUATE,
            research_quality_score=0.8,
            execution_time_seconds=30.0,
        )

        assert result.original_query == "test query"
        assert result.iterations == iterations
        assert result.final_report == "Test report"
        assert result.total_evidence_count == 0
        assert result.completion_level == CompletionLevel.ADEQUATE
        assert result.research_quality_score == 0.8
        assert result.execution_time_seconds == 30.0


class TestIterativeResearchOrchestrator:
    """Test suite for IterativeResearchOrchestrator."""

    def test_init_default(self):
        """Test IterativeResearchOrchestrator initialization with defaults."""
        orchestrator = IterativeResearchOrchestrator()

        assert orchestrator.max_iterations == 3
        assert orchestrator.min_completion_score == 0.75
        assert orchestrator.budget == 100
        assert hasattr(orchestrator, "planner")
        assert hasattr(orchestrator, "researcher")
        assert hasattr(orchestrator, "evaluator")
        assert hasattr(orchestrator, "writer")

    def test_init_custom_params(self):
        """Test IterativeResearchOrchestrator with custom parameters."""
        orchestrator = IterativeResearchOrchestrator(max_iterations=5, min_completion_score=0.9, budget=200)

        assert orchestrator.max_iterations == 5
        assert orchestrator.min_completion_score == 0.9
        assert orchestrator.budget == 200

    @pytest.mark.asyncio
    @patch("domain.services.iterative_research_svc.get_event_logger")
    async def test_execute_deep_research_single_iteration_success(self, mock_get_logger):
        """Test successful deep research that completes in one iteration."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        orchestrator = IterativeResearchOrchestrator(min_completion_score=0.7)

        # Mock the services
        orchestrator.planner.create_plan = Mock(
            return_value=ResearchPlan(main_query="test query", sub_tasks=[ResearchSubTask(id="task1", query="subquery1", sources=["web"])])
        )

        mock_evidence = [
            Evidence(
                id="ev1",
                source=EvidenceSource(url="http://test.com", title="Test", fetched_at=datetime.utcnow()),
                excerpt="Test evidence",
                hash="hash1",
                tool_call_id="call1",
                score=0.9,
                tags=["test"],
            )
        ]

        orchestrator.researcher.execute_plan_parallel = AsyncMock(return_value=mock_evidence)

        mock_completion_score = CompletionScore(
            overall_score=0.8,  # Above threshold
            completion_level=CompletionLevel.ADEQUATE,
            coverage_areas={"market": 0.8},
            identified_gaps=[],
            confidence=0.9,
            reasoning="Good coverage",
        )

        orchestrator.evaluator.evaluate_research_completeness = Mock(return_value=mock_completion_score)
        orchestrator.writer.write_report = Mock(return_value="Final report content")

        # Execute
        result = await orchestrator.execute_deep_research("test query")

        # Assertions
        assert result.original_query == "test query"
        assert len(result.iterations) == 1
        assert result.total_evidence_count == 1
        assert result.completion_level == CompletionLevel.ADEQUATE
        assert result.research_quality_score == 0.8
        assert result.final_report == "Final report content"

        # Verify iteration details
        iteration = result.iterations[0]
        assert iteration.iteration_number == 1
        assert iteration.queries_executed == ["subquery1"]
        assert len(iteration.evidence_collected) == 1
        assert iteration.completion_score == mock_completion_score

    @pytest.mark.asyncio
    @patch("domain.services.iterative_research_svc.get_event_logger")
    async def test_execute_deep_research_multi_iteration(self, mock_get_logger):
        """Test deep research that requires multiple iterations."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        orchestrator = IterativeResearchOrchestrator(max_iterations=2, min_completion_score=0.8)

        # Mock the services
        orchestrator.planner.create_plan = Mock(
            return_value=ResearchPlan(main_query="test query", sub_tasks=[ResearchSubTask(id="task1", query="subquery1", sources=["web"])])
        )

        mock_evidence_iter1 = [
            Evidence(
                id="ev1",
                source=EvidenceSource(url="http://test1.com", title="Test1", fetched_at=datetime.utcnow()),
                excerpt="Evidence 1",
                hash="hash1",
                tool_call_id="call1",
                score=0.8,
                tags=["test"],
            )
        ]

        mock_evidence_iter2 = [
            Evidence(
                id="ev2",
                source=EvidenceSource(url="http://test2.com", title="Test2", fetched_at=datetime.utcnow()),
                excerpt="Evidence 2",
                hash="hash2",
                tool_call_id="call2",
                score=0.9,
                tags=["test"],
            )
        ]

        # First iteration - low score, needs refinement
        low_score = CompletionScore(
            overall_score=0.6,  # Below threshold
            completion_level=CompletionLevel.PARTIAL,
            coverage_areas={"market": 0.6},
            identified_gaps=[],
            confidence=0.7,
            reasoning="Needs more evidence",
        )

        # Second iteration - high score, complete
        high_score = CompletionScore(
            overall_score=0.85,  # Above threshold
            completion_level=CompletionLevel.ADEQUATE,
            coverage_areas={"market": 0.85},
            identified_gaps=[],
            confidence=0.9,
            reasoning="Good coverage achieved",
        )

        # Mock researcher to return different evidence for each iteration
        orchestrator.researcher.execute_plan_parallel = AsyncMock(return_value=mock_evidence_iter1)
        orchestrator._execute_refinement_queries_parallel = AsyncMock(return_value=mock_evidence_iter2)

        # Mock evaluator to return different scores
        orchestrator.evaluator.evaluate_research_completeness = Mock(side_effect=[low_score, high_score])
        orchestrator.evaluator.identify_information_gaps = Mock(return_value=[])

        # Create mock refinement queries for second iteration
        from domain.models.evaluation import RefinementQuery

        mock_refinement_queries = [
            RefinementQuery(query="additional research query", gap_addressed="market_data", priority=3, expected_sources=["web", "news"])
        ]
        orchestrator.evaluator.generate_refinement_queries = Mock(return_value=mock_refinement_queries)

        orchestrator.writer.write_report = Mock(return_value="Multi-iteration report")

        # Execute
        result = await orchestrator.execute_deep_research("test query")

        # Assertions
        assert result.original_query == "test query"
        assert len(result.iterations) == 2
        assert result.total_evidence_count == 2  # Combined from both iterations
        assert result.completion_level == CompletionLevel.ADEQUATE
        assert result.research_quality_score == 0.85
        assert result.final_report == "Multi-iteration report"

        # Verify both iterations
        assert result.iterations[0].iteration_number == 1
        assert result.iterations[0].completion_score == low_score
        assert result.iterations[1].iteration_number == 2
        assert result.iterations[1].completion_score == high_score

    @pytest.mark.asyncio
    @patch("domain.services.iterative_research_svc.get_event_logger")
    async def test_execute_deep_research_max_iterations_reached(self, mock_get_logger):
        """Test deep research that reaches max iterations without meeting threshold."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        orchestrator = IterativeResearchOrchestrator(max_iterations=2, min_completion_score=0.9)  # High threshold

        # Mock services
        orchestrator.planner.create_plan = Mock(
            return_value=ResearchPlan(main_query="test query", sub_tasks=[ResearchSubTask(id="task1", query="subquery1", sources=["web"])])
        )

        mock_evidence = [
            Evidence(
                id="ev1",
                source=EvidenceSource(url="http://test.com", title="Test", fetched_at=datetime.utcnow()),
                excerpt="Limited evidence",
                hash="hash1",
                tool_call_id="call1",
                score=0.7,
                tags=["test"],
            )
        ]

        orchestrator.researcher.execute_plan_parallel = AsyncMock(return_value=mock_evidence)

        # Always return score below threshold
        low_score = CompletionScore(
            overall_score=0.7,  # Below 0.9 threshold
            completion_level=CompletionLevel.PARTIAL,
            coverage_areas={"market": 0.7},
            identified_gaps=[],
            confidence=0.8,
            reasoning="Limited coverage",
        )

        orchestrator.evaluator.evaluate_research_completeness = Mock(return_value=low_score)
        orchestrator.evaluator.identify_information_gaps = Mock(return_value=[])
        orchestrator.evaluator.generate_refinement_queries = Mock(return_value=[])
        orchestrator.writer.write_report = Mock(return_value="Limited report")

        # Execute
        result = await orchestrator.execute_deep_research("test query")

        # Should complete with max iterations even if score is low
        assert len(result.iterations) == 2
        assert result.research_quality_score == 0.7
        assert result.completion_level == CompletionLevel.PARTIAL

    @pytest.mark.asyncio
    async def test_execute_refinement_queries_parallel_empty_list(self):
        """Test _execute_refinement_queries_parallel with empty query list."""
        orchestrator = IterativeResearchOrchestrator()

        result = await orchestrator._execute_refinement_queries_parallel([])

        assert result == []

    @pytest.mark.asyncio
    async def test_execute_refinement_queries_parallel_with_queries(self):
        """Test _execute_refinement_queries_parallel with actual queries."""
        orchestrator = IterativeResearchOrchestrator()

        # Create mock refinement queries
        from domain.models.evaluation import RefinementQuery

        refinement_queries = [
            RefinementQuery(query="refinement query 1", gap_addressed="market_data", priority=5, expected_sources=["web", "news"]),
            RefinementQuery(query="refinement query 2", gap_addressed="competitive_analysis", priority=4, expected_sources=["web"]),
        ]

        mock_evidence = [
            Evidence(
                id="ref_ev1",
                source=EvidenceSource(url="http://ref.com", title="Refinement", fetched_at=datetime.utcnow()),
                excerpt="Refined evidence",
                hash="ref_hash",
                tool_call_id="ref_call",
                score=0.9,
                tags=["refined"],
            )
        ]

        orchestrator.researcher.execute_plan_parallel = AsyncMock(return_value=mock_evidence)

        result = await orchestrator._execute_refinement_queries_parallel(refinement_queries)

        assert result == mock_evidence

        # Verify that researcher was called with correct plan structure
        orchestrator.researcher.execute_plan_parallel.assert_called_once()
        called_plan = orchestrator.researcher.execute_plan_parallel.call_args[0][0]

        assert called_plan.main_query == "Refinement research"
        assert len(called_plan.sub_tasks) == 2
        assert called_plan.sub_tasks[0].query == "refinement query 1"
        assert called_plan.sub_tasks[1].query == "refinement query 2"

    def test_get_research_summary(self):
        """Test get_research_summary method."""
        orchestrator = IterativeResearchOrchestrator()

        # Create real InformationGap instances
        from domain.models.evaluation import InformationGap

        gaps = [
            InformationGap(gap_type="competitor_data", description="Missing competitor analysis", priority=5, suggested_query="Find main competitors"),
            InformationGap(gap_type="market_size", description="Market size data missing", priority=4, suggested_query="Research market size data"),
        ]

        iterations = [
            ResearchIteration(
                iteration_number=1,
                queries_executed=["query1", "query2"],
                evidence_collected=[Mock(), Mock(), Mock()],  # 3 evidence items
                completion_score=CompletionScore(
                    overall_score=0.6,
                    completion_level=CompletionLevel.PARTIAL,
                    coverage_areas={},
                    identified_gaps=gaps,  # Real InformationGap instances
                    confidence=0.7,
                    reasoning="First iteration",
                ),
                gaps_identified=gaps,
                refinement_queries=None,
            ),
            ResearchIteration(
                iteration_number=2,
                queries_executed=["refined_query"],
                evidence_collected=[Mock(), Mock()],  # 2 evidence items
                completion_score=CompletionScore(
                    overall_score=0.85,
                    completion_level=CompletionLevel.ADEQUATE,
                    coverage_areas={},
                    identified_gaps=[],
                    confidence=0.9,
                    reasoning="Final iteration",
                ),
                gaps_identified=[],
                refinement_queries=None,
            ),
        ]

        result = DeepResearchResult(
            original_query="test summary query",
            iterations=iterations,
            final_evidence=[Mock()] * 5,  # 5 total evidence items
            final_report="Summary report",
            total_evidence_count=5,
            completion_level=CompletionLevel.ADEQUATE,
            research_quality_score=0.85,
            execution_time_seconds=45.2,
        )

        summary = orchestrator.get_research_summary(result)

        # Verify summary structure
        assert summary["query"] == "test summary query"
        assert summary["iterations"] == 2
        assert summary["total_evidence"] == 5
        assert summary["quality_score"] == 0.85
        assert summary["completion_level"] == CompletionLevel.ADEQUATE
        assert summary["execution_time"] == 45.2

        # Verify iteration details
        assert len(summary["iteration_details"]) == 2

        iter1_details = summary["iteration_details"][0]
        assert iter1_details["iteration"] == 1
        assert iter1_details["queries"] == 2
        assert iter1_details["evidence"] == 3
        assert iter1_details["score"] == 0.6
        assert iter1_details["gaps_found"] == 2

        iter2_details = summary["iteration_details"][1]
        assert iter2_details["iteration"] == 2
        assert iter2_details["queries"] == 1
        assert iter2_details["evidence"] == 2
        assert iter2_details["score"] == 0.85
        assert iter2_details["gaps_found"] == 0


class TestIterativeResearchOrchestratorIntegration:
    """Integration-style tests for the orchestrator."""

    @pytest.mark.asyncio
    @patch("domain.services.iterative_research_svc.get_event_logger")
    async def test_full_workflow_with_event_logging(self, mock_get_logger):
        """Test the full workflow includes proper event logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        orchestrator = IterativeResearchOrchestrator(max_iterations=1)

        # Setup minimal mocks for a successful run
        orchestrator.planner.create_plan = Mock(
            return_value=ResearchPlan(main_query="integration test", sub_tasks=[ResearchSubTask(id="t1", query="sub1", sources=["web"])])
        )

        orchestrator.researcher.execute_plan_parallel = AsyncMock(return_value=[])

        orchestrator.evaluator.evaluate_research_completeness = Mock(
            return_value=CompletionScore(
                overall_score=0.8, completion_level=CompletionLevel.ADEQUATE, coverage_areas={}, identified_gaps=[], confidence=0.8, reasoning="Test"
            )
        )

        orchestrator.writer.write_report = Mock(return_value="Integration test report")

        # Execute
        result = await orchestrator.execute_deep_research("integration test")

        # Verify event logging was called
        mock_logger.set_task_context.assert_called_once()
        mock_logger.log_research_started.assert_called_once()
        mock_logger.log_plan_created.assert_called_once()
        mock_logger.log_research_completed.assert_called_once()

        # Verify result structure
        assert result.original_query == "integration test"
        assert result.final_report == "Integration test report"
