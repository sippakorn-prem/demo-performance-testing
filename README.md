# Performance Testing 101 with Locust - Workshop Materials

A complete demo project for learning performance testing using FastAPI, Locust, Prometheus, and Grafana.

## 🎯 Workshop Goals

After completing this workshop, you will be able to:
- Understand different types of performance tests (load, stress, spike, soak, etc.)
- Write Locust test scripts
- Run performance tests and interpret results
- Identify performance bottlenecks (CPU, database, connection limits)
- Use monitoring tools (Prometheus, Grafana) to observe system behavior

## 📋 Prerequisites

- **Python 3.11+** (check with `python --version`)
- **Docker & Docker Compose** (for running the full stack)
- Basic understanding of HTTP APIs
- A terminal/command line

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Start the entire stack (API, Postgres, Prometheus, Grafana):

```bash
make up
# or
docker-compose up -d
```

This starts:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3500 (admin/admin)
- **cAdvisor**: http://localhost:8080

### Option 2: Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Postgres** (or use Docker):
```bash
docker run -d --name demo-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=demo_db -p 5432:5432 postgres:15-alpine
```

3. **Set database URL:**
```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/demo_db
```

4. **Run API:**
```bash
uvicorn app.main:app --reload
```

## 🔄 Database Migrations

The project uses **Alembic** for database schema management. Migrations run automatically on API startup, but you can also manage them manually.

### Automatic Migrations

Migrations run automatically when the API starts. The application will:
1. Check current database version
2. Apply any pending migrations
3. Continue with normal startup

### Manual Migration Management

**Run migrations:**
```bash
make migrate
# or
alembic upgrade head
```

**Create a new migration:**
```bash
# After modifying models in app/models.py
make migrate-create MSG='add new column to products'
# or
alembic revision --autogenerate -m "add new column to products"
```

**View migration history:**
```bash
make migrate-history
# or
alembic history
```

**Check current version:**
```bash
make migrate-current
# or
alembic current
```

**Downgrade one revision:**
```bash
make migrate-downgrade
# or
alembic downgrade -1
```

**Downgrade to specific revision:**
```bash
alembic downgrade <revision_id>
```

### Migration Workflow

1. **Modify models** in `app/models.py`
2. **Create migration:**
   ```bash
   make migrate-create MSG='description of changes'
   ```
3. **Review** the generated migration in `alembic/versions/`
4. **Apply migration:**
   ```bash
   make migrate
   ```

### Initial Migration

The initial migration (`001_initial_schema.py`) creates:
- `products` table with indexes
- `cart_items` table with indexes

This migration is automatically applied on first startup.

## 🌱 Data Seeding

The API automatically seeds **10,000 products** on first startup for quick testing. For massive datasets and all test scenarios, use the dedicated seeder script.

### Quick Seeding (Automatic)

The API automatically creates 10,000 products on first startup. This is sufficient for basic testing.

### Massive Data Seeding

For comprehensive testing with large datasets:

```bash
# Using Docker (recommended)
make seed-massive
# or
docker-compose exec api python -m app.seed_data

# Using local Python
python -m app.seed_data
```

**What gets seeded:**
- **100,000+ products** with realistic names, prices, descriptions
- **Cart items** for 1,000 users (5 items per user average)
- **Hot products** (IDs: 1, 2, 3, 4, 5, 10, 20, 50, 100, 500) with high stock
- **Low-stock products** (100 products with stock=1) for concurrency testing
- **Varied stock levels** (10% low stock, 20% medium, 70% high stock)

**Seeder Features:**
- ✅ Batch processing for efficiency
- ✅ Progress tracking
- ✅ Skips if data already exists
- ✅ Statistics report after seeding
- ✅ Realistic product data (categories, prices, descriptions)

**Customization via Command Line:**

```bash
# Seed 500,000 products
python -m app.seed_data --products 500000

# Seed with more users
python -m app.seed_data --users 5000 --items-per-user 10

# Skip cart items (products only)
python -m app.seed_data --skip-cart

# Skip low-stock products
python -m app.seed_data --skip-low-stock

# Custom batch size for performance
python -m app.seed_data --batch-size 2000

# Combine options
python -m app.seed_data --products 200000 --users 2000 --items-per-user 8
```

