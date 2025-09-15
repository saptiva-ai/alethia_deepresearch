"""
Tests for domain models.
"""
from datetime import datetime

from pydantic import ValidationError
import pytest

from domain.models.evaluation import (
    CompletionLevel,
    CompletionScore,
    InformationGap,
    RefinementQuery,
)
from domain.models.evidence import (
    Evidence,
    EvidenceSource,
)
from domain.models.plan import (
    ResearchPlan,
    ResearchSubTask,
)


def test_completion_level():
    """Test the CompletionLevel enum."""
    assert CompletionLevel.INSUFFICIENT == "insufficient"
    assert CompletionLevel.PARTIAL == "partial"
    assert CompletionLevel.ADEQUATE == "adequate"
    assert CompletionLevel.COMPREHENSIVE == "comprehensive"


def test_information_gap():
    """Test the InformationGap model."""
    gap = InformationGap(
        gap_type="missing_competitor",
        description="Missing information about a key competitor.",
        priority=5,
        suggested_query="Who are the main competitors of Acme Inc.?",
    )
    assert gap.gap_type == "missing_competitor"
    assert gap.priority == 5


def test_completion_score():
    """Test the CompletionScore model."""
    score = CompletionScore(
        overall_score=0.8,
        completion_level=CompletionLevel.ADEQUATE,
        coverage_areas={"competitors": 0.8, "market_size": 0.6},
        identified_gaps=[],
        confidence=0.9,
        reasoning="Good coverage of competitors, but market size is lacking.",
    )
    assert score.overall_score == 0.8
    assert score.completion_level == CompletionLevel.ADEQUATE
    assert not score.identified_gaps


def test_refinement_query():
    """Test the RefinementQuery model."""
    query = RefinementQuery(
        query="What is the market size of the global widget industry?",
        gap_addressed="market_size",
        priority=4,
        expected_sources=["web", "financial_reports"],
    )
    assert query.priority == 4
    assert "web" in query.expected_sources


def test_information_gap_validation():
    """Test validation error for InformationGap."""
    with pytest.raises(ValidationError):
        InformationGap(gap_type="missing_competitor", description="Missing info")


def test_completion_score_validation():
    """Test validation error for CompletionScore."""
    with pytest.raises(ValidationError):
        CompletionScore(overall_score=0.8, completion_level=CompletionLevel.ADEQUATE)


def test_refinement_query_validation():
    """Test validation error for RefinementQuery."""
    with pytest.raises(ValidationError):
        RefinementQuery(query="What is the market size?")


def test_evidence_source():
    """Test the EvidenceSource model."""
    source = EvidenceSource(
        url="http://example.com",
        title="Example",
    )
    assert source.url == "http://example.com"
    assert isinstance(source.fetched_at, datetime)


def test_evidence():
    """Test the Evidence model."""
    source = EvidenceSource(url="http://example.com", title="Example")
    evidence = Evidence(
        id="123",
        source=source,
        excerpt="This is an excerpt.",
    )
    assert evidence.id == "123"
    assert evidence.source == source
    assert evidence.excerpt == "This is an excerpt."
    assert evidence.tags == []


def test_research_sub_task():
    """Test the ResearchSubTask model."""
    sub_task = ResearchSubTask(
        id="1",
        query="What is the capital of France?",
    )
    assert sub_task.id == "1"
    assert sub_task.query == "What is the capital of France?"
    assert sub_task.sources == ["web"]
    assert not sub_task.completed


def test_research_plan():
    """Test the ResearchPlan model."""
    sub_task = ResearchSubTask(id="1", query="sub-query")
    plan = ResearchPlan(
        main_query="Main query",
        sub_tasks=[sub_task],
    )
    assert plan.main_query == "Main query"
    assert len(plan.sub_tasks) == 1
    assert plan.sub_tasks[0] == sub_task
