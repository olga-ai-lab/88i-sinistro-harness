# 88i Custom Tools Documentation

## Overview

Phase 2 introduces 10 custom tools (organized in 4 tool modules) that extend Hermes agent capabilities for sinistro (insurance claim) processing workflows:

1. **sinistro_tools** — Wraps Phase 1 skills (analyzer, fraude-detector) — 2 tools
2. **supabase_tool** — CRUD operations on sinistro database — 3 tools
3. **inngest_tool** — Async workflow triggers and cron scheduling — 2 tools
4. **langraph_tool** — Conversation state management — 3 tools

All tools follow the Hermes registry pattern, support JSON input/output schemas, and gracefully handle missing environment variables.

---

## Tools Reference

### 1. sinistro_extract_fields

**Module:** `tools._88i_sinistro_tools`

**Description:** Extract structured fields from a sinistro document using sinistro-analyzer skill. Parses document content to identify claim number, date, type, and other key attributes.

**Input Schema:**
```json
{
  "documento_tipo": "boletim_ocorrencia",
  "documento_texto": "Número BO: 12345\nData: 2026-05-27\nTipo: Roubo\n...",
  "sinistro_id": "sin_001"
}
```

**Output:**
```json
{
  "sucesso": true,
  "sinistro_id": "sin_001",
  "campos_extraidos": {
    "numero_bo": "12345",
    "data": "2026-05-27",
    "tipo": "roubo",
    "documento_tipo": "boletim_ocorrencia"
  },
  "confianca": 0.95,
  "skill_usado": "sinistro-analyzer"
}
```

**Error Response:**
```json
{
  "sucesso": false,
  "erro": "Document parsing failed",
  "sinistro_id": "sin_001"
}
```

---

### 2. sinistro_fraud_score

**Module:** `tools._88i_sinistro_tools`

**Description:** Score fraud risk for a sinistro using fraude-detector skill. Analyzes extracted fields and historical data to compute fraud probability (0-100).

**Input Schema:**
```json
{
  "sinistro_id": "sin_001",
  "segurado_id": "seg_001",
  "campos_extraidos": {
    "numero_bo": "12345",
    "valor_indenizacao": 5000,
    "tipo_sinistro": "roubo"
  }
}
```

**Output:**
```json
{
  "sucesso": true,
  "sinistro_id": "sin_001",
  "segurado_id": "seg_001",
  "score_fraude": 25,
  "risco_nivel": "baixo",
  "skill_usado": "fraude-detector"
}
```

**Risk Levels:**
- `baixo` — 0-30: Low fraud probability
- `medio` — 31-70: Medium fraud probability
- `alto` — 71-100: High fraud probability

---

### 3. supabase_read_sinistro

**Module:** `tools._88i_supabase_tool`

**Description:** Read a sinistro record from Supabase database. Returns complete sinistro data including status, fields, and audit trail.

**Input Schema:**
```json
{
  "sinistro_id": "sin_001"
}
```

**Output (Found):**
```json
{
  "sucesso": true,
  "sinistro": {
    "id": "sin_001",
    "segurado_id": "seg_001",
    "status": "triagem",
    "tipo": "roubo",
    "valor_indenizacao": 5000,
    "campos_extraidos": {...},
    "score_fraude": null,
    "data_registro": "2026-05-27T10:00:00Z"
  },
  "encontrado": true
}
```

**Output (Not Found):**
```json
{
  "sucesso": true,
  "encontrado": false,
  "sinistro_id": "sin_001"
}
```

**Required Environment:** `SUPABASE_URL`, `SUPABASE_KEY`

---

### 4. supabase_update_sinistro

**Module:** `tools._88i_supabase_tool`

**Description:** Update sinistro status or other fields in Supabase. Only provided fields are updated; partial updates are supported.

**Input Schema:**
```json
{
  "sinistro_id": "sin_001",
  "status": "analise_fraude",
  "score_fraude": 25,
  "campos_extraidos": {
    "numero_bo": "12345",
    "data": "2026-05-27"
  }
}
```

**Output:**
```json
{
  "sucesso": true,
  "sinistro_id": "sin_001",
  "novo_status": "analise_fraude",
  "campos_atualizados": ["status", "score_fraude", "campos_extraidos"]
}
```

