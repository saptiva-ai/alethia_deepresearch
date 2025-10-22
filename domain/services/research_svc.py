import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os

from adapters.tavily_search.tavily_client import TavilySearchAdapter
from adapters.weaviate_vector.weaviate_adapter import WeaviateVectorAdapter
from domain.models.evidence import Evidence
from domain.models.plan import ResearchPlan
from ports.vector_store_port import VectorStorePort


class ResearchService:
    def __init__(self):
        # Initialize search adapter
        try:
            self.search_adapter = TavilySearchAdapter()
            self.search_enabled = True
        except ValueError as e:
            print(f"Disabling search functionality: {e}")
            self.search_enabled = False

        # Initialize vector store based on configuration
        vector_backend = os.getenv("VECTOR_BACKEND", "weaviate").lower()

        if vector_backend == "none":
            # Use Weaviate in mock mode (no connection attempts)
            self.vector_store: VectorStorePort = WeaviateVectorAdapter(force_mock=True)
            print("Vector storage disabled - using mock storage (no Weaviate connection).")
        else:
            # Initialize vector store for RAG
            self.vector_store: VectorStorePort = WeaviateVectorAdapter()

            # Check if vector store is healthy
            if self.vector_store.health_check():
                print("Weaviate vector store is healthy and ready.")
            else:
                print("Weaviate not available - using mock vector storage.")

    def execute_plan(self, plan: ResearchPlan) -> list[Evidence]:
        """
        Executes the research plan by searching for evidence for each sub-task.
        Now stores evidence in vector database for RAG.
        """
        if not self.search_enabled:
            print("ResearchService search is disabled due to missing API key.")
            return []

        # Create a collection for this research session
        collection_name = f"research_{self._generate_collection_id(plan.main_query)}"
        self.vector_store.create_collection(collection_name)

        all_evidence = []
        for task in plan.sub_tasks:
            if "web" in task.sources:
                print(f"--- Executing Research Sub-Task: {task.query} ---")
                search_results = self.search_adapter.search(query=task.query)

                for result in search_results:
                    # result is already an Evidence object from TavilySearchAdapter
                    # Just update the tool_call_id to track which task it came from
                    result.tool_call_id = f"tavily:{task.id}"
                    evidence = result

                    # Store in vector database
                    stored = self.vector_store.store_evidence(evidence, collection_name)
                    if stored:
                        print(f"Stored evidence {evidence.id} in vector store")

                    all_evidence.append(evidence)

        print(f"Research completed. Stored {len(all_evidence)} pieces of evidence in collection {collection_name}")
        return all_evidence

    async def execute_plan_parallel(self, plan: ResearchPlan) -> list[Evidence]:
        """
        Executes the research plan with parallel search processing for improved performance.
        Uses asyncio and ThreadPoolExecutor to run searches concurrently.
        """
        if not self.search_enabled:
            print("ResearchService search is disabled due to missing API key.")
            return []

        # Create a collection for this research session
        collection_name = f"research_{self._generate_collection_id(plan.main_query)}"
        self.vector_store.create_collection(collection_name)

        # Filter tasks that need web search
        web_tasks = [task for task in plan.sub_tasks if "web" in task.sources]

        if not web_tasks:
            print("No web search tasks found in plan")
            return []

        print(f"🚀 Executing {len(web_tasks)} research tasks in parallel...")

        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=min(len(web_tasks), 5)) as executor:
            # Submit all search tasks concurrently
            search_futures = [executor.submit(self._execute_single_search_task, task) for task in web_tasks]

            # Collect results as they complete
            all_evidence = []
            completed_tasks = 0

            for future in asyncio.as_completed([asyncio.wrap_future(f) for f in search_futures]):
                try:
                    task_evidence = await future
                    all_evidence.extend(task_evidence)
                    completed_tasks += 1
                    print(f"✅ Task {completed_tasks}/{len(web_tasks)} completed, found {len(task_evidence)} evidence items")
                except Exception as e:
                    print(f"❌ Task failed: {e}")
                    completed_tasks += 1

        # Store all evidence in vector database in parallel
        await self._store_evidence_batch(all_evidence, collection_name)

        print(f"🎉 Parallel research completed. Stored {len(all_evidence)} pieces of evidence in collection {collection_name}")
        return all_evidence

    def _execute_single_search_task(self, task) -> list[Evidence]:
        """Execute a single search task synchronously."""
        print(f"🔍 Searching: {task.query}")
        search_results = self.search_adapter.search(query=task.query)

        evidence_list = []
        for result in search_results:
            # Update tool_call_id to track which task it came from
            result.tool_call_id = f"tavily:{task.id}"
            evidence_list.append(result)

        return evidence_list

    async def _store_evidence_batch(self, evidence_list: list[Evidence], collection_name: str):
        """Store evidence items in vector database using batch processing."""
        if not evidence_list:
            return

        # Use ThreadPoolExecutor for parallel storage operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            storage_futures = [executor.submit(self.vector_store.store_evidence, evidence, collection_name) for evidence in evidence_list]

            stored_count = 0
            for future in asyncio.as_completed([asyncio.wrap_future(f) for f in storage_futures]):
                try:
                    stored = await future
                    if stored:
                        stored_count += 1
                except Exception as e:
                    print(f"⚠️  Error storing evidence: {e}")

            print(f"📦 Batch storage completed: {stored_count}/{len(evidence_list)} items stored")

    def search_existing_evidence(self, query: str, collection_name: str = "default", limit: int = 5) -> list[Evidence]:
        """
        Search for existing evidence in the vector store using semantic similarity.
        """
        return self.vector_store.search_similar(query, collection_name, limit)

    def _generate_collection_id(self, main_query: str) -> str:
        """Generate a unique collection ID based on the main query."""
        return hashlib.sha256(main_query.encode()).hexdigest()[:8]

    def _generate_hash(self, content: str) -> str:
        """Generate a hash for content deduplication."""
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
