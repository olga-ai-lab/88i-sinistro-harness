# plugins/enabled - Plugin Directory

**Purpose:** Directory for enabled plugins that extend 88i sinistro harness functionality  
**Version:** 1.0.0  
**Last Updated:** May 27, 2026  

---

## Overview

This directory contains plugins that are automatically discovered and loaded when the 88i agent starts. Plugins extend the system with:

- **Tools** - Actions the LLM can take
- **Skills** - Automatic response patterns
- **Context Providers** - Domain knowledge for prompt injection

---

## Directory Structure

```
plugins/enabled/
├── README.md                          # This file
├── __init__.py                        # Python package marker
├── tool_*.py                          # Tool plugins
├── skill_*.py                         # Skill plugins
├── context_*.py                       # Context plugins
└── examples/                          # Example implementations
    ├── tool_example_reembolso.py
    ├── skill_example_notification.py
    └── context_example_commercial.py
```

---

## Plugin Naming Conventions

Follow these conventions for plugins to be discovered correctly:

### Tool Plugins
```
tool_<feature_name>.py

Examples:
- tool_reembolso.py
- tool_document_extractor.py
- tool_fraud_scorer.py
- tool_payment_processor.py
```

### Skill Plugins
```
skill_<feature_name>.py

Examples:
- skill_notification.py
- skill_escalation.py
- skill_document_upload.py
```

### Context Plugins
```
context_<domain_name>.py

Examples:
- context_insurance_rules.py
- context_regulatory_rules.py
- context_commercial_pricing.py
- context_fraud_patterns.py
```

### Example/Test Plugins
```
example_<name>.py
test_<name>.py

These are NOT auto-loaded during discovery.
Use for testing and reference implementations.
```

---

## Plugin Discovery Process

When the agent starts, the plugin loader performs:

1. **Scan** - Discovers all `*.py` files in this directory
2. **Filter** - Applies naming convention rules
3. **Import** - Dynamically imports discovered modules
4. **Detect** - Finds `Plugin` subclasses
5. **Register** - Registers with appropriate registry
6. **Initialize** - Calls `plugin.initialize()`
7. **Ready** - Plugin available for use

**Discovery Code:**
```python
from plugins.plugin_loader import PluginLoader

loader = PluginLoader(plugins_dir="plugins/enabled")
discovered = await loader.discover_plugins()
# Returns: {"tools": [...], "skills": [...], "context": [...]}

loaded = await loader.load_plugins()
# Loads and initializes all discovered plugins
```

---

## Creating Your First Plugin

### Quick Start

1. **Create a file** in this directory following naming convention:
   ```bash
   touch plugins/enabled/tool_my_feature.py
   ```

2. **Write the plugin code:**
   ```python
   from plugins.base import ToolPlugin, PluginMetadata
   
   class MyFeaturePlugin(ToolPlugin):
       name = "my_feature"
       version = "1.0.0"
       tool_name = "my_feature"
       
       metadata = PluginMetadata(
           name="my_feature",
           version="1.0.0",
           description="Description of what your plugin does"
       )
       
       async def initialize(self):
           """Setup resources here."""
           pass
       
       async def execute(self, **kwargs):
           """Main plugin logic here."""
           return {
               "sucesso": True,
               "resultado": {...}
           }
   ```

3. **Test your plugin:**
   ```bash
   pytest tests/plugins/test_my_feature.py -v
   ```

4. **Verify loading:**
   ```bash
   python -c "from plugins.enabled.tool_my_feature import MyFeaturePlugin"
   ```

See [PLUGIN_DEVELOPMENT_GUIDE.md](../PLUGIN_DEVELOPMENT_GUIDE.md) for detailed tutorial.

---

## Built-in Plugin Examples

The following example plugins demonstrate best practices:

### Tool Plugin Example

**File:** `example_tool_reembolso.py`

Calculates claim reimbursement with automatic deductible application:

```python
from plugins.base import ToolPlugin

class ReembolsoToolPlugin(ToolPlugin):
    name = "reembolso_tool"
    version = "1.0.0"
    tool_name = "reembolso_process"
    
    async def execute(
        self,
        sinistro_id: str,
        valor_indenizacao: float,
        metodo_pagamento: str = "transferencia"
    ) -> Dict:
        return {
            "sucesso": True,
            "sinistro_id": sinistro_id,
            "valor_processado": valor_indenizacao,
            "status": "processando"
        }
```

