"""
AegisTwin Plugin Loader

Discovery and loading of plugins via entry points.

@ai_prompt: Use discover_plugins() to find installed plugins.
@context_boundary: aegistwin/plugins/loader

# AI-GENERATED 2026-01-07
"""

import importlib
import importlib.metadata
import logging
import sys
from pathlib import Path
from typing import Any

from aegistwin.plugins.base import AegisTwinPlugin, PluginInfo

logger = logging.getLogger(__name__)

# Entry point group name for AegisTwin plugins
ENTRY_POINT_GROUP = "aegistwin.plugins"


def discover_plugins() -> list[AegisTwinPlugin]:
    """
    Discover installed plugins via entry points.

    Looks for plugins registered under the 'aegistwin.plugins' entry point group.

    Returns:
        List of discovered plugin instances
    """
    plugins = []

    try:
        eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)

        for ep in eps:
            try:
                plugin_class = ep.load()

                # Instantiate plugin
                if isinstance(plugin_class, type):
                    plugin = plugin_class()
                else:
                    plugin = plugin_class

                plugins.append(plugin)

            except Exception as e:
                logger.warning("Failed to load plugin %s: %s", ep.name, e)

    except Exception as e:
        logger.warning("Plugin discovery failed: %s", e)

    return plugins


def load_plugin(path: str) -> AegisTwinPlugin | None:
    """
    Load a plugin from a file path.

    Args:
        path: Path to Python file containing plugin class

    Returns:
        Plugin instance or None if loading failed
    """
    plugin_path = Path(path)

    if not plugin_path.exists():
        raise FileNotFoundError(f"Plugin file not found: {path}")

    if not plugin_path.suffix == ".py":
        raise ValueError(f"Plugin file must be a .py file: {path}")

    try:
        # Add parent directory to path
        sys.path.insert(0, str(plugin_path.parent))

        # Import module
        module_name = plugin_path.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if (isinstance(attr, type) and
                hasattr(attr, 'name') and
                hasattr(attr, 'version') and
                hasattr(attr, 'register') and
                hasattr(attr, 'unregister') and
                attr_name != 'BasePlugin'):

                return attr()

        raise ValueError(f"No plugin class found in {path}")

    except Exception as e:
        raise ImportError(f"Failed to load plugin from {path}: {e}") from e

    finally:
        # Remove from path
        if str(plugin_path.parent) in sys.path:
            sys.path.remove(str(plugin_path.parent))


def load_plugin_class(module_path: str, class_name: str) -> type[AegisTwinPlugin]:
    """
    Load a plugin class from a module path.

    Args:
        module_path: Python module path (e.g., 'mypackage.plugins.my_plugin')
        class_name: Name of the plugin class

    Returns:
        Plugin class (not instantiated)
    """
    try:
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)

        return plugin_class

    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to load plugin class: {e}") from e


def get_plugin_info(plugin: AegisTwinPlugin) -> PluginInfo:
    """
    Get information about a plugin.

    Args:
        plugin: Plugin instance

    Returns:
        PluginInfo with plugin details
    """
    description = ""
    if hasattr(plugin, 'description'):
        description = plugin.description
    elif hasattr(plugin, '__doc__') and plugin.__doc__:
        description = plugin.__doc__.strip().split('\n')[0]

    return PluginInfo(
        name=plugin.name,
        version=plugin.version,
        description=description,
    )


def list_available_plugins() -> list[dict[str, str]]:
    """
    List available plugins from entry points without loading them.

    Returns:
        List of dicts with plugin entry point info
    """
    available = []

    try:
        eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)

        for ep in eps:
            available.append({
                "name": ep.name,
                "value": ep.value,
                "group": ep.group,
            })

    except Exception:
        pass

    return available


def validate_plugin(plugin: Any) -> bool:
    """
    Validate that an object is a valid plugin.

    Args:
        plugin: Object to validate

    Returns:
        True if valid plugin
    """
    required_attrs = ['name', 'version', 'register', 'unregister']

    for attr in required_attrs:
        if not hasattr(plugin, attr):
            return False

    if not callable(getattr(plugin, 'register', None)):
        return False

    if not callable(getattr(plugin, 'unregister', None)):
        return False

    return True