**Available Options:**
- `--products N` - Number of products (default: 100000)
- `--users N` - Number of users for cart items (default: 1000)
- `--items-per-user N` - Average items per user (default: 5)
- `--skip-cart` - Skip cart item seeding
- `--skip-low-stock` - Skip low-stock product creation
- `--batch-size N` - Batch size for performance tuning (default: 1000)

**Example Output:**
```
🚀 Starting Data Seeding Process...
🌱 Seeding 100,000 products...
  Progress: 10.0% - Seeded products 1 to 1,000 (1,000 products)
  Progress: 20.0% - Seeded products 1,001 to 2,000 (1,000 products)
  ...
✅ Successfully seeded 100,000 products!
🔥 Ensuring hot products exist...
✅ Hot products ready!
⚠️  Creating 100 low-stock products for concurrency testing...
✅ Set 100 products to stock=1 for concurrency testing
🛒 Seeding cart items for 1,000 users...
✅ Successfully seeded cart items for 1,000 users!

📊 Database Statistics:
============================================================
Products: 100,000
Total Stock: 45,234,567
Average Price: $502.34
Low Stock Products (<10): 10,100

Cart Items: 5,000
Users with Cart Items: 1,000
============================================================
```

## 📊 Monitoring Setup

### Grafana Dashboard

1. Open http://localhost:3500
2. Login with `admin` / `admin`
3. The "Performance Testing Workshop Dashboard" is automatically provisioned
4. Dashboard includes:
   - Request Rate (RPS)
   - Response Time (p50, p95, p99)
   - Error Rate
   - CPU & Memory Usage

### Prometheus

- Open http://localhost:9090
- Query metrics directly using PromQL
- Example queries:
  - `rate(http_server_requests_total[5m])` - Request rate
  - `histogram_quantile(0.95, http_server_request_duration_seconds_bucket)` - p95 latency

## 🧪 Running Locust Tests

### Install Locust

Locust is included in `requirements.txt`. If running locally:

```bash
pip install -r requirements.txt
```

### Test Types Overview

| Test Type | Purpose | Command |
|-----------|---------|---------|
| **Baseline** | Establish baseline metrics | `make test-baseline` |
| **Load** | Expected production traffic | `make test-load` |
| **Stress** | Find breaking point | `make test-stress` |
| **Spike** | Sudden traffic spike | `make test-spike` |
| **Soak** | Endurance/stability test | `make test-soak` |
| **Concurrency** | Race condition testing | `make test-concurrency` |
| **Capacity** | SLO validation | `make test-capacity` |
| **Resilience** | Failure handling | `make test-resilience` |

### 1. Baseline Test

**Purpose**: Establish baseline performance metrics with minimal load.

```bash
locust -f test/locust_baseline.py --host http://localhost:8000 --users 10 --spawn-rate 2
```

**What to observe:**
- p95 latency (should be < 500ms)
- RPS (requests per second)
- Error rate (should be < 1%)
- **Write down these numbers as your baseline!**

### 2. Load Test

**Purpose**: Simulate expected production traffic.

```bash
locust -f test/locust_load.py --host http://localhost:8000 --users 50 --spawn-rate 5
```

**What to observe:**
- Compare metrics to baseline
- System should handle load gracefully
- Latency may increase slightly but should remain stable

### 3. Stress Test

**Purpose**: Gradually increase load until system breaks.

```bash
locust -f test/locust_stress.py --host http://localhost:8000
```

**What to observe:**
- Staged ramp-up: 10 → 25 → 50 → 100 → 150 → 200 users
- Watch for when errors start appearing
- Observe latency degradation
- Identify breaking point

**Expected pattern:**
- Early stages: Stable performance
- Mid stages: Latency increases, some errors
- High load: Many errors, system struggling

### 4. Spike Test

**Purpose**: Test system response to sudden traffic spike (flash sale scenario).

```bash
locust -f test/locust_spike.py --host http://localhost:8000 --users 200 --spawn-rate 50
```

**What to observe:**
- Sudden load increase
- System may struggle initially
- Recovery time after spike
- Error rate spike

### 5. Soak Test

**Purpose**: Test system stability over extended period (memory leaks, resource exhaustion).

```bash
locust -f test/locust_soak.py --host http://localhost:8000 --users 30 --spawn-rate 3 --run-time 30m
```

