#!/bin/bash
#
# test_octa_health.sh
# Aguarda e valida que o serviço Octa está healthy no Render
#

SERVICE_URL="https://srv-d8bo09cp3tds73als7u0.onrender.com"
MAX_ATTEMPTS=20
SLEEP_INTERVAL=15

echo "════════════════════════════════════════════════════════════════════════════"
echo "                    🚀 TESTANDO OCTA NO RENDER"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Service: $SERVICE_URL"
echo "Max tentativas: $MAX_ATTEMPTS x ${SLEEP_INTERVAL}s = $(( MAX_ATTEMPTS * SLEEP_INTERVAL ))s"
echo ""

for attempt in $(seq 1 $MAX_ATTEMPTS); do
  echo -n "[$attempt/$MAX_ATTEMPTS] Testando /health... "
  
  response=$(curl -s -w "\n%{http_code}" "$SERVICE_URL/health" 2>&1)
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')
  
  case $http_code in
    200)
      echo "✅ OK (200)"
      echo ""
      echo "Resposta:"
      echo "$body" | jq . 2>/dev/null || echo "$body"
      echo ""
      echo "════════════════════════════════════════════════════════════════════════════"
      echo "✅ HEALTH CHECK PASSOU!"
      echo "════════════════════════════════════════════════════════════════════════════"
      exit 0
      ;;
    404)
      echo "404 (app ainda iniciando ou não responde...)"
      ;;
    500|502|503)
      echo "$http_code (servidor erro - pode estar recovering)"
      ;;
    *)
      echo "$http_code (inesperado)"
      ;;
  esac
  
  if [ $attempt -lt $MAX_ATTEMPTS ]; then
    echo "  Aguardando ${SLEEP_INTERVAL}s antes da próxima tentativa..."
    sleep $SLEEP_INTERVAL
  fi
done

echo ""
echo "❌ FALHA: Não conseguiu conectar após $(( MAX_ATTEMPTS * SLEEP_INTERVAL ))s"
echo ""
echo "Próximos passos:"
echo "  1. Verificar logs do Render:"
echo "     https://dashboard.render.com/srv-d8bo09cp3tds73als7u0"
echo "  2. Procurar por errors como:"
echo "     - ModuleNotFoundError"
echo "     - ImportError"
echo "     - SyntaxError"
echo "  3. Se vir algum erro, compartilhar comigo!"
exit 1
