"""
Locust-based Stress Test Script for Performance Testing Workshop

TEACHING PURPOSE: This script demonstrates how to run Locust programmatically
to test CPU, memory, and latency bottlenecks together.

Usage:
    python stress_test.py                    # Default: 20 users, 30 seconds, combined stress test
    python stress_test.py --users 50         # 50 concurrent users
    python stress_test.py --duration 60       # Run for 60 seconds
    python stress_test.py --headless          # Run without web UI
"""

import argparse
import sys

# Import Locust modules
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import gevent


# ============================================================================
# LOCUST USER CLASSES FOR DIFFERENT SCENARIOS
# ============================================================================

class CombinedStressUser(HttpUser):
    """
    Combined stress test - tests CPU, Memory, and Latency together.
    
    TEACHING PURPOSE: Demonstrates how different types of bottlenecks
    affect system performance simultaneously. Perfect for watching
    CPU and Memory metrics in Grafana.
    """
    wait_time = between(0.2, 1.0)
    
    @task(5)
    def stress_cpu(self):
        """CPU stress - configurable CPU-intensive computation."""
        self.client.post("/stress/cpu", name="POST /stress/cpu")
    
    @task(4)
    def stress_memory(self):
        """Memory stress - allocates configurable amount of memory."""
        self.client.post("/stress/memory", name="POST /stress/memory")
    
    @task(3)
    def stress_both(self):
        """Combined CPU and memory stress."""
        self.client.post("/stress/both", name="POST /stress/both")
    
    @task(3)
    def heavy_endpoint(self):
        """Heavy endpoint - high latency (800-1200ms)."""
        self.client.get("/heavy", name="GET /heavy")
    
    @task(2)
    def products(self):
        """Products - variable latency (100-300ms)."""
        self.client.get("/products", name="GET /products")
    
    @task(1)
    def login(self):
        """Login - CPU-intensive."""
        self.client.post("/login", name="POST /login")
    
    @task(1)
    def health_check(self):
        """Health check - fast endpoint."""
        self.client.get("/health", name="GET /health")


class CPUScenarioUser(HttpUser):
    """
    CPU-focused scenario - emphasizes CPU-intensive endpoints.
    
    TEACHING PURPOSE: Demonstrates CPU bottlenecks by focusing on
    CPU-intensive tasks like password hashing, encryption, etc.
    """
    wait_time = between(0.1, 0.5)  # Faster wait time to increase load
    
    @task(10)
    def stress_cpu(self):
        """CPU stress endpoint - configurable CPU-intensive task."""
        self.client.post("/stress/cpu", name="POST /stress/cpu")
    
    @task(5)
    def login(self):
        """Login - CPU-intensive endpoint."""
        self.client.post("/login", name="POST /login")
    
    @task(1)
    def health_check(self):
        """Occasional health check."""
        self.client.get("/health", name="GET /health")


class PoolScenarioUser(HttpUser):
    """
    Connection pool scenario - emphasizes pool-limited endpoints.
    
    TEACHING PURPOSE: Demonstrates connection pool bottlenecks by
    focusing on endpoints that use the connection pool.
    """
    wait_time = between(0.1, 0.3)  # Faster to saturate pool quickly
    
    @task(5)
    def view_product_detail(self):
        """View product detail - uses connection pool."""
        self.client.get("/products/1", name="GET /products/{id}")
    
    @task(5)
    def checkout(self):
        """Checkout - uses connection pool."""
        self.client.post("/checkout", name="POST /checkout")
    
    @task(1)
    def health_check(self):
        """Occasional health check."""
        self.client.get("/health", name="GET /health")


class LatencyScenarioUser(HttpUser):
    """
    Latency-focused scenario - emphasizes high-latency endpoints.
    
    TEACHING PURPOSE: Demonstrates how slow endpoints affect
    overall system performance and p95 metrics.
    """
    wait_time = between(0.5, 2.0)  # Longer wait time
    
    @task(3)
    def heavy_endpoint(self):
        """Heavy endpoint - high latency (800-1200ms)."""
        self.client.get("/heavy", name="GET /heavy")
    
    @task(2)
    def products(self):
        """Products - variable latency (100-300ms)."""
        self.client.get("/products", name="GET /products")
    
    @task(1)
    def health_check(self):
        """Occasional health check."""
        self.client.get("/health", name="GET /health")