**Usage:**
```python
# LLM can call this tool
result = await plugin.execute(
    sinistro_id="sin_001",
    valor_indenizacao=5000.00
)
```

### Skill Plugin Example

**File:** `example_skill_notification.py`

Auto-triggered by text patterns to notify policyholders:

```python
from plugins.base import SkillPlugin

class NotificacaoSkillPlugin(SkillPlugin):
    name = "notificacao_skill"
    version = "1.0.0"
    skill_name = "notificar_segurado"
    skill_triggers = ["notificar", "enviar mensagem", "comunicar"]
    
    async def execute(
        self,
        segurado_id: str,
        canal: str = "email"
    ) -> Dict:
        return {
            "sucesso": True,
            "status": "enviado"
        }
```

**Triggering:**
```
User: "Please notify the customer about the decision"
      ↓
System detects trigger pattern "notify"
      ↓
Automatically invokes notificacao_skill
      ↓
Sends notification
```

### Context Plugin Example

**File:** `example_context_commercial.py`

Provides commercial rules for prompt injection:

```python
from plugins.base import ContextPlugin

class ComercialContextPlugin(ContextPlugin):
    name = "comercial_context"
    version = "1.0.0"
    context_provider_name = "comercial_rules"
    
    async def get_context(self, **kwargs) -> Dict:
        return {
            "comercial": {
                "desconto_fidelidade": 0.15,
                "bonus_multiplas_apolices": 0.10,
                "taxa_administrativo": 50.00
            }
        }
```

**Usage:**
```python
# In context engine
context = await plugin.get_context(segurado_tipo="vip")
# Injected into prompt for LLM to use
```

---

## Plugin Lifecycle

### Initialization Phase

```
1. System Startup
   ↓
2. Configuration Loaded
   ↓
3. Plugin Loader Created
   ↓
4. Plugins Discovered (*.py files scanned)
   ↓
5. Modules Imported Dynamically
   ↓
6. Plugin Classes Instantiated
   ↓
7. plugin.initialize() Called
   ↓
8. Registered in Appropriate Registry
   ↓
9. Tool Schemas Advertised to LLM
   ↓
10. Ready for Use
```

### Execution Phase

```
User Input
  ↓
Agent Receives Message
  ↓
For Tool Plugins:
  → LLM Decides to Call Tool
  → Tool Plugin.execute() Invoked
  → Result Returned to LLM
  ↓
For Skill Plugins:
  → Text Pattern Matched
  → Skill Plugin.execute() Invoked
  → Result Stored (not sent to LLM)
  ↓
For Context Plugins:
  → Automatic (during prompt injection)
  → get_context() Called
  → Context Injected into Prompt
  ↓
Response Generated
```

### Shutdown Phase

```
Graceful Shutdown Signal
  ↓
For Each Plugin:
  → Call cleanup() if defined
  → Close resources
  → Remove from registry
  ↓
Agent Stops
```

---

## Plugin Interface Reference

### Base Class Structure

All plugins inherit from `Plugin`:

```python
class Plugin(ABC):
    name: str                      # Unique identifier
    version: str                   # Semantic version
    metadata: PluginMetadata       # Full metadata
    
    async def initialize(self):
        """Setup resources (called once at startup)."""
        pass
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main plugin logic (called on use)."""
        pass
```

### ToolPlugin Interface

```python
class ToolPlugin(Plugin):
    tool_name: str                 # Name in tool registry
    tool_schema: Dict = {}         # OpenAI-compatible schema
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic."""
        pass
```

**Tool Schema Example:**
```python
tool_schema = {
    "type": "object",
    "properties": {
        "sinistro_id": {
            "type": "string",
            "description": "Claim ID"
        },
        "valor": {
            "type": "number",
            "description": "Amount in BRL"
        }
    },
    "required": ["sinistro_id", "valor"]
}
```

### SkillPlugin Interface

```python
class SkillPlugin(Plugin):
    skill_name: str                # Name in skill registry
    skill_triggers: list           # Text patterns
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute skill logic."""
        pass
```

**Trigger Patterns:**
```python
skill_triggers = [
    "notify",
    "send message",
    "communicate with",
    "contatar",
    "informar"
]
```

Matching is case-insensitive, partial matching allowed.

### ContextPlugin Interface

```python
class ContextPlugin(Plugin):
    context_provider_name: str     # Name in context engine
    
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Get context data."""
        pass
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute (delegates to get_context)."""
        pass
```