**Supported Fields:**
- `status` — Current processing stage (triagem, extração, validação, fraude, decisão, reembolso)
- `score_fraude` — Fraud score (0-100)
- `campos_extraidos` — Extracted document fields (JSON object)
- `analise_cobertura` — Coverage analysis results (JSON object)
- `decisao` — Final decision (aprovado, reprovado, pendente)

**Required Environment:** `SUPABASE_URL`, `SUPABASE_KEY`

---

### 5. supabase_insert_sinistro

**Module:** `tools._88i_supabase_tool`

**Description:** Insert a new sinistro record into Supabase. Returns the newly created sinistro_id and initial status.

**Input Schema:**
```json
{
  "segurado_id": "seg_001",
  "tipo": "roubo",
  "campos_extraidos": {
    "numero_bo": "12345",
    "data": "2026-05-27"
  },
  "score_fraude": 0
}
```

**Output:**
```json
{
  "sucesso": true,
  "sinistro_id": "sin_new_001",
  "status_inicial": "triagem",
  "data_registro": "2026-05-27T10:00:00Z"
}
```

**Required Fields:**
- `segurado_id` — Policyholder ID
- `tipo` — Claim type (roubo, colisao, incendio, etc.)

**Optional Fields:**
- `campos_extraidos` — Pre-extracted document fields
- `score_fraude` — Initial fraud score (default: 0)
- `analise_cobertura` — Initial coverage analysis

**Required Environment:** `SUPABASE_URL`, `SUPABASE_KEY`

---

### 6. inngest_trigger_workflow

**Module:** `tools._88i_inngest_tool`

**Description:** Trigger an async workflow via Inngest. Enqueues a workflow event that runs asynchronously without blocking the agent conversation.

**Input Schema:**
```json
{
  "workflow": "process_sinistro",
  "sinistro_id": "sin_001",
  "etapa": "validacao"
}
```

**Output:**
```json
{
  "sucesso": true,
  "event_id": "event_sin_001_process_sinistro",
  "workflow": "process_sinistro",
  "status": "agendado"
}
```

**Supported Workflows:**
- `process_sinistro` — Full claim processing pipeline
- `validate_documents` — Document validation workflow
- `calculate_coverage` — Coverage calculation workflow
- `send_notification` — Notification delivery workflow

**Event Data Structure:**
```python
{
  "sinistro_id": "sin_001",
  "etapa": "validacao",
  "timestamp": "2026-05-27T10:00:00Z",
  "workflow_context": {...}
}
```

**Required Environment:** `INNGEST_KEY`

---

### 7. inngest_schedule_job

**Module:** `tools._88i_inngest_tool`

**Description:** Schedule a recurring cron job via Inngest. Jobs run at specified intervals without manual triggering.

**Input Schema:**
```json
{
  "job_name": "cleanup_pending",
  "schedule": "0 2 * * *"
}
```

**Output:**
```json
{
  "sucesso": true,
  "cron_id": "cron_cleanup_pending_0_2_*_*_*",
  "job_name": "cleanup_pending",
  "status": "agendado"
}
```

**Schedule Format:** Standard cron syntax (minute hour day month weekday)

**Example Schedules:**
- `0 2 * * *` — Daily at 2:00 AM
- `0 */6 * * *` — Every 6 hours
- `*/15 * * * *` — Every 15 minutes
- `0 0 * * 0` — Weekly on Sunday at midnight

**Common Jobs:**
- `cleanup_pending` — Archive old pending claims
- `generate_reports` — Daily claim reports
- `refresh_cache` — Cache refresh
- `audit_log_cleanup` — Audit trail maintenance

**Required Environment:** `INNGEST_KEY`

---

### 8. langraph_save_state

**Module:** `tools._88i_langraph_tool`

**Description:** Save conversation state for multi-turn sinistro workflows. Persists workflow context (extracted fields, fraud scores, decisions) across conversation turns.

**Input Schema:**
```json
{
  "conversation_id": "conv_001",
  "sinistro_id": "sin_001",
  "estado": {
    "etapa_atual": "validacao",
    "campos_extraidos": {
      "numero_bo": "12345",
      "data": "2026-05-27"
    },
    "score_fraude": 25
  }
}
```

