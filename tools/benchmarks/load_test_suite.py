#!/usr/bin/env python3
"""
Load Testing Suite for Aletheia Deep Research API.
Tests system performance under various load conditions and stress scenarios.
"""
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import random
import statistics
import time

import httpx


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""

    name: str
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    total_requests: int = 100
    ramp_up_time: float = 5.0  # seconds
    test_duration: float = 60.0  # seconds
    timeout: float = 30.0  # seconds
    think_time: float = 1.0  # seconds between requests
    enable_detailed_logging: bool = False


@dataclass
class RequestResult:
    """Result of a single request."""

    timestamp: float
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error: str | None = None
    response_size: int = 0


@dataclass
class LoadTestResults:
    """Results of a complete load test."""

    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    success_rate: float
    error_distribution: dict[str, int]
    throughput_timeline: list[tuple[float, int]]  # (timestamp, rps)


class LoadTestRunner:
    """Main load testing orchestrator."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: list[RequestResult] = []
        self.start_time = 0.0

    async def run_health_check_load_test(self) -> LoadTestResults:
        """Test health check endpoint under load."""
        print(f"🔥 Running health check load test: {self.config.concurrent_users} users, {self.config.total_requests} requests")

        async def make_health_request(session: httpx.AsyncClient, _user_id: int) -> RequestResult:
            start_time = time.time()
            try:
                response = await session.get(f"{self.config.base_url}/health", timeout=self.config.timeout)
                end_time = time.time()

                return RequestResult(
                    timestamp=start_time,
                    endpoint="/health",
                    method="GET",
                    status_code=response.status_code,
                    response_time=(end_time - start_time) * 1000,  # ms
                    success=response.status_code == 200,
                    response_size=len(response.content),
                )
            except Exception as e:
                end_time = time.time()
                return RequestResult(
                    timestamp=start_time,
                    endpoint="/health",
                    method="GET",
                    status_code=0,
                    response_time=(end_time - start_time) * 1000,
                    success=False,
                    error=str(e),
                )

        return await self._run_concurrent_test(make_health_request, "Health Check Load Test")

    async def run_research_endpoint_load_test(self) -> LoadTestResults:
        """Test research endpoint under load."""
        print(f"🔥 Running research endpoint load test: {self.config.concurrent_users} users, {self.config.total_requests} requests")

        # Sample queries for realistic testing
        test_queries = [
            "Market analysis of fintech industry 2024",
            "Competitive analysis of digital banks in Mexico",
            "Technology trends in artificial intelligence",
            "Economic impact of remote work policies",
            "Sustainable energy solutions analysis",
            "Cybersecurity threats in financial services",
            "Consumer behavior post-pandemic analysis",
            "Blockchain adoption in supply chain",
            "E-commerce growth strategies 2024",
            "Healthcare innovation technology review",
        ]

        async def make_research_request(session: httpx.AsyncClient, user_id: int) -> RequestResult:
            query = random.choice(test_queries)  # noqa: S311
            payload = {
                "query": f"{query} - User {user_id}",
                "scope": "comprehensive",
                "budget": random.randint(50, 150),  # noqa: S311
            }

            start_time = time.time()
            try:
                response = await session.post(f"{self.config.base_url}/research", json=payload, timeout=self.config.timeout)
                end_time = time.time()

                return RequestResult(
                    timestamp=start_time,
                    endpoint="/research",
                    method="POST",
                    status_code=response.status_code,
                    response_time=(end_time - start_time) * 1000,
                    success=response.status_code == 202,
                    response_size=len(response.content),
                )
            except Exception as e:
                end_time = time.time()
                return RequestResult(
                    timestamp=start_time,
                    endpoint="/research",
                    method="POST",
                    status_code=0,
                    response_time=(end_time - start_time) * 1000,
                    success=False,
                    error=str(e),
                )

        return await self._run_concurrent_test(make_research_request, "Research Endpoint Load Test")

    async def run_mixed_workload_test(self) -> LoadTestResults:
        """Test mixed workload of different endpoints."""
        print(f"🔥 Running mixed workload test: {self.config.concurrent_users} users, {self.config.total_requests} requests")

        async def make_mixed_request(session: httpx.AsyncClient, user_id: int) -> RequestResult:
            # Random endpoint selection (70% health, 30% research)
            if random.random() < 0.7:  # noqa: S311
                # Health check request
                start_time = time.time()
                try:
                    response = await session.get(f"{self.config.base_url}/health", timeout=self.config.timeout)
                    end_time = time.time()

                    return RequestResult(
                        timestamp=start_time,
                        endpoint="/health",
                        method="GET",
                        status_code=response.status_code,
                        response_time=(end_time - start_time) * 1000,
                        success=response.status_code == 200,
                        response_size=len(response.content),
                    )
                except Exception as e:
                    end_time = time.time()
                    return RequestResult(
                        timestamp=start_time,
                        endpoint="/health",
                        method="GET",
                        status_code=0,
                        response_time=(end_time - start_time) * 1000,
                        success=False,
                        error=str(e),
                    )
            else:
                # Research request
                payload = {
                    "query": f"Mixed workload test query {user_id}_{time.time()}",
                    "budget": 75,
                }

                start_time = time.time()
                try:
                    response = await session.post(
                        f"{self.config.base_url}/research",
                        json=payload,
                        timeout=self.config.timeout,
                    )
                    end_time = time.time()

                    return RequestResult(
                        timestamp=start_time,
                        endpoint="/research",
                        method="POST",
                        status_code=response.status_code,
                        response_time=(end_time - start_time) * 1000,
                        success=response.status_code == 202,
                        response_size=len(response.content),
                    )
                except Exception as e:
                    end_time = time.time()
                    return RequestResult(
                        timestamp=start_time,
                        endpoint="/research",
                        method="POST",
                        status_code=0,
                        response_time=(end_time - start_time) * 1000,
                        success=False,
                        error=str(e),
                    )

        return await self._run_concurrent_test(make_mixed_request, "Mixed Workload Test")

    async def run_stress_test(self) -> LoadTestResults:
        """Run stress test with gradually increasing load."""
        print(f"🔥 Running stress test: ramping up to {self.config.concurrent_users} users over {self.config.ramp_up_time}s")

        async def make_stress_request(session: httpx.AsyncClient, _user_id: int) -> RequestResult:
            # Simulate realistic user behavior with think time
            await asyncio.sleep(random.uniform(0, self.config.think_time))  # noqa: S311

            start_time = time.time()
            try:
                response = await session.get(f"{self.config.base_url}/health", timeout=self.config.timeout)
                end_time = time.time()

                return RequestResult(
                    timestamp=start_time,
                    endpoint="/health",
                    method="GET",
                    status_code=response.status_code,
                    response_time=(end_time - start_time) * 1000,
                    success=response.status_code == 200,
                    response_size=len(response.content),
                )
            except Exception as e:
                end_time = time.time()
                return RequestResult(
                    timestamp=start_time,
                    endpoint="/health",
                    method="GET",
                    status_code=0,
                    response_time=(end_time - start_time) * 1000,
                    success=False,
                    error=str(e),
                )

        return await self._run_ramp_up_test(make_stress_request, "Stress Test")

    async def _run_concurrent_test(self, request_func, test_name: str) -> LoadTestResults:
        """Run concurrent test with fixed number of users."""
        start_time = datetime.utcnow()
        self.start_time = time.time()
        all_results = []

        # Calculate requests per user
        requests_per_user = self.config.total_requests // self.config.concurrent_users
        remaining_requests = self.config.total_requests % self.config.concurrent_users

        async with httpx.AsyncClient() as session:
            # Create tasks for each user
            tasks = []

            for user_id in range(self.config.concurrent_users):
                user_requests = requests_per_user
                if user_id < remaining_requests:
                    user_requests += 1

                tasks.append(self._user_session(session, user_id, user_requests, request_func))

            # Run all user sessions concurrently
            results = await asyncio.gather(*tasks)

            # Flatten results
            for user_results in results:
                all_results.extend(user_results)

        end_time = datetime.utcnow()

        return self._analyze_results(all_results, start_time, end_time, test_name)

    async def _run_ramp_up_test(self, request_func, test_name: str) -> LoadTestResults:
        """Run test with gradual ramp-up of users."""
        start_time = datetime.utcnow()
        self.start_time = time.time()
        all_results = []

        # Calculate user ramp-up schedule
        ramp_up_interval = self.config.ramp_up_time / self.config.concurrent_users
        requests_per_user = max(1, self.config.total_requests // self.config.concurrent_users)

        async with httpx.AsyncClient() as session:
            tasks = []

            for user_id in range(self.config.concurrent_users):
                # Stagger user start times
                start_delay = user_id * ramp_up_interval

                tasks.append(self._delayed_user_session(session, user_id, requests_per_user, request_func, start_delay))

            # Run all user sessions with staggered starts
            results = await asyncio.gather(*tasks)

            # Flatten results
            for user_results in results:
                all_results.extend(user_results)

        end_time = datetime.utcnow()

        return self._analyze_results(all_results, start_time, end_time, test_name)

    async def _user_session(self, session: httpx.AsyncClient, user_id: int, num_requests: int, request_func) -> list[RequestResult]:
        """Simulate a single user session."""
        results = []

        for request_num in range(num_requests):
            result = await request_func(session, user_id)
            results.append(result)

            if self.config.enable_detailed_logging:
                status = "✅" if result.success else "❌"
                print(f"{status} User {user_id}, Request {request_num + 1}: {result.response_time:.1f}ms")

            # Think time between requests
            if request_num < num_requests - 1:  # Not the last request
                await asyncio.sleep(self.config.think_time)

        return results

    async def _delayed_user_session(
        self,
        session: httpx.AsyncClient,
        user_id: int,
        num_requests: int,
        request_func,
        delay: float,
    ) -> list[RequestResult]:
        """User session with initial delay for ramp-up."""
        await asyncio.sleep(delay)
        return await self._user_session(session, user_id, num_requests, request_func)

    def _analyze_results(self, results: list[RequestResult], start_time: datetime, end_time: datetime, test_name: str) -> LoadTestResults:
        """Analyze test results and generate comprehensive report."""
        if not results:
            raise ValueError("No results to analyze")

        # Basic metrics
        successful_requests = sum(1 for r in results if r.success)
        failed_requests = len(results) - successful_requests
        success_rate = (successful_requests / len(results)) * 100

        # Response time metrics
        response_times = [r.response_time for r in results if r.success]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)

            response_times_sorted = sorted(response_times)
            p95_index = int(0.95 * len(response_times_sorted))
            p99_index = int(0.99 * len(response_times_sorted))
            p95_response_time = response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else max_response_time
            p99_response_time = response_times_sorted[p99_index] if p99_index < len(response_times_sorted) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p95_response_time = p99_response_time = 0.0

        # Throughput calculation
        test_duration = (end_time - start_time).total_seconds()
        requests_per_second = len(results) / test_duration if test_duration > 0 else 0

        # Error distribution
        error_distribution = {}
        for result in results:
            if not result.success and result.error:
                error_type = type(result.error).__name__ if hasattr(result.error, "__class__") else str(result.error)[:50]
                error_distribution[error_type] = error_distribution.get(error_type, 0) + 1

        # Throughput timeline (requests per 5-second window)
        throughput_timeline = self._calculate_throughput_timeline(results)

        return LoadTestResults(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            total_requests=len(results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            success_rate=success_rate,
            error_distribution=error_distribution,
            throughput_timeline=throughput_timeline,
        )

    def _calculate_throughput_timeline(self, results: list[RequestResult]) -> list[tuple[float, int]]:
        """Calculate throughput over time in 5-second windows."""
        if not results:
            return []

        # Group requests by 5-second windows
        window_size = 5.0  # seconds
        start_timestamp = min(r.timestamp for r in results)
        end_timestamp = max(r.timestamp for r in results)

        timeline = []
        current_time = start_timestamp

        while current_time < end_timestamp:
            window_end = current_time + window_size
            requests_in_window = sum(1 for r in results if current_time <= r.timestamp < window_end)
            rps = requests_in_window / window_size
            timeline.append((current_time - start_timestamp, rps))
            current_time = window_end

        return timeline


class LoadTestReporter:
    """Generate detailed load test reports."""

    @staticmethod
    def print_summary(results: LoadTestResults):
        """Print a comprehensive summary of load test results."""
        print("\n" + "=" * 80)
        print(f"📊 LOAD TEST RESULTS: {results.config.name}")
        print("=" * 80)

        # Test Configuration
        print("🔧 Configuration:")
        print(f"   • Concurrent Users: {results.config.concurrent_users}")
        print(f"   • Total Requests: {results.total_requests}")
        print(f"   • Test Duration: {(results.end_time - results.start_time).total_seconds():.1f}s")
        print(f"   • Base URL: {results.config.base_url}")

        # Performance Metrics
        print("\n⚡ Performance Metrics:")
        print(f"   • Requests per Second: {results.requests_per_second:.2f}")
        print(f"   • Average Response Time: {results.avg_response_time:.1f}ms")
        print(f"   • Min Response Time: {results.min_response_time:.1f}ms")
        print(f"   • Max Response Time: {results.max_response_time:.1f}ms")
        print(f"   • 50th Percentile (Median): {results.p50_response_time:.1f}ms")
        print(f"   • 95th Percentile: {results.p95_response_time:.1f}ms")
        print(f"   • 99th Percentile: {results.p99_response_time:.1f}ms")

        # Success/Failure Metrics
        print("\n✅ Reliability Metrics:")
        print(f"   • Success Rate: {results.success_rate:.1f}%")
        print(f"   • Successful Requests: {results.successful_requests}")
        print(f"   • Failed Requests: {results.failed_requests}")

        # Error Analysis
        if results.error_distribution:
            print("\n❌ Error Distribution:")
            for error, count in results.error_distribution.items():
                percentage = (count / results.total_requests) * 100
                print(f"   • {error}: {count} ({percentage:.1f}%)")

        # Performance Assessment
        print("\n🎯 Performance Assessment:")
        LoadTestReporter._assess_performance(results)

        print("=" * 80)

    @staticmethod
    def _assess_performance(results: LoadTestResults):
        """Provide performance assessment and recommendations."""
        # Response time assessment
        if results.avg_response_time < 100:
            print("   • ✅ Excellent response times (<100ms average)")
        elif results.avg_response_time < 500:
            print("   • 🟡 Good response times (<500ms average)")
        elif results.avg_response_time < 1000:
            print("   • 🟠 Acceptable response times (<1s average)")
        else:
            print("   • ❌ Poor response times (>1s average) - optimization needed")

        # Success rate assessment
        if results.success_rate >= 99.9:
            print("   • ✅ Excellent reliability (>99.9% success)")
        elif results.success_rate >= 99.0:
            print("   • 🟡 Good reliability (>99% success)")
        elif results.success_rate >= 95.0:
            print("   • 🟠 Acceptable reliability (>95% success)")
        else:
            print("   • ❌ Poor reliability (<95% success) - investigation needed")

        # Throughput assessment
        if results.requests_per_second > 1000:
            print("   • ✅ High throughput (>1000 req/s)")
        elif results.requests_per_second > 100:
            print("   • 🟡 Good throughput (>100 req/s)")
        elif results.requests_per_second > 10:
            print("   • 🟠 Moderate throughput (>10 req/s)")
        else:
            print("   • ❌ Low throughput (<10 req/s) - scaling needed")

        # P95/P99 assessment
        if results.p95_response_time < 200:
            print("   • ✅ Consistent performance (P95 <200ms)")
        elif results.p95_response_time < 1000:
            print("   • 🟡 Generally consistent (P95 <1s)")
        else:
            print("   • ❌ Inconsistent performance (P95 >1s) - investigate outliers")

    @staticmethod
    def save_detailed_report(results: LoadTestResults, filename: str):
        """Save detailed results to JSON file."""
        report_data = asdict(results)
        # Convert datetime objects to strings
        report_data["start_time"] = results.start_time.isoformat()
        report_data["end_time"] = results.end_time.isoformat()

        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"💾 Detailed results saved to: {filename}")


async def run_comprehensive_load_tests():
    """Run all load testing scenarios."""
    print("🚀 Starting Comprehensive Load Testing Suite for Aletheia Deep Research")
    print("=" * 80)

    # Test configurations
    test_configs = [
        LoadTestConfig(name="Light Load Test", concurrent_users=5, total_requests=50, think_time=0.5),
        LoadTestConfig(name="Moderate Load Test", concurrent_users=15, total_requests=150, think_time=1.0),
        LoadTestConfig(name="Heavy Load Test", concurrent_users=30, total_requests=300, think_time=0.2),
        LoadTestConfig(
            name="Stress Test",
            concurrent_users=50,
            total_requests=200,
            ramp_up_time=10.0,
            think_time=0.1,
        ),
    ]

    all_results = []

    for config in test_configs:
        runner = LoadTestRunner(config)

        try:
            print(f"\n🎯 Running {config.name}...")

            # Run different test types
            health_results = await runner.run_health_check_load_test()
            LoadTestReporter.print_summary(health_results)
            all_results.append(health_results)

            # Brief pause between tests
            await asyncio.sleep(2)

            research_results = await runner.run_research_endpoint_load_test()
            LoadTestReporter.print_summary(research_results)
            all_results.append(research_results)

            await asyncio.sleep(2)

            # Mixed workload for this configuration
            config.name = f"{config.name} - Mixed Workload"
            runner.config = config
            mixed_results = await runner.run_mixed_workload_test()
            LoadTestReporter.print_summary(mixed_results)
            all_results.append(mixed_results)

        except Exception as e:
            print(f"❌ Error during {config.name}: {e}")

    # Generate overall summary
    print("\n" + "=" * 80)
    print("📈 OVERALL LOAD TEST SUMMARY")
    print("=" * 80)

    if all_results:
        avg_success_rate = statistics.mean(r.success_rate for r in all_results)
        avg_response_time = statistics.mean(r.avg_response_time for r in all_results)
        max_throughput = max(r.requests_per_second for r in all_results)

        print(f"• Tests Completed: {len(all_results)}")
        print(f"• Average Success Rate: {avg_success_rate:.1f}%")
        print(f"• Average Response Time: {avg_response_time:.1f}ms")
        print(f"• Peak Throughput: {max_throughput:.1f} req/s")

        # Save summary
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        for i, result in enumerate(all_results):
            filename = f"load_test_results_{timestamp}_{i+1}.json"
            LoadTestReporter.save_detailed_report(result, filename)

        # Overall assessment
        if avg_success_rate >= 95 and avg_response_time < 1000:
            print("\n🎉 ✅ System passed load testing - Ready for production deployment!")
        elif avg_success_rate >= 90 and avg_response_time < 2000:
            print("\n🟡 System shows acceptable performance under load - Monitor closely in production")
        else:
            print("\n❌ System needs optimization before production deployment")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_load_tests())
