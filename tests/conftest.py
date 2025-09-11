"""
Global pytest configuration and fixtures for Aletheia Deep Research tests.
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["SAPTIVA_API_KEY"] = "test_saptiva_key"
os.environ["TAVILY_API_KEY"] = "test_tavily_key"
os.environ["VECTOR_BACKEND"] = "none"
os.environ["WEAVIATE_HOST"] = "http://localhost:8080"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_saptiva_client():
    """Mock Saptiva client for testing."""
    with patch("adapters.saptiva_model.saptiva_client.SaptivaModelAdapter") as mock:
        mock_instance = Mock()
        # Default response that can be overridden by individual tests
        mock_instance.generate.return_value = {
            "content": "Mock response from Saptiva",
            "model": "Saptiva Turbo",
            "usage": {"tokens": 100}
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily client for testing."""
    with patch("adapters.tavily_search.tavily_adapter.TavilyAdapter") as mock:
        mock_instance = Mock()
        mock_instance.search.return_value = [
            {
                "title": "Mock Search Result",
                "url": "https://example.com/mock",
                "content": "Mock content for testing",
                "score": 0.95
            }
        ]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_weaviate_client():
    """Mock Weaviate client for testing."""
    with patch("adapters.weaviate_vector.weaviate_adapter.WeaviateAdapter") as mock:
        mock_instance = Mock()
        mock_instance.store_evidence.return_value = "mock_evidence_id"
        mock_instance.search_similar.return_value = []
        mock_instance.collection_exists.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_research_plan():
    """Sample research plan for testing."""
    from domain.models.plan import ResearchPlan, ResearchSubTask
    
    return ResearchPlan(
        main_query="Test research query",
        sub_tasks=[
            ResearchSubTask(
                id="task_1",
                query="Test sub-query 1",
                sources=["web", "academic"]
            ),
            ResearchSubTask(
                id="task_2", 
                query="Test sub-query 2",
                sources=["web", "news"]
            )
        ]
    )


@pytest.fixture
def sample_evidence_list():
    """Sample evidence list for testing."""
    from domain.models.evidence import Evidence, EvidenceSource
    from datetime import datetime
    
    return [
        Evidence(
            id="evidence_1",
            source=EvidenceSource(
                url="https://example.com/1",
                title="Test Source 1",
                fetched_at=datetime.utcnow()
            ),
            excerpt="Sample excerpt from source 1",
            hash="hash_1",
            tool_call_id="call_1",
            score=0.9,
            tags=["test", "sample"]
        ),
        Evidence(
            id="evidence_2",
            source=EvidenceSource(
                url="https://example.com/2", 
                title="Test Source 2",
                fetched_at=datetime.utcnow()
            ),
            excerpt="Sample excerpt from source 2",
            hash="hash_2",
            tool_call_id="call_2",
            score=0.8,
            tags=["test", "example"]
        )
    ]


@pytest.fixture
def sample_completion_score():
    """Sample completion score for testing."""
    from domain.models.evaluation import CompletionScore, CompletionLevel
    
    return CompletionScore(
        overall_score=0.75,
        completion_level=CompletionLevel.ADEQUATE,
        coverage_areas={
            "competitors": 0.8,
            "market_analysis": 0.7,
            "regulations": 0.9
        },
        identified_gaps=[],
        confidence=0.85,
        reasoning="Test completion score"
    )


@pytest.fixture
def test_query():
    """Standard test query."""
    return "Análisis competitivo de bancos digitales en México 2024"


# Async fixtures for services
@pytest.fixture
async def planner_service(mock_saptiva_client):
    """Planner service with mocked dependencies."""
    from domain.services.planner_svc import PlannerService
    return PlannerService()


@pytest.fixture
async def research_service(mock_tavily_client, mock_weaviate_client):
    """Research service with mocked dependencies."""
    from domain.services.research_svc import ResearchService
    return ResearchService()


@pytest.fixture
async def evaluation_service(mock_saptiva_client):
    """Evaluation service with mocked dependencies."""
    from domain.services.evaluation_svc import EvaluationService
    return EvaluationService()


@pytest.fixture
async def writer_service(mock_saptiva_client, mock_weaviate_client):
    """Writer service with mocked dependencies."""
    from domain.services.writer_svc import WriterService
    return WriterService()


# FastAPI test fixtures
@pytest.fixture
async def test_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from apps.api.main import app
    
    with TestClient(app) as client:
        yield client


# Environment fixtures
@pytest.fixture(autouse=True)
def ensure_test_environment():
    """Ensure we're running in test environment."""
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "test"
    yield
    if original_env:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)


# Markers for organizing tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "external_api: Tests requiring external APIs")