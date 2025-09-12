from datetime import datetime
import hashlib
import os
from typing import Any, Dict, List, Optional

from tavily import TavilyClient

from domain.models.evidence import Evidence, EvidenceSource
from ports.search_port import SearchPort


class TavilySearchAdapter(SearchPort):
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key or self.api_key == "pon_tu_api_key_aqui":
            raise ValueError("TAVILY_API_KEY environment variable not set or is a placeholder.")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 10, **kwargs: Any) -> List[Evidence]:
        """
        Perform a web search and return evidence.
        """
        try:
            search_depth = kwargs.get("search_depth", "advanced")
            response = self.client.search(query=query, search_depth=search_depth, max_results=max_results)
            results = response.get("results", [])
            return self._convert_to_evidence(results, query)
        except Exception as e:
            print(f"Error during Tavily search: {e}")
            return []

    def search_news(self, query: str, max_results: int = 10, days: int = 30) -> List[Evidence]:
        """
        Search for news articles.
        """
        try:
            # Tavily has news search capability
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                topic="news"
            )
            results = response.get("results", [])
            return self._convert_to_evidence(results, query)
        except Exception as e:
            print(f"Error during Tavily news search: {e}")
            return []

    def search_academic(self, query: str, max_results: int = 10) -> List[Evidence]:
        """
        Search for academic papers and research.
        """
        # Add academic sources to the query
        academic_query = f"{query} site:arxiv.org OR site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov"
        return self.search(academic_query, max_results)

    def get_source_content(self, url: str) -> Optional[str]:
        """
        Extract full content from a URL.
        """
        try:
            # Tavily can extract content from URLs
            response = self.client.extract(urls=[url])
            if response and "results" in response:
                return response["results"][0].get("content", "")
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
        return None

    def health_check(self) -> bool:
        """
        Check if the search service is available and healthy.
        """
        try:
            # Test with a simple search
            response = self.client.search(query="test", max_results=1)
            return "results" in response
        except Exception:
            return False

    def get_search_quota(self) -> Dict[str, Any]:
        """
        Get current search quota and usage information.
        """
        try:
            # Tavily doesn't have a direct quota endpoint, so we'll return a placeholder
            return {
                "quota_used": 0,
                "quota_remaining": 1000,  # Default assumption
                "quota_total": 1000
            }
        except Exception:
            return {"error": "Unable to retrieve quota information"}

    def _convert_to_evidence(self, results: List[dict], query: str) -> List[Evidence]:
        """
        Convert Tavily search results to Evidence objects.
        """
        evidence_list = []
        for i, result in enumerate(results):
            # Create evidence ID
            url = result.get("url", "")
            id_string = f"{query}_{url}_{i}"
            evidence_id = f"tavily_{hashlib.md5(id_string.encode()).hexdigest()[:8]}"

            # Create evidence source
            source = EvidenceSource(
                url=result.get("url", ""),
                title=result.get("title", ""),
                fetched_at=datetime.utcnow()
            )

            # Create evidence object
            evidence = Evidence(
                id=evidence_id,
                source=source,
                excerpt=result.get("content", "")[:1000],  # Limit excerpt to 1000 chars
                tool_call_id=f"tavily:search:{evidence_id}",
                score=result.get("score", 0.8),  # Tavily provides relevance scores
                tags=["web", "tavily"],
                cit_key=f"TavilyResult{i+1}"
            )
            evidence_list.append(evidence)

        return evidence_list
