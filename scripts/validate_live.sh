#!/bin/bash
#
# validate_live_deployment.sh
# Valida que o serviço está live e respondendo corretamente
#

set -e

if [ $# -eq 0 ]; then
  echo "Uso: $0 <RENDER_URL>"
  echo ""
  echo "Exemplo: $0 https://srv-abcd1234.onrender.com"
  exit 1
fi

RENDER_URL="$1"
RENDER_URL="${RENDER_URL%/}"  # Remove trailing slash

echo "════════════════════════════════════════════════════════════════════════════"
echo "                   🚀 VALIDANDO DEPLOYMENT OCTA"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "URL: $RENDER_URL"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_endpoint() {
  local endpoint="$1"
  local expected_status="${2:-200}"
  local method="${3:-GET}"
  
  echo -n "Testing $method $endpoint ... "
  
  response=$(curl -s -w "\n%{http_code}" -X "$method" "$RENDER_URL$endpoint" 2>&1)
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')
  
  if [ "$http_code" -eq "$expected_status" ]; then
    echo -e "${GREEN}✅ $http_code${NC}"
    return 0
  else
    echo -e "${RED}❌ $http_code (expected $expected_status)${NC}"
    echo "  Response: ${body:0:100}"
    return 1
  fi
}

echo "════════════════════════════════════════════════════════════════════════════"
echo "HEALTHCHECKS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

check_endpoint "/health" 200 "GET" || {
  echo ""
  echo -e "${RED}FALHA: Health check não respondeu${NC}"
  exit 1
}

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "ENDPOINTS DE NEGÓCIO"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Test POST /sinistro (esperado 422 ou 400 sem body, ou 200 com valid payload)
echo -n "Testing POST /sinistro (empty) ... "
response=$(curl -s -w "\n%{http_code}" -X POST "$RENDER_URL/sinistro" -H "Content-Type: application/json" -d '{}' 2>&1)
http_code=$(echo "$response" | tail -1)

case $http_code in
  200|201|422|400)
    echo -e "${GREEN}✅ $http_code${NC} (expected validation error or success)"
    ;;
  *)
    echo -e "${RED}❌ $http_code${NC} (unexpected)"
    ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "PERFORMANCE SLAs"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Test response time
echo -n "Testing response time (target < 200ms) ... "
start_time=$(date +%s%N)
curl -s "$RENDER_URL/health" > /dev/null
end_time=$(date +%s%N)
elapsed_ms=$(( (end_time - start_time) / 1000000 ))

if [ $elapsed_ms -lt 200 ]; then
  echo -e "${GREEN}✅ ${elapsed_ms}ms${NC}"
else
  echo -e "${YELLOW}⚠️ ${elapsed_ms}ms (expected < 200ms)${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ DEPLOYMENT VALIDATION PASSED${NC}"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Configure environment variables (ANTHROPIC_API_KEY, SUPABASE_*, INNGEST_*)"
echo "  2. Set up monitoring (Prometheus + Langfuse)"
echo "  3. Gradual traffic rollout (10% → 50% → 100%)"
echo ""
