"""
Rate limiting and security middleware for Aletheia Deep Research API.
Implements various rate limiting strategies and security policies.
"""
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """Configuration for a rate limiting rule."""

    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int | None = None  # Allow burst of requests
    whitelist_ips: list[str] = field(default_factory=list)
    blacklist_ips: list[str] = field(default_factory=list)


@dataclass
class SecurityPolicy:
    """Security policy configuration."""

    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])
    require_api_key: bool = False
    api_key_header: str = "X-API-Key"
    block_suspicious_queries: bool = True
    max_query_length: int = 1000
    suspicious_patterns: list[str] = field(
        default_factory=lambda: [
            "UNION SELECT",
            "DROP TABLE",
            "INSERT INTO",
            "DELETE FROM",
            "UPDATE SET",
            "CREATE TABLE",
            "<script>",
            "javascript:",
            "eval(",
            "exec(",
            "system(",
            "import os",
        ]
    )


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def is_allowed(self, identifier: str, request: Request) -> tuple[bool, dict | None]:
        """Check if request is allowed. Returns (allowed, metadata)."""
        pass

    @abstractmethod
    def get_remaining_quota(self, identifier: str) -> dict:
        """Get remaining quota information."""
        pass


class TokenBucketRateLimiter(RateLimiter):
    """Token bucket based rate limiter with multiple time windows."""

    def __init__(self, rule: RateLimitRule):
        self.rule = rule
        # Storage for different time windows: {identifier: {window: (count, timestamp)}}
        self.minute_buckets: dict[str, tuple[int, float]] = {}
        self.hour_buckets: dict[str, tuple[int, float]] = {}
        self.day_buckets: dict[str, tuple[int, float]] = {}
        self.burst_buckets: dict[str, deque] = defaultdict(deque)

    async def is_allowed(self, identifier: str, request: Request) -> tuple[bool, dict | None]:
        """Check if request is within rate limits."""
        current_time = time.time()

        # Check IP whitelist/blacklist
        client_ip = self._get_client_ip(request)
        if client_ip in self.rule.blacklist_ips:
            return False, {"reason": "IP blacklisted", "retry_after": 3600}

        if client_ip in self.rule.whitelist_ips:
            return True, {"whitelisted": True}

        # Check burst limit first (if configured)
        if self.rule.burst_limit and not self._check_burst_limit(identifier, current_time):
            return False, {"reason": "Burst limit exceeded", "retry_after": 60}

        # Check minute limit
        if not self._check_time_window(identifier, current_time, 60, self.rule.requests_per_minute, self.minute_buckets):
            retry_after = 60 - (current_time % 60)
            return False, {"reason": "Minute limit exceeded", "retry_after": retry_after}

        # Check hour limit
        if not self._check_time_window(identifier, current_time, 3600, self.rule.requests_per_hour, self.hour_buckets):
            retry_after = 3600 - (current_time % 3600)
            return False, {"reason": "Hour limit exceeded", "retry_after": retry_after}

        # Check day limit
        if not self._check_time_window(identifier, current_time, 86400, self.rule.requests_per_day, self.day_buckets):
            retry_after = 86400 - (current_time % 86400)
            return False, {"reason": "Daily limit exceeded", "retry_after": retry_after}

        # All checks passed - increment counters
        self._increment_counters(identifier, current_time)

        return True, {"allowed": True}

    def _check_burst_limit(self, identifier: str, current_time: float) -> bool:
        """Check burst limit using sliding window."""
        burst_window = 10.0  # 10 second window for burst
        burst_queue = self.burst_buckets[identifier]

        # Remove old entries
        while burst_queue and current_time - burst_queue[0] > burst_window:
            burst_queue.popleft()

        if len(burst_queue) >= self.rule.burst_limit:
            return False

        burst_queue.append(current_time)
        return True

    def _check_time_window(
        self,
        identifier: str,
        current_time: float,
        window_size: int,
        limit: int,
        bucket: dict[str, tuple[int, float]],
    ) -> bool:
        """Check if request is within time window limit."""
        window_start = int(current_time // window_size) * window_size

        if identifier in bucket:
            count, timestamp = bucket[identifier]
            if timestamp >= window_start:
                return count < limit

        return True  # First request in this window

    def _increment_counters(self, identifier: str, current_time: float):
        """Increment all relevant counters."""
        # Minute counter
        minute_start = int(current_time // 60) * 60
        if identifier in self.minute_buckets and self.minute_buckets[identifier][1] >= minute_start:
            count, _ = self.minute_buckets[identifier]
            self.minute_buckets[identifier] = (count + 1, minute_start)
        else:
            self.minute_buckets[identifier] = (1, minute_start)

        # Hour counter
        hour_start = int(current_time // 3600) * 3600
        if identifier in self.hour_buckets and self.hour_buckets[identifier][1] >= hour_start:
            count, _ = self.hour_buckets[identifier]
            self.hour_buckets[identifier] = (count + 1, hour_start)
        else:
            self.hour_buckets[identifier] = (1, hour_start)

        # Day counter
        day_start = int(current_time // 86400) * 86400
        if identifier in self.day_buckets and self.day_buckets[identifier][1] >= day_start:
            count, _ = self.day_buckets[identifier]
            self.day_buckets[identifier] = (count + 1, day_start)
        else:
            self.day_buckets[identifier] = (1, day_start)

    def get_remaining_quota(self, identifier: str) -> dict:
        """Get remaining quota for all time windows."""
        current_time = time.time()

        # Calculate remaining quotas
        minute_remaining = self._get_window_remaining(identifier, current_time, 60, self.rule.requests_per_minute, self.minute_buckets)
        hour_remaining = self._get_window_remaining(identifier, current_time, 3600, self.rule.requests_per_hour, self.hour_buckets)
        day_remaining = self._get_window_remaining(identifier, current_time, 86400, self.rule.requests_per_day, self.day_buckets)

        return {
            "minute_remaining": minute_remaining,
            "hour_remaining": hour_remaining,
            "day_remaining": day_remaining,
            "reset_times": {
                "minute_reset": int(current_time // 60 + 1) * 60,
                "hour_reset": int(current_time // 3600 + 1) * 3600,
                "day_reset": int(current_time // 86400 + 1) * 86400,
            },
        }

    def _get_window_remaining(
        self,
        identifier: str,
        current_time: float,
        window_size: int,
        limit: int,
        bucket: dict[str, tuple[int, float]],
    ) -> int:
        """Get remaining requests in time window."""
        window_start = int(current_time // window_size) * window_size

        if identifier in bucket:
            count, timestamp = bucket[identifier]
            if timestamp >= window_start:
                return max(0, limit - count)

        return limit

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header first (for proxy/load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class SecurityValidator:
    """Validates requests against security policies."""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    async def validate_request(self, request: Request) -> tuple[bool, str | None]:
        """Validate request against security policy."""

        # Check request size
        if hasattr(request, "_body"):
            body_size = len(request._body)
            if body_size > self.policy.max_request_size:
                return (
                    False,
                    f"Request too large: {body_size} bytes > {self.policy.max_request_size}",
                )

        # Check API key if required
        if self.policy.require_api_key:
            api_key = request.headers.get(self.policy.api_key_header)
            if not api_key:
                return False, f"Missing required header: {self.policy.api_key_header}"

            # You would implement actual API key validation here
            if not self._validate_api_key(api_key):
                return False, "Invalid API key"

        # Check for suspicious content
        if self.policy.block_suspicious_queries:
            body = await self._get_request_body(request)
            if body and self._contains_suspicious_patterns(body):
                return False, "Request contains suspicious content"

        return True, None

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key. Implement your key validation logic here."""
        # For demo purposes - in production, check against database/cache
        return len(api_key) >= 32 and api_key.startswith("ak_")

    async def _get_request_body(self, request: Request) -> str | None:
        """Extract request body for analysis."""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                return body.decode("utf-8", errors="ignore")
        except Exception as exc:
            logger.debug("Request body extraction failed: %s", exc)
        return None

    def _contains_suspicious_patterns(self, content: str) -> bool:
        """Check if content contains suspicious patterns."""
        content_lower = content.lower()
        return any(pattern.lower() in content_lower for pattern in self.policy.suspicious_patterns)


class ProductionSecurityMiddleware:
    """Production-ready security middleware combining rate limiting and validation."""

    def __init__(self, rate_limit_rules: dict[str, RateLimitRule], security_policy: SecurityPolicy):
        self.rate_limiters = {endpoint: TokenBucketRateLimiter(rule) for endpoint, rule in rate_limit_rules.items()}
        self.default_limiter = TokenBucketRateLimiter(
            RateLimitRule(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=10,
            )
        )
        self.security_validator = SecurityValidator(security_policy)
        self.blocked_ips: set = set()
        self.suspicious_activity: dict[str, int] = defaultdict(int)

    async def __call__(self, request: Request, call_next):
        """Process request through security middleware."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return self._create_error_response(status.HTTP_403_FORBIDDEN, "IP address blocked", request)

        # Security validation
        is_valid, error_message = await self.security_validator.validate_request(request)
        if not is_valid:
            await self._log_suspicious_activity(client_ip, error_message)
            return self._create_error_response(status.HTTP_400_BAD_REQUEST, f"Security validation failed: {error_message}", request)

        # Rate limiting
        identifier = self._get_rate_limit_identifier(request)
        limiter = self._get_rate_limiter(request.url.path)

        is_allowed, metadata = await limiter.is_allowed(identifier, request)
        if not is_allowed:
            await self._log_rate_limit_exceeded(client_ip, request.url.path)

            retry_after = metadata.get("retry_after", 60) if metadata else 60
            headers = {"Retry-After": str(int(retry_after))}

            return self._create_error_response(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Rate limit exceeded: {metadata.get('reason', 'Too many requests')}",
                request,
                headers,
            )

        # Add rate limiting headers to response
        quota_info = limiter.get_remaining_quota(identifier)

        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add rate limit headers
        response.headers["X-RateLimit-Minute-Remaining"] = str(quota_info["minute_remaining"])
        response.headers["X-RateLimit-Hour-Remaining"] = str(quota_info["hour_remaining"])
        response.headers["X-RateLimit-Day-Remaining"] = str(quota_info["day_remaining"])

        # Add performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response

    def _get_rate_limit_identifier(self, request: Request) -> str:
        """Generate identifier for rate limiting (IP + User-Agent hash)."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # Create a hash to avoid storing full user agent strings
        identifier_hash = hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()
        return f"{client_ip}:{identifier_hash[:8]}"

    def _get_rate_limiter(self, path: str) -> RateLimiter:
        """Get appropriate rate limiter for endpoint."""
        # Check for specific endpoint rules
        for endpoint_pattern, limiter in self.rate_limiters.items():
            if endpoint_pattern in path:
                return limiter

        return self.default_limiter

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"

    async def _log_suspicious_activity(self, client_ip: str, reason: str):
        """Log and track suspicious activity."""
        self.suspicious_activity[client_ip] += 1

        # Block IP after multiple suspicious requests
        if self.suspicious_activity[client_ip] >= 5:
            self.blocked_ips.add(client_ip)
            print(f"🚨 SECURITY: Blocked IP {client_ip} after {self.suspicious_activity[client_ip]} suspicious requests")

        print(f"🔒 SECURITY: Suspicious activity from {client_ip}: {reason}")

    async def _log_rate_limit_exceeded(self, client_ip: str, path: str):
        """Log rate limit violations."""
        print(f"⚠️ RATE_LIMIT: {client_ip} exceeded rate limit for {path}")

    def _create_error_response(self, status_code: int, message: str, request: Request, headers: dict = None) -> JSONResponse:
        """Create standardized error response."""
        error_response = {
            "error": {
                "code": status_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            }
        }

        return JSONResponse(status_code=status_code, content=error_response, headers=headers or {})


# Production-ready configurations
PRODUCTION_RATE_LIMITS = {
    "/research": RateLimitRule(
        requests_per_minute=10,  # Research is expensive
        requests_per_hour=100,
        requests_per_day=500,
        burst_limit=3,
    ),
    "/deep-research": RateLimitRule(
        requests_per_minute=5,  # Deep research is very expensive
        requests_per_hour=50,
        requests_per_day=200,
        burst_limit=2,
    ),
    "/health": RateLimitRule(
        requests_per_minute=60,  # Health checks are lightweight
        requests_per_hour=3600,
        requests_per_day=86400,
        burst_limit=20,
    ),
    "/reports": RateLimitRule(
        requests_per_minute=30,  # Moderate cost
        requests_per_hour=500,
        requests_per_day=2000,
        burst_limit=10,
    ),
}

PRODUCTION_SECURITY_POLICY = SecurityPolicy(
    max_request_size=5 * 1024 * 1024,  # 5MB limit
    require_api_key=False,  # Set to True for production with API keys
    block_suspicious_queries=True,
    max_query_length=2000,
    suspicious_patterns=[
        # SQL injection patterns
        "UNION SELECT",
        "DROP TABLE",
        "INSERT INTO",
        "DELETE FROM",
        "UPDATE SET",
        "CREATE TABLE",
        "ALTER TABLE",
        "TRUNCATE",
        # Script injection patterns
        "<script>",
        "</script>",
        "javascript:",
        "onload=",
        "onerror=",
        # Command injection patterns
        "system(",
        "exec(",
        "eval(",
        "os.system",
        "subprocess.",
        # Path traversal patterns
        "../",
        "..\\",
        "/etc/passwd",
        "/etc/shadow",
        # Other suspicious patterns
        "union all select",
        "concat(",
        "char(",
        "ascii(",
    ],
)
