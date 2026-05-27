# Plugin Development Guide

**Version:** 1.0.0  
**Date:** May 27, 2026  
**Target Audience:** Plugin Developers  
**Difficulty Level:** Intermediate  

---

## Table of Contents

1. [Introduction](#introduction)
2. [Environment Setup](#environment-setup)
3. [Plugin Anatomy](#plugin-anatomy)
4. [Creating Your First Plugin](#creating-your-first-plugin)
5. [Plugin Types](#plugin-types)
6. [Best Practices](#best-practices)
7. [Testing Your Plugin](#testing-your-plugin)
8. [Distribution & Publication](#distribution--publication)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Introduction

This guide walks you through creating plugins for the 88i sinistro harness. Plugins extend agent capabilities by:

- **Adding Tools** - New actions the agent can take
- **Adding Skills** - New triggers the agent can respond to
- **Providing Context** - Domain knowledge for prompt injection

### What Makes a Good Plugin?

✅ **Good Plugins:**
- Solve a specific problem
- Have clear input/output schemas
- Include error handling
- Are thoroughly tested
- Follow naming conventions
- Include docstrings and comments

❌ **Poor Plugins:**
- Catch-all functionality
- Vague or missing documentation
- No error handling
- Untested code
- Violate naming conventions

### Plugin Anatomy

Every plugin consists of:
1. **Metadata** - Name, version, description
2. **Initialization** - Setup required resources
3. **Execution** - Core logic
4. **Error Handling** - Graceful failure modes
5. **Cleanup** - Resource teardown

---

## Environment Setup

### Prerequisites

- Python 3.9+
- 88i sinistro harness repository cloned
- Virtual environment activated

```bash
cd ~/Projects/88i-sinistro-harness
source .venv/bin/activate
```

### File Structure

Create your plugin in `plugins/enabled/`:

```
plugins/
├── enabled/
│   ├── __init__.py
│   ├── tool_my_plugin.py       # Tool plugins
│   ├── skill_my_plugin.py      # Skill plugins
│   ├── context_my_plugin.py    # Context plugins
│   └── README.md
└── base.py                      # Base classes (read-only)
```

### Import the Base Classes

```python
from plugins.base import (
    Plugin,
    ToolPlugin,
    SkillPlugin,
    ContextPlugin,
    PluginMetadata
)
```

---

## Plugin Anatomy

### Plugin Base Class Structure

```python
@dataclass
class PluginMetadata:
    name: str                    # Unique identifier
    version: str                 # Semantic versioning (e.g., "1.0.0")
    author: str = "88i"          # Who wrote this
    description: str = ""        # What it does
    dependencies: list = None    # External dependencies
    enabled: bool = True         # Can be toggled on/off


class Plugin(ABC):
    """Base class for all plugins."""
    
    name: str                    # Must match metadata.name
    version: str                 # Must match metadata.version
    metadata: PluginMetadata     # Full metadata
    
    @abstractmethod
    async def initialize(self):
        """Setup resources (DB connections, API clients, etc.)."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Core plugin logic."""
        pass
```

### Minimal Plugin Example

```python
from plugins.base import ToolPlugin, PluginMetadata

class HelloWorldPlugin(ToolPlugin):
    # Required attributes
    name = "hello_world"
    version = "1.0.0"
    tool_name = "greet_user"
    
    metadata = PluginMetadata(
        name="hello_world",
        version="1.0.0",
        description="Simple greeting tool"
    )
    
    async def initialize(self):
        """Initialize the plugin."""
        print(f"Initializing {self.name}")
    
    async def execute(self, name: str = "World") -> Dict:
        """Execute the tool."""
        return {"greeting": f"Hello, {name}!"}
```

---

## Creating Your First Plugin

### Step 1: Define What Your Plugin Does

Ask yourself:
- What problem does it solve?
- What inputs does it need?
- What output should it produce?
- When should it be triggered?

**Example:** A tool to calculate claim reimbursement amount

```
Input: Claim amount, claim type, deductible percentage
Output: Reimbursed amount, deductible applied, net amount
Purpose: Automate reimbursement calculation
```

### Step 2: Choose the Plugin Type

| Type | When to Use | Example |
|------|------------|---------|
| **ToolPlugin** | LLM calls it to take action | Reembolso processor, document extractor |
| **SkillPlugin** | Auto-triggered by text patterns | Notification sender, escalation handler |
| **ContextPlugin** | Provides domain knowledge | Insurance rules, pricing rules |

**Decision Tree:**
```
Does the LLM call it directly?
├─ YES → ToolPlugin
└─ NO → Does it auto-trigger?
        ├─ YES → SkillPlugin
        └─ NO → Is it context data?
                └─ YES → ContextPlugin
```

### Step 3: Create the Plugin File

Create `plugins/enabled/tool_calculate_reembolso.py`:

```python
"""Tool for calculating claim reimbursement."""

from typing import Dict, Any
from plugins.base import ToolPlugin, PluginMetadata


class CalculateReembolsoPlugin(ToolPlugin):
    """Calculate reimbursement for approved claims."""
    
    name = "calculate_reembolso"
    version = "1.0.0"
    tool_name = "calcular_reembolso"
    
    metadata = PluginMetadata(
        name="calculate_reembolso",
        version="1.0.0",
        description="Calculate claim reimbursement amount",
        dependencies=["pydantic>=2.0"]
    )
    
    async def initialize(self):
        """Initialize the plugin."""
        print("Reembolso calculator initialized")
    
    async def execute(
        self,
        valor_reclamacao: float,
        tipo_sinistro: str,
        percentual_franquia: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """Calculate reimbursement amount."""
        
        # Input validation
        if valor_reclamacao <= 0:
            return {"erro": "Valor must be positive"}
        
        # Calculate deductible
        valor_franquia = valor_reclamacao * percentual_franquia
        
        # Apply claim type rules
        if tipo_sinistro == "roubo":
            # Theft claims deduct 10% additional fraud check fee
            valor_franquia += valor_reclamacao * 0.10
        elif tipo_sinistro == "colisao":
            # Collision claims have reduced deductibles
            valor_franquia *= 0.8
        
        # Calculate final reimbursement
        valor_reembolso = valor_reclamacao - valor_franquia
        
        return {
            "sucesso": True,
            "valor_reclamacao": valor_reclamacao,
            "valor_franquia": valor_franquia,
            "valor_reembolso": valor_reembolso,
            "tipo_sinistro": tipo_sinistro,
            "percentual_aplicado": (valor_franquia / valor_reclamacao) * 100
        }
```

### Step 4: Define Tool Schema (For Tools Only)

Tell the LLM what arguments your tool accepts:

```python
class CalculateReembolsoPlugin(ToolPlugin):
    # ... existing code ...
    
    tool_schema = {
        "type": "object",
        "properties": {
            "valor_reclamacao": {
                "type": "number",
                "description": "Claim amount in BRL"
            },
            "tipo_sinistro": {
                "type": "string",
                "enum": ["roubo", "colisao", "incendio"],
                "description": "Type of claim"
            },
            "percentual_franquia": {
                "type": "number",
                "description": "Deductible percentage (0.0-1.0)",
                "default": 0.1
            }
        },
        "required": ["valor_reclamacao", "tipo_sinistro"]
    }
```

### Step 5: Add Error Handling

Always handle errors gracefully:

```python
async def execute(self, **kwargs) -> Dict[str, Any]:
    """Calculate reimbursement with error handling."""
    try:
        valor = kwargs.get("valor_reclamacao")
        
        if not valor:
            return {
                "sucesso": False,
                "erro": "valor_reclamacao is required"
            }
        
        if valor < 0:
            return {
                "sucesso": False,
                "erro": "valor_reclamacao must be positive"
            }
        
        # ... calculation logic ...
        
        return {
            "sucesso": True,
            "valor_reembolso": valor_reembolso,
            # ... other fields ...
        }
    
    except Exception as e:
        return {
            "sucesso": False,
            "erro": f"Error calculating reimbursement: {str(e)}"
        }
```

### Step 6: Test Your Plugin

Create `tests/plugins/test_calculate_reembolso.py`:

```python
"""Tests for reembolso calculator plugin."""

import pytest
from plugins.enabled.tool_calculate_reembolso import (
    CalculateReembolsoPlugin
)


@pytest.mark.asyncio
async def test_basic_calculation():
    """Test basic reimbursement calculation."""
    plugin = CalculateReembolsoPlugin()
    await plugin.initialize()
    
    result = await plugin.execute(
        valor_reclamacao=1000.0,
        tipo_sinistro="colisao"
    )
    
    assert result["sucesso"] is True
    assert result["valor_reclamacao"] == 1000.0
    assert result["valor_reembolso"] < 1000.0  # Deductible applied


@pytest.mark.asyncio
async def test_theft_claim_additional_fee():
    """Test theft claims have additional fee."""
    plugin = CalculateReembolsoPlugin()
    await plugin.initialize()
    
    result_theft = await plugin.execute(
        valor_reclamacao=1000.0,
        tipo_sinistro="roubo",
        percentual_franquia=0.1
    )
    
    result_collision = await plugin.execute(
        valor_reclamacao=1000.0,
        tipo_sinistro="colisao",
        percentual_franquia=0.1
    )
    
    # Theft should have higher deductible
    assert result_theft["valor_franquia"] > result_collision["valor_franquia"]
```

---

## Plugin Types

### ToolPlugin - Complete Reference

Tools are callable by the LLM agent directly.

**When to Create:**
- User wants agent to perform an action
- Agent needs to call external systems
- Result should be fed back to LLM

**Example: Payment Processor**

```python
from plugins.base import ToolPlugin, PluginMetadata

class PaymentProcessorPlugin(ToolPlugin):
    name = "payment_processor"
    version = "1.0.0"
    tool_name = "processar_pagamento"
    
    metadata = PluginMetadata(
        name="payment_processor",
        version="1.0.0",
        description="Process claim payments",
        dependencies=["requests>=2.28"]
    )
    
    async def initialize(self):
        """Initialize payment gateway connection."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": "Bearer token"
        })
    
    async def execute(
        self,
        sinistro_id: str,
        valor: float,
        metodo: str = "transferencia"
    ) -> Dict[str, Any]:
        """Process payment."""
        try:
            response = self.session.post(
                "https://api.exemplo.com/pagamentos",
                json={
                    "sinistro_id": sinistro_id,
                    "valor": valor,
                    "metodo": metodo
                }
            )
            
            return {
                "sucesso": response.status_code == 200,
                "transacao_id": response.json().get("id"),
                "status": "processando"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }
```

### SkillPlugin - Complete Reference

Skills are auto-triggered by text patterns.

**When to Create:**
- Pattern should always trigger skill
- Agent doesn't need to decide to trigger it
- Results shouldn't be fed back to LLM

**Example: Auto-Notifier**

```python
from plugins.base import SkillPlugin, PluginMetadata

class NotificationSkillPlugin(SkillPlugin):
    name = "notificacao_skill"
    version = "1.0.0"
    skill_name = "notificar_segurado"
    skill_triggers = [
        "notify",
        "enviar mensagem",
        "communicate",
        "comunicar com"
    ]
    
    metadata = PluginMetadata(
        name="notificacao_skill",
        version="1.0.0",
        description="Automatically notify policyholders"
    )
    
    async def initialize(self):
        """Setup notification service."""
        pass
    
    async def execute(
        self,
        segurado_id: str,
        canal: str = "email",
        mensagem: str = ""
    ) -> Dict[str, Any]:
        """Send notification."""
        # Implementation...
        return {
            "sucesso": True,
            "canal": canal,
            "status": "enviado"
        }
```

### ContextPlugin - Complete Reference

Context plugins provide domain knowledge.

**When to Create:**
- You have reference data for prompts
- Rules should be injected into every relevant prompt
- Data is relatively static

**Example: Regulatory Rules**

```python
from plugins.base import ContextPlugin, PluginMetadata

class RegulatoryContextPlugin(ContextPlugin):
    name = "regulatory_context"
    version = "1.0.0"
    context_provider_name = "regulatory_rules"
    
    metadata = PluginMetadata(
        name="regulatory_context",
        version="1.0.0",
        description="Provide SUSEP regulatory rules"
    )
    
    # Static rules loaded at init
    SUSEP_RULES = {
        "max_response_time": 30,  # days
        "max_deductible": 0.20,   # 20%
        "mandatory_fields": ["BO", "photos", "medical_report"],
        "grace_period": 7  # days
    }
    
    async def initialize(self):
        """Load rules from database if needed."""
        pass
    
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Return regulatory context."""
        return {
            "regulatory": self.SUSEP_RULES,
            "last_updated": "2026-05-27"
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute (delegates to get_context)."""
        return await self.get_context(**kwargs)
```

---

## Best Practices

### 1. Follow Naming Conventions

```python
# ✅ Good
class ValidateDocumentPlugin(ToolPlugin)
class NotifyPolicyholder(SkillPlugin)
class InsuranceRulesContext(ContextPlugin)

# ❌ Bad
class tool(ToolPlugin)
class X(SkillPlugin)
class do_stuff(ContextPlugin)
```

### 2. Comprehensive Docstrings

```python
class AnalyzeDocumentPlugin(ToolPlugin):
    """
    Analyze claim documents using OCR and NLP.
    
    This plugin extracts text from claim documents (PDFs, images)
    and returns structured data suitable for claim processing.
    
    Supports:
    - PDF documents
    - JPEG/PNG images
    - Handwritten forms
    
    Performance:
    - Avg latency: 2-5 seconds per document
    - Accuracy: 95% for printed text
    """
```

### 3. Input Validation

```python
async def execute(self, **kwargs) -> Dict[str, Any]:
    # Validate required fields
    required = ["campo_obrigatorio"]
    for field in required:
        if field not in kwargs:
            return {"erro": f"{field} is required"}
    
    # Validate types
    valor = kwargs.get("valor")
    if not isinstance(valor, (int, float)):
        return {"erro": "valor must be numeric"}
    
    # Validate ranges
    if valor < 0 or valor > 1000000:
        return {"erro": "valor out of acceptable range"}
```

### 4. Meaningful Error Messages

```python
# ✅ Good
return {
    "sucesso": False,
    "erro": "Document OCR failed: Unable to process encrypted PDF",
    "codigo_erro": "OCR_ENCRYPTION_ERROR",
    "pode_retentar": True
}

# ❌ Bad
return {
    "sucesso": False,
    "erro": "Error"
}
```

### 5. Return Consistent Schemas

```python
# Every response has same structure
return {
    "sucesso": True/False,
    "resultado": {...},           # Main data
    "metadados": {                # Metadata
        "duracao_ms": 1234,
        "versao_plugin": "1.0.0",
        "timestamp": "2026-05-27T10:30:00Z"
    },
    "erro": None or "Error message"
}
```

### 6. Logging

```python
import logging

logger = logging.getLogger(__name__)

async def execute(self, **kwargs):
    logger.info(f"Processing claim: {kwargs.get('sinistro_id')}")
    
    try:
        result = await self._do_work(**kwargs)
        logger.info(f"Success: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return {"sucesso": False, "erro": str(e)}
```

### 7. Async/Await Patterns

```python
# ✅ Good - all I/O is async
async def execute(self, **kwargs):
    # Database call
    result = await self.db.query(...)
    
    # API call
    response = await self.http.post(...)
    
    return result

# ❌ Bad - blocking calls
def execute(self, **kwargs):
    result = requests.post(...)  # Blocks event loop!
    return result
```

---

## Testing Your Plugin

### Unit Tests

```python
"""Test individual plugin functionality."""

@pytest.mark.asyncio
async def test_plugin_initialization():
    """Test plugin initializes correctly."""
    plugin = MyPlugin()
    await plugin.initialize()
    # No exceptions = pass


@pytest.mark.asyncio
async def test_happy_path():
    """Test successful execution."""
    plugin = MyPlugin()
    result = await plugin.execute(input="valid")
    
    assert result["sucesso"] is True
    assert "resultado" in result


@pytest.mark.asyncio
async def test_error_handling():
    """Test error cases."""
    plugin = MyPlugin()
    result = await plugin.execute(input=None)
    
    assert result["sucesso"] is False
    assert "erro" in result
```

### Integration Tests

```python
"""Test plugin with real dependencies."""

@pytest.mark.asyncio
async def test_with_real_database():
    """Test plugin against real database."""
    plugin = MyPlugin()
    await plugin.initialize()  # Connects to test DB
    
    result = await plugin.execute(sinistro_id="sin_test_001")
    
    assert result["sucesso"] is True
```

### Run Tests

```bash
# Test single plugin
pytest tests/plugins/test_my_plugin.py -v

# Test all plugins
pytest tests/plugins/ -v

# Test with coverage
pytest tests/plugins/ --cov=plugins/enabled
```

---

## Distribution & Publication

### Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes

```python
# Start at 1.0.0
version = "1.0.0"

# New feature → 1.1.0
version = "1.1.0"

# Bug fix → 1.0.1
version = "1.0.1"

# Breaking change → 2.0.0
version = "2.0.0"
```

### Documentation Template

Create `plugins/enabled/MY_PLUGIN_README.md`:

```markdown
# My Plugin

**Version:** 1.0.0  
**Type:** ToolPlugin / SkillPlugin / ContextPlugin

## Description

What does this plugin do?

## Usage

```python
# How to use it
```

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1 | str | Yes | Description |
| param2 | float | No | Default: 0.5 |

## Outputs

```json
{
  "sucesso": true,
  "resultado": {...}
}
```

## Examples

```python
result = await plugin.execute(
    param1="value",
    param2=0.8
)
```

## Testing

```bash
pytest tests/plugins/test_my_plugin.py -v
```
```

### Checklist Before Release

- [ ] All tests pass
- [ ] Code has no syntax errors
- [ ] Docstrings are complete
- [ ] Error handling covers edge cases
- [ ] Version number updated
- [ ] README created
- [ ] Plugin file follows naming convention
- [ ] No hardcoded secrets/API keys
- [ ] Dependencies documented
- [ ] Performance acceptable (< 5s latency)

---

## Troubleshooting

### Plugin Not Loading

**Error:** `ModuleNotFoundError: No module named 'plugins.enabled.my_plugin'`

**Solution:**
1. Check filename matches convention: `tool_my_plugin.py`, `skill_my_plugin.py`, etc.
2. File is in `plugins/enabled/` directory
3. No syntax errors: `python -m py_compile plugins/enabled/my_plugin.py`

### Plugin.execute() Not Being Called

**Error:** Plugin loads but execute doesn't run

**Solution:**
1. For **ToolPlugins** - Make sure agent has `tool_plugins` enabled
2. For **SkillPlugins** - Verify trigger text matches user input
3. Check plugin's `enabled` flag in metadata

### Async Errors

**Error:** `RuntimeError: Event loop is closed`

**Solution:**
```python
# ✅ Correct - all I/O is async
async def execute(self, **kwargs):
    result = await self.async_operation()

# ❌ Wrong - mixing sync and async
async def execute(self, **kwargs):
    result = sync_operation()  # This blocks!
```

### Plugin Dependencies

**Error:** `ModuleNotFoundError` for required package

**Solution:**
1. List dependency in `metadata.dependencies`
2. Install: `pip install package_name`
3. Check `.venv` is activated

---

## Examples

### Complete Tool Plugin Example

```python
"""Complete reembolso calculation plugin."""

import logging
from typing import Dict, Any
from plugins.base import ToolPlugin, PluginMetadata

logger = logging.getLogger(__name__)


class ReembolsoCalculatorPlugin(ToolPlugin):
    """
    Calculate reimbursement amounts for approved claims.
    
    Applies franquia (deductible) based on claim type,
    vehicle type, and policy terms.
    """
    
    # Required fields
    name = "reembolso_calculator"
    version = "1.0.0"
    tool_name = "calcular_reembolso"
    
    # Metadata
    metadata = PluginMetadata(
        name="reembolso_calculator",
        version="1.0.0",
        author="88i Development",
        description="Calculate claim reimbursement with franquia",
        dependencies=["pydantic>=2.0"],
        enabled=True
    )
    
    # Tool schema for LLM
    tool_schema = {
        "type": "object",
        "properties": {
            "valor_sinistro": {
                "type": "number",
                "description": "Claim amount in BRL"
            },
            "tipo_sinistro": {
                "type": "string",
                "enum": ["roubo", "colisao", "incendio"],
                "description": "Type of claim"
            },
            "franquia_pct": {
                "type": "number",
                "description": "Deductible percentage",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["valor_sinistro", "tipo_sinistro"]
    }
    
    # Deductible rules by claim type
    FRANQUIA_RULES = {
        "roubo": {
            "base": 0.10,
            "fraud_check_fee": 0.05,  # Additional 5%
            "max_coverage": 50000.00
        },
        "colisao": {
            "base": 0.05,
            "fraud_check_fee": 0,
            "max_coverage": 30000.00
        },
        "incendio": {
            "base": 0.15,
            "fraud_check_fee": 0.10,
            "max_coverage": 100000.00
        }
    }
    
    async def initialize(self):
        """Initialize plugin (no external resources needed)."""
        logger.info(f"Initializing {self.name} v{self.version}")
    
    async def execute(
        self,
        valor_sinistro: float,
        tipo_sinistro: str,
        franquia_pct: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calculate reimbursement amount.
        
        Args:
            valor_sinistro: Claim amount in BRL
            tipo_sinistro: Type of claim (roubo, colisao, incendio)
            franquia_pct: Override deductible percentage (0-1)
        
        Returns:
            Dict with reimbursement details or error
        """
        try:
            # Input validation
            if not valor_sinistro or valor_sinistro <= 0:
                return {
                    "sucesso": False,
                    "erro": "valor_sinistro must be positive",
                    "metadados": {"timestamp": self._timestamp()}
                }
            
            if tipo_sinistro not in self.FRANQUIA_RULES:
                return {
                    "sucesso": False,
                    "erro": f"Unsupported tipo_sinistro: {tipo_sinistro}",
                    "metadados": {"timestamp": self._timestamp()}
                }
            
            # Get deductible rules
            rules = self.FRANQUIA_RULES[tipo_sinistro]
            
            # Use override or default
            franquia_pct = franquia_pct or rules["base"]
            
            # Calculate components
            valor_base_franquia = valor_sinistro * franquia_pct
            valor_fraud_fee = valor_sinistro * rules["fraud_check_fee"]
            valor_total_franquia = valor_base_franquia + valor_fraud_fee
            
            # Apply coverage cap
            max_coverage = rules["max_coverage"]
            if valor_sinistro > max_coverage:
                valor_sinistro = max_coverage
                valor_total_franquia = min(
                    valor_total_franquia,
                    max_coverage * (franquia_pct + rules["fraud_check_fee"])
                )
            
            # Calculate final reimbursement
            valor_reembolso = valor_sinistro - valor_total_franquia
            
            logger.info(
                f"Calculated reimbursement: "
                f"claim={valor_sinistro}, type={tipo_sinistro}, "
                f"deductible={valor_total_franquia}, "
                f"reimbursement={valor_reembolso}"
            )
            
            return {
                "sucesso": True,
                "resultado": {
                    "valor_sinistro": valor_sinistro,
                    "tipo_sinistro": tipo_sinistro,
                    "valor_franquia_base": valor_base_franquia,
                    "valor_fraud_fee": valor_fraud_fee,
                    "valor_franquia_total": valor_total_franquia,
                    "valor_reembolso": valor_reembolso,
                    "percentual_total": (valor_total_franquia / valor_sinistro) * 100
                },
                "metadados": {
                    "versao_plugin": self.version,
                    "timestamp": self._timestamp()
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculating reimbursement: {e}", exc_info=True)
            return {
                "sucesso": False,
                "erro": f"Unexpected error: {str(e)}",
                "metadados": {"timestamp": self._timestamp()}
            }
    
    def _timestamp(self) -> str:
        """Get ISO format timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
```

---

## Quick Reference

### Create a Tool Plugin

```bash
# 1. Create file
touch plugins/enabled/tool_my_feature.py

# 2. Copy template
cat > plugins/enabled/tool_my_feature.py << 'EOF'
from plugins.base import ToolPlugin, PluginMetadata

class MyFeaturePlugin(ToolPlugin):
    name = "my_feature"
    version = "1.0.0"
    tool_name = "my_feature"
    
    metadata = PluginMetadata(
        name="my_feature",
        version="1.0.0",
        description="..."
    )
    
    async def initialize(self):
        pass
    
    async def execute(self, **kwargs):
        return {"sucesso": True, "resultado": {...}}
EOF

# 3. Test
pytest tests/plugins/test_my_feature.py -v

# 4. Verify loading
python -c "from plugins.enabled.tool_my_feature import MyFeaturePlugin"
```

---

## Need Help?

- Check [PHASE3_CONTEXT_PLUGINS.md](./PHASE3_CONTEXT_PLUGINS.md) for architecture
- Review example plugins in `plugins/examples.py`
- Run existing plugin tests as reference
- Check logs: `~/.hermes/logs/agent.log`

---

**Last Updated:** May 27, 2026  
**Maintained By:** 88i Development Team