---

## Best Practices

### ✅ DO:

- **Validate inputs** - Check for required fields and types
- **Handle errors** - Return error objects, don't raise exceptions
- **Use async/await** - All I/O must be asynchronous
- **Log operations** - Use `logging` module for debugging
- **Document code** - Include docstrings and comments
- **Test thoroughly** - Write tests for all scenarios
- **Version semantically** - MAJOR.MINOR.PATCH format
- **Use consistent schemas** - All responses have same structure

### ❌ DON'T:

- **Mix sync/async** - Don't call blocking functions in async code
- **Hardcode secrets** - Use environment variables
- **Catch all exceptions** - Be specific about what you handle
- **Return raw exceptions** - Convert to error objects
- **Modify global state** - Keep plugins isolated
- **Create infinite loops** - Set timeout/retry limits
- **Ignore performance** - Keep latency < 5 seconds

---

## Configuration & Control

### Enable/Disable Plugins

Set in `.env` or runtime:

```bash
# Disable specific plugin
DISABLED_PLUGINS=plugin_name_1,plugin_name_2

# Control discovery
PLUGINS_AUTO_DISCOVERY=true
PLUGINS_AUTO_LOAD=true

# Set plugins directory
PLUGINS_ENABLED_DIR=plugins/enabled
```

### Environment Variables

Plugins can read environment variables:

```python
import os

class MyPlugin(ToolPlugin):
    async def initialize(self):
        api_key = os.getenv("MY_PLUGIN_API_KEY")
        if not api_key:
            raise ValueError("MY_PLUGIN_API_KEY not set")
```

### Configuration Files

Store plugin config in `config/plugins/`:

```
config/plugins/
├── tool_reembolso.json
├── skill_notification.json
└── context_insurance.json
```

**Example config:**
```json
{
  "enabled": true,
  "version": "1.0.0",
  "options": {
    "timeout_seconds": 10,
    "max_retries": 3,
    "cache_ttl": 3600
  }
}
```

---

## Troubleshooting

### Plugin Not Loading

**Check:**
1. Filename follows convention: `tool_*.py`, `skill_*.py`, `context_*.py`
2. File is in `plugins/enabled/` directory
3. No syntax errors: `python -m py_compile plugins/enabled/tool_name.py`
4. Class extends correct base: `ToolPlugin`, `SkillPlugin`, `ContextPlugin`

**Debug:**
```bash
# Check what was discovered
python -c "from plugins.plugin_loader import PluginLoader; import asyncio; print(asyncio.run(PluginLoader().discover_plugins()))"
```

### Plugin Crashes on Execute

**Check:**
1. All required async operations use `await`
2. Input validation catches edge cases
3. Error handling returns proper format
4. No blocking I/O calls

**Debug:**
```bash
# Check logs
tail -f ~/.hermes/logs/agent.log | grep "plugin_name"

# Test directly
pytest tests/plugins/test_plugin_name.py -v -s
```

### Plugin Discovery But Not Executing

**For Tools:**
- Verify `tool_schema` is properly formatted
- Check `tool_name` matches what agent expects

**For Skills:**
- Verify `skill_triggers` are descriptive
- Test trigger matching: "text contains trigger pattern"

**For Context:**
- Verify `get_context()` returns non-empty dict
- Check `context_provider_name` uniqueness

---

## Testing Your Plugin

### Unit Test Template

```python
import pytest
from plugins.enabled.tool_my_plugin import MyPluginClass

@pytest.mark.asyncio
async def test_initialization():
    """Test plugin initializes without errors."""
    plugin = MyPluginClass()
    await plugin.initialize()
    assert plugin is not None

@pytest.mark.asyncio
async def test_happy_path():
    """Test successful execution."""
    plugin = MyPluginClass()
    result = await plugin.execute(required_param="value")
    
    assert result["sucesso"] is True
    assert "resultado" in result

@pytest.mark.asyncio
async def test_error_handling():
    """Test error cases."""
    plugin = MyPluginClass()
    result = await plugin.execute(required_param=None)
    
    assert result["sucesso"] is False
    assert "erro" in result
```

### Run Tests

```bash
# Single plugin
pytest tests/plugins/test_my_plugin.py -v

# All plugins
pytest tests/plugins/ -v

# With coverage
pytest tests/plugins/ --cov=plugins/enabled
```

---

## Documentation Templates

