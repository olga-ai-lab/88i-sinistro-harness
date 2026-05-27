#!/usr/bin/env bash
set -euo pipefail

HERMES_REPO_URL="${HERMES_REPO_URL:-https://github.com/NousResearch/hermes-agent}"
TARGET_DIR="${1:-third_party/hermes-agent}"

if [ -d "$TARGET_DIR/.git" ]; then
  echo "[INFO] Hermes já existe em $TARGET_DIR"
else
  echo "[INFO] Clonando Hermes de $HERMES_REPO_URL em $TARGET_DIR"
  git clone "$HERMES_REPO_URL" "$TARGET_DIR"
fi

mkdir -p "$TARGET_DIR/olga"
cp -f docs/olga/system_prompt.md "$TARGET_DIR/olga/system_prompt.md"
cp -f docs/olga/output_schema.json "$TARGET_DIR/olga/output_schema.json"
cp -f docs/olga/http_contracts.md "$TARGET_DIR/olga/http_contracts.md"

cat > "$TARGET_DIR/olga/README.md" <<'MD'
# Olga overlay

Arquivos iniciais para transformar o runtime Hermes em agente Olga:

- `system_prompt.md`
- `output_schema.json`
- `http_contracts.md`

Próximos passos:
1. Plugar prompt e schema no entrypoint/config de agente do Hermes.
2. Implementar tools HTTP para `/health`, `/sinistro`, `/sinistro/{protocolo}/documentos`.
3. Rodar smoke tests de integração.
MD

echo "[OK] Overlay Olga copiado para $TARGET_DIR/olga"
