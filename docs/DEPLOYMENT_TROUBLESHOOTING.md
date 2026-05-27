# Deployment Troubleshooting Guide

> Comprehensive troubleshooting guide for common deployment issues on Railway.app, with symptoms, solutions, and code examples.

## Table of Contents

1. [Health Check Fails](#1-health-check-fails)
2. [Port Binding Error](#2-port-binding-error)
3. [Database Connection Fails](#3-database-connection-fails)
4. [API Key Errors](#4-api-key-errors)
5. [Out of Memory Errors](#5-out-of-memory-errors)
6. [Slow Deployment or Timeout](#6-slow-deployment-or-timeout)
7. [Container Crashes](#7-container-crashes-immediately)
8. [Service Not Accessible](#8-service-not-accessible)
9. [Log Collection and Analysis](#log-collection-and-analysis)
10. [Preventive Measures](#preventive-measures)

---

## 1. Health Check Fails

### Symptom

After deployment, the service shows as unhealthy:

```
❌ Health check failed: GET /health returned 503 Service Unavailable
❌ Status: Failed (health checks did not pass)
❌ Load balancer: No healthy instances
```

Or in logs:
```
ERROR: /health endpoint timeout
ERROR: Connection refused on port 8000
ERROR: Database connection failed
```

### Root Causes

- Application takes too long to start
- Missing environment variables
- Database not accessible
- API keys invalid
- Required services not running
- Port not properly exposed
- Memory/resource constraints

### Solutions

#### Solution 1: Check Application Logs

```bash
# View real-time logs as service starts
railway logs --follow

# View last 100 lines
railway logs -n 100

# Filter for errors
railway logs | grep -i "error"

# Filter for startup messages
railway logs | grep -i "startup\|listening\|ready"

# Expected startup sequence:
# INFO: Starting Uvicorn...
# INFO: Application startup complete
# INFO: /health endpoint ready
# INFO: Listening on 0.0.0.0:8000
```

#### Solution 2: Verify Environment Variables

```bash
# Check all variables are set
railway variables list

# Look for missing required variables:
# - ANTHROPIC_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY
# - INNGEST_API_KEY
# - LANGFUSE_PUBLIC_KEY
# - LANGFUSE_SECRET_KEY

# If variables are missing, set them:
railway variables set ANTHROPIC_API_KEY=sk-your-key
railway variables set SUPABASE_URL=https://your-project.supabase.co
# ... etc

# Redeploy after setting variables
railway up
```

#### Solution 3: Verify Database Connectivity

Test database connection locally first:

```bash
# Check if SUPABASE_URL and SUPABASE_KEY are correct
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-key

# Test connectivity with Python
python << 'EOF'
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:10]}...")

try:
    supabase = create_client(url, key)
    result = supabase.table("test").select("*").limit(1).execute()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
```

#### Solution 4: Increase Health Check Timeout

In Dockerfile:

```dockerfile
# Increase start period from 5s to 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1
```

Then rebuild and deploy:

```bash
docker build -t 88i-sinistro:latest .
railway up
```

#### Solution 5: Check API Keys

Verify API keys are valid and not expired:

```bash
# Test Anthropic API key
python << 'EOF'
import os
from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key or not api_key.startswith("sk-"):
    print("❌ Invalid ANTHROPIC_API_KEY format")
    exit(1)

try:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "test"}]
    )
    print("✅ Anthropic API key is valid")
except Exception as e:
    print(f"❌ API key error: {e}")
EOF
```

#### Solution 6: Check Application Code

Ensure the `/health` endpoint exists and is correctly implemented:

```python
# app/health.py
from fastapi import APIRouter, HTTPException
import os
import time
from datetime import datetime

router = APIRouter()

app_start_time = time.time()

@router.get("/health")
async def health():
    """Basic health check for load balancer."""
    try:
        # Quick checks
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/health/live")
async def health_live():
    """Liveness probe - is app running?"""
    return {"status": "live"}

@router.get("/health/ready")
async def health_ready():
    """Readiness probe - can accept traffic?"""
    try:
        # Check dependencies
        # - Database connection
        # - Cache connectivity
        # - API keys configured
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/health/detailed")
async def health_detailed():
    """Detailed health status."""
    uptime = time.time() - app_start_time
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": int(uptime),
        "checks": {
            "database": "ok",
            "api_keys": "ok",
            "memory": "ok"
        }
    }
```

Register in main app:

```python
# main.py
from fastapi import FastAPI
from app.health import router as health_router

app = FastAPI()
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

#### Solution 7: Test Locally

Before deploying to Railway, test locally:

```bash
# Start app locally
docker-compose up

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"ok","timestamp":"2026-05-27T..."}

# Test detailed health
curl http://localhost:8000/health/detailed

# Check logs
docker-compose logs -f app
```

---

## 2. Port Binding Error

### Symptom

```
❌ Error: Address already in use: ('0.0.0.0', 8000)
❌ Error: Port 8000 is already in use
❌ Error: bind: permission denied
```

Or in logs:
```
OSError: [Errno 48] Address already in use
ERROR: Cannot start application on port 8000
```

### Root Causes

- Hardcoded port instead of using PORT environment variable
- Port is already in use by another process
- Permission denied (trying to use privileged port < 1024)
- Docker container not releasing port

### Solutions

#### Solution 1: Use PORT Environment Variable

The application MUST read the PORT from the environment variable:

```python
# ✅ CORRECT - reads from environment
import os
import uvicorn

port = int(os.environ.get("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
```

```python
# ❌ WRONG - hardcoded port
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)  # Wrong!
```

In Dockerfile:

```dockerfile
# ✅ CORRECT - uses $PORT variable
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
```

#### Solution 2: Check Environment Variable is Set

```bash
# Verify PORT is set in Railway
railway variables list | grep PORT

# If not set, add it
railway variables set PORT=8000

# Redeploy
railway up
```

#### Solution 3: Find and Kill Process Using Port

If testing locally and port is in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use Docker to kill container
docker-compose down

# Verify port is free
lsof -i :8000  # Should return nothing
```

#### Solution 4: Use Different Port for Local Testing

```bash
# Run on different port locally
PORT=8001 python main.py

# Or with docker-compose
PORT=8001 docker-compose up
```

#### Solution 5: Check Dockerfile Syntax

Ensure environment variables are properly expanded:

```dockerfile
# ✅ CORRECT - uses variable
EXPOSE ${PORT:-8000}
CMD [..., "--port", "${PORT:-8000}"]

# ✅ ALSO CORRECT - hardcoded with default
EXPOSE 8000
# Railway will override PORT at runtime

# ❌ WRONG - quotes prevent expansion
CMD [..., "--port", '${PORT:-8000}']  # Won't expand!
```

---

## 3. Database Connection Fails

### Symptom

```
❌ Error: could not connect to server: Connection refused
❌ Error: FATAL: no password supplied
❌ Error: FATAL: password authentication failed
❌ Error: database "postgres" does not exist
```

Or in logs:
```
ERROR: psycopg2.OperationalError: could not connect to server
ERROR: Connection to Supabase failed
ERROR: Authentication failed for database user
```

### Root Causes

- SUPABASE_URL or SUPABASE_KEY not set
- Credentials are incorrect
- Database server is down or not accessible
- Database user lacks permissions
- Connection pool exhausted
- Network/firewall blocking access

### Solutions

#### Solution 1: Verify Credentials

Check that database credentials are correct:

```bash
# Get Supabase credentials from dashboard
# https://app.supabase.com → your-project → Settings → Database

# View current variables
railway variables list

# Verify SUPABASE_URL format
railway variables list | grep SUPABASE_URL
# Should be: https://[project-id].supabase.co

# Verify SUPABASE_KEY format
railway variables list | grep SUPABASE_KEY
# Should be: eyJhbGc... (JWT token)
```

#### Solution 2: Test Connection Locally

```bash
# Create test script
python << 'EOF'
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:20]}...")

if not url or not key:
    print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

try:
    supabase = create_client(url, key)
    
    # Test query
    result = supabase.table("sinistros").select("*").limit(1).execute()
    print("✅ Database connection successful")
    print(f"Tables accessible: {len(result.data)} rows")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
EOF
```

#### Solution 3: Test PostgreSQL Directly

If using direct PostgreSQL connection:

```bash
# Test with psql
psql -h your-project.supabase.co \
     -p 5432 \
     -U postgres \
     -d postgres \
     -c "SELECT 1;"

# Or with Python psycopg2
python << 'EOF'
import psycopg2

try:
    conn = psycopg2.connect(
        host="your-project.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="your-password"
    )
    print("✅ Direct PostgreSQL connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

#### Solution 4: Check Database Exists

```bash
# Query available databases
psql -h your-host -U postgres -c "\l"

# Create database if missing
psql -h your-host -U postgres -c "CREATE DATABASE sinistros;"

# Or run migrations
python -m alembic upgrade head
```

#### Solution 5: Increase Connection Pool

If getting "too many connections" errors:

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.environ.get("DATABASE_URL"),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

#### Solution 6: Check Network Access

Railway service must be able to reach Supabase:

```bash
# From Railway container, test connectivity
railway ssh
curl https://your-project.supabase.co/health

# Or within app:
python << 'EOF'
import socket
import os

url = os.environ.get("SUPABASE_URL").replace("https://", "")
port = 443

try:
    result = socket.create_connection((url, port), timeout=5)
    print(f"✅ Can reach {url}:{port}")
    result.close()
except Exception as e:
    print(f"❌ Cannot reach {url}:{port}: {e}")
EOF
```

---

## 4. API Key Errors

### Symptom

```
❌ Error: Invalid API key
❌ Error: Unauthorized - missing API key
❌ Error: 401 Unauthorized
❌ Error: API key is expired
❌ Error: API key has insufficient permissions
```

Or in logs:
```
ERROR: anthropic.error.AuthenticationError: Unauthorized
ERROR: Invalid INNGEST_API_KEY
ERROR: Langfuse authentication failed
```

### Root Causes

- API key not set in environment variables
- API key is incorrect or malformed
- API key has been revoked or expired
- API key lacks required permissions
- Typo in environment variable name
- API service account deprecated

### Solutions

#### Solution 1: Verify API Keys Are Set

```bash
# Check all API keys are set
railway variables list

# Should include:
# - ANTHROPIC_API_KEY
# - INNGEST_API_KEY
# - LANGFUSE_PUBLIC_KEY
# - LANGFUSE_SECRET_KEY

# If missing, set them:
railway variables set ANTHROPIC_API_KEY=sk-ant-xxxx
railway variables set INNGEST_API_KEY=inngest_xxxx
railway variables set LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
railway variables set LANGFUSE_SECRET_KEY=sk-lf-xxxx
```

#### Solution 2: Test Anthropic API Key

```bash
# Test API key format and validity
python << 'EOF'
import os
from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY not set")
    exit(1)

if not api_key.startswith("sk-ant-"):
    print("❌ Invalid API key format (should start with 'sk-ant-')")
    exit(1)

print(f"✅ API key format valid: {api_key[:10]}...")

try:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "test"}]
    )
    print("✅ API key is valid and working")
except Exception as e:
    print(f"❌ API key error: {e}")
EOF
```

#### Solution 3: Test Inngest API Key

```bash
# Test Inngest connectivity
python << 'EOF'
import os
import requests

api_key = os.environ.get("INNGEST_API_KEY")

if not api_key:
    print("❌ INNGEST_API_KEY not set")
    exit(1)

try:
    response = requests.get(
        "https://api.inngest.com/v0/health",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if response.status_code == 200:
        print("✅ Inngest API key is valid")
    else:
        print(f"❌ Inngest API key error: {response.status_code}")
except Exception as e:
    print(f"❌ Inngest connectivity error: {e}")
EOF
```

#### Solution 4: Regenerate Expired Keys

For each service, regenerate the API key:

```bash
# Anthropic (Claude)
# 1. Go to https://console.anthropic.com/
# 2. Settings → API Keys
# 3. Create new key
# 4. Update in Railway:
railway variables set ANTHROPIC_API_KEY=sk-ant-new-key

# Inngest
# 1. Go to https://app.inngest.com
# 2. Settings → API Keys
# 3. Regenerate key
# 4. Update in Railway:
railway variables set INNGEST_API_KEY=inngest_new_key

# Langfuse
# 1. Go to https://cloud.langfuse.com
# 2. Settings → API Keys
# 3. Regenerate keys
# 4. Update in Railway:
railway variables set LANGFUSE_PUBLIC_KEY=pk-lf-new-key
railway variables set LANGFUSE_SECRET_KEY=sk-lf-new-key
```

#### Solution 5: Check Variable Names (Typos)

API keys are case-sensitive. Verify exact names:

```bash
# ✅ CORRECT variable names:
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_KEY
INNGEST_API_KEY
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY

# ❌ WRONG (will cause issues):
anthropic_api_key        # lowercase
ANTHROPIC_KEY            # missing API_
ANTHROPICAPIKEY          # no underscores
```

Verify in code:

```python
# app/config.py
import os

# Ensure these match Railway environment variables exactly
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
INNGEST_API_KEY = os.environ.get("INNGEST_API_KEY")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")

# Validate on startup
def validate_config():
    required = [
        ANTHROPIC_API_KEY,
        SUPABASE_URL,
        SUPABASE_KEY,
        INNGEST_API_KEY,
        LANGFUSE_PUBLIC_KEY,
        LANGFUSE_SECRET_KEY,
    ]
    
    missing = [k for k in required if not k]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
```

---

## 5. Out of Memory Errors

### Symptom

```
❌ Error: MemoryError
❌ Process killed (out of memory)
❌ Killed (signal SIGKILL)
```

Or in logs:
```
ERROR: MemoryError: Unable to allocate 256 MiB
ERROR: Process exhausted available memory
```

### Root Causes

- Application memory leak
- Railway plan has insufficient memory
- Large dataset being loaded into memory
- Unbounded cache growth
- Memory not being garbage collected

### Solutions

#### Solution 1: Upgrade Railway Memory

```bash
# Check current memory allocation
railway status

# View available plans
railway plan

# Increase memory allocation
# 1. Open Railway dashboard
# 2. Go to project → settings
# 3. Change plan to higher tier
# 4. Redeploy application
railway up
```

#### Solution 2: Monitor Memory Usage

```bash
# Monitor memory in real-time
while true; do
  railway status | grep -E "Memory|CPU"
  sleep 5
done

# Or check detailed metrics
curl https://$DOMAIN/metrics | grep "memory"
```

#### Solution 3: Find Memory Leaks

Add memory profiling:

```python
# app/memory_monitor.py
import tracemalloc
import os
from fastapi import APIRouter

router = APIRouter()
tracemalloc.start()

@router.get("/debug/memory")
async def debug_memory():
    """Get memory usage snapshot."""
    current, peak = tracemalloc.get_traced_memory()
    
    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "top_allocations": [
            {
                "file": str(stat.traceback[0]),
                "size_mb": stat.size / 1024 / 1024,
                "count": stat.count,
            }
            for stat in tracemalloc.take_snapshot().statistics("lineno")[:10]
        ]
    }

@router.post("/debug/gc")
async def debug_gc():
    """Force garbage collection."""
    import gc
    collected = gc.collect()
    return {"collected_objects": collected}
```

#### Solution 4: Limit Cache Size

```python
# app/cache.py
from functools import lru_cache
from cachetools import TTLCache

# ✅ GOOD - bounded cache
cache = TTLCache(maxsize=1000, ttl=3600)

# ❌ BAD - unbounded cache
cache = {}

# ✅ GOOD - limited LRU cache
@lru_cache(maxsize=100)
def expensive_function(x):
    return x ** 2
```

#### Solution 5: Stream Large Responses

```python
# app/routes.py
from fastapi.responses import StreamingResponse
import json

# ❌ BAD - loads entire dataset into memory
@app.get("/sinistros")
async def get_all_sinistros():
    sinistros = fetch_all_sinistros()  # Loads all data!
    return sinistros

# ✅ GOOD - streams results
@app.get("/sinistros")
async def get_all_sinistros():
    async def generate():
        async for sinistro in fetch_sinistros_paginated():
            yield json.dumps(sinistro) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")
```

#### Solution 6: Enable Memory Limits in App

```python
# app/middleware.py
import psutil
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def memory_middleware(request: Request, call_next):
    """Monitor memory and reject if too high."""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Reject if memory > 80% of limit
    if memory_mb > 400:  # Assuming 512MB limit
        return JSONResponse(
            status_code=503,
            content={"error": "Memory pressure - service unavailable"}
        )
    
    response = await call_next(request)
    return response
```

---

## 6. Slow Deployment or Timeout

### Symptom

```
⏳ Deployment in progress... (5 minutes elapsed)
⏳ Still waiting for health checks... (10 minutes elapsed)
❌ Deployment timeout - exceeded maximum time
```

Or in Railway:
```
Status: Building... (stuck)
Status: Deploying... (hung)
```

### Root Causes

- Large Docker image size
- Many dependencies to install
- Network connectivity issues
- Insufficient resources in build environment
- Build caching not working
- Heavy build process

### Solutions

#### Solution 1: Check Docker Image Size

```bash
# Build and check size
docker build -t 88i-sinistro:latest .
docker images | grep 88i-sinistro

# Check layer sizes
docker history 88i-sinistro:latest

# Optimize: remove unnecessary layers
# - Use slim Python image (instead of full)
# - Remove build dependencies in final image
# - Multi-stage build already implemented
```

#### Solution 2: Optimize Dockerfile

Reduce image size:

```dockerfile
# ✅ GOOD - multi-stage build
FROM python:3.13-slim as builder
# ... build here ...

FROM python:3.13-slim
# ... copy only necessary files ...

# ❌ BAD - everything in one stage
FROM python:3.13
# ... all files and dependencies ...
```

#### Solution 3: Optimize Requirements

Reduce number of dependencies:

```bash
# Check what's installed
pip freeze | wc -l

# Remove unused dependencies
# Audit with: pip install pipdeptree
pipdeptree

# Use specific versions for faster resolution
# Instead of: requests
# Use: requests==2.31.0
```

#### Solution 4: Use Docker Layer Caching

Order Dockerfile to leverage cache:

```dockerfile
# ✅ GOOD - frequently changing files last
FROM python:3.13-slim

# Stable layer - rarely changes
COPY requirements.txt .
RUN pip install -r requirements.txt

# Volatile layer - changes often
COPY . .
RUN python setup.py install

# ❌ BAD - copying everything first
FROM python:3.13-slim
COPY . .
RUN pip install -r requirements.txt
```

#### Solution 5: Parallel Builds

Run builds in parallel for faster completion:

```bash
# In .github/workflows/deploy.yml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        platform: [linux/amd64, linux/arm64]
    steps:
      - name: Build for multiple platforms
        uses: docker/build-push-action@v4
        with:
          platforms: ${{ matrix.platform }}
```

#### Solution 6: Increase Build Timeout

In Railway, increase timeout:

```bash
# Set deployment timeout (in railway.json)
{
  "deploy": {
    "buildTimeout": 1800  # 30 minutes
  }
}
```

#### Solution 7: Monitor Build Process

```bash
# View build logs in real-time
railway logs --follow --deployment <deployment-id>

# Check if Docker is caching properly
docker builder prune  # Clear cache if needed

# Rebuild without cache
docker build --no-cache -t 88i-sinistro:latest .
```

---

## 7. Container Crashes Immediately

### Symptom

```
❌ Status: Failed
❌ Container exited with code 1
❌ CrashLoopBackOff
```

Or in logs:
```
ERROR: Application failed to start
Traceback (most recent call last):
  ...
SystemExit: 1
```

### Root Causes

- Unhandled exception in main startup code
- Missing import or module not found
- Invalid configuration
- Database schema missing
- Syntax error in code

### Solutions

#### Solution 1: Check Startup Logs Immediately

```bash
# View logs right after deployment starts
railway logs -n 200

# Search for stack trace
railway logs | grep -A 20 "Traceback"

# Look for specific error
railway logs | grep -i "error\|failed\|exception"
```

#### Solution 2: Add Startup Validation

```python
# app/startup.py
import os
from dotenv import load_dotenv

def validate_startup():
    """Validate all requirements at startup."""
    errors = []
    
    # Check environment variables
    required_vars = [
        "ANTHROPIC_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f"Missing: {var}")
    
    # Check database
    try:
        from app.database import check_connection
        check_connection()
    except Exception as e:
        errors.append(f"Database error: {e}")
    
    # Check API keys
    try:
        from anthropic import Anthropic
        Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    except Exception as e:
        errors.append(f"API key error: {e}")
    
    if errors:
        raise RuntimeError("\n".join(errors))
    
    print("✅ All startup checks passed")
```

Use in main:

```python
# main.py
from fastapi import FastAPI
from app.startup import validate_startup

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    validate_startup()
```

#### Solution 3: Test Startup Locally

```bash
# Run app locally to catch errors early
docker-compose up

# Watch for startup errors
docker-compose logs -f app | head -50

# Fix errors and rebuild
docker-compose restart
```

#### Solution 4: Handle Graceful Shutdown

```python
# app/shutdown.py
import signal
import os

def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    print("Received signal, shutting down...")
    
    # Cleanup
    # - Close database connections
    # - Cancel running tasks
    # - Save state
    
    os.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
```

---

## 8. Service Not Accessible

### Symptom

```
❌ Cannot connect to service
❌ Connection refused
❌ curl: (7) Failed to connect
❌ DNS resolution failed
```

Or browser shows:
```
ERR_CONNECTION_REFUSED
Unable to reach this page
```

### Root Causes

- Service not started properly
- Port not exposed correctly
- SSL/TLS certificate issues
- Custom domain not configured
- Load balancer not routing traffic
- Network policy restricting access

### Solutions

#### Solution 1: Verify Service is Running

```bash
# Check service status
railway status

# Should show: Status: Running

# Check deployment is active
railway deployment list

# Check if health checks are passing
curl https://$DOMAIN/health
```

#### Solution 2: Check Domain Configuration

```bash
# Get service domain from Railway
DOMAIN=$(railway status | grep "URL:" | awk '{print $NF}')

# Test DNS resolution
nslookup $DOMAIN
dig $DOMAIN

# Should return IP address(es)

# Test connectivity
curl -I https://$DOMAIN

# Check SSL certificate
openssl s_client -connect $DOMAIN:443
```

#### Solution 3: Test with IP Address

If domain doesn't work, get IP and test directly:

```bash
# Get service IP
IP=$(dig +short $DOMAIN | head -1)

# Test with IP
curl https://$IP/health

# If works with IP but not domain, DNS issue
# If doesn't work with IP, service not accessible
```

#### Solution 4: Check Firewall/Network

```bash
# Railway service should be accessible publicly
# Check if any network policies restrict access

# From local machine
telnet $DOMAIN 443

# Should connect (even if response times out)
```

#### Solution 5: Verify Service Binding

In Dockerfile, ensure app binds to all interfaces:

```dockerfile
# ✅ CORRECT - listens on all interfaces
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]

# ❌ WRONG - only localhost
CMD ["python", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "${PORT:-8000}"]
```

---

## Log Collection and Analysis

### Viewing Logs

```bash
# Real-time logs
railway logs --follow

# Last 50 lines
railway logs -n 50

# Last 200 lines
railway logs -n 200

# Save to file
railway logs > app-logs.txt

# Filter by level
railway logs | grep '"level":"ERROR"'

# Filter by component
railway logs | grep "database\|api\|health"

# Pretty print JSON logs
railway logs | jq '.'
```

### Structured Logging

The application uses structured JSON logging:

```json
{
  "timestamp": "2026-05-27T10:30:00Z",
  "level": "INFO",
  "message": "request_complete",
  "request_id": "abc-123-def",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 5
}
```

Parse with jq:

```bash
# Extract specific fields
railway logs | jq '.timestamp, .level, .message'

# Filter by level
railway logs | jq 'select(.level == "ERROR")'

# Calculate average duration
railway logs | jq 'select(.duration_ms) | .duration_ms' | awk '{sum+=$1; count++} END {print "Average:", sum/count}'
```

### Common Log Patterns

```bash
# Find errors
railway logs | grep '"level":"ERROR"'

# Find slow requests (> 1 second)
railway logs | jq 'select(.duration_ms > 1000)'

# Find failed health checks
railway logs | grep '"path":"/health"' | grep -v '"status_code":200'

# Find database errors
railway logs | grep -i "database\|connection\|query"

# Find API key errors
railway logs | grep -i "unauthorized\|authentication\|api.*key"
```

---

## Preventive Measures

### 1. Health Check Monitoring

```bash
# Monitor health checks continuously
while true; do
  STATUS=$(curl -s https://$DOMAIN/health | jq '.status')
  TIMESTAMP=$(date -Iseconds)
  echo "[$TIMESTAMP] Health: $STATUS"
  
  if [ "$STATUS" != "ok" ]; then
    echo "❌ Health check failed!"
    # Trigger alert
  fi
  
  sleep 30
done
```

### 2. Regular Deployment Tests

```bash
# Before each production deployment
# 1. Test locally with docker-compose
docker-compose up
curl http://localhost:8000/health

# 2. Run full test suite
pytest tests/ -v

# 3. Check Docker image size
docker images | grep 88i-sinistro

# 4. Dry-run deployment (if supported)
railway up --dry-run
```

### 3. Database Backup Verification

```bash
# Regular backups (set in Supabase)
# 1. Enable automated backups
# 2. Test restore process monthly
# 3. Monitor backup completion
```

### 4. Log Monitoring Setup

```bash
# Set up alerts for:
# - Error rate > 5% over 5 minutes
# - Health check failures > 3 consecutive
# - Memory usage > 80%
# - Database connection errors
# - Slow requests > 5 seconds (p95)
```

### 5. Security Scanning

```bash
# Before deployment
# Scan dependencies for vulnerabilities
pip install safety
safety check

# Scan Docker image
docker run --rm -i anchore/grype:latest < <(docker save 88i-sinistro:latest) | head -20
```

### 6. Performance Baseline

Establish baseline metrics for comparison:

```bash
# Record baseline metrics
AB_RESULTS="baseline-$(date +%s).txt"
ab -n 1000 -c 50 -t 30 https://$DOMAIN/health > $AB_RESULTS
cat $AB_RESULTS
```

### 7. Runbook Creation

Create an incident runbook:

```markdown
# Incident Response Runbook

## Service Down

1. Check status: `railway status`
2. View logs: `railway logs -n 100`
3. Check health: `curl https://$DOMAIN/health/detailed`
4. Rollback if needed: `./scripts/rollback.sh`

## High Error Rate

1. Check metrics: `curl https://$DOMAIN/metrics`
2. Analyze logs: `railway logs | grep ERROR`
3. Scale up if needed: `railway plan upgrade`

## Database Issues

1. Check connection: `psql -h $HOST -U $USER -c "SELECT 1"`
2. Check migrations: `alembic current`
3. Run migrations: `alembic upgrade head`
```

---

## Summary

This troubleshooting guide covers:

✅ Health check failures  
✅ Port binding errors  
✅ Database connection issues  
✅ API key authentication  
✅ Memory errors  
✅ Slow deployment timeouts  
✅ Container crashes  
✅ Service accessibility  
✅ Log analysis  
✅ Preventive measures  

**For additional help:**
- Railway Support: https://railway.app/support
- GitHub Issues: https://github.com/olga-ai-lab/88i-sinistro-harness/issues
- Check `docs/PHASE5_DEPLOYMENT_GUIDE.md` for deployment instructions

**Last Updated**: May 27, 2026  
**Version**: 1.0  
