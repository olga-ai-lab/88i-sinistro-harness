"""Plugin loader and manager."""

import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from plugins.base import Plugin, ToolPlugin, SkillPlugin, ContextPlugin

logger = logging.getLogger(__name__)


class PluginLoader:
    """Loads and manages plugins dynamically."""
    
    def __init__(self, plugins_dir: str = "plugins/enabled"):
        self.plugins_dir = Path(plugins_dir)
        self.tool_plugins: Dict[str, ToolPlugin] = {}
        self.skill_plugins: Dict[str, SkillPlugin] = {}
        self.context_plugins: Dict[str, ContextPlugin] = {}
        self.all_plugins: Dict[str, Plugin] = {}
    
    async def discover_plugins(self) -> Dict[str, List[str]]:
        """Discover available plugins in plugins directory."""
        discovered = {
            "tools": [],
            "skills": [],
            "context": []
        }
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return discovered
        
        for module_file in self.plugins_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue
            
            module_name = module_file.stem
            try:
                # Discover plugin type from file naming convention
                if "tool_" in module_name:
                    discovered["tools"].append(module_name)
                elif "skill_" in module_name:
                    discovered["skills"].append(module_name)
                elif "context_" in module_name:
                    discovered["context"].append(module_name)
            except Exception as e:
                logger.error(f"Error discovering plugin {module_name}: {e}")
        
        return discovered
    
    async def load_plugins(self, plugins: List[str] = None) -> Dict[str, bool]:
        """Load specified plugins or all discovered plugins."""
        results = {}
        
        discovered = await self.discover_plugins()
        all_plugins = plugins or (
            discovered["tools"] + discovered["skills"] + discovered["context"]
        )
        
        for plugin_name in all_plugins:
            try:
                plugin = await self._load_plugin(plugin_name)
                if plugin:
                    await plugin.initialize()
                    self.all_plugins[plugin.name] = plugin
                    results[plugin_name] = True
                    logger.info(f"Loaded plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_name}: {e}")
                results[plugin_name] = False
        
        return results
    
    async def _load_plugin(self, module_name: str) -> Optional[Plugin]:
        """Load a single plugin from module."""
        try:
            # Dynamic import
            module = importlib.import_module(f"plugins.enabled.{module_name}")
            
            # Find Plugin class in module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    plugin_instance = attr()
                    return plugin_instance
        except Exception as e:
            logger.error(f"Error loading plugin module {module_name}: {e}")
        
        return None
    
    def register_tool_plugin(self, plugin: ToolPlugin):
        """Register a tool plugin."""
        self.tool_plugins[plugin.name] = plugin
        self.all_plugins[plugin.name] = plugin
        logger.info(f"Registered tool plugin: {plugin.name}")
    
    def register_skill_plugin(self, plugin: SkillPlugin):
        """Register a skill plugin."""
        self.skill_plugins[plugin.name] = plugin
        self.all_plugins[plugin.name] = plugin
        logger.info(f"Registered skill plugin: {plugin.name}")
    
    def register_context_plugin(self, plugin: ContextPlugin):
        """Register a context plugin."""
        self.context_plugins[plugin.name] = plugin
        self.all_plugins[plugin.name] = plugin
        logger.info(f"Registered context plugin: {plugin.name}")
    
    def get_plugins(self, plugin_type: str = None) -> Dict[str, Plugin]:
        """Get plugins by type (all, tool, skill, context)."""
        if plugin_type == "tool":
            return self.tool_plugins
        elif plugin_type == "skill":
            return self.skill_plugins
        elif plugin_type == "context":
            return self.context_plugins
        else:
            return self.all_plugins