**What to observe:**
- Memory usage over time (should be stable)
- CPU usage (should be stable)
- Error rate (should remain low)
- Latency (should not degrade over time)

**Run for at least 30 minutes to detect:**
- Memory leaks
- Connection pool exhaustion
- Resource leaks

### 6. Concurrency Test

**Purpose**: Test race conditions in stock management (all users checkout same product).

```bash
locust -f test/locust_concurrency.py --host http://localhost:8000 --users 100 --spawn-rate 20
```

**What to observe:**
- 409 (Conflict) errors when stock runs out
- Race conditions in stock updates
- Demonstrates need for proper database transactions/locking

**Expected behavior:**
- First requests succeed
- As stock depletes, 409 errors appear
- Shows concurrency issues without proper locking

### 7. Capacity Test

**Purpose**: Validate system meets SLOs (Service Level Objectives).

```bash
locust -f test/locust_capacity.py --host http://localhost:8000
```

**SLOs:**
- p95 latency < 300ms
- Error rate < 1%

**What to observe:**
- Stepwise load increase
- SLO validation at each step
- PASS/FAIL logging
- Maximum capacity before SLO violation

### 8. Resilience Test

**Purpose**: Test system behavior when failures are introduced.

```bash
# Terminal 1: Start test
locust -f test/locust_resilience.py --host http://localhost:8000 --users 50 --spawn-rate 5

# Terminal 2: Introduce failures
curl -X POST http://localhost:8000/admin/failure \
  -H "Content-Type: application/json" \
  -d '{"checkout": 0.1}'
```

**What to observe:**
- Error rate increases when failures introduced
- System continues operating (graceful degradation)
- Recovery when failures removed

## 🎓 Workshop Exercises

### Exercise 1: Baseline Measurement

1. Start the API: `make up`
2. Run baseline test: `make test-baseline`
3. Record metrics:
   - p95 latency: _____ ms
   - RPS: _____ req/s
   - Error rate: _____ %

### Exercise 2: Introduce Latency

1. Add latency to products endpoint:
```bash
curl -X POST http://localhost:8000/admin/latency \
  -H "Content-Type: application/json" \
  -d '{"products": 500}'
```

2. Run load test again: `make test-load`
3. Compare metrics to baseline
4. **Observe**: Latency increased significantly

5. Remove latency:
```bash
curl -X POST http://localhost:8000/admin/latency \
  -H "Content-Type: application/json" \
  -d '{"products": 0}'
```

### Exercise 3: Introduce Failures

1. Add failure rate to checkout:
```bash
curl -X POST http://localhost:8000/admin/failure \
  -H "Content-Type: application/json" \
  -d '{"checkout": 0.1}'
```

2. Run load test: `make test-load`
3. **Observe**: Error rate increases for checkout endpoint
4. Check Locust "Failures" tab for error details

5. Remove failures:
```bash
curl -X POST http://localhost:8000/admin/failure \
  -H "Content-Type: application/json" \
  -d '{"checkout": 0}'
```

### Exercise 4: CPU Bottleneck

1. Increase CPU-intensive hashing for login:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"auth_hashing_rounds": 100000}'
```

2. Run load test: `make test-load`
3. **Observe**:
   - `/auth/login` latency increases dramatically
   - CPU usage spikes (check Grafana or system monitor)
   - May affect other endpoints if CPU is saturated

4. Restore:
```bash
curl -X POST http://localhost:8000/admin/config \
  -H "Content-Type: application/json" \
  -d '{"auth_hashing_rounds": 10000}'
