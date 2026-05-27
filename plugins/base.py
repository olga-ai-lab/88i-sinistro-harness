"""Base classes for plugins."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    author: str = "88i"
    description: str = ""
    dependencies: list = None
    enabled: bool = True


class Plugin(ABC):
    """Base class for all plugins."""
    
    name: str
    version: str
    metadata: PluginMetadata
    
    @abstractmethod
    async def initialize(self):
        """Initialize plugin."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute plugin logic."""
        pass


class ToolPlugin(Plugin):
    """Plugin that registers a tool."""
    
    tool_name: str
    tool_schema: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic."""
        pass


class SkillPlugin(Plugin):
    """Plugin that registers a skill."""
    
    skill_name: str
    skill_triggers: list = []
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute skill logic."""
        pass


class ContextPlugin(Plugin):
    """Plugin that provides context."""
    
    context_provider_name: str
    
    @abstractmethod
    async def get_context(self, **kwargs) -> Dict[str, Any]:
        """Get context data."""
        pass
