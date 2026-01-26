# Performance Testing 101 using Locust - Workshop Materials

Welcome to the performance testing workshop! This repository contains everything you need to learn performance testing with Locust.

## Prerequisites

- **Python 3.10+** (check with `python --version`)
- Basic understanding of HTTP APIs
- A terminal/command line

## Quick Start

### Option 1: Run API Locally (Recommended for Learning)

1. **Create and activate virtual environment:**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the FastAPI demo API:**
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Option 2: Run API with Docker (Includes Grafana Monitoring)

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

The following services will be available:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Prometheus Metrics**: http://localhost:8000/metrics
- **Prometheus UI**: http://localhost:9090
- **cAdvisor UI**: http://localhost:8080 (container metrics)
- **Grafana Dashboard**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`

2. **Access Grafana Dashboard:**
   - Open http://localhost:3000 in your browser
   - Login with credentials above
   - The "Performance Testing Workshop Dashboard" will be automatically loaded
   - This dashboard shows real-time metrics including:
     - **CPU Usage** (gauge + time series)
     - **Memory Usage** (gauge + time series)
     - Request Rate (RPS)
     - Response Time (p95) - Latency
     - Error Rate
     - Response Time Percentiles by Endpoint

## Installing and Running Locust

1. **Locust is already in requirements.txt**, so if you installed dependencies above, you're ready!

2. **Run Locust:**
```bash
locust
```

3. **Open Locust Web UI:**
   - Navigate to http://localhost:8089
   - Enter:
     - **Number of users**: Start with 10
     - **Spawn rate**: 2 (users per second)
     - **Host**: http://localhost:8000

4. **Click "Start swarming"** to begin the test!

## Monitoring with Grafana

When running with Docker Compose, Grafana provides visual dashboards for real-time performance metrics.

### Grafana Dashboard Features:

#### System Metrics (Top Row):
1. **CPU Usage (%)**
   - Real-time CPU usage gauge and time series graph
   - Watch CPU spike when running CPU-intensive tasks (e.g., `/login` with high `loginCpuRounds`)
   - Helps identify CPU bottlenecks

2. **Memory Usage**
   - Current memory consumption gauge and time series graph
   - Monitor memory growth over time
   - Useful for detecting memory leaks

#### Application Metrics:
3. **Request Rate (RPS)**
   - Shows requests per second for each endpoint
   - Helps identify which endpoints are under load

4. **Response Time (p95) - Latency**
   - 95th percentile response time
   - Critical metric for user experience
   - Watch this when testing connection pool limits or high latency endpoints

5. **Error Rate**
   - Tracks 5xx errors in real-time
   - Visual indicator when system is struggling

6. **Response Time Percentiles**
   - p50, p95, p99 by endpoint
   - Compare performance across different endpoints

### Using Grafana During Workshop:

- **Keep Grafana open** alongside Locust UI to see both perspectives
- **Watch CPU usage** when you increase `loginCpuRounds` - you'll see CPU spike!
- **Watch memory** to see if it grows steadily (potential memory leak)
- **Watch latency (p95)** when you reduce `poolMax` - you'll see it increase
- **Compare metrics** before and after configuration changes
- **Dashboard auto-refreshes** every 5 seconds for real-time updates

### Accessing Monitoring Services:

- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus UI**: http://localhost:9090 (for raw metrics queries)
- **cAdvisor UI**: http://localhost:8080 (container metrics)
- **API Metrics Endpoint**: http://localhost:8000/metrics

## What to Observe in Locust UI

### Key Metrics to Watch:

1. **p95 Latency** (95th percentile)
   - **What it means**: 95% of requests completed faster than this time
   - **Why it matters**: Shows worst-case user experience
   - **Example**: p95 = 500ms means 95% of users see < 500ms response time

2. **RPS** (Requests Per Second)
   - **What it means**: How many requests the server handles per second
   - **Why it matters**: Shows system throughput
   - **Watch for**: RPS plateauing = system at capacity

3. **Failure Rate**
   - **What it means**: Percentage of requests that failed
   - **Why it matters**: Shows system reliability
   - **Healthy**: < 1% failures
   - **Warning**: > 5% failures = system struggling

4. **Response Times (Median, p95, p99)**
   - **Median**: Typical user experience
   - **p95**: Worst 5% of users
   - **p99**: Worst 1% of users

### Locust UI Tabs:

- **Statistics**: Overview of all endpoints
- **Charts**: Real-time graphs of RPS, response times, failures
- **Failures**: List of failed requests with error details
- **Exceptions**: Python exceptions (if any)

## Workshop Exercises

### Exercise 1: Baseline Run

**Goal**: Establish baseline performance metrics.

1. Start the API (if not already running)
2. Open Locust UI (http://localhost:8089)
3. Run with:
   - **Users**: 20
   - **Spawn rate**: 2
   - **Duration**: 2 minutes
4. **Observe**:
   - What is the p95 latency?
   - What is the RPS?
   - What is the failure rate?
   - **Write down these numbers!**

### Exercise 2: Connection Pool Bottleneck

**Goal**: See how connection pool limits cause 503 errors.

1. **Reduce connection pool** (in another terminal):
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"poolMax": 5, "poolWaitTimeoutMs": 50}'
```

