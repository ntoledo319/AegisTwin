"""
AegisTwin Plugin System

Extensibility via plugins for connectors, analyzers, and policies.

@ai_prompt: Use discover_plugins() to find installed plugins, register() to add.
@context_boundary: aegistwin/plugins

## Quick Start
```python
from aegistwin.plugins import discover_plugins, PluginRegistry

# Discover installed plugins
plugins = discover_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")

# Register with runtime
registry = PluginRegistry()
registry.register(plugin)
```

# AI-GENERATED 2026-01-07
"""

from aegistwin.plugins.base import (
    AegisTwinPlugin,
    AnalyzerPlugin,
    ConnectorPlugin,
    PluginInfo,
    PolicyPlugin,
)
from aegistwin.plugins.loader import (
    discover_plugins,
    get_plugin_info,
    load_plugin,
)
from aegistwin.plugins.registry import PluginRegistry

__all__ = [
    # Base classes
    "AegisTwinPlugin",
    "ConnectorPlugin",
    "AnalyzerPlugin",
    "PolicyPlugin",
    "PluginInfo",
    # Registry
    "PluginRegistry",
    # Loader
    "discover_plugins",
    "load_plugin",
    "get_plugin_info",
]
