from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from domain.models.evidence import Evidence

class BrowserPort(ABC):
    """Port for web browsing and content extraction operations."""
    
    @abstractmethod
    def navigate_to(self, url: str) -> bool:
        """
        Navigate to a specific URL.
        
        Args:
            url: Target URL to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self, url: str) -> Optional[str]:
        """
        Extract text content from a web page.
        
        Args:
            url: URL to extract text from
            
        Returns:
            Extracted text content or None if extraction fails
        """
        pass
    
    @abstractmethod
    def extract_evidence(self, url: str, context: str = "") -> Optional[Evidence]:
        """
        Extract structured evidence from a web page.
        
        Args:
            url: URL to extract evidence from
            context: Optional context to guide extraction
            
        Returns:
            Evidence object or None if extraction fails
        """
        pass
    
    @abstractmethod
    def take_screenshot(self, url: str, save_path: str) -> bool:
        """
        Take a screenshot of a web page.
        
        Args:
            url: URL to screenshot
            save_path: Path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_links(self, url: str, filter_pattern: Optional[str] = None) -> List[str]:
        """
        Extract links from a web page.
        
        Args:
            url: URL to extract links from
            filter_pattern: Optional regex pattern to filter links
            
        Returns:
            List of extracted URLs
        """
        pass
    
    @abstractmethod
    def wait_for_element(self, url: str, selector: str, timeout: int = 10) -> bool:
        """
        Wait for a specific element to appear on the page.
        
        Args:
            url: URL to monitor
            selector: CSS selector for the element
            timeout: Maximum wait time in seconds
            
        Returns:
            True if element appears, False if timeout
        """
        pass
    
    @abstractmethod
    def execute_javascript(self, url: str, script: str) -> Any:
        """
        Execute JavaScript on a web page.
        
        Args:
            url: URL to execute script on
            script: JavaScript code to execute
            
        Returns:
            Result of script execution
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the browser service is available and healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass