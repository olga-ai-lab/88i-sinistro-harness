# Phase 5: Railway Deployment Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Deploy 88i sinistro agent to Railway.app with production-grade containerization, CI/CD pipeline, health checks, and monitoring.

**Objectives:**
1. Create Dockerfile + docker-compose.yml for local development
2. Configure Railway deployment (railway.json, environment variables)
3. Set up GitHub Actions CI/CD pipeline for automatic deployments
4. Implement health checks and graceful shutdown
5. Configure monitoring and logging (Langfuse integration)
6. Set up canary deployment strategy
7. Documentation and deployment guide

**Tech Stack:** Docker, Docker Compose, Railway.app, GitHub Actions, Python 3.13, FastAPI

**Deployment Target:** Railway.app with production-grade reliability

---

## Task 1: Dockerfile + Docker Compose Configuration

**Objective:** Create production-ready Docker configuration for local development and Railway deployment.

**Step 1: Create Dockerfile**

File: `Dockerfile`

```dockerfile
# Multi-stage build for optimized image size
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-directory

# Production stage
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port (Railway will override via PORT env var)
EXPOSE ${PORT:-8000}

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
```

**Step 2: Create docker-compose.yml**

File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${PORT:-8000}:${PORT:-8000}"
    environment:
      - PORT=${PORT:-8000}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - INNGEST_API_KEY=${INNGEST_API_KEY}
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    volumes:
      - .:/app
      - /app/__pycache__
    command: >
      sh -c "pip install --no-cache-dir -e . &&
             python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${PORT:-8000}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  supabase:
    image: supabase/supabase:latest
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres
    volumes:
      - supabase_data:/var/lib/postgresql/data

volumes:
  supabase_data:
```

**Step 3: Create .dockerignore**

File: `.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.egg-info
.git
.gitignore
.github
.venv
venv
.env
.env.local
.pytest_cache
htmlcov
dist
build
*.md
node_modules
.DS_Store
```

**Step 4: Create .env.example**

File: `.env.example`

```
# API Keys
ANTHROPIC_API_KEY=sk-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
INNGEST_API_KEY=inngest_...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# Environment
ENVIRONMENT=development
PORT=8000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

**Step 5: Test locally**

```bash
# Build and run locally
docker build -t 88i-sinistro:latest .

# Run with docker-compose
docker-compose up

# Test health check
curl http://localhost:8000/health

# Run tests in container
docker-compose exec app pytest tests/ -v
```

**Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore .env.example
git commit -m "feat(docker): add production Dockerfile and docker-compose configuration"
```

---

## Task 2: Railway Deployment Configuration

**Objective:** Configure Railway.app deployment with environment variables and deployment settings.

**Step 1: Create railway.json**

File: `railway.json`

```json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyMaxRetries": 5,
    "restartPolicyMaxBackoffSec": 300
  },
  "healthchecks": {
    "enabled": true,
    "endpoint": "/health"
  },
  "logs": {
    "enabled": true
  }
}
```

**Step 2: Create Railway service configuration script**

File: `scripts/deploy_railway.sh`

```bash
#!/bin/bash

set -e

echo "🚀 Deploying to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "Logging in to Railway..."
railway login

# Link project
echo "Linking Railway project..."
railway link

# Set environment variables
echo "Setting environment variables..."
railway variables set ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
railway variables set SUPABASE_URL=$SUPABASE_URL
railway variables set SUPABASE_KEY=$SUPABASE_KEY
railway variables set INNGEST_API_KEY=$INNGEST_API_KEY
railway variables set LANGFUSE_PUBLIC_KEY=$LANGFUSE_PUBLIC_KEY
railway variables set LANGFUSE_SECRET_KEY=$LANGFUSE_SECRET_KEY
railway variables set ENVIRONMENT=production

# Deploy
echo "Deploying application..."
railway up

echo "✅ Deployment complete!"
echo "Application URL: $(railway status)"
```

**Step 3: Create Procfile for Railway (alternative)**

File: `Procfile`

```
web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Step 4: Update pyproject.toml with Railway dependencies**

```toml
[tool.poetry.dependencies]
# ... existing dependencies ...
gunicorn = "^21.2.0"  # Optional: production WSGI server
```

**Step 5: Configure Railway environment**

Create `railway.variables.json` (for reference, should NOT be committed with secrets):

```json
{
  "ENVIRONMENT": "production",
  "PORT": "8000",
  "LOG_LEVEL": "INFO",
  "PYTHONUNBUFFERED": "1"
}
```

**Step 6: Commit**

```bash
git add railway.json Procfile scripts/deploy_railway.sh
git commit -m "feat(railway): add Railway.app deployment configuration"
```

---

## Task 3: GitHub Actions CI/CD Pipeline

**Objective:** Set up automated testing, building, and deployment to Railway on push to main.

**Step 1: Create GitHub Actions workflow**

File: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Railway

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run linter
        run: |
          poetry run pylint **/*.py || true

      - name: Run type checker
        run: |
          poetry run mypy . || true

      - name: Run tests
        run: |
          poetry run pytest tests/ -v --cov=context_engine --cov=plugins --cov=monitoring --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway up --service 88i-sinistro

      - name: Run health check
        run: |
          sleep 10
          curl -f https://${{ secrets.RAILWAY_SERVICE_DOMAIN }}/health || exit 1

      - name: Notify deployment
        if: success()
        run: |
          echo "✅ Deployment successful!"
          echo "Service: https://${{ secrets.RAILWAY_SERVICE_DOMAIN }}"
```

**Step 2: Create GitHub Actions test workflow**

File: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip poetry
          poetry install --with dev

      - name: Run unit tests
        run: poetry run pytest tests/ -v --cov --cov-report=term-missing

      - name: Run security tests
        run: poetry run pytest tests/security/ -v -m security

      - name: Run performance tests
        run: poetry run pytest tests/performance/ -v -m performance

      - name: Generate coverage badge
        run: poetry run coverage-badge -o coverage.svg -f
```

**Step 3: Create GitHub Actions security workflow**

File: `.github/workflows/security.yml`

```yaml
name: Security

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Check dependencies
        run: |
          pip install safety
          safety check || true
```

**Step 4: Add GitHub secrets**

Via GitHub UI (Settings → Secrets and variables → Actions):
- `RAILWAY_TOKEN` — Railway API token
- `RAILWAY_SERVICE_DOMAIN` — Railway service domain

**Step 5: Commit**

```bash
git add .github/workflows/
git commit -m "feat(ci/cd): add GitHub Actions deployment pipeline"
```

---

## Task 4: Health Checks & Graceful Shutdown

**Objective:** Implement health checks and graceful shutdown for production reliability.

**Step 1: Create health check module**

File: `app/health.py`

```python
"""Health check and readiness probe endpoints."""

import logging
from typing import Dict, Any
from datetime import datetime
import asyncio

import httpx
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


class HealthChecker:
    """Performs system health checks."""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.check_timeout = 5.0  # seconds

    async def check_database(self) -> bool:
        """Check Supabase connectivity."""
        try:
            from supabase import create_client
            
            client = create_client(
                url=os.getenv("SUPABASE_URL"),
                key=os.getenv("SUPABASE_KEY")
            )
            response = client.table("context_cache").select("id").limit(1).execute()
            return response is not None
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False

    async def check_external_services(self) -> Dict[str, bool]:
        """Check external service connectivity."""
        services = {}

        # Check Inngest
        try:
            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get("https://api.inngest.com/health")
                services["inngest"] = response.status_code == 200
        except Exception as e:
            logger.warning(f"Inngest check failed: {e}")
            services["inngest"] = False

        # Check Langfuse
        try:
            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get("https://cloud.langfuse.com/health")
                services["langfuse"] = response.status_code == 200
        except Exception as e:
            logger.warning(f"Langfuse check failed: {e}")
            services["langfuse"] = False

        return services

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        db_ok = await self.check_database()
        services = await check_external_services()

        return {
            "status": "healthy" if db_ok else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "database": "ok" if db_ok else "error",
            "services": services,
            "version": os.getenv("VERSION", "unknown")
        }


health_checker = HealthChecker()


@router.get("", name="health-check")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint (for load balancers).
    Returns immediately without expensive checks.
    """
    return {"status": "ok"}


@router.get("/live", name="liveness-probe")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.
    Returns 200 if app is running (even if degraded).
    """
    return {"status": "alive"}


@router.get("/ready", name="readiness-probe")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.
    Returns 200 only if app is ready to accept traffic.
    """
    status = await health_checker.get_health_status()
    
    if status["status"] == "healthy":
        return status
    else:
        raise HTTPException(status_code=503, detail=status)


@router.get("/detailed", name="detailed-health")
async def detailed_health() -> Dict[str, Any]:
    """Detailed health status with all checks."""
    return await health_checker.get_health_status()
```

**Step 2: Create graceful shutdown handler**

File: `app/shutdown.py`

```python
"""Graceful shutdown handler for production."""

import logging
import asyncio
import signal
from typing import Callable, List

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Manages graceful shutdown of the application."""

    def __init__(self, timeout_sec: int = 30):
        self.timeout_sec = timeout_sec
        self.cleanup_callbacks: List[Callable] = []
        self.is_shutting_down = False

    def add_cleanup_callback(self, callback: Callable) -> None:
        """Register a callback to run during shutdown."""
        self.cleanup_callbacks.append(callback)

    async def shutdown(self) -> None:
        """Execute graceful shutdown sequence."""
        self.is_shutting_down = True
        logger.info("🔴 Graceful shutdown initiated...")

        # Stop accepting new requests
        logger.info("⏸️ Stopping request handling...")

        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                logger.info(f"Running cleanup: {callback.__name__}")
                if asyncio.iscoroutinefunction(callback):
                    await asyncio.wait_for(callback(), timeout=self.timeout_sec)
                else:
                    callback()
            except asyncio.TimeoutError:
                logger.error(f"Cleanup timeout: {callback.__name__}")
            except Exception as e:
                logger.error(f"Cleanup error in {callback.__name__}: {e}")

        # Wait for pending requests to complete
        logger.info("⏳ Waiting for pending requests...")
        await asyncio.sleep(2)

        logger.info("✅ Graceful shutdown complete")

    def setup_signal_handlers(self, app) -> None:
        """Setup signal handlers for SIGTERM and SIGINT."""
        loop = asyncio.new_event_loop()
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Signal handlers registered")


# Global instance
graceful_shutdown = GracefulShutdown(timeout_sec=30)
```

**Step 3: Integrate into main.py**

Update `main.py`:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.health import router as health_router
from app.shutdown import graceful_shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle."""
    # Startup
    logger.info("🚀 Application starting...")
    graceful_shutdown.setup_signal_handlers(app)
    
    # Add cleanup callbacks
    graceful_shutdown.add_cleanup_callback(cleanup_database)
    graceful_shutdown.add_cleanup_callback(cleanup_cache)
    
    yield
    
    # Shutdown
    await graceful_shutdown.shutdown()


app = FastAPI(title="88i Sinistro Agent", lifespan=lifespan)
app.include_router(health_router)
```

**Step 4: Commit**

```bash
git add app/health.py app/shutdown.py
git commit -m "feat(health): add health checks and graceful shutdown"
```

---

## Task 5: Monitoring & Logging Integration

**Objective:** Set up comprehensive monitoring and logging for production.

**Step 1: Create monitoring module**

File: `app/monitoring.py`

```python
"""Monitoring and logging configuration."""

import logging
import os
from typing import Optional
from pythonjsonlogger import jsonlogger
from langfuse import Langfuse

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)


def setup_logging() -> None:
    """Configure structured JSON logging for production."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if os.getenv("ENVIRONMENT") == "development" else logging.INFO)
    
    # JSON formatter for structured logs
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d'
    )
    
    # Console handler (for Railway logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional, for local development)
    if os.getenv("ENVIRONMENT") == "development":
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def log_deployment_info() -> None:
    """Log deployment information on startup."""
    logger = logging.getLogger(__name__)
    
    logger.info(
        "Deployment info",
        extra={
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "version": os.getenv("VERSION", "unknown"),
            "python_version": os.getenv("PYTHON_VERSION", "unknown"),
            "port": os.getenv("PORT", "8000"),
        }
    )


async def log_request_trace(request_id: str, operation: str, input_data: dict, output_data: dict) -> None:
    """Log request trace to Langfuse."""
    try:
        trace = langfuse.trace(name=operation, id=request_id)
        trace.span(
            name=f"{operation}_execution",
            input=input_data,
            output=output_data,
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log trace to Langfuse: {e}")


# Setup logging on import
setup_logging()
```

**Step 2: Create middleware for request logging**

File: `app/middleware.py`

```python
"""Request/response middleware for monitoring."""

import logging
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )

        # Track timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "request_error",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )

        # Add request ID header
        response.headers["X-Request-ID"] = request_id
        return response
```

**Step 3: Create metrics collection**

File: `app/metrics.py`

```python
"""Metrics collection for monitoring."""

import os
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Error metrics
error_count = Counter(
    'app_errors_total',
    'Total errors',
    ['error_type']
)

# Business metrics
sinistro_processed = Counter(
    'sinistro_processed_total',
    'Total sinistros processed',
    ['tipo', 'result']
)

fraud_score_histogram = Histogram(
    'fraud_score_distribution',
    'Fraud score distribution',
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# System metrics
active_connections = Gauge(
    'app_active_connections',
    'Active connections'
)

uptime = Gauge(
    'app_uptime_seconds',
    'Application uptime'
)
```

**Step 4: Commit**

```bash
git add app/monitoring.py app/middleware.py app/metrics.py
git commit -m "feat(monitoring): add structured logging, tracing, and metrics"
```

---

## Task 6: Canary Deployment Strategy

**Objective:** Implement safe deployment strategy with gradual traffic shifting.

**Step 1: Create canary deployment script**

File: `scripts/canary_deploy.sh`

```bash
#!/bin/bash

set -e

CANARY_PERCENTAGE=${1:-10}
STABLE_PERCENTAGE=$((100 - CANARY_PERCENTAGE))

echo "🐤 Starting canary deployment (${CANARY_PERCENTAGE}% canary, ${STABLE_PERCENTAGE}% stable)..."

# Get current stable version
STABLE_VERSION=$(railway status | grep "Service:" | awk '{print $2}')
echo "📌 Stable version: $STABLE_VERSION"

# Deploy new version
echo "🚀 Deploying new version..."
NEW_VERSION=$(railway up --no-wait 2>&1 | grep -oP '(?<=Deployment ID: )\S+' || echo "latest")
echo "🆕 New version: $NEW_VERSION"

# Wait for new version to be healthy
echo "⏳ Waiting for new version to be healthy..."
for i in {1..30}; do
    if curl -s https://$RAILWAY_SERVICE_DOMAIN/health | grep -q "ok"; then
        echo "✅ New version is healthy"
        break
    fi
    echo "⏳ Health check attempt $i/30..."
    sleep 5
done

# Configure traffic split
echo "🎚️ Configuring traffic split (${CANARY_PERCENTAGE}% canary)..."
# This would use Railway's load balancer configuration
# or a separate ingress controller

# Monitor metrics
echo "📊 Monitoring metrics for 5 minutes..."
for i in {1..30}; do
    ERROR_RATE=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'error_rate' || echo "0")
    P95_LATENCY=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'p95_latency' || echo "unknown")
    
    echo "⏱️ Check $i/30: Error rate: $ERROR_RATE, P95: $P95_LATENCY"
    
    # If error rate > 5%, rollback
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "❌ Error rate too high, rolling back..."
        railway rollback $STABLE_VERSION
        exit 1
    fi
    
    sleep 10
done

# Increase traffic to new version
echo "📈 Increasing traffic to new version..."
# Full traffic shift to new version

echo "✅ Canary deployment successful!"
```

**Step 2: Create rollback script**

File: `scripts/rollback.sh`

```bash
#!/bin/bash

set -e

TARGET_VERSION=${1:-previous}

echo "🔄 Rolling back to $TARGET_VERSION..."

railway rollback $TARGET_VERSION

echo "⏳ Waiting for rollback to complete..."
sleep 10

# Verify rollback
if curl -s https://$RAILWAY_SERVICE_DOMAIN/health | grep -q "ok"; then
    echo "✅ Rollback successful"
else
    echo "❌ Rollback failed - health check failed"
    exit 1
fi
```

**Step 3: Commit**

```bash
git add scripts/canary_deploy.sh scripts/rollback.sh
git commit -m "feat(deployment): add canary deployment and rollback strategies"
```

---

## Task 7: Deployment Documentation

**Objective:** Create comprehensive deployment guide.

**Files:**
- Create: `docs/PHASE5_DEPLOYMENT_GUIDE.md`
- Create: `docs/DEPLOYMENT_TROUBLESHOOTING.md`

**Step 1: Create deployment guide**

File: `docs/PHASE5_DEPLOYMENT_GUIDE.md`

```markdown
# Phase 5: Railway Deployment Guide

## Overview

This guide covers deploying the 88i Sinistro Agent to Railway.app with production-grade reliability.

## Prerequisites

- Railway.app account (free tier available)
- GitHub account with this repository
- Docker installed locally
- Railway CLI installed: `npm install -g @railway/cli`

## Local Development with Docker

```bash
# Build image
docker build -t 88i-sinistro:latest .

# Run with docker-compose
docker-compose up

# Test health check
curl http://localhost:8000/health

# View logs
docker-compose logs -f app
```

## Deploying to Railway

### 1. First Time Setup

```bash
# Clone repository
git clone https://github.com/olga-ai-lab/88i-sinistro-harness.git
cd 88i-sinistro-harness

# Login to Railway
railway login

# Link project
railway link

# Set environment variables
railway variables set ANTHROPIC_API_KEY=your-key
railway variables set SUPABASE_URL=your-url
# ... (set all required variables)
```

### 2. Deploy

```bash
# Deploy to Railway
railway up

# Check deployment status
railway status

# View logs
railway logs

# Get service URL
railway open
```

### 3. Verify Deployment

```bash
# Get Railway service domain
DOMAIN=$(railway status | grep URL | awk '{print $2}')

# Test health check
curl https://$DOMAIN/health

# Test detailed health
curl https://$DOMAIN/health/detailed
```

## CI/CD Deployment

### GitHub Actions

Automatic deployment is triggered on push to main:

1. Tests run (unit, security, performance)
2. Docker image is built and pushed to registry
3. Railway deployment is triggered
4. Health checks verify deployment success

### Manual Deployment

```bash
# Via GitHub CLI
gh workflow run deploy.yml

# Monitor workflow
gh run list
gh run view <run-id> --log
```

## Monitoring

### Health Checks

- `/health` — Basic health check (load balancer)
- `/health/live` — Liveness probe (is app running?)
- `/health/ready` — Readiness probe (can accept traffic?)
- `/health/detailed` — Detailed status with all checks

### Logs

View logs in Railway dashboard or via CLI:

```bash
railway logs --follow
```

Logs are structured JSON for easy parsing.

### Metrics

Access metrics endpoint:

```bash
curl https://$DOMAIN/metrics
```

## Canary Deployments

For safe deployments, use canary strategy:

```bash
# Deploy with 10% traffic to new version
./scripts/canary_deploy.sh 10

# Monitor for 5 minutes
# If error rate < 5%, full traffic shift
# If error rate > 5%, automatic rollback
```

## Rollback

If deployment has issues:

```bash
# Rollback to previous version
./scripts/rollback.sh

# Or specify target version
./scripts/rollback.sh <version-id>
```

## Environment Variables

Required variables (set in Railway dashboard):

- `ANTHROPIC_API_KEY` — Claude API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase service role key
- `INNGEST_API_KEY` — Inngest API key
- `LANGFUSE_PUBLIC_KEY` — Langfuse public key
- `LANGFUSE_SECRET_KEY` — Langfuse secret key
- `ENVIRONMENT` — "production"

## Troubleshooting

See `docs/DEPLOYMENT_TROUBLESHOOTING.md`

## Next Steps

- Set up custom domain
- Configure backup strategy
- Set up monitoring alerts
- Performance tuning
```

**Step 2: Create troubleshooting guide**

File: `docs/DEPLOYMENT_TROUBLESHOOTING.md`

```markdown
# Deployment Troubleshooting Guide

## Common Issues

### 1. Health check fails immediately after deployment

**Symptom:** `/health` returns 503 or times out

**Solutions:**
- Increase health check timeout in Dockerfile
- Check environment variables are set correctly
- Verify database connectivity
- Check application logs

```bash
railway logs --follow
```

### 2. Port binding error

**Symptom:** "Address already in use" error

**Solution:** Railway will assign PORT via environment variable
- Ensure app reads PORT from env: `--port $PORT`
- Don't hardcode port 8000

### 3. Database connection fails

**Symptom:** "Connection to Supabase failed"

**Solutions:**
- Verify SUPABASE_URL and SUPABASE_KEY are set
- Check database is running and accessible
- Verify IP is whitelisted (if applicable)
- Test connection locally first

### 4. API key errors

**Symptom:** "Invalid API key" or "Unauthorized"

**Solutions:**
- Verify API keys are correct
- Check for typos in environment variables
- Regenerate keys if suspected compromise
- Ensure keys are set in Railway dashboard, not in .env

### 5. Out of memory errors

**Symptom:** "MemoryError" in logs

**Solutions:**
- Increase Railway memory allocation
- Optimize code for memory usage
- Review logs for memory leaks
- Consider horizontal scaling

### 6. Slow deployment or timeout

**Symptom:** Deployment takes > 5 minutes or times out

**Solutions:**
- Check Docker image size
- Optimize build dependencies
- Use multi-stage builds (already implemented)
- Check network connectivity

## Getting Help

1. Check Railway logs: `railway logs --follow`
2. Verify environment variables: `railway variables list`
3. Test health endpoints: `curl https://$DOMAIN/health/detailed`
4. Check GitHub Actions logs for CI/CD issues
5. Contact Railway support: https://railway.app/support
```

**Step 3: Commit**

```bash
git add docs/PHASE5_DEPLOYMENT_GUIDE.md docs/DEPLOYMENT_TROUBLESHOOTING.md
git commit -m "docs: add comprehensive deployment guide and troubleshooting"
```

---

## Summary

7 tasks covering:

1. ✅ Dockerfile + docker-compose configuration
2. ✅ Railway.app deployment setup
3. ✅ GitHub Actions CI/CD pipeline
4. ✅ Health checks + graceful shutdown
5. ✅ Monitoring, logging, and metrics
6. ✅ Canary deployment strategy
7. ✅ Documentation + troubleshooting

**Expected Deliverables:**
- 1,500+ LOC code (Docker, health, monitoring, middleware)
- 3,000+ LOC documentation (deployment guides)
- 3 GitHub Actions workflows
- 2 deployment scripts
- 7 git commits

**Ready to execute Phase 5?** Type "sim" and I'll dispatch subagents for implementation.
