"""Tests for plugin system."""

import pytest
from plugins.plugin_loader import PluginLoader
from plugins.base import ToolPlugin, SkillPlugin


@pytest.mark.asyncio
async def test_plugin_loader_initialization():
    """Test plugin loader can be initialized."""
    loader = PluginLoader(plugins_dir="plugins/enabled")
    assert loader is not None
    assert hasattr(loader, 'load_plugins')
    assert hasattr(loader, 'register_tool_plugin')


@pytest.mark.asyncio
async def test_tool_plugin_registration():
    """Test registering a tool plugin."""
    loader = PluginLoader(plugins_dir="plugins/enabled")
    
    # Create a mock plugin
    class MockToolPlugin(ToolPlugin):
        name = "mock_tool"
        version = "1.0.0"
        
        async def initialize(self):
            pass
        
        async def execute(self, **kwargs):
            return {"sucesso": True}
    
    plugin = MockToolPlugin()
    loader.register_tool_plugin(plugin)
    
    assert "mock_tool" in loader.tool_plugins
    assert loader.tool_plugins["mock_tool"] == plugin


@pytest.mark.asyncio
async def test_plugin_discovery():
    """Test plugin discovery from directory."""
    loader = PluginLoader(plugins_dir="plugins/enabled")
    discovered = await loader.discover_plugins()
    
    assert discovered is not None
    assert isinstance(discovered, dict)
