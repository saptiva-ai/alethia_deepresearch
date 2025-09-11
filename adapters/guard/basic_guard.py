import re
import urllib.parse
from typing import List, Dict, Any, Optional
import logging

from ports.guard_port import GuardPort, GuardAction, GuardResult

logger = logging.getLogger(__name__)

class BasicGuardAdapter(GuardPort):
    """Basic security and content filtering implementation."""
    
    def __init__(self):
        # Basic PII patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        }
        
        # Basic toxicity keywords (simple implementation)
        self.toxic_keywords = [
            'attack', 'hack', 'exploit', 'malware', 'virus', 'phishing',
            'scam', 'fraud', 'steal', 'illegal', 'criminal', 'terrorist'
        ]
        
        # Allowed domains list (example)
        self.allowed_domains = [
            'wikipedia.org', 'github.com', 'stackoverflow.com', 'arxiv.org',
            'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov', 'nature.com',
            'sciencedirect.com', 'ieee.org', 'acm.org'
        ]
        
        # Blocked domains list (example)
        self.blocked_domains = [
            'malicious-site.com', 'phishing-example.com'
        ]
    
    def check_content(self, content: str, context: str = "") -> GuardResult:
        """Check content for security, safety, and policy violations."""
        violations = []
        max_confidence = 0.0
        action = GuardAction.ALLOW
        
        # Check for PII
        pii_result = self.check_pii(content)
        if pii_result.action in [GuardAction.BLOCK, GuardAction.FILTER]:
            violations.append(f"PII detected: {pii_result.reason}")
            max_confidence = max(max_confidence, pii_result.confidence)
            action = GuardAction.FILTER  # Filter PII rather than block entirely
        
        # Check for toxicity
        toxicity_result = self.check_toxicity(content)
        if toxicity_result.action == GuardAction.BLOCK:
            violations.append(f"Toxic content: {toxicity_result.reason}")
            max_confidence = max(max_confidence, toxicity_result.confidence)
            action = GuardAction.BLOCK
        
        if violations:
            return GuardResult(
                action=action,
                confidence=max_confidence,
                reason="; ".join(violations),
                filtered_content=self.filter_content(content, ['pii']) if action == GuardAction.FILTER else None
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            confidence=1.0,
            reason="Content passed all security checks"
        )
    
    def check_pii(self, content: str) -> GuardResult:
        """Check for personally identifiable information (PII)."""
        detected_pii = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(content)
            if matches:
                detected_pii.append(f"{pii_type} ({len(matches)} instances)")
        
        if detected_pii:
            return GuardResult(
                action=GuardAction.FILTER,
                confidence=0.9,
                reason=f"PII detected: {', '.join(detected_pii)}",
                filtered_content=self.redact_pii(content)
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            confidence=0.8,
            reason="No PII detected"
        )
    
    def check_toxicity(self, content: str) -> GuardResult:
        """Check for toxic or harmful content."""
        content_lower = content.lower()
        detected_keywords = []
        
        for keyword in self.toxic_keywords:
            if keyword in content_lower:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            confidence = min(0.9, len(detected_keywords) * 0.3)  # Higher confidence with more keywords
            return GuardResult(
                action=GuardAction.WARN if len(detected_keywords) <= 2 else GuardAction.BLOCK,
                confidence=confidence,
                reason=f"Potentially toxic content detected: {', '.join(detected_keywords)}"
            )
        
        return GuardResult(
            action=GuardAction.ALLOW,
            confidence=0.7,
            reason="No toxic content detected"
        )
    
    def check_url_safety(self, url: str) -> GuardResult:
        """Check if a URL is safe to access."""
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check against blocked domains
            for blocked in self.blocked_domains:
                if domain == blocked or domain.endswith(f'.{blocked}'):
                    return GuardResult(
                        action=GuardAction.BLOCK,
                        confidence=0.95,
                        reason=f"URL domain {domain} is blocked"
                    )
            
            # Check against allowed domains (if using allowlist approach)
            # For now, we'll be permissive and only block known bad domains
            
            return GuardResult(
                action=GuardAction.ALLOW,
                confidence=0.8,
                reason="URL appears safe"
            )
        
        except Exception as e:
            return GuardResult(
                action=GuardAction.WARN,
                confidence=0.6,
                reason=f"Could not parse URL: {e}"
            )
    
    def filter_content(self, content: str, filters: List[str]) -> str:
        """Apply content filters to text."""
        filtered_content = content
        
        for filter_name in filters:
            if filter_name == 'pii':
                filtered_content = self.redact_pii(filtered_content)
        
        return filtered_content
    
    def redact_pii(self, content: str, pii_types: Optional[List[str]] = None) -> str:
        """Redact PII from content."""
        redacted_content = content
        
        patterns_to_use = self.pii_patterns
        if pii_types:
            patterns_to_use = {k: v for k, v in self.pii_patterns.items() if k in pii_types}
        
        for pii_type, pattern in patterns_to_use.items():
            if pii_type == 'email':
                redacted_content = pattern.sub('[EMAIL_REDACTED]', redacted_content)
            elif pii_type == 'phone':
                redacted_content = pattern.sub('[PHONE_REDACTED]', redacted_content)
            elif pii_type == 'ssn':
                redacted_content = pattern.sub('[SSN_REDACTED]', redacted_content)
            elif pii_type == 'credit_card':
                redacted_content = pattern.sub('[CARD_REDACTED]', redacted_content)
            elif pii_type == 'ip_address':
                redacted_content = pattern.sub('[IP_REDACTED]', redacted_content)
        
        return redacted_content
    
    def validate_domain(self, domain: str) -> bool:
        """Validate if a domain is allowed."""
        domain = domain.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check if domain is explicitly blocked
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith(f'.{blocked}'):
                return False
        
        # For now, allow all domains except blocked ones
        # In a production system, you might want to implement an allowlist
        return True
    
    def get_policy_violations(self, content: str) -> List[Dict[str, Any]]:
        """Get detailed policy violations found in content."""
        violations = []
        
        # Check PII violations
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(content)
            if matches:
                violations.append({
                    'type': 'pii',
                    'subtype': pii_type,
                    'severity': 'medium',
                    'count': len(matches),
                    'description': f'{pii_type.upper()} detected in content'
                })
        
        # Check toxicity violations
        detected_keywords = [kw for kw in self.toxic_keywords if kw in content.lower()]
        if detected_keywords:
            violations.append({
                'type': 'toxicity',
                'subtype': 'keywords',
                'severity': 'high' if len(detected_keywords) > 2 else 'medium',
                'keywords': detected_keywords,
                'description': 'Potentially toxic keywords detected'
            })
        
        return violations
    
    def health_check(self) -> bool:
        """Check if the guard service is available and healthy."""
        try:
            # Test basic functionality
            test_result = self.check_content("This is a test message")
            return test_result.action in [GuardAction.ALLOW, GuardAction.WARN]
        except Exception:
            return False