```

### Exercise 5: Concurrency Issues

1. Run concurrency test: `make test-concurrency`
2. **Observe**:
   - All users checkout product_id=1
   - 409 (Conflict) errors appear as stock depletes
   - Demonstrates race condition without proper locking

## 📈 Interpreting Results

### Healthy System
- ✅ p95 latency: < 500ms
- ✅ Error rate: < 1%
- ✅ RPS: Steady or increasing with load
- ✅ Response times: Stable

### System Under Stress
- ⚠️ p95 latency: > 1000ms
- ⚠️ Error rate: > 5%
- ⚠️ RPS: Plateaus (not increasing with more users)
- ⚠️ Response times: Increasing over time

### System Breaking
- ❌ p95 latency: > 5000ms
- ❌ Error rate: > 20%
- ❌ RPS: Decreasing
- ❌ Many 503 errors (Service Unavailable)

## 🔧 API Endpoints

### Health & Metrics
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Authentication
- `POST /auth/login` - Login (returns access_token)

### Products
- `GET /products?page=1&limit=20` - List products (paginated)
- `GET /products/{id}` - Product detail (with caching)

### Cart & Checkout
- `POST /cart/items` - Add to cart (requires auth)
- `POST /cart/checkout` - Checkout (requires auth, stock management)

### Admin (Workshop Configuration)
- `GET /admin/config` - Get current configuration
- `POST /admin/latency` - Set artificial latency per endpoint group
- `POST /admin/failure` - Set failure rate per endpoint group
- `POST /admin/cache` - Configure cache settings

## 🏗️ Project Structure

```
/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── settings.py        # Configuration
│   ├── db.py              # Database connection
│   ├── models.py          # SQLAlchemy models
│   ├── migrations.py      # Migration utilities
│   ├── seed_data.py       # Data seeder script
│   └── routers/           # API routers
│       ├── health.py
│       ├── auth.py
│       ├── products.py
│       ├── cart.py
│       └── admin.py
├── alembic/                # Database migrations
│   ├── versions/          # Migration files
│   ├── env.py            # Alembic environment
│   └── script.py.mako     # Migration template
├── alembic.ini            # Alembic configuration
├── test/                  # Locust test scripts
│   ├── locust_common.py   # Shared helpers
│   ├── locust_baseline.py
│   ├── locust_load.py
│   ├── locust_stress.py
│   ├── locust_spike.py
│   ├── locust_soak.py
│   ├── locust_concurrency.py
│   ├── locust_capacity.py
│   └── locust_resilience.py
├── prometheus/            # Prometheus configuration
│   └── prometheus.yml
├── grafana/               # Grafana provisioning
│   ├── provisioning/
│   └── dashboards/
├── docker-compose.yml     # Docker Compose setup
├── Makefile               # Convenience commands
└── README.md             # This file
```

## 🐛 Troubleshooting

### API won't start
- Check if port 8000 is in use
- Verify Postgres is running: `docker ps`
- Check logs: `docker-compose logs api`

### Locust can't connect
- Verify API is running: `curl http://localhost:8000/health`
- Check Host URL in Locust UI matches API URL

### Database connection errors
- Ensure Postgres is running: `docker ps | grep postgres`
- Check database URL in settings
- Verify network connectivity in docker-compose

### No metrics in Grafana
- Verify Prometheus is scraping: http://localhost:9090/targets
- Check Prometheus config: `cat prometheus/prometheus.yml`
- Ensure API metrics endpoint works: `curl http://localhost:8000/metrics`

### Migration errors
- Ensure database is running: `docker ps | grep postgres`
- Check database URL in `alembic.ini` or `app/settings.py`
- Verify you're using the correct database URL for your environment
- If migrations fail, check: `alembic current` to see current version
- To reset: Drop database and run migrations again (⚠️ **WARNING**: This deletes all data)

## 📚 Resources

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🎯 Workshop Timeline (3 hours)

### Part 1: Introduction (30 min)
- Performance testing concepts
- Types of performance tests
- Locust basics

### Part 2: Baseline & Load Testing (30 min)
- Run baseline test
- Run load test
- Compare results
- Exercise: Introduce latency

### Part 3: Stress & Spike Testing (30 min)
- Run stress test (staged ramp-up)
- Run spike test
- Observe breaking points
- Exercise: CPU bottleneck

### Part 4: Advanced Testing (30 min)
- Concurrency test (race conditions)
- Soak test (stability)
- Capacity test (SLO validation)

### Part 5: Monitoring & Analysis (30 min)
- Using Grafana dashboards
- Interpreting Prometheus metrics
- Identifying bottlenecks
- Exercise: Resilience testing

### Part 6: Wrap-up (30 min)
- Q&A
- Best practices
- Next steps

## 📝 Notes

- All tests are designed for educational purposes
- The API intentionally includes bottlenecks for demonstration
- Results may vary based on system resources
- Use production-like environments for real testing

Happy testing! 🚀
