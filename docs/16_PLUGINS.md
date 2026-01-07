# AegisTwin Plugin System

This document describes how to create, distribute, and use plugins with AegisTwin.

## Overview

The plugin system allows extending AegisTwin with:
- **Connectors**: Data ingestion from external sources
- **Analyzers**: Custom data analysis
- **Policies**: Authorization rules

## Quick Start

### Using Plugins

```python
from aegistwin import AegisTwinRuntime
from aegistwin.plugins import PluginRegistry, discover_plugins

# Create runtime and registry
runtime = AegisTwinRuntime()
registry = PluginRegistry(runtime)

# Discover and register plugins
for plugin in discover_plugins():
    registry.register(plugin)

# Use plugins
analyzer = registry.get("my-analyzer")
result = analyzer.analyze({"text": "Hello world"})
```

### Creating a Plugin

```python
from aegistwin.plugins.base import AnalyzerPlugin

class MyAnalyzerPlugin(AnalyzerPlugin):
    name = "my-analyzer"
    version = "1.0.0"
    description = "My custom analyzer"
    
    def analyze(self, data):
        # Your analysis logic
        return {"result": "analyzed"}
```

## Plugin Types

### ConnectorPlugin

For data ingestion from external sources:

```python
from aegistwin.plugins.base import ConnectorPlugin

class MyConnector(ConnectorPlugin):
    name = "my-connector"
    version = "1.0.0"
    source_type = "my-source"
    
    def connect(self) -> bool:
        # Establish connection
        return True
    
    def disconnect(self) -> None:
        # Clean up connection
        pass
    
    def fetch(self, **kwargs) -> dict:
        # Fetch data
        return {"records": [...]}
```

### AnalyzerPlugin

For data analysis:

```python
from aegistwin.plugins.base import AnalyzerPlugin

class MyAnalyzer(AnalyzerPlugin):
    name = "my-analyzer"
    version = "1.0.0"
    analysis_type = "custom"
    
    def analyze(self, data: dict) -> dict:
        # Perform analysis
        return {"insights": [...]}
```

### PolicyPlugin

For authorization rules:

```python
from aegistwin.plugins.base import PolicyPlugin
from aegistwin.governance.policy import Policy, PolicyEffect

class MyPolicies(PolicyPlugin):
    name = "my-policies"
    version = "1.0.0"
    
    def get_policies(self):
        return [
            Policy(
                id="my-custom-policy",
                action="custom_action",
                resource="*",
                effect=PolicyEffect.ALLOW,
                reason="Custom policy",
            ),
        ]
```

## Plugin API

### Required Methods

All plugins must implement:

| Method | Description |
|--------|-------------|
| `register(runtime)` | Called when plugin is registered |
| `unregister(runtime)` | Called when plugin is unregistered |

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Unique plugin name |
| `version` | str | Semantic version |

### Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `description` | str | Plugin description |
| `dependencies` | list | Required packages |

## Distribution

### Via PyPI

1. Create a `pyproject.toml`:

```toml
[project]
name = "aegistwin-my-plugin"
version = "1.0.0"

[project.entry-points."aegistwin.plugins"]
my-plugin = "my_package.plugin:MyPlugin"
```

2. Publish to PyPI:

```bash
pip install build twine
python -m build
twine upload dist/*
```

3. Users install:

```bash
pip install aegistwin-my-plugin
```

### Via Entry Points

Register your plugin in `pyproject.toml`:

```toml
[project.entry-points."aegistwin.plugins"]
my-analyzer = "my_package.analyzers:SentimentAnalyzer"
my-connector = "my_package.connectors:SlackConnector"
```

## Plugin Registry

### Registration

```python
from aegistwin.plugins import PluginRegistry

registry = PluginRegistry(runtime)
registry.register(my_plugin)
```

### Lookup

```python
plugin = registry.get("plugin-name")
plugins = registry.list_plugins()
```

### Unregistration

```python
registry.unregister("plugin-name")
registry.clear()  # Unregister all
```

## Discovery

### Automatic Discovery

```python
from aegistwin.plugins import discover_plugins

plugins = discover_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")
```

### Manual Loading

```python
from aegistwin.plugins import load_plugin

plugin = load_plugin("/path/to/plugin.py")
```

## Best Practices

1. **Version Your Plugins**: Use semantic versioning
2. **Handle Errors Gracefully**: Never crash the runtime
3. **Clean Up Resources**: Properly unregister
4. **Document Your Plugin**: Include docstrings
5. **Test Thoroughly**: Include unit tests
6. **Respect Policies**: Don't bypass security

## Example Plugins

### Sentiment Analyzer

```python
class SentimentPlugin(AnalyzerPlugin):
    name = "sentiment"
    version = "1.0.0"
    
    def analyze(self, data):
        text = data.get("text", "")
        # Simple sentiment logic
        score = 0.5  # neutral
        return {
            "sentiment": "neutral",
            "score": score,
        }
```

### Slack Connector

```python
class SlackConnector(ConnectorPlugin):
    name = "slack"
    version = "1.0.0"
    source_type = "slack"
    
    def __init__(self, token=None):
        super().__init__()
        self.token = token or os.getenv("SLACK_TOKEN")
    
    def connect(self):
        # Initialize Slack client
        return True
    
    def fetch(self, channel=None, limit=100):
        # Fetch messages
        return {"records": [...]}
```

## Troubleshooting

### Plugin Not Found

```
Warning: Failed to load plugin xxx: ModuleNotFoundError
```

**Solution**: Ensure the plugin package is installed.

### Registration Failed

```
ValueError: Plugin 'xxx' already registered
```

**Solution**: Unregister the existing plugin first.

### Import Errors

```
ImportError: Failed to load plugin from /path/to/plugin.py
```

**Solution**: Check for syntax errors and missing dependencies.

---

*Last updated: 2026-01-07*
