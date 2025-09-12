from datetime import datetime
import hashlib
import logging
import re
from typing import Any, List, Optional
from urllib.parse import urljoin

import requests

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from domain.models.evidence import Evidence, EvidenceSource
from ports.browser_port import BrowserPort

logger = logging.getLogger(__name__)

class BasicBrowserAdapter(BrowserPort):
    """Basic browser implementation using requests and BeautifulSoup."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.timeout = 30

        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup4 not available. Install with: pip install beautifulsoup4")

    def navigate_to(self, url: str) -> bool:
        """Navigate to a specific URL."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False

    def extract_text(self, url: str) -> Optional[str]:
        """Extract text content from a web page."""
        if not BS4_AVAILABLE:
            logger.error("BeautifulSoup4 required for text extraction")
            return None

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\\n".join(chunk for chunk in chunks if chunk)

            return text if text else None

        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return None

    def extract_evidence(self, url: str, context: str = "") -> Optional[Evidence]:
        """Extract structured evidence from a web page."""
        text_content = self.extract_text(url)
        if not text_content:
            return None

        try:
            # Get page title if possible
            response = self.session.get(url, timeout=self.timeout)
            title = url

            if BS4_AVAILABLE:
                soup = BeautifulSoup(response.content, "html.parser")
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text().strip()

            # Create evidence ID
            evidence_id = f"web_{hashlib.md5(f'{url}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:8]}"

            # Create evidence source
            source = EvidenceSource(
                url=url,
                title=title,
                fetched_at=datetime.utcnow()
            )

            # Limit excerpt to first 1000 characters
            excerpt = text_content[:1000] if len(text_content) > 1000 else text_content

            # Create evidence object
            evidence = Evidence(
                id=evidence_id,
                source=source,
                excerpt=excerpt,
                tool_call_id=f"browser:extract:{evidence_id}",
                score=0.8,  # Default confidence
                tags=["web", "browser", "extracted"],
                cit_key=f"WebPage{evidence_id}"
            )

            return evidence

        except Exception as e:
            logger.error(f"Error creating evidence from {url}: {e}")
            return None

    def take_screenshot(self, url: str, save_path: str) -> bool:
        """Take a screenshot of a web page."""
        # This would require a headless browser like Selenium or Playwright
        # For now, this is a placeholder implementation
        logger.warning("Screenshot functionality not implemented in basic browser adapter")
        return False

    def extract_links(self, url: str, filter_pattern: Optional[str] = None) -> List[str]:
        """Extract links from a web page."""
        if not BS4_AVAILABLE:
            logger.error("BeautifulSoup4 required for link extraction")
            return []

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            links = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)

                # Apply filter pattern if provided
                if filter_pattern:
                    if re.search(filter_pattern, absolute_url):
                        links.append(absolute_url)
                else:
                    links.append(absolute_url)

            return list(set(links))  # Remove duplicates

        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []

    def wait_for_element(self, url: str, selector: str, timeout: int = 10) -> bool:
        """Wait for a specific element to appear on the page."""
        # This would require a dynamic browser like Selenium
        # For static content, we just check if the element exists
        if not BS4_AVAILABLE:
            logger.error("BeautifulSoup4 required for element checking")
            return False

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            element = soup.select_one(selector)

            return element is not None

        except Exception as e:
            logger.error(f"Error checking for element {selector} on {url}: {e}")
            return False

    def execute_javascript(self, url: str, script: str) -> Any:
        """Execute JavaScript on a web page."""
        # This requires a browser with JavaScript engine
        # Not supported in basic requests/BeautifulSoup implementation
        logger.warning("JavaScript execution not supported in basic browser adapter")
        return None

    def health_check(self) -> bool:
        """Check if the browser service is available and healthy."""
        try:
            # Test with a simple HTTP request
            response = self.session.get("https://httpbin.org/status/200", timeout=10)
            return response.status_code == 200
        except Exception:
            # Fallback to testing local connectivity
            try:
                response = self.session.get("https://google.com", timeout=5)
                return response.status_code == 200
            except Exception:
                return False
