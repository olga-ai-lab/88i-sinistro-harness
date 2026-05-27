# Phase 3: Context Engine + Plugin System Architecture

**Version:** 1.0.0  
**Date:** May 27, 2026  
**Status:** Active Development  
**Authors:** 88i Sinistro Development Team  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Context Engine Design](#context-engine-design)
4. [Plugin System Design](#plugin-system-design)
5. [Integration Points](#integration-points)
6. [Storage Architecture](#storage-architecture)
7. [Monitoring & Observability](#monitoring--observability)
8. [Deployment Configuration](#deployment-configuration)
9. [Security Considerations](#security-considerations)
10. [Future Roadmap](#future-roadmap)

---

## Overview

Phase 3 introduces two major systems to enhance the 88i sinistro harness with domain-specific knowledge injection and dynamic extensibility:

### Context Engine
A knowledge injection framework that automatically enriches LLM prompts with domain-specific rules, policies, and reference data without requiring prompt engineering for every scenario.

### Plugin System
A dynamic registration and management system enabling developers to extend agent capabilities with custom tools, skills, and context providers at runtime.

**Key Metrics:**
- 1,500+ lines of implementation code
- 20+ test cases covering all scenarios
- Support for 3 plugin types (tools, skills, context)
- Langfuse integration for observability
- Supabase-backed persistent storage

---

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                            │
│             (Query / Sinistro Request)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │   Plugin Loader System    │
         │  (Discovery + Loading)    │
         └───────────┬───────────────┘
                     │
         ┌───────────┴──────────────────┐
         │                              │
         ▼                              ▼
   ┌──────────────┐            ┌──────────────┐
   │   Context    │            │   Dynamic    │
   │   Engine     │            │   Tools/     │
   │ (Domain      │            │   Skills     │
   │  Knowledge)  │            │   Registry   │
   └──────┬───────┘            └──────┬───────┘
          │                           │
          └───────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Enriched Prompt with      │
        │   Context + Tools           │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   LLM Agent Execution       │
        │   (with Tool Calling)       │
        └─────────────┬───────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
  ┌──────────────┐        ┌──────────────┐
  │  Langfuse    │        │  Supabase    │
  │  Tracing &   │        │  Persistent  │
  │  Monitoring  │        │  Storage     │
  └──────────────┘        └──────────────┘
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │    Final Response +          │
        │    Telemetry                 │
        └─────────────────────────────┘
```

### Component Interaction Flow

**Initialization Phase:**
1. System starts, loads configuration from `.env` and config files
2. Plugin Loader discovers plugins in `plugins/enabled/` directory
3. Context Engine registers domain-specific context providers
4. Storage backends (Supabase/Redis/InMemory) are initialized
5. Langfuse monitoring client is configured

**Execution Phase:**
1. User sends query/sinistro request
2. Plugin system loads applicable tools and skills
3. Context Engine injects domain knowledge based on request metadata
4. Enhanced prompt is sent to LLM with full tool schemas
5. Tool calls are executed and traced
6. Results are cached in storage for future reference
7. Final response is returned with metadata

---

## Context Engine Design

### Core Components

#### 1. ContextProvider Base Class

```python
class ContextProvider(ABC):
    """Abstract base for context providers."""
    
    @abstractmethod
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Get context data for prompt injection."""
        pass
```

All context providers extend this interface to provide domain-specific knowledge.

#### 2. ContextEngine Class

**Responsibilities:**
- Register and manage context providers
- Inject context into prompts
- Cache context for performance
- Coordinate between multiple providers

**Key Methods:**
```python
async def inject_context(
    prompt: str,
    providers: List[str],
    context_data: Dict[str, Any] = None,
    cache_key: Optional[str] = None
) -> str:
    """Inject context from registered providers into prompt."""
```

### Domain-Specific Context Providers

#### Insurance Context Provider (`insurance_context.py`)

Provides domain knowledge for insurance claim processing:

**Coverage Types Supported:**
- Roubo (Theft)
- Colisão (Collision)
- Incêndio (Fire)
- Alagamento (Flooding)
- Furto (Burglary)

**Vehicle Types Covered:**
- Moto (Motorcycle)
- Carro (Car)
- Caminhão (Truck)

**Context Injected:**
- Business rules per claim type
- Standard coverage levels
- Deductible percentages
- Required documentation
- Processing SLA
- Workflow stages

**Example Context Output:**
```json
{
  "sistema": "88i Seguradora Digital",
  "versao": "1.0.0",
  "sinistro_info": {
    "regras": [
      "Requer Boletim de Ocorrência (BO)",
      "Valor máximo indenização: R$ 50.000",
      "Prazo de análise: 10 dias úteis",
      "Documentos obrigatórios: BO, RG, CPF, comprovante endereço"
    ],
    "cobertura_padrao": "Roubo Total + Parcial",
    "franquia": "10%"
  },
  "workflow": {
    "etapas": [
      "triagem", "extração", "validação", "fraude_scoring",
      "análise_cobertura", "decisão", "reembolso"
    ],
    "sla_dias": 10
  }
}
```

### Context Caching Strategy

**Caching Layers:**
1. **In-Memory Cache** - Fast access for recent contexts
2. **Storage Backend Cache** - Persistent, queryable storage
3. **TTL Management** - Automatic expiration (default: 24 hours)

**Cache Key Format:**
```
context:{provider_name}:{sinistro_id}:{cache_version}
```

**Cache Hit Examples:**
- Same claim type + vehicle type = reuse context
- Similar policy holder profile = reuse rules
- Same claim date = reuse time-sensitive rules

---

## Plugin System Design

### Plugin Architecture

#### Plugin Type Hierarchy

```
Plugin (Abstract Base)
├── ToolPlugin
│   └── Tools that can be called by LLM
│   └── Example: ReembolsoToolPlugin
│
├── SkillPlugin
│   └── Skills triggered by text patterns
│   └── Example: NotificacaoSkillPlugin
│
└── ContextPlugin
    └── Context providers
    └── Example: ComercialContextPlugin
```

### Plugin Lifecycle

```
Discovery → Load → Register → Initialize → Ready → Execute → Teardown
```

**Phases:**

1. **Discovery** (PluginLoader.discover_plugins)
   - Scans `plugins/enabled/` directory
   - Identifies plugin type from filename convention
   - Returns plugin manifest

2. **Load** (PluginLoader._load_plugin)
   - Dynamically imports plugin module
   - Instantiates plugin class
   - Validates plugin interface

3. **Register** (PluginLoader.register_*_plugin)
   - Registers in appropriate registry
   - Updates global plugin mapping
   - Logs registration event

4. **Initialize** (Plugin.initialize)
   - Plugin sets up resources
   - Establishes database connections
   - Loads configuration

5. **Ready** 
   - Plugin available for execution
   - Advertised in tool schemas
   - Callable by LLM

6. **Execute** (Plugin.execute)
   - Plugin logic runs
   - Traced with Langfuse
   - Results cached

7. **Teardown** (on shutdown)
   - Resources cleaned up
   - Connections closed
   - State persisted

### Plugin Discovery Convention

**Filename Patterns:**
```
plugins/enabled/tool_*.py     → ToolPlugin
plugins/enabled/skill_*.py    → SkillPlugin
plugins/enabled/context_*.py  → ContextPlugin
plugins/enabled/example_*.py  → Examples (skipped)
```

**Plugin Detection Example:**
```
tool_reembolso.py
  ↓
Module discovered as tool type
  ↓
Imported as plugins.enabled.tool_reembolso
  ↓
Scans for ToolPlugin subclass
  ↓
Instantiates and registers
```

### Plugin Metadata

Each plugin declares metadata:

```python
@dataclass
class PluginMetadata:
    name: str                    # Unique identifier
    version: str                 # Semantic versioning
    author: str = "88i"          # Plugin author
    description: str = ""        # Human-readable description
    dependencies: list = None    # Required packages/plugins
    enabled: bool = True         # Enable/disable toggle
```

### Tool Plugins in Detail

**Interface:**
```python
class ToolPlugin(Plugin):
    tool_name: str              # Name in agent's tool registry
    tool_schema: Dict = {}      # OpenAI-compatible schema
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic."""
        pass
```

**Example Tool Plugin:**
```python
class ReembolsoToolPlugin(ToolPlugin):
    name = "reembolso_tool"
    version = "1.0.0"
    tool_name = "reembolso_process"
    
    async def execute(
        self,
        sinistro_id: str,
        valor_indenizacao: float,
        metodo_pagamento: str = "transferencia"
    ) -> Dict[str, Any]:
        return {
            "sucesso": True,
            "sinistro_id": sinistro_id,
            "valor_processado": valor_indenizacao,
            "metodo_pagamento": metodo_pagamento,
            "status": "processando"
        }
```

### Skill Plugins in Detail

**Interface:**
```python
class SkillPlugin(Plugin):
    skill_name: str          # Name in agent's skill registry
    skill_triggers: list     # Text patterns that trigger skill
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute skill logic."""
        pass
```

**Trigger Matching:**
Text patterns are matched against user input to auto-invoke skills:
```python
skill_triggers = ["notificar", "enviar mensagem", "comunicar"]
# Matches: "Please notify the customer"
# Matches: "Send a message to policyholder"
# Matches: "Communicate with segurado"
```

### Context Plugins in Detail

**Interface:**
```python
class ContextPlugin(Plugin):
    context_provider_name: str    # Name in context engine
    
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Get context data."""
        pass
```

**Example Context Plugin:**
```python
class ComercialContextPlugin(ContextPlugin):
    name = "comercial_context"
    context_provider_name = "comercial_rules"
    
    async def get_context(self, segurado_tipo: str = None) -> Dict:
        return {
            "comercial": {
                "desconto_fidelidade": 0.15,
                "bonus_multiplas_apolices": 0.10,
                "taxa_administrativo": 50.00,
                "margem_lucro": 0.25
            }
        }
```

---

## Integration Points

### 1. AIAgent Integration

**Plugin Loading:**
```python
# In agent initialization
loader = PluginLoader(plugins_dir="plugins/enabled")
plugins = await loader.load_plugins()

# Tools are automatically registered in agent's toolset
agent.enable_tools(loader.get_plugins("tool"))
```

**Context Injection:**
```python
# Before each prompt
context = await engine.inject_context(
    prompt=user_message,
    providers=["insurance", "comercial"],
    context_data={"sinistro_id": sinistro_id}
)

# Enhanced prompt is sent to LLM
response = await agent.chat(context)
```

### 2. Tool Calling Loop

```
User Input
    ↓
Plugin/Context Injection
    ↓
Tool Schemas (from Plugins)
    ↓
LLM Response with Tool Calls
    ↓
Plugin Tool Execution
    ↓
Result Caching
    ↓
Tool Result Message to LLM
    ↓
(Loop or Final Response)
```

### 3. Skill Triggering

```
User Input
    ↓
Skill Trigger Pattern Matching
    ↓
Auto-invoke Applicable Skill Plugins
    ↓
Skill Execution
    ↓
Inject Results into Prompt
    ↓
Continue with Tool Calling
```

---

## Storage Architecture

### Storage Backend Selection

**Environment Variable:** `CONTEXT_STORAGE`

**Options:**

1. **InMemory** (Default for Phase 3)
   - Fast, no external dependencies
   - Lost on restart
   - Good for development/testing
   - Configuration: `CONTEXT_STORAGE=memory`

2. **Supabase** (Recommended for Production)
   - Persistent, distributed
   - Full-text search support
   - Row-level security
   - Configuration: `CONTEXT_STORAGE=supabase`
   - Requires: `SUPABASE_URL`, `SUPABASE_KEY`

3. **Redis** (Optional, for caching)
   - Sub-millisecond latency
   - Cluster support
   - Configuration: `CONTEXT_STORAGE=redis`
   - Requires: `REDIS_URL`, `REDIS_PASSWORD`

### Context Cache Table Schema (Supabase)

```sql
CREATE TABLE context_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    conversation_id VARCHAR(255) NOT NULL,
    sinistro_id VARCHAR(255),
    context_data JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    ttl_hours INT DEFAULT 24,
    expires_at TIMESTAMP GENERATED ALWAYS AS 
        (created_at + INTERVAL '1 hour' * ttl_hours) STORED
);

CREATE INDEX idx_conversation_id ON context_cache(conversation_id);
CREATE INDEX idx_sinistro_id ON context_cache(sinistro_id);
CREATE INDEX idx_cache_key ON context_cache(cache_key);
CREATE INDEX idx_expires_at ON context_cache(expires_at);
```

### Storage Interface

All backends implement:

```python
class ContextStorage(ABC):
    async def save(self, key: str, data: Dict[str, Any]) -> bool
    async def load(self, key: str) -> Optional[Dict[str, Any]]
    async def delete(self, key: str) -> bool
```

### TTL & Expiration

- **Default TTL:** 24 hours
- **Configurable via:** `CONTEXT_CACHE_TTL_HOURS`
- **Auto-cleanup:** Database triggers/cron jobs
- **Query optimization:** Indexes on `expires_at` for efficient cleanup

---

## Monitoring & Observability

### Langfuse Integration

**Purpose:** Distributed tracing for all agent operations

**Components:**

1. **LangfuseMonitor** - Central monitoring hub
   ```python
   monitor = LangfuseMonitor(
       public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
       secret_key=os.getenv("LANGFUSE_SECRET_KEY")
   )
   ```

2. **Span Creation** - Track individual operations
   ```python
   span = await monitor.create_span(
       name="extract_fields",
       input={"documento": "..."},
       metadata={"sinistro_id": "sin_001"}
   )
   ```

3. **Execution Tracing** - Log operation metrics
   ```python
   await monitor.trace_execution(
       operation_name="process_claim",
       input_data={...},
       output_data={...},
       duration_ms=1234
   )
   ```

4. **Cost Tracking** - Monitor token usage & spend
   ```python
   await monitor.log_cost(
       operation="claim_analysis",
       model="gpt-4",
       input_tokens=500,
       output_tokens=300,
       cost_usd=0.0234
   )
   ```

### Tracing Decorators

**Tool Execution:**
```python
@trace_tool_execution("reembolso_process")
async def execute(self, sinistro_id: str, valor: float):
    # Automatically traced with timing, errors logged
    pass
```

**Skill Execution:**
```python
@trace_skill_execution("notificar_segurado")
async def execute(self, segurado_id: str, canal: str):
    # Automatically traced with timing, errors logged
    pass
```

### Metrics Collected

- **Execution Time** - Per operation, per tool, per skill
- **Token Usage** - Input + output per LLM call
- **Cost** - Per operation, aggregated per day/week
- **Error Rate** - By plugin type and operation
- **Cache Hit Rate** - Context reuse efficiency
- **Plugin Performance** - Tool/skill execution stats

### Dashboard Integration

Langfuse provides built-in dashboards showing:
- Agent conversation flow
- Tool execution timeline
- Cost breakdown
- Error analysis
- Latency distribution
- Cache effectiveness

---

## Deployment Configuration

### Environment Variables

**Core Phase 3 Configuration:**
```bash
# Context Engine
CONTEXT_STORAGE=supabase              # memory|supabase|redis
CONTEXT_CACHE_TTL_HOURS=24
CONTEXT_MAX_CACHE_SIZE=1000

# Plugin System
PLUGINS_ENABLED_DIR=plugins/enabled
PLUGINS_AUTO_DISCOVERY=true
PLUGINS_AUTO_LOAD=true

# Langfuse Monitoring
LANGFUSE_PUBLIC_KEY=pk_xxxxxxxxxx
LANGFUSE_SECRET_KEY=sk_xxxxxxxxxx
LANGFUSE_ENABLED=true

# Storage Backends
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxxxxxxxxx
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_password

# Feature Flags
FEATURE_CONTEXT_INJECTION=true
FEATURE_PLUGIN_AUTO_LOAD=true
FEATURE_DISTRIBUTED_TRACING=true
```

### Docker Compose Configuration

```yaml
services:
  agent:
    image: 88i-sinistro:latest
    environment:
      CONTEXT_STORAGE: supabase
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_KEY: ${SUPABASE_KEY}
    volumes:
      - ./plugins/enabled:/app/plugins/enabled
      - ./migrations:/app/migrations
    depends_on:
      - supabase
      
  supabase:
    image: supabase/supabase:latest
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

### Railway Deployment

Set these config variables in Railway dashboard:
- `CONTEXT_STORAGE=supabase`
- `LANGFUSE_PUBLIC_KEY=...`
- `LANGFUSE_SECRET_KEY=...`
- `SUPABASE_URL=...`
- `SUPABASE_KEY=...`

---

## Security Considerations

### Data Protection

1. **Context Data Sensitivity**
   - Context cache may contain PII (policyholder info)
   - Implement row-level security (RLS) in Supabase
   - Use environment variables for secrets (never commit keys)

2. **Plugin Validation**
   - All plugins must pass security review
   - Verify module signatures before loading
   - Sandbox plugin execution where possible

3. **Tool Permissions**
   - Tools can access sensitive data (claims, payments)
   - Implement fine-grained authorization
   - Log all tool executions for audit

### Access Control

**Supabase RLS Policies:**
```sql
-- Only authenticated users can read
CREATE POLICY "read_context" ON context_cache
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only users own sinistro can modify
CREATE POLICY "write_own_context" ON context_cache
    FOR UPDATE USING (conversation_id = auth.user_id());
```

### Secrets Management

**Never commit to repository:**
- API keys (Langfuse, Supabase, OpenAI)
- Database credentials
- Bearer tokens

**Use `.env` file (not in git):**
```bash
LANGFUSE_SECRET_KEY=sk_xxxxxxxxxx
SUPABASE_KEY=eyJxxxxxxxxxx
```

### Audit Logging

All operations logged for compliance:
- Plugin loading
- Context injection
- Tool execution
- Data access patterns

---

## Future Roadmap

### Phase 3.1: Enhanced Context Providers
- Medical context provider (claim types specific to health)
- Regulatory context provider (SUSEP rules, compliance)
- Competitive intelligence provider (market rates)

### Phase 3.2: Advanced Plugin Features
- Plugin dependency resolution
- Version management & rollback
- Hot reload without restart
- Plugin marketplace/registry

### Phase 3.3: Performance Optimization
- Redis clustering for distributed caching
- Context quantization for LLM efficiency
- Plugin lazy loading
- Async plugin initialization

### Phase 3.4: Enterprise Features
- Multi-tenant plugin isolation
- Custom storage backend adapters
- Advanced RBAC for plugins
- Plugin versioning & A/B testing

### Phase 4: Integration
- Plugin ecosystem marketplace
- Community plugin repository
- Standardized plugin SDK
- CLI for plugin scaffolding & testing

---

## Quick Start

### 1. Enable Context Engine

```python
from context_engine.base import ContextEngine
from context_engine.insurance_context import InsuranceContextProvider

engine = ContextEngine()
provider = InsuranceContextProvider()
engine.register_provider("insurance", provider)

enriched_prompt = await engine.inject_context(
    prompt="Analyze this claim",
    providers=["insurance"],
    context_data={"sinistro_tipo": "roubo"}
)
```

### 2. Load Plugins

```python
from plugins.plugin_loader import PluginLoader

loader = PluginLoader(plugins_dir="plugins/enabled")
plugins = await loader.load_plugins()

# Use plugins
tool_plugins = loader.get_plugins("tool")
skill_plugins = loader.get_plugins("skill")
```

### 3. Enable Monitoring

```python
from monitoring.langfuse_integration import LangfuseMonitor

monitor = LangfuseMonitor()

await monitor.trace_execution(
    operation_name="process_claim",
    input_data={"sinistro_id": "sin_001"},
    output_data={"status": "approved"},
    duration_ms=1234
)
```

---

## Troubleshooting

### Context Engine Not Injecting Context

**Check:**
- Provider is registered: `engine.providers.keys()`
- Provider returns non-empty dict
- Cache keys don't conflict

**Debug:**
```python
context = await provider.get_context(sinistro_tipo="roubo")
print(f"Context: {context}")  # Should not be empty
```

### Plugins Not Loading

**Check:**
- Files in `plugins/enabled/` follow naming convention
- No syntax errors in plugin code
- Plugin class extends appropriate base class

**Debug:**
```python
discovered = await loader.discover_plugins()
print(f"Discovered: {discovered}")
```

### Langfuse Not Recording

**Check:**
- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` set
- Network connectivity to Langfuse API
- Monitor is initialized before use

**Debug:**
```python
monitor = LangfuseMonitor()
print(f"Enabled: {monitor.enabled}")
print(f"Client: {monitor.client}")
```

---

## References

- [Plugin Development Guide](./PLUGIN_DEVELOPMENT_GUIDE.md)
- [88i Architecture Documentation](./arquitetura.md)
- [Phase 2 Summary](./PHASE2_SUMMARY.md)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Supabase Documentation](https://supabase.com/docs)

---

**Last Updated:** May 27, 2026  
**Maintainers:** 88i Development Team  
**Status:** Active Development - Phase 3