2. **Run Locust again** with same settings (20 users, 2 spawn rate, 2 minutes)

3. **Observe**:
   - How many 503 errors do you see?
   - What happens to RPS? (Does it plateau?)
   - What happens to p95 latency?
   - **Compare to baseline!**

4. **Restore connection pool**:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"poolMax": 30, "poolWaitTimeoutMs": 300}'
```

### Exercise 3: CPU Bottleneck

**Goal**: See how CPU-intensive tasks affect performance.

1. **Increase CPU burn** for login:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"loginCpuRounds": 50000}'
```

2. **Run Locust again** (20 users, 2 spawn rate, 2 minutes)

3. **Observe**:
   - What happens to `/login` endpoint latency?
   - Does it affect other endpoints?
   - What happens to overall RPS?
   - **Check your CPU usage** (Activity Monitor / Task Manager)

4. **Restore CPU settings**:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"loginCpuRounds": 10000}'
```

### Exercise 4: Error Rate Monitoring

**Goal**: Understand how error rates are tracked.

1. **Increase checkout failure rate**:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"checkoutFailRate": 0.1}'
```

2. **Run Locust again** (20 users, 2 spawn rate, 2 minutes)

3. **Observe**:
   - What is the failure rate for `/checkout`?
   - How does it show up in Locust UI?
   - What status codes do you see? (502 = Bad Gateway)

4. **Restore failure rate**:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"checkoutFailRate": 0.02}'
```

## Interpreting Results

### Healthy System:
- ✅ p95 latency: < 500ms
- ✅ Failure rate: < 1%
- ✅ RPS: Steady or increasing with load
- ✅ Response times: Stable

### System Under Stress:
- ⚠️ p95 latency: > 1000ms
- ⚠️ Failure rate: > 5%
- ⚠️ RPS: Plateaus (not increasing with more users)
- ⚠️ Response times: Increasing over time

### System Breaking:
- ❌ p95 latency: > 5000ms
- ❌ Failure rate: > 20%
- ❌ RPS: Decreasing
- ❌ Many 503 errors (Service Unavailable)

## API Endpoints Reference

- `GET /health` - Health check with pool status
- `GET /products` - List products (100-300ms latency)
- `GET /products/{id}` - Product detail (uses connection pool)
- `POST /login` - Login (CPU-intensive)
- `POST /checkout` - Checkout (uses pool + random failures)
- `GET /heavy` - Heavy computation (800-1200ms latency)
- `GET /admin/config` - Get current configuration
- `POST /admin/config` - Update configuration (for workshop exercises)

## Troubleshooting

### API won't start:
- Check if port 8000 is already in use
- Verify Python version: `python --version` (need 3.10+)
- Check virtual environment is activated

### Locust can't connect:
- Verify API is running: `curl http://localhost:8000/health`
- Check the Host URL in Locust UI matches your API URL

### No failures showing:
- Check the "Failures" tab in Locust UI
- Verify you're running with enough users to trigger failures

## Next Steps

After completing the exercises:
1. Try different user counts (10, 50, 100)
2. Experiment with different spawn rates
3. Try running tests for longer durations
4. Explore the Locust charts to see trends over time

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Performance Testing Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)

Happy testing! 🚀