### For Tool Plugins

```python
class MyToolPlugin(ToolPlugin):
    """
    Brief description of what tool does.
    
    Longer description of:
    - What problem it solves
    - What inputs it accepts
    - What outputs it produces
    - Any side effects or dependencies
    
    Examples:
        Basic usage:
        >>> result = await plugin.execute(param1="value")
        >>> print(result["resultado"])
    """
```

### For Skill Plugins

```python
class MySkillPlugin(SkillPlugin):
    """
    Brief description of skill.
    
    This skill is triggered by patterns like:
    - "keyword 1"
    - "keyword 2"
    - "phrase pattern"
    
    It performs:
    - Action 1
    - Action 2
    """
    
    skill_triggers = [
        "keyword 1",
        "keyword 2"
    ]
```

### For Context Plugins

```python
class MyContextPlugin(ContextPlugin):
    """
    Provides context about [domain].
    
    Context includes:
    - Rule set A
    - Reference data B
    - Policy guidelines C
    
    Used in prompts to:
    - Inform decisions
    - Validate outputs
    - Provide domain knowledge
    """
```

---

## Performance Considerations

### Latency Targets

- **Tools** - Should complete in < 5 seconds
- **Skills** - Should complete in < 2 seconds
- **Context** - Should load in < 1 second

### Optimization Tips

1. **Cache when possible** - Store frequently accessed data
2. **Use async I/O** - Don't block the event loop
3. **Validate early** - Fail fast on invalid input
4. **Set timeouts** - Prevent hanging requests
5. **Monitor performance** - Log execution times

```python
import time

async def execute(self, **kwargs):
    start = time.time()
    try:
        result = await self._do_work(**kwargs)
        elapsed = time.time() - start
        logger.info(f"Execution took {elapsed:.2f}s")
        return result
    finally:
        elapsed = time.time() - start
        if elapsed > 5:
            logger.warning(f"Slow execution: {elapsed:.2f}s")
```

---

## Integration with Agent

### Automatic Tool Registration

Tools are automatically registered in agent's available tools:

```python
# In agent startup
loader = PluginLoader()
plugins = await loader.load_plugins()

# Tools available to LLM
for tool_plugin in loader.get_plugins("tool").values():
    agent.register_tool(
        name=tool_plugin.tool_name,
        schema=tool_plugin.tool_schema,
        handler=tool_plugin.execute
    )
```

### Context Injection

Context plugins are injected automatically:

```python
# In prompt building
context_data = {}
for context_plugin in loader.get_plugins("context").values():
    ctx = await context_plugin.get_context(**user_params)
    context_data.update(ctx)

# Injected into prompt
enhanced_prompt = f"Context: {context_data}\n\nUser Query: {user_input}"
```

---

## Contributing a Plugin

### Checklist

- [ ] Follows naming convention
- [ ] Passes all tests
- [ ] Has comprehensive docstrings
- [ ] Includes error handling
- [ ] No hardcoded secrets
- [ ] Performance acceptable
- [ ] Dependencies documented
- [ ] README created
- [ ] Example usage provided
- [ ] Security reviewed

### Submission Process

1. Create feature branch: `git checkout -b feature/plugin-name`
2. Implement plugin in `plugins/enabled/`
3. Write tests in `tests/plugins/`
4. Document in plugin's docstring + README
5. Run tests: `pytest tests/plugins/test_name.py -v`
6. Commit: `git commit -m "feat: add plugin_name plugin"`
7. Push and create PR

---

## Resources

- **Architecture:** [PHASE3_CONTEXT_PLUGINS.md](../PHASE3_CONTEXT_PLUGINS.md)
- **Development Guide:** [PLUGIN_DEVELOPMENT_GUIDE.md](../PLUGIN_DEVELOPMENT_GUIDE.md)
- **Base Classes:** `plugins/base.py`
- **Examples:** `plugins/examples.py`
- **Loader:** `plugins/plugin_loader.py`

---

## Support

For issues, questions, or plugin ideas:

1. Check [PLUGIN_DEVELOPMENT_GUIDE.md](../PLUGIN_DEVELOPMENT_GUIDE.md) for detailed tutorial
2. Review existing plugins in this directory
3. Check test files for usage examples
4. Review logs: `~/.hermes/logs/agent.log`

---

**Last Updated:** May 27, 2026  
**Maintained By:** 88i Development Team  
**Status:** Active Development - Phase 3
