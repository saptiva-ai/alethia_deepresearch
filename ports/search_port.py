from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from domain.models.evidence import Evidence

class SearchPort(ABC):
    """Port for web search operations."""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 10, **kwargs: Any) -> List[Evidence]:
        """
        Perform a web search and return evidence.
        
        Args:
            query: Search query text
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters (domain filters, date ranges, etc.)
            
        Returns:
            List of Evidence objects from search results
        """
        pass
    
    @abstractmethod
    def search_news(self, query: str, max_results: int = 10, days: int = 30) -> List[Evidence]:
        """
        Search for news articles.
        
        Args:
            query: Search query text
            max_results: Maximum number of results
            days: Number of days back to search
            
        Returns:
            List of Evidence objects from news results
        """
        pass
    
    @abstractmethod
    def search_academic(self, query: str, max_results: int = 10) -> List[Evidence]:
        """
        Search for academic papers and research.
        
        Args:
            query: Search query text
            max_results: Maximum number of results
            
        Returns:
            List of Evidence objects from academic sources
        """
        pass
    
    @abstractmethod
    def get_source_content(self, url: str) -> Optional[str]:
        """
        Extract full content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Full text content or None if extraction fails
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the search service is available and healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_search_quota(self) -> Dict[str, Any]:
        """
        Get current search quota and usage information.
        
        Returns:
            Dict containing quota information
        """
        pass