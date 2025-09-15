#!/usr/bin/env python3
"""
Quick Load Test for Aletheia Deep Research API.
"""
import asyncio
from datetime import datetime
import statistics
import time

import httpx


async def quick_load_test():
    """Run a quick load test to verify system performance."""
    print("🚀 Quick Load Test for Aletheia Deep Research API")
    print("=" * 50)

    base_url = "http://localhost:8000"
    concurrent_users = 10
    requests_per_user = 5

    async def make_health_request(user_id: int) -> dict:
        """Make a health check request."""
        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=10.0)
                end_time = time.time()

                return {
                    "user_id": user_id,
                    "success": response.status_code == 200,
                    "response_time": (end_time - start_time) * 1000,
                    "status_code": response.status_code,
                }
        except Exception as e:
            end_time = time.time()
            return {
                "user_id": user_id,
                "success": False,
                "response_time": (end_time - start_time) * 1000,
                "error": str(e),
                "status_code": 0,
            }

    print(f"🎯 Testing {concurrent_users} concurrent users, {requests_per_user} requests each")
    print(f"📡 Target: {base_url}/health")

    start_time = datetime.utcnow()

    # Create tasks for all requests
    tasks = []
    for user_id in range(concurrent_users):
        for _ in range(requests_per_user):
            tasks.append(make_health_request(user_id))

    # Execute all requests concurrently
    results = await asyncio.gather(*tasks)

    end_time = datetime.utcnow()
    test_duration = (end_time - start_time).total_seconds()

    # Analyze results
    successful_requests = sum(1 for r in results if r["success"])
    failed_requests = len(results) - successful_requests
    success_rate = (successful_requests / len(results)) * 100

    response_times = [r["response_time"] for r in results if r["success"]]

    if response_times:
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
    else:
        avg_response_time = min_response_time = max_response_time = p95_response_time = 0

    requests_per_second = len(results) / test_duration

    # Print results
    print("\n📊 LOAD TEST RESULTS")
    print("=" * 50)
    print(f"⏱️  Test Duration: {test_duration:.1f}s")
    print(f"📈 Total Requests: {len(results)}")
    print(f"✅ Successful: {successful_requests}")
    print(f"❌ Failed: {failed_requests}")
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    print(f"⚡ Requests/sec: {requests_per_second:.1f}")
    print(f"🕐 Avg Response Time: {avg_response_time:.1f}ms")
    print(f"📊 Min/Max Response: {min_response_time:.1f}ms / {max_response_time:.1f}ms")
    print(f"📈 95th Percentile: {p95_response_time:.1f}ms")

    # Assessment
    print("\n🎯 PERFORMANCE ASSESSMENT")
    print("=" * 50)

    if success_rate >= 99:
        print("✅ Excellent reliability (>99% success)")
    elif success_rate >= 95:
        print("🟡 Good reliability (>95% success)")
    else:
        print("❌ Poor reliability (<95% success)")

    if avg_response_time < 100:
        print("✅ Excellent response times (<100ms)")
    elif avg_response_time < 500:
        print("🟡 Good response times (<500ms)")
    else:
        print("❌ Slow response times (>500ms)")

    if requests_per_second > 100:
        print("✅ High throughput (>100 req/s)")
    elif requests_per_second > 50:
        print("🟡 Good throughput (>50 req/s)")
    else:
        print("🟠 Moderate throughput (<50 req/s)")

    print("=" * 50)

    return {
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "requests_per_second": requests_per_second,
        "test_passed": success_rate >= 95 and avg_response_time < 1000,
    }


if __name__ == "__main__":
    result = asyncio.run(quick_load_test())
    if result["test_passed"]:
        print("🎉 Load test PASSED - System ready for production!")
    else:
        print("⚠️ Load test FAILED - System needs optimization")