**Output:**
```json
{
  "sucesso": true,
  "conversation_id": "conv_001",
  "sinistro_id": "sin_001",
  "estado_salvo": true
}
```

**State Structure:**
```python
{
  "etapa_atual": str,              # Current workflow stage
  "campos_extraidos": dict,        # Extracted document fields
  "score_fraude": int,             # Fraud score (0-100)
  "analise_cobertura": dict,       # Coverage analysis
  "decisao": str,                  # Final decision
  "historico": list,               # Workflow history
  "timestamp": str                 # Last update time
}
```

---

### 9. langraph_load_state

**Module:** `tools._88i_langraph_tool`

**Description:** Load conversation state for resuming multi-turn workflows. Retrieves saved state by conversation_id.

**Input Schema:**
```json
{
  "conversation_id": "conv_001"
}
```

**Output (Found):**
```json
{
  "sucesso": true,
  "conversation_id": "conv_001",
  "sinistro_id": "sin_001",
  "estado": {
    "etapa_atual": "validacao",
    "campos_extraidos": {...},
    "score_fraude": 25,
    "timestamp": "2026-05-27T10:05:00Z"
  },
  "encontrado": true
}
```

**Output (Not Found):**
```json
{
  "sucesso": true,
  "conversation_id": "conv_001",
  "encontrado": false
}
```

---

### 10. langraph_update_state

**Module:** `tools._88i_langraph_tool`

**Description:** Update conversation state by merging new values with existing state. Supports partial updates of nested objects.

**Input Schema:**
```json
{
  "conversation_id": "conv_001",
  "atualizacoes": {
    "etapa_atual": "fraude_scoring",
    "score_fraude": 35
  }
}
```

**Output:**
```json
{
  "sucesso": true,
  "conversation_id": "conv_001",
  "atualizacoes_aplicadas": ["etapa_atual", "score_fraude"],
  "novo_estado": {
    "etapa_atual": "fraude_scoring",
    "campos_extraidos": {...},
    "score_fraude": 35,
    "timestamp": "2026-05-27T10:10:00Z"
  }
}
```

---

## Usage Examples

### Example 1: Complete Sinistro Workflow

```python
# 1. Extract fields from document
campos = await sinistro_extract_fields(
    documento_tipo="boletim_ocorrencia",
    documento_texto="Número BO: 12345\nData: 2026-05-27\nTipo: Roubo",
    sinistro_id="sin_001"
)

# 2. Score fraud
fraude = await sinistro_fraud_score(
    sinistro_id="sin_001",
    segurado_id="seg_001",
    campos_extraidos=campos["campos_extraidos"]
)

# 3. Create sinistro record in database
sinistro = await supabase_insert_sinistro(
    segurado_id="seg_001",
    tipo="roubo",
    campos_extraidos=campos["campos_extraidos"],
    score_fraude=fraude["score_fraude"]
)

# 4. Update with fraud score
await supabase_update_sinistro(
    sinistro_id=sinistro["sinistro_id"],
    status="analise_fraude",
    score_fraude=fraude["score_fraude"],
    campos_extraidos=campos["campos_extraidos"]
)

# 5. Trigger async validation workflow
await inngest_trigger_workflow(
    workflow="process_sinistro",
    sinistro_id=sinistro["sinistro_id"],
    etapa="validacao"
)
```

### Example 2: State Management Across Turns

```python
# Turn 1: Save initial state
await langraph_save_state(
    conversation_id="conv_001",
    sinistro_id="sin_001",
    estado={
        "etapa_atual": "extração",
        "campos_extraidos": {
            "numero_bo": "12345",
            "data": "2026-05-27"
        }
    }
)

# Turn 2: Load state and resume
estado = await langraph_load_state(
    conversation_id="conv_001"
)

# Continue processing with loaded context
sinistro_data = await supabase_read_sinistro(
    sinistro_id=estado["sinistro_id"]
)

# Turn 3: Update state with fraud score
await langraph_update_state(
    conversation_id="conv_001",
    atualizacoes={
        "etapa_atual": "fraude_scoring",
        "score_fraude": 25
    }
)
```

### Example 3: Error Handling

