# Runbook — 88i Sinistro Harness

## Deploy Railway (produção)

```bash
# 1. Criar projeto no Railway
railway init
railway link

# 2. Configurar variáveis de ambiente
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set SUPABASE_URL=https://xxx.supabase.co
railway variables set SUPABASE_SERVICE_KEY=eyJ...
railway variables set INNGEST_SIGNING_KEY=...
railway variables set LANGFUSE_PUBLIC_KEY=pk-lf-...
railway variables set LANGFUSE_SECRET_KEY=sk-lf-...
railway variables set SHADOW_MODE=shadow

# 3. Deploy
railway up
```

---

## Migrations Supabase

```bash
supabase login
supabase link --project-ref <project-id>
supabase db push
```

Ou manualmente no painel SQL do Supabase:
`supabase/migrations/001_sinistros.sql`

---

## Deploy Edge Function

```bash
supabase functions deploy sinistro-webhook
supabase secrets set INNGEST_EVENT_KEY=...
```

---

## Procedimento de Cutover (CloudWalk)

### Pré-condições (checar antes de mudar para cutover)

- [ ] FastAPI healthcheck respondendo: `GET /health` → 200
- [ ] Supabase conectado: `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` configurados
- [ ] Langfuse configurado: traces aparecendo no dashboard
- [ ] Shadow mode com >= 100 sinistros e concordância >= 95%: `GET /shadow/relatorio`
- [ ] Eval dataset passando quality gate: `python eval_runner.py --dry-run`
- [ ] Migrations aplicadas: tabelas `sinistros`, `hitl_tarefas`, `raw_inbox` existem
- [ ] HITL fila funcional: `GET /hitl/fila` retorna 200
- [ ] Test suite verde: todos os testes passando

### Passo a passo

```bash
# 1. Verificar relatório shadow
curl https://seu-agente.railway.app/shadow/relatorio

# 2. Ativar canary 10%
railway variables set SHADOW_MODE=canary CANARY_PERCENT=10
railway redeploy

# 3. Monitorar por 24h
# Acompanhar /shadow/relatorio e Langfuse

# 4. Aumentar canary 50%
railway variables set CANARY_PERCENT=50
railway redeploy

# 5. Monitorar por 24h

# 6. Cutover completo
railway variables set SHADOW_MODE=cutover
railway redeploy

# 7. Desativar OCTA n8n
```

### Rollback de emergência

```bash
railway variables set SHADOW_MODE=shadow
railway redeploy
```

O OCTA volta a receber 100% dos sinistros imediatamente.

---

## Monitoramento

### Métricas principais

| Métrica | Onde ver | Alerta se |
|---|---|---|
| Taxa de concordância shadow | `GET /shadow/relatorio` | < 95% |
| Score eval | `python eval_runner.py` | < 80% |
| Sinistros na fila HITL | `GET /hitl/fila` | > 50 pendentes |
| Traces Langfuse | dashboard.langfuse.com | erros aumentando |
| Latência p95 | Railway metrics | > 30s |

### Alertas críticos

- `fraud_escalation` na fila HITL → Rosi precisa agir em até 4h
- `divergencias_criticas` no shadow > 5% → pausar canary, investigar
- `confianca < 0.3` frequente → revisar prompt BAML

---

## Adicionando nova plataforma

1. Adicionar enum em `baml_src/sinistro.baml` (enum `Plataforma`)
2. Rodar `baml-cli generate`
3. Adicionar linhas em `dmn_tables.py` (`TIPO_SINISTRO_COBERTURA`)
4. Determinar regime: `PLATAFORMAS_UBER` ou `PLATAFORMAS_PADRAO` em `dmn_tables.py`
5. Adicionar casos de teste em `test_semana3.py`
6. Adicionar casos ao `eval_dataset.json`
7. Rodar regressão completa

---

## Adicionando novo produto/cobertura

1. Atualizar skill `olga-analista-seguros-88i` com as regras do produto
2. Adicionar linhas em `dmn_tables.py`:
   - `TIPO_SINISTRO_COBERTURA` — mapeamento tipo → cobertura
   - `DOCS_POR_COBERTURA` — documentos obrigatórios
   - `PARAMETROS_COBERTURA` — cooldowns, franquias
3. Adicionar regras em `REGRAS_D` se necessário
4. Atualizar `rules_engine.py` se a lógica for diferente
5. Testar

---

## Debugging

### Sinistro foi para a rota errada

Checar o `log_execucao` no state:
```python
resultado = processar_narrativa(narrativa)
for linha in resultado["log_execucao"]:
    print(linha)
```

Perguntas antes de mexer no código (do CLAUDE.md):
1. A expectativa estava errada?
2. A definição estava ambígua (prompt)?
3. A lógica de fluxo (código) estava errada?

### BAML não regenerou

```bash
baml-cli generate
# Confirmar que baml_client/inlinedbaml.py foi atualizado
```

### Taxa de concordância shadow baixando

1. Ver `GET /shadow/relatorio` — qual campo diverge mais?
2. Ver traces no Langfuse — qual narrativa causou?
3. Checar se foi mudança no BAML (schema mudou → cliente desatualizado?)
4. Rodar `python eval_runner.py --verbose` para identificar padrão
