"""
AegisTwin Plugin Registry

Central registry for managing plugins.

@ai_prompt: Use PluginRegistry to register/unregister plugins.
@context_boundary: aegistwin/plugins/registry

# AI-GENERATED 2026-01-07
"""

from typing import Any

from aegistwin.plugins.base import AegisTwinPlugin, PluginInfo


class PluginRegistry:
    """
    Registry for managing AegisTwin plugins.

    Provides:
    - Plugin registration/unregistration
    - Plugin lookup by name
    - Plugin listing

    Attributes:
        _plugins: Dict mapping plugin names to instances
        _runtime: Associated runtime (optional)
    """

    def __init__(self, runtime: Any | None = None):
        """
        Initialize plugin registry.

        Args:
            runtime: Optional runtime to register plugins with
        """
        self._plugins: dict[str, AegisTwinPlugin] = {}
        self._runtime = runtime

    def register(self, plugin: AegisTwinPlugin) -> bool:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Returns:
            True if registered successfully

        Raises:
            ValueError: If plugin with same name already registered
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")

        self._plugins[plugin.name] = plugin

        # Register with runtime if available
        if self._runtime is not None:
            plugin.register(self._runtime)

        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin by name.

        Args:
            name: Name of plugin to unregister

        Returns:
            True if unregistered successfully
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]

        # Unregister from runtime if available
        if self._runtime is not None:
            plugin.unregister(self._runtime)

        del self._plugins[name]
        return True

    def get(self, name: str) -> AegisTwinPlugin | None:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[PluginInfo]:
        """
        List all registered plugins.

        Returns:
            List of PluginInfo for each plugin
        """
        return [
            PluginInfo(name=p.name, version=p.version)
            for p in self._plugins.values()
        ]

    def get_all(self) -> list[AegisTwinPlugin]:
        """
        Get all registered plugins.

        Returns:
            List of all plugin instances
        """
        return list(self._plugins.values())

    def set_runtime(self, runtime: Any) -> None:
        """
        Set or update the runtime.

        Args:
            runtime: Runtime instance
        """
        old_runtime = self._runtime
        self._runtime = runtime

        # Re-register all plugins with new runtime
        for plugin in self._plugins.values():
            if old_runtime is not None:
                plugin.unregister(old_runtime)
            plugin.register(runtime)

    def clear(self) -> None:
        """Unregister all plugins."""
        for name in list(self._plugins.keys()):
            self.unregister(name)

    @property
    def count(self) -> int:
        """Number of registered plugins."""
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        """Check if plugin is registered."""
        return name in self._plugins

    def __len__(self) -> int:
        """Number of registered plugins."""
        return len(self._plugins)