```python
# Graceful handling of missing environment variables
result = await supabase_read_sinistro(sinistro_id="sin_001")
if not result["sucesso"]:
    print(f"Database error: {result['erro']}")
    # Fallback to in-memory state or queue retry
    return await langraph_load_state(conversation_id="conv_001")

# Handling missing sinistro
if not result["encontrado"]:
    # Create new record
    novo_sinistro = await supabase_insert_sinistro(
        segurado_id="seg_001",
        tipo="roubo"
    )
```

### Example 4: Async Background Processing

```python
# Process claim in background while agent responds to user
event = await inngest_trigger_workflow(
    workflow="process_sinistro",
    sinistro_id="sin_001",
    etapa="validacao"
)

# Schedule periodic cleanup job
cleanup = await inngest_schedule_job(
    job_name="cleanup_pending",
    schedule="0 2 * * *"  # Daily at 2 AM
)

# Agent can immediately respond while workflows run async
return "Sinistro enqueued for processing. Check status at any time."
```

---

## Environment Variables

All tools gracefully degrade if environment variables are not set (returning `sucesso: false`).

### Required Variables (for specific tools)

**Supabase Tools** (supabase_read_sinistro, supabase_update_sinistro, supabase_insert_sinistro):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

**Inngest Tools** (inngest_trigger_workflow, inngest_schedule_job):
```bash
INNGEST_KEY=your-inngest-key
```

**LangGraph Tools** (langraph_save_state, langraph_load_state, langraph_update_state):
- No environment variables required (uses in-memory store for Phase 2)
- Phase 3+ will migrate to Supabase-backed persistence

### Local Development (.env)

Create `.env` file in project root:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Inngest
INNGEST_KEY=your-inngest-key

# Optional: tool-specific flags
DEBUG_TOOLS=true
TOOLS_TIMEOUT=30
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Railway Deployment

Set variables in Railway Dashboard → Variables tab:

| Variable | Value | Source |
|----------|-------|--------|
| SUPABASE_URL | https://your-project.supabase.co | Supabase API Settings |
| SUPABASE_KEY | (anon key) | Supabase API Settings |
| INNGEST_KEY | (API key) | Inngest Dashboard |

**Security:** Never commit `.env` file. Use `.env.example` for documentation.

---

## Testing

### Unit Tests

Run individual tool tests:
```bash
# Sinistro tools
pytest tests/tools/test_88i_sinistro_tools.py -v

# Supabase tool
pytest tests/tools/test_88i_supabase_tool.py -v

# Inngest tool
pytest tests/tools/test_88i_inngest_tool.py -v

# LangGraph tool
pytest tests/tools/test_88i_langraph_tool.py -v
```

### Integration Tests

Run end-to-end workflow tests:
```bash
pytest tests/integration/test_88i_tools_e2e.py -v
```

### All Tests

```bash
pytest tests/tools/ tests/integration/ -v --tb=short
```

### Expected Results

```
tests/tools/test_88i_sinistro_tools.py::test_sinistro_tools_registered PASSED
tests/tools/test_88i_sinistro_tools.py::test_extract_fields_tool PASSED
tests/tools/test_88i_sinistro_tools.py::test_fraud_score_tool PASSED
tests/tools/test_88i_supabase_tool.py::test_supabase_tool_registered PASSED
tests/tools/test_88i_supabase_tool.py::test_read_sinistro PASSED
tests/tools/test_88i_supabase_tool.py::test_update_sinistro_status PASSED
tests/tools/test_88i_inngest_tool.py::test_inngest_tool_registered PASSED
tests/tools/test_88i_inngest_tool.py::test_trigger_workflow PASSED
tests/tools/test_88i_inngest_tool.py::test_schedule_job PASSED
tests/tools/test_88i_langraph_tool.py::test_langraph_tool_registered PASSED
tests/tools/test_88i_langraph_tool.py::test_save_state PASSED
tests/tools/test_88i_langraph_tool.py::test_load_update_state PASSED
tests/integration/test_88i_tools_e2e.py::test_complete_workflow PASSED
tests/integration/test_88i_tools_e2e.py::test_state_persistence PASSED

====== 14 passed in 1.23s ======
```

### Testing with Missing Environment Variables

Tools handle missing env vars gracefully:

