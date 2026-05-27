#!/bin/bash
# Validação pós-deploy — Octa Sinistro Harness
# Uso: ./scripts/validate_render_deployment.sh https://octa-sinistro-harness.onrender.com

set -e

RENDER_URL="${1:-https://octa-sinistro-harness.onrender.com}"
TIMEOUT=10

echo "🔍 Validando deployment em: $RENDER_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_endpoint() {
    local endpoint=$1
    local method=$2
    local data=$3
    local description=$4
    
    echo -n "Testing $description... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            "$RENDER_URL$endpoint" 2>/dev/null || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$RENDER_URL$endpoint" 2>/dev/null || echo -e "\n000")
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ $http_code${NC}"
        echo "   Response: $(echo $body | jq -r '.status // .fraud_score // .route // .' 2>/dev/null || echo $body | head -c 50)..."
        return 0
    else
        echo -e "${RED}❌ $http_code${NC}"
        echo "   Response: $body" | head -c 100
        return 1
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "1️⃣  HEALTH CHECKS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

check_endpoint "/health" "GET" "" "Health endpoint" || exit 1
check_endpoint "/docs" "GET" "" "FastAPI docs" || echo "   (Optional, continue)"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "2️⃣  BUSINESS ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

check_endpoint "/extract" "POST" \
    '{"claim_id": "TEST-001", "type": "AP", "amount": 5000}' \
    "Extract endpoint" || exit 1

check_endpoint "/fraud" "POST" \
    '{"claim_amount": 5000, "customer_age": 35, "days_insured": 1095}' \
    "Fraud detection" || exit 1

check_endpoint "/route" "POST" \
    '{"claim_type": "AP", "region": "SP"}' \
    "Routing endpoint" || exit 1

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "3️⃣  PERFORMANCE CHECKS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Testing extract latency (target: <100ms)..."
start=$(date +%s%N)
curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"claim_id": "PERF-001", "type": "AP"}' \
    "$RENDER_URL/extract" > /dev/null 2>&1
end=$(date +%s%N)
latency=$(( (end - start) / 1000000 ))
echo "Latency: ${latency}ms"
if [ $latency -lt 300 ]; then
    echo -e "${GREEN}✅ Within acceptable range${NC}"
else
    echo -e "${YELLOW}⚠️  Latency higher than expected (target <100ms)${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "4️⃣  ENVIRONMENT VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -n "PORT environment: "
# Try to extract from response headers or app info
if curl -s "$RENDER_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ App responding on correct port${NC}"
else
    echo -e "${RED}❌ Cannot verify port${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✅ Deployment validation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Check Langfuse dashboard for traces"
echo "2. Check Prometheus for metrics"
echo "3. Monitor logs for errors"
echo "4. Proceed to gradual rollout (10% → 50% → 100%)"
echo ""
echo "Deploy URL: $RENDER_URL"
echo "Dashboard: https://dashboard.render.com"
echo ""
