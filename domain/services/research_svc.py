import hashlib

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

    def search_existing_evidence(self, query: str, collection_name: str = "default", limit: int = 5) -> list[Evidence]:
        """
        Search for existing evidence in the vector store using semantic similarity.
        """
        return self.vector_store.search_similar(query, collection_name, limit)

    def _generate_collection_id(self, main_query: str) -> str:
        """Generate a unique collection ID based on the main query."""
        hash_obj = hashlib.md5(main_query.encode())
        return hash_obj.hexdigest()[:8]

    def _generate_hash(self, content: str) -> str:
        """Generate a hash for content deduplication."""
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