class MemoryScenarioUser(HttpUser):
    """
    Memory-focused scenario - emphasizes memory-intensive endpoints.
    
    TEACHING PURPOSE: Demonstrates memory bottlenecks and memory usage patterns.
    Watch memory usage increase in Grafana when running this scenario.
    """
    wait_time = between(0.2, 1.0)
    
    @task(10)
    def stress_memory(self):
        """Memory stress endpoint - allocates configurable amount of memory."""
        self.client.post("/stress/memory", name="POST /stress/memory")
    
    @task(3)
    def stress_both(self):
        """Combined CPU and memory stress."""
        self.client.post("/stress/both", name="POST /stress/both")
    
    @task(1)
    def health_check(self):
        """Occasional health check."""
        self.client.get("/health", name="GET /health")


# ============================================================================
# SCENARIO MAPPING
# ============================================================================

# Use combined stress test as default
SCENARIOS = {
    "combined": CombinedStressUser,
    "cpu": CPUScenarioUser,
    "pool": PoolScenarioUser,
    "latency": LatencyScenarioUser,
    "memory": MemoryScenarioUser,
}


# ============================================================================
# EVENT HANDLERS FOR STATISTICS
# ============================================================================

def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("\n" + "=" * 80)
    print("🚀 STRESS TEST STARTED")
    print("=" * 80)
    print(f"   Scenario:     {environment.parsed_options.scenario}")
    print(f"   Target Host:   {environment.host}")
    print(f"   Users:         {environment.parsed_options.num_users}")
    print(f"   Spawn Rate:    {environment.parsed_options.spawn_rate} users/sec")
    print(f"   Duration:      {environment.parsed_options.run_time} seconds")
    print("=" * 80 + "\n")


