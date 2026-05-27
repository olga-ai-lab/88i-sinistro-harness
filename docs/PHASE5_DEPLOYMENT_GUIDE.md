# Phase 5: Railway Deployment Guide

> Complete guide for deploying the 88i Sinistro Agent to Railway.app with production-grade reliability, monitoring, and safe deployment practices.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development with Docker](#local-development-with-docker)
- [First Time Setup](#first-time-setup)
- [Deploy](#deploy)
- [Verify Deployment](#verify-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring](#monitoring)
- [Canary Deployments](#canary-deployments)
- [Rollback](#rollback)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Overview

This guide covers deploying the **88i Sinistro Agent** to Railway.app with production-grade reliability, comprehensive monitoring, structured logging, and safe deployment strategies including canary deployments and rollback procedures.

### What is Railroad/Railway?

Railway.app is a modern cloud platform for deploying applications with:
- Automatic SSL/TLS termination
- GitHub integration for CI/CD
- Environment variable management
- Built-in logging and monitoring
- Horizontal scaling
- PostgreSQL, Redis, and other services
- Health check monitoring
- Graceful deployment management

### Architecture Overview

```
Local Development
├── Docker (local containerization)
├── Docker Compose (multi-service setup)
└── Environment (.env file)
                ↓
           Git Push
                ↓
        GitHub Actions
           (CI Pipeline)
├── Run tests
├── Security scans
├── Build Docker image
└── Push to Railway
                ↓
        Railway.app
├── Load Balancer (SSL/TLS)
├── Health Checks (30s interval)
├── Application Instances
├── Monitoring & Logging
└── Graceful Shutdown
```

---

## Prerequisites

Before deploying to Railway, ensure you have:

### 1. Accounts and Credentials

- **Railway.app account** (free tier available at https://railway.app)
- **GitHub account** with access to this repository
- **API Keys:**
  - Anthropic API key (Claude)
  - Supabase credentials (URL + service role key)
  - Inngest API key
  - Langfuse credentials (public and secret keys)

### 2. Local Tools

Install the following tools on your machine:

```bash
# Docker Desktop (includes docker and docker-compose)
# Download from: https://www.docker.com/products/docker-desktop/

# Verify Docker installation
docker --version
docker-compose --version

# Railway CLI
npm install -g @railway/cli

# Verify Railway CLI
railway --version

# GitHub CLI (optional, for CI/CD automation)
brew install gh
gh --version
```

### 3. Repository Access

```bash
# Clone the repository
git clone https://github.com/olga-ai-lab/88i-sinistro-harness.git
cd 88i-sinistro-harness

# Verify required files exist
ls -la Dockerfile docker-compose.yml .dockerignore
ls -la scripts/deploy_railway.sh scripts/canary_deploy.sh scripts/rollback.sh
```

### 4. Environment Variables Setup

Create a local `.env.local` file (never commit this to git):

```bash
# Copy the example file
cp .env.example .env.local

# Edit with your credentials
nano .env.local
```

---

## Local Development with Docker

### Building the Docker Image

Build the Docker image locally to test the Dockerfile and ensure everything works:

```bash
# Build the image (tagged as latest)
docker build -t 88i-sinistro:latest .

# Build with a version tag
docker build -t 88i-sinistro:v1.0.0 .

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.13 \
  -t 88i-sinistro:latest .
```

### Running with Docker Compose

Docker Compose manages multiple services locally (app + Supabase):

```bash
# Start all services in the background
docker-compose up -d

# View logs for the app service
docker-compose logs -f app

# View logs for Supabase
docker-compose logs -f supabase

# View logs for all services
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Health Check Testing

Test the health endpoints while running locally:

```bash
# Basic health check (used by load balancer)
curl http://localhost:8000/health

# Expected output:
# {"status":"ok","timestamp":"2026-05-27T10:30:00Z"}

# Liveness probe (is app running?)
curl http://localhost:8000/health/live

# Readiness probe (can accept traffic?)
curl http://localhost:8000/health/ready

# Detailed health status
curl http://localhost:8000/health/detailed

# Expected output:
# {
#   "status": "ok",
#   "checks": {
#     "database": "ok",
#     "api_keys": "ok",
#     "memory": "ok"
#   },
#   "uptime_seconds": 3600,
#   "timestamp": "2026-05-27T10:30:00Z"
# }
```

### Running Tests in Container

```bash
# Run pytest inside the app container
docker-compose exec app pytest tests/ -v

# Run specific test file
docker-compose exec app pytest tests/test_health.py -v

# Run tests with coverage
docker-compose exec app pytest tests/ --cov=app --cov-report=html

# Interactive shell in container
docker-compose exec app /bin/bash
```

### Debugging in Container

```bash
# View real-time logs
docker-compose logs -f app

# View last 50 lines
docker-compose logs --tail=50 app

# Check container status
docker-compose ps

# Inspect container
docker inspect 88i-sinistro-harness_app_1

# Access Python shell in running container
docker-compose exec app python

# Run a one-off command
docker-compose run app python -c "import app; print(app.__version__)"
```

---

## First Time Setup

### Step 1: Railway Project Creation

Create a new project on Railway:

```bash
# Login to Railway
railway login

# You'll be redirected to a browser to authenticate
# Return to terminal after authentication

# Verify login
railway status
```

### Step 2: Link Your Repository

```bash
# Link your local repository to a Railway project
railway link

# Select your project (create new if needed)
# This creates a `.railway` directory in your repo
```

### Step 3: Configure Environment Variables

Set all required environment variables in Railway:

```bash
# Set variables one by one
railway variables set ANTHROPIC_API_KEY=sk-your-actual-key
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=eyJhbGc...your-actual-key
railway variables set INNGEST_API_KEY=inngest_your-actual-key
railway variables set LANGFUSE_PUBLIC_KEY=pk-your-actual-key
railway variables set LANGFUSE_SECRET_KEY=sk-your-actual-key
railway variables set ENVIRONMENT=production
railway variables set PORT=8000
railway variables set LOG_LEVEL=INFO
railway variables set PYTHONUNBUFFERED=1

# Verify variables are set
railway variables list
```

### Step 4: Create Database (if needed)

If using Supabase, ensure it's configured:

```bash
# In Railway dashboard:
# 1. Click "New" → PostgreSQL
# 2. Name it "postgres"
# 3. Connect to your app service
# 4. Variables will be auto-added (DATABASE_URL, etc.)
```

### Step 5: Create Configuration File

Create `railway.json` in the project root (if not already present):

```bash
cat > railway.json << 'EOF'
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
EOF
```

---

## Deploy

### Initial Deployment

Deploy the application to Railway:

```bash
# Deploy to Railway (will wait for completion)
railway up

# Deploy without waiting (asynchronous)
railway up --no-wait

# Check deployment status
railway status

# Get service URL
railway open

# View deployment logs in real-time
railway logs --follow
```

### What Happens During Deployment

1. **Build Phase** (2-5 minutes):
   - Docker image is built using your Dockerfile
   - Dependencies are installed
   - Image is pushed to Railway's registry

2. **Deploy Phase** (1-3 minutes):
   - Container is started on Railway infrastructure
   - Environment variables are injected
   - Service is registered with load balancer

3. **Health Check Phase** (starts immediately):
   - Every 30 seconds, load balancer hits `/health` endpoint
   - If 3 consecutive checks fail, deployment is considered failed
   - If healthy, service receives traffic

### Monitoring Deployment Progress

```bash
# Watch logs as deployment happens
railway logs --follow

# Watch in another terminal while deployment is happening
railway status

# Expected sequence:
# [1] Building Docker image...
# [2] Pushing to registry...
# [3] Starting container...
# [4] App is listening on 0.0.0.0:8000
# [5] Health check: OK
# [6] Service is live at https://your-domain.railway.app
```

---

## Verify Deployment

After deployment, verify everything is working:

### 1. Get Service Domain

```bash
# Get the Railway service domain
DOMAIN=$(railway status | grep "URL:" | awk '{print $NF}')
echo "Service URL: https://$DOMAIN"

# Or open in browser automatically
railway open
```

### 2. Test Health Endpoints

```bash
# Replace $DOMAIN with your actual domain
DOMAIN="your-domain.railway.app"

# Basic health check
curl https://$DOMAIN/health
# Expected: {"status":"ok","timestamp":"2026-05-27T..."}

# Liveness check
curl https://$DOMAIN/health/live
# Expected: {"status":"live"}

# Readiness check
curl https://$DOMAIN/health/ready
# Expected: {"status":"ready"}

# Detailed health status
curl https://$DOMAIN/health/detailed
# Expected: {...detailed status...}
```

### 3. Test Core Functionality

```bash
# Test the main API endpoint (example)
curl -X POST https://$DOMAIN/api/sinistros \
  -H "Content-Type: application/json" \
  -d '{"tipo":"fraude","descricao":"test claim"}'

# Expected: 200 OK with analysis results
```

### 4. Check Logs

```bash
# View logs in Railway dashboard
railway logs --follow

# Or use Railway CLI to tail logs
railway logs -n 50  # Last 50 lines

# Search logs
railway logs | grep "ERROR"
```

### 5. Monitor Metrics

```bash
# Get metrics endpoint (if exposed)
curl https://$DOMAIN/metrics

# Filter for specific metrics
curl https://$DOMAIN/metrics | grep "requests_total"
```

### 6. Performance Baseline

```bash
# Measure response time
time curl https://$DOMAIN/health

# Stress test (light)
ab -n 100 -c 10 https://$DOMAIN/health

# Check for errors
curl -i https://$DOMAIN/health/detailed
```

---

## CI/CD Pipeline

### GitHub Actions Automatic Deployment

When you push to the main branch, GitHub Actions automatically:

1. Runs all tests
2. Performs security scans
3. Builds and pushes Docker image
4. Triggers Railway deployment
5. Runs smoke tests on production

### Deployment Workflow File

The workflow is defined in `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway up --no-wait

  verify:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Wait for deployment
        run: sleep 30
      - name: Health check
        run: |
          curl --fail https://${{ secrets.RAILWAY_DOMAIN }}/health || exit 1
```

### Manual Deployment via CLI

```bash
# Trigger deployment manually
gh workflow run deploy.yml

# Monitor the workflow
gh run list

# View detailed logs
gh run view <run-id> --log

# Check workflow status
gh run list --status completed
```

### Disable Auto-Deploy

To deploy manually instead of on every push:

```bash
# Remove the 'push' trigger from .github/workflows/deploy.yml
# and use 'workflow_dispatch' instead for manual triggers
```

---

## Monitoring

### Health Check Endpoints

The application exposes several health check endpoints for load balancers and monitoring:

#### `/health` (Basic Health Check)

Used by Railway load balancer every 30 seconds:

```bash
curl https://$DOMAIN/health
```

Response (200 OK):
```json
{
  "status": "ok",
  "timestamp": "2026-05-27T10:30:00Z"
}
```

#### `/health/live` (Liveness Probe)

Indicates if the application is running:

```bash
curl https://$DOMAIN/health/live
```

Response (200 OK):
```json
{
  "status": "live"
}
```

#### `/health/ready` (Readiness Probe)

Indicates if the application is ready to accept traffic:

```bash
curl https://$DOMAIN/health/ready
```

Response (200 OK):
```json
{
  "status": "ready"
}
```

#### `/health/detailed` (Detailed Status)

Comprehensive health status including all subsystems:

```bash
curl https://$DOMAIN/health/detailed
```

Response (200 OK):
```json
{
  "status": "ok",
  "timestamp": "2026-05-27T10:30:00Z",
  "uptime_seconds": 3600,
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 5
    },
    "cache": {
      "status": "ok",
      "latency_ms": 2
    },
    "api_keys": {
      "status": "ok",
      "configured": 7
    },
    "memory": {
      "status": "ok",
      "used_mb": 256,
      "limit_mb": 512
    }
  }
}
```

### Structured Logging

Application logs are structured JSON for easy parsing:

```bash
# View logs with Railway CLI
railway logs --follow

# Logs are structured JSON:
# {"timestamp":"2026-05-27T10:30:00Z","level":"INFO","message":"request_complete","request_id":"abc-123","status_code":200,"duration_ms":45}

# Filter logs by level
railway logs | grep '"level":"ERROR"'

# Filter by request ID
railway logs | grep 'request_id":"abc-123"'

# Parse with jq
railway logs | jq '.level, .message, .duration_ms'
```

### Metrics Endpoint

Prometheus-format metrics are available:

```bash
curl https://$DOMAIN/metrics
```

Response (text/plain format):
```
# HELP app_requests_total Total requests
# TYPE app_requests_total counter
app_requests_total{method="GET",endpoint="/health",status="200"} 1542

# HELP app_request_duration_seconds Request duration
# TYPE app_request_duration_seconds histogram
app_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.01"} 500
app_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.1"} 1540
app_request_duration_seconds_bucket{method="GET",endpoint="/health",le="+Inf"} 1542

# HELP app_errors_total Total errors
# TYPE app_errors_total counter
app_errors_total{error_type="database_timeout"} 2
app_errors_total{error_type="api_key_invalid"} 1

# HELP sinistro_processed_total Total sinistros processed
# TYPE sinistro_processed_total counter
sinistro_processed_total{tipo="fraude",result="detected"} 42
sinistro_processed_total{tipo="fraude",result="safe"} 158
```

### Railway Dashboard Monitoring

Access your application's dashboard:

```bash
# Open Railway dashboard in browser
railway open

# Or via CLI
railway status

# View metrics in Railway UI:
# - CPU usage
# - Memory usage
# - Network I/O
# - Deployment history
# - Health check status
```

### Setting Up Alerts (Optional)

Monitor for issues by setting up alerts in Railway:

1. **Health Check Alerts**:
   - Alert if `/health` returns non-200 for 2+ minutes
   - Alert if deployment fails
   - Alert if restart loop detected

2. **Performance Alerts**:
   - Alert if response time > 5s
   - Alert if error rate > 5%
   - Alert if memory usage > 80%

3. **Availability Alerts**:
   - Alert on deployment failure
   - Alert on service restart

---

## Canary Deployments

Canary deployments gradually shift traffic to a new version while monitoring for errors.

### Why Use Canary Deployments?

- **Safe rollouts**: Detect issues before full traffic shift
- **Quick rollback**: If error rate spikes, automatically rollback
- **Progressive**: Start with 10% traffic, gradually increase
- **Confidence**: Monitor metrics before full commitment

### Canary Deployment Process

```bash
# 1. Deploy new version (10% canary traffic)
./scripts/canary_deploy.sh 10

# 2. Script does the following:
#    - Creates new deployment
#    - Waits for health checks to pass
#    - Routes 10% of traffic to new version
#    - Monitors for 5 minutes:
#      - Error rate
#      - Response latency
#      - Resource usage
#    - If error rate > 5%, automatic rollback
#    - If healthy, increases traffic to 25% → 50% → 75% → 100%
```

### Canary Deployment Script Breakdown

The script performs these steps:

```bash
#!/bin/bash

set -e

# 1. Get current stable version
STABLE_VERSION=$(railway status | grep "Service:" | awk '{print $2}')

# 2. Deploy new version (in background)
NEW_VERSION=$(railway up --no-wait)

# 3. Wait for new version to be healthy
for i in {1..30}; do
    if curl -s https://$RAILWAY_SERVICE_DOMAIN/health | grep -q "ok"; then
        break
    fi
    sleep 5
done

# 4. Configure traffic split (10% canary, 90% stable)
# This requires custom ingress controller or Railway traffic manager

# 5. Monitor metrics for 5 minutes
for i in {1..30}; do
    ERROR_RATE=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'error_rate')
    P95_LATENCY=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'p95_latency')
    
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "Error rate too high, rolling back..."
        railway rollback $STABLE_VERSION
        exit 1
    fi
    sleep 10
done

# 6. If healthy, shift to 100% new version
echo "Canary deployment successful!"
```

### Manual Canary Deployment

If using custom ingress or load balancer:

```bash
# 1. Deploy new version (get ID)
NEW_ID=$(railway up --no-wait)

# 2. Wait for health
sleep 30
curl https://$DOMAIN/health

# 3. Route traffic
# Using your load balancer configuration:
# - Route 10% to new-id
# - Route 90% to old-id

# 4. Monitor
railway logs --follow

# 5. After 5 minutes of successful monitoring, increase traffic
# - Route 25% to new-id
# - Route 75% to old-id
# ... repeat ...

# 6. Eventually route 100% to new-id
```

---

## Rollback

If a deployment causes issues, rollback to the previous version:

### Automatic Rollback

The canary deployment script automatically rolls back if:
- Health checks fail
- Error rate exceeds 5%
- Response latency exceeds threshold

### Manual Rollback

```bash
# 1. Identify the version to rollback to
railway deployment list

# 2. Rollback to previous version
./scripts/rollback.sh

# 3. Or specify a specific deployment ID
./scripts/rollback.sh <deployment-id>

# 4. Verify rollback
curl https://$DOMAIN/health

# Expected: {"status":"ok",...}
```

### Rollback Script Details

```bash
#!/bin/bash

set -e

TARGET_VERSION=${1:-previous}

echo "Rolling back to $TARGET_VERSION..."

# Railway rollback command
railway rollback $TARGET_VERSION

# Wait for rollback to complete
sleep 10

# Verify health check
if curl -s https://$DOMAIN/health | grep -q "ok"; then
    echo "Rollback successful"
else
    echo "Rollback failed - health check failed"
    exit 1
fi
```

### Emergency Rollback

If the service is completely down:

```bash
# 1. Check recent deployments
railway deployment list

# 2. Force rollback to stable version
railway rollback --force <stable-deployment-id>

# 3. Monitor logs
railway logs --follow

# 4. Verify health
curl https://$DOMAIN/health/detailed
```

---

## Environment Variables

All configuration is done via environment variables. Set these in the Railway dashboard:

### Required Variables

```bash
# Anthropic API (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Supabase (Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Inngest (Task Queue)
INNGEST_API_KEY=inngest_xxxxxxxxxxxxx

# Langfuse (Observability)
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxx

# Environment
ENVIRONMENT=production
PORT=8000
```

### Optional Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
PYTHONUNBUFFERED=1               # Force Python output buffering off

# Performance
MAX_WORKERS=4                     # Number of worker threads
REQUEST_TIMEOUT=30               # Request timeout in seconds
CACHE_TTL=3600                  # Cache time-to-live in seconds

# Feature Flags
FEATURE_CANARY=true             # Enable canary deployments
FEATURE_MONITORING=true         # Enable detailed monitoring
FEATURE_DEBUG_ENDPOINTS=false   # Enable /debug endpoints

# Database
DATABASE_URL=postgresql://user:pass@localhost/db  # Supabase provides this
DATABASE_POOL_SIZE=10            # Max connections

# External Services
REDIS_URL=redis://localhost:6379  # If using Redis
STRIPE_API_KEY=sk-xxxxx          # If using Stripe
```

### Managing Variables

```bash
# Set a variable
railway variables set KEY=value

# List all variables
railway variables list

# Delete a variable
railway variables delete KEY

# Update a variable
railway variables set KEY=new-value

# Export variables to .env file (for local use)
railway variables list --format=json > variables.json
```

### Security Best Practices

1. **Never commit secrets to git**:
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **Use Railway secrets, not .env**:
   - Set in Railway dashboard
   - Never checked into version control
   - Rotated easily without redeployment

3. **Rotate keys regularly**:
   ```bash
   # Regenerate API keys in respective services
   # Update in Railway dashboard
   # Monitor logs for errors during rotation
   ```

4. **Audit access**:
   - Review who has Railway access
   - Monitor environment variable changes
   - Enable Railway audit logs

---

## Troubleshooting

For detailed troubleshooting steps, see `docs/DEPLOYMENT_TROUBLESHOOTING.md`.

### Common Issues Quick Reference

| Issue | Command to Debug | Solution |
|-------|-----------------|----------|
| Health check fails | `railway logs --follow` | Check app logs, verify dependencies |
| Port binding error | `railway variables list` | Ensure PORT env var is read correctly |
| Database connection | `curl https://$DOMAIN/health/detailed` | Verify SUPABASE_URL, SUPABASE_KEY |
| API key errors | `railway logs \| grep -i "api"` | Check key format, expiration, permissions |
| Out of memory | `railway status` | Increase Railway plan, optimize code |
| Slow deployment | `railway deployment list` | Check Docker image size, dependencies |

### Getting Help

1. **Check Rails logs**:
   ```bash
   railway logs --follow
   ```

2. **Verify environment**:
   ```bash
   railway variables list
   ```

3. **Test endpoints**:
   ```bash
   curl https://$DOMAIN/health/detailed
   ```

4. **Review deployment history**:
   ```bash
   railway deployment list
   ```

5. **Contact support**:
   - Railway Support: https://railway.app/support
   - GitHub Issues: https://github.com/olga-ai-lab/88i-sinistro-harness/issues
   - Email: support@olga-ai-lab.com

---

## Next Steps

After successful deployment:

### 1. Set Up Custom Domain

```bash
# In Railway dashboard:
# 1. Go to project → service
# 2. Click "Domains"
# 3. Add custom domain
# 4. Configure DNS (CNAME record)
```

### 2. Configure SSL/TLS

Railway automatically provides Let's Encrypt certificates:
- Auto-renewal every 3 months
- HTTP redirects to HTTPS
- No additional configuration needed

### 3. Set Up Backups

```bash
# PostgreSQL/Supabase backups:
# 1. Enable in Supabase dashboard
# 2. Set retention policy (7/30/90 days)
# 3. Download backup schedule
```

### 4. Configure Monitoring Alerts

Set up alerts in Railway for:
- Deployment failures
- Health check failures
- High error rates
- Memory/CPU limits

### 5. Performance Tuning

```bash
# After a week of production:
# 1. Analyze response time distribution
# 2. Identify slow endpoints
# 3. Optimize hot paths
# 4. Consider caching strategies
# 5. Horizontal scaling if needed
```

### 6. Disaster Recovery Plan

```bash
# Create runbook for:
# 1. Complete service failure
# 2. Database corruption
# 3. DDoS attack
# 4. Security breach
# 5. Cascading failures
```

### 7. Documentation Updates

- [ ] Update team runbooks with production URLs
- [ ] Document on-call procedures
- [ ] Create incident response templates
- [ ] Record deployment videos for team
- [ ] Update API documentation with production endpoints

---

## Summary

This deployment guide covers:

✅ Local development with Docker  
✅ First-time Railway setup  
✅ Deployment and verification  
✅ CI/CD automation via GitHub Actions  
✅ Comprehensive health monitoring  
✅ Safe canary deployments  
✅ Rollback procedures  
✅ Environment variable management  
✅ Troubleshooting reference  
✅ Next steps for production readiness  

For detailed troubleshooting, see `docs/DEPLOYMENT_TROUBLESHOOTING.md`.

**Last Updated**: May 27, 2026  
**Status**: Production Ready  
**Maintained By**: DevOps Team  