```python
# Without SUPABASE_KEY set
result = await supabase_read_sinistro(sinistro_id="sin_001")
assert result["sucesso"] is False
assert "not available" in result["erro"]

# Tool continues to function, returning error responses
```

### Testing Tool Registration

```python
from tools.registry import registry

# Verify all 10 tools are registered
tools = registry.list_tools()
tool_names = [t.name for t in tools]

assert "sinistro_extract_fields" in tool_names
assert "sinistro_fraud_score" in tool_names
assert "supabase_read_sinistro" in tool_names
assert "supabase_update_sinistro" in tool_names
assert "supabase_insert_sinistro" in tool_names
assert "inngest_trigger_workflow" in tool_names
assert "inngest_schedule_job" in tool_names
assert "langraph_save_state" in tool_names
assert "langraph_load_state" in tool_names
assert "langraph_update_state" in tool_names
```

---

## Tool Discovery & Registration

All tools are auto-discovered via Hermes registry pattern:

```python
# tools/_88i_sinistro_tools.py, tools/_88i_supabase_tool.py, etc.
from tools.registry import registry

registry.register(
    name="sinistro_extract_fields",
    handler=extract_fields_handler,
    toolset="delegated_ai",
    availability_check=lambda: True,
    input_schema={...},
    description="Extract structured fields from a sinistro document"
)
```

**Discovery:**
1. Hermes imports tools/* modules at startup
2. Each tool module calls `registry.register()` at import time
3. `model_tools.discover_builtin_tools()` collects all registered tools
4. Tools available in agent's tool_calls and Hermes CLI

---

## Error Handling

All tools follow consistent error response format:

```json
{
  "sucesso": false,
  "erro": "Human-readable error message",
  "details": {...}
}
```

### Common Errors

| Error | Tool | Cause | Resolution |
|-------|------|-------|-----------|
| `Supabase client not available` | supabase_* | Missing SUPABASE_URL/KEY | Set env vars or use in-memory state |
| `Inngest client not available` | inngest_* | Missing INNGEST_KEY | Set env var or skip async processing |
| `sinistro_id is required` | Any | Missing required field | Check input schema |
| `No rows updated` | supabase_update_sinistro | Sinistro not found | Check sinistro_id exists |
| `No rows inserted` | supabase_insert_sinistro | Invalid data | Validate required fields |

---

## Performance Considerations

### Timeouts

- **Supabase operations:** 5s timeout (network calls)
- **Inngest workflows:** Immediate return (async processing)
- **LangGraph state:** <100ms (in-memory operations)

### Scalability

- All tools are async-ready (marked with `async def`)
- Supabase SDK handles connection pooling automatically
- Inngest handles job queue scalability
- LangGraph state uses in-memory store (Phase 2) — migrate to Supabase in Phase 3

### Caching

Phase 3 will introduce:
- Supabase query result caching
- State mutation batching
- Connection pool optimization

---

## Next Steps

### Phase 3: Plugins & Custom Context

- [ ] Supabase-backed state persistence for LangGraph tools
- [ ] Custom context engine with domain-specific knowledge
- [ ] Memory plugin integration (Mem0, Honcho)
- [ ] Langfuse monitoring integration

### Phase 4: Comprehensive Testing

- [ ] Full integration tests with real Supabase data
- [ ] End-to-end workflow tests (document upload → decision)
- [ ] Load testing (throughput, latency benchmarks)
- [ ] Security audit (SQL injection, auth mechanisms)

### Phase 5: Railway Deployment

- [ ] Docker containerization
- [ ] Railway CI/CD pipeline
- [ ] Health checks and canary deployment
- [ ] Monitoring dashboard (Langfuse + Railway metrics)

---

## Summary

The 88i custom tools layer provides:

✅ **Complete API Reference** — 10 tools with input/output schemas
✅ **Skill Integration** — Wraps Phase 1 skills (sinistro-analyzer, fraude-detector)
✅ **Database Abstraction** — Supabase CRUD operations
✅ **Async Workflows** — Inngest event-driven processing
✅ **State Management** — Multi-turn conversation persistence
✅ **Error Handling** — Graceful degradation with missing env vars
✅ **Testing** — Unit + integration test suite
✅ **Hermes Patterns** — Registry-based discovery, Pydantic schemas

Ready for Phase 3 context engines and Railway deployment.