def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("\n" + "=" * 80)
    print("✅ STRESS TEST COMPLETED")
    print("=" * 80)
    
    # Print summary statistics
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    success_rate = ((total_requests - total_failures) / total_requests * 100) if total_requests > 0 else 0
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Requests:    {total_requests:,}")
    print(f"   Successful:       {total_requests - total_failures:,}")
    print(f"   Failed:           {total_failures:,}")
    print(f"   Success Rate:     {success_rate:.2f}%")
    
    if stats.total.total_response_time:
        print(f"\n⏱️  Response Times:")
        print(f"   Mean:              {stats.total.avg_response_time * 1000:.2f} ms")
        print(f"   Median:            {stats.total.median_response_time * 1000:.2f} ms")
        print(f"   Min:               {stats.total.min_response_time * 1000:.2f} ms")
        print(f"   Max:               {stats.total.max_response_time * 1000:.2f} ms")
    
    if stats.total.total_rps:
        print(f"\n📈 Throughput:")
        print(f"   RPS:               {stats.total.total_rps:.2f} requests/sec")
    
    # Per-endpoint statistics
    if len(stats.entries) > 1:  # More than just the total
        print(f"\n📋 Per-Endpoint Statistics:")
        for name, entry in sorted(stats.entries.items()):
            if name != "Aggregated" and entry.num_requests > 0:
                endpoint_success_rate = ((entry.num_requests - entry.num_failures) / entry.num_requests * 100) if entry.num_requests > 0 else 0
                print(f"\n   {name}:")
                print(f"      Requests:      {entry.num_requests:,} (✓ {entry.num_requests - entry.num_failures:,} / ✗ {entry.num_failures:,})")
                print(f"      Success Rate:   {endpoint_success_rate:.2f}%")
                print(f"      Mean:          {entry.avg_response_time * 1000:.2f} ms")
                if entry.median_response_time:
                    print(f"      Median:        {entry.median_response_time * 1000:.2f} ms")
                if entry.get_response_time_percentile(0.95):
                    print(f"      p95:           {entry.get_response_time_percentile(0.95) * 1000:.2f} ms")
                if entry.get_response_time_percentile(0.99):
                    print(f"      p99:           {entry.get_response_time_percentile(0.99) * 1000:.2f} ms")
    
    print("\n" + "=" * 80)
    print("\n💡 Tips:")
    print("   - Watch Grafana dashboard (http://localhost:3000) for real-time metrics")
    print("   - Check CPU/Memory usage during CPU-intensive scenarios")
    print("   - Observe error rates when testing connection pool limits")
    print("   - Compare p95 latency across different scenarios")
    print("=" * 80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_stress_test(
    host: str = "http://localhost:8000",
    num_users: int = 20,
    spawn_rate: int = 2,
    run_time: int = 30,
    scenario: str = "combined",
    headless: bool = False,
    web_port: int = 8089
):
    """
    Run Locust stress test programmatically.
    
    TEACHING PURPOSE: Shows how to run Locust tests programmatically
    without the web UI, useful for CI/CD and automated testing.
    """
    # Validate scenario
    if scenario not in SCENARIOS:
        print(f"❌ Error: Unknown scenario '{scenario}'")
        print(f"   Available scenarios: {', '.join(SCENARIOS.keys())}")
        sys.exit(1)
    
    # Get the user class for the scenario
    user_class = SCENARIOS[scenario]
    
    # Setup logging
    setup_logging("INFO", None)
    
    # Create Locust environment
    env = Environment(user_classes=[user_class])
    env.create_local_runner()
    
    # Set host
    env.host = host
    
    # Store parsed options for event handlers and WebUI
    # WebUI expects certain attributes, so we provide defaults for all of them
    class ParsedOptions:
        def __init__(self):
            # Custom attributes for our script
            self.scenario = scenario
            self.num_users = num_users
            self.spawn_rate = spawn_rate
            self.run_time = run_time
            # Attributes that Locust's WebUI expects
            self.stats_history_enabled = False
            self.stats_history_size = 120
            self.csv = None
            self.html = None
            self.logfile = None
            self.loglevel = "INFO"
            self.log_json = False
            self.print_stats = True
            self.only_summary = False
            self.reset_stats = False
            self.skip_log_setup = False
            self.expect_workers = 0
            self.master = False
            self.worker = False
            self.master_host = None
            self.master_port = 5557
            self.web_host = "127.0.0.1"
            self.web_port = web_port
            self.tls_cert = None
            self.tls_key = None
            self.run_time = run_time
    
    env.parsed_options = ParsedOptions()
    
    # Register event handlers
    events.test_start.add_listener(on_test_start)
    events.test_stop.add_listener(on_test_stop)
    
    # Start web UI or run headless
    if headless:
        # Headless mode - run directly
        print(f"Running in headless mode...")
        env.runner.start(num_users, spawn_rate=spawn_rate)
        if run_time:
            gevent.spawn_later(run_time, lambda: env.runner.quit())
        env.runner.greenlet.join()
    else:
        # Web UI mode - let user start from web interface
        env.create_web_ui("127.0.0.1", web_port)
        print(f"\n🌐 Locust Web UI available at: http://localhost:{web_port}")
        print(f"   Scenario: {scenario}")
        print(f"   Host: {host}")
        print(f"   Start the test from the web UI")
        print(f"\n   Press Ctrl+C to exit\n")
        
        try:
            # Keep the web UI running until interrupted
            env.runner.greenlet.join()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            if env.runner:
                env.runner.quit()


def main():
    """Main entry point with command-line argument parsing."""
    # Create parser with add_help=False first to avoid conflicts, then add help manually
    parser = argparse.ArgumentParser(
        description="Locust-based stress test for Performance Testing Workshop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        conflict_handler='resolve',
        epilog="""
Examples:
  python stress_test.py                          # Default: 20 users, 30s, combined stress (CPU+Memory+Latency)
  python stress_test.py --users 50              # 50 concurrent users
  python stress_test.py --duration 60            # Run for 60 seconds
  python stress_test.py --headless               # Run without web UI
  python stress_test.py --users 30 --duration 60 --headless
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--users",
        type=int,
        default=20,
        help="Number of concurrent users (default: 20)"
    )
    
    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=2,
        help="Number of users to spawn per second (default: 2)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds (default: 30). Use 0 for indefinite (web UI only)"
    )
    
    parser.add_argument(
        "--scenario",
        type=str,
        default="combined",
        choices=list(SCENARIOS.keys()),
        help="Test scenario: combined (CPU+Memory+Latency), cpu, pool, latency, or memory (default: combined)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no web UI)"
    )
    
    parser.add_argument(
        "--web-port",
        type=int,
        default=8089,
        help="Web UI port (default: 8089, only used when not headless)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate duration for headless mode
    if args.headless and args.duration <= 0:
        print("❌ Error: Duration must be > 0 in headless mode")
        sys.exit(1)
    
    # Run the stress test
    run_stress_test(
        host=args.host,
        num_users=args.users,
        spawn_rate=args.spawn_rate,
        run_time=args.duration if args.duration > 0 else None,
        scenario=args.scenario,
        headless=args.headless,
        web_port=args.web_port
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
