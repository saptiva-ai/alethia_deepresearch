from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from adapters.telemetry.events import get_event_logger

# Telemetry imports
from adapters.telemetry.tracing import trace_async_operation, trace_operation
from domain.models.evaluation import (
    CompletionLevel,
    CompletionScore,
    InformationGap,
    RefinementQuery,
)
from domain.models.evidence import Evidence
from domain.models.plan import ResearchPlan, ResearchSubTask
from domain.services.evaluation_svc import EvaluationService
from domain.services.planner_svc import PlannerService
from domain.services.research_svc import ResearchService
from domain.services.writer_svc import WriterService


@dataclass
class ResearchIteration:
    """Represents one iteration of the research process"""
    iteration_number: int
    queries_executed: List[str]
    evidence_collected: List[Evidence]
    completion_score: Optional[CompletionScore] = None
    gaps_identified: List[InformationGap] = None
    refinement_queries: List[RefinementQuery] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class DeepResearchResult:
    """Complete result of iterative deep research process"""
    original_query: str
    iterations: List[ResearchIteration]
    final_evidence: List[Evidence]
    final_report: str
    total_evidence_count: int
    completion_level: CompletionLevel
    research_quality_score: float
    execution_time_seconds: float

class IterativeResearchOrchestrator:
    """
    Implements Together AI iterative research pattern with Saptiva agents.
    Orchestrates multiple research iterations with evaluation and refinement.
    """

    def __init__(self, max_iterations: int = 3, min_completion_score: float = 0.75, budget: int = 100):
        self.max_iterations = max_iterations
        self.min_completion_score = min_completion_score
        self.budget = budget

        # Initialize all agent services
        self.planner = PlannerService()
        self.researcher = ResearchService()
        self.evaluator = EvaluationService()
        self.writer = WriterService()

    @trace_async_operation("deep_research.execute", {"research_type": "iterative"})
    async def execute_deep_research(self, query: str, tracer: Optional[trace.Tracer] = None) -> DeepResearchResult:
        """
        Execute iterative deep research following Together AI pattern.
        """
        start_time = datetime.utcnow()
        iterations = []
        all_evidence = []

        # Initialize event logging
        event_logger = get_event_logger()
        task_id = f"deep_research_{int(start_time.timestamp())}"
        event_logger.set_task_context(task_id)

        # Log research start
        event_logger.log_research_started(task_id, query, {
            "max_iterations": self.max_iterations,
            "min_completion_score": self.min_completion_score,
            "budget": self.budget
        })

        print(f"🚀 Starting iterative deep research for: '{query}'")
        print(f"📊 Configuration: max_iterations={self.max_iterations}, min_score={self.min_completion_score}")

        # Initial research iteration
        with trace_operation("deep_research.planning", {"query_length": len(query)}, tracer=tracer) as span:
            initial_plan = self.planner.create_plan(query)
            span.set_attribute("plan.subtask_count", len(initial_plan.sub_tasks))

        event_logger.log_plan_created(task_id, query, len(initial_plan.sub_tasks))
        print(f"📋 Initial plan created with {len(initial_plan.sub_tasks)} sub-tasks")

        for iteration_num in range(1, self.max_iterations + 1):
            print(f"\n🔄 === ITERATION {iteration_num} ===")

            # Log iteration start
            iteration_queries = []
            if iteration_num == 1:
                iteration_queries = [task.query for task in initial_plan.sub_tasks]
            else:
                iteration_queries = [rq.query for rq in iterations[-1].refinement_queries or []]

            event_logger.log_iteration_started(task_id, iteration_num, iteration_queries)

            # Execute research for this iteration with parallel processing
            if iteration_num == 1:
                # First iteration: use initial plan with parallel execution
                iteration_evidence = await self.researcher.execute_plan_parallel(initial_plan)
                queries_executed = [task.query for task in initial_plan.sub_tasks]
            else:
                # Subsequent iterations: use refinement queries with parallel execution
                refinement_queries = iterations[-1].refinement_queries or []
                iteration_evidence = await self._execute_refinement_queries_parallel(refinement_queries)
                queries_executed = [rq.query for rq in refinement_queries]

            all_evidence.extend(iteration_evidence)

            print(f"🔍 Collected {len(iteration_evidence)} new evidence items")
            print(f"📈 Total evidence: {len(all_evidence)} items")

            # Evaluate research completeness
            completion_score = self.evaluator.evaluate_research_completeness(query, all_evidence)
            print(f"📊 Completion Score: {completion_score.overall_score:.2f} ({completion_score.completion_level})")

            # Create iteration record
            iteration = ResearchIteration(
                iteration_number=iteration_num,
                queries_executed=queries_executed,
                evidence_collected=iteration_evidence,
                completion_score=completion_score
            )

            # Check if research is complete
            if completion_score.overall_score >= self.min_completion_score:
                print(f"✅ Research completed! Score {completion_score.overall_score:.2f} meets threshold {self.min_completion_score}")
                iterations.append(iteration)
                break

            # If not final iteration, identify gaps and generate refinements
            if iteration_num < self.max_iterations:
                print("🔍 Identifying information gaps...")
                gaps = self.evaluator.identify_information_gaps(query, all_evidence)
                print(f"🎯 Found {len(gaps)} information gaps")

                refinement_queries = self.evaluator.generate_refinement_queries(gaps, query)
                print(f"🎯 Generated {len(refinement_queries)} refinement queries")

                iteration.gaps_identified = gaps
                iteration.refinement_queries = refinement_queries

                # Log gaps for visibility
                for gap in gaps[:3]:  # Show top 3 gaps
                    print(f"   Gap: {gap.gap_type} (Priority: {gap.priority})")

            iterations.append(iteration)

        # Generate final report
        print("\n📝 Generating final report...")
        with trace_operation("deep_research.report_generation", {"evidence_count": len(all_evidence)}, tracer=tracer) as span:
            final_report = self.writer.write_report(query, all_evidence)
            span.set_attribute("report.length", len(final_report))

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Create final result
        result = DeepResearchResult(
            original_query=query,
            iterations=iterations,
            final_evidence=all_evidence,
            final_report=final_report,
            total_evidence_count=len(all_evidence),
            completion_level=iterations[-1].completion_score.completion_level,
            research_quality_score=iterations[-1].completion_score.overall_score,
            execution_time_seconds=execution_time
        )

        # Log research completion with metrics
        event_logger.log_research_completed(
            task_id,
            len(all_evidence),
            result.research_quality_score,
            execution_time
        )

        print("\n🎉 Deep research completed!")
        print(f"📊 Final Stats: {len(all_evidence)} evidence items, {len(iterations)} iterations, {execution_time:.1f}s")
        print(f"🏆 Quality Score: {result.research_quality_score:.2f} ({result.completion_level})")

        return result

    async def _execute_refinement_queries(self, refinement_queries: List[RefinementQuery]) -> List[Evidence]:
        """Execute refinement queries to address identified gaps (sequential version)."""
        if not refinement_queries:
            return []

        # Convert refinement queries to research sub-tasks
        sub_tasks = []
        for i, rq in enumerate(refinement_queries):
            sub_task = ResearchSubTask(
                id=f"refinement_{i+1}",
                query=rq.query,
                sources=rq.expected_sources
            )
            sub_tasks.append(sub_task)

        # Create plan for refinement queries
        refinement_plan = ResearchPlan(
            main_query="Refinement research",
            sub_tasks=sub_tasks
        )

        # Execute refinement research
        return self.researcher.execute_plan(refinement_plan)

    async def _execute_refinement_queries_parallel(self, refinement_queries: List[RefinementQuery]) -> List[Evidence]:
        """Execute refinement queries to address identified gaps with parallel processing."""
        if not refinement_queries:
            return []

        print(f"🔄 Executing {len(refinement_queries)} refinement queries in parallel...")

        # Convert refinement queries to research sub-tasks
        sub_tasks = []
        for i, rq in enumerate(refinement_queries):
            sub_task = ResearchSubTask(
                id=f"refinement_{i+1}",
                query=rq.query,
                sources=rq.expected_sources
            )
            sub_tasks.append(sub_task)

        # Create plan for refinement queries
        refinement_plan = ResearchPlan(
            main_query="Refinement research",
            sub_tasks=sub_tasks
        )

        # Execute refinement research with parallel processing
        return await self.researcher.execute_plan_parallel(refinement_plan)

    def get_research_summary(self, result: DeepResearchResult) -> Dict[str, Any]:
        """Generate a summary of the research process for API responses."""
        return {
            "query": result.original_query,
            "iterations": len(result.iterations),
            "total_evidence": result.total_evidence_count,
            "quality_score": result.research_quality_score,
            "completion_level": result.completion_level,
            "execution_time": result.execution_time_seconds,
            "iteration_details": [
                {
                    "iteration": it.iteration_number,
                    "queries": len(it.queries_executed),
                    "evidence": len(it.evidence_collected),
                    "score": it.completion_score.overall_score if it.completion_score else None,
                    "gaps_found": len(it.gaps_identified) if it.gaps_identified else 0
                }
                for it in result.iterations
            ]
        }