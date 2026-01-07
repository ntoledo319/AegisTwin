"""
AegisTwin Plugin Base Classes

Protocol definitions for plugin interfaces.

@ai_prompt: Inherit from AegisTwinPlugin or specific plugin types.
@context_boundary: aegistwin/plugins/base

# AI-GENERATED 2026-01-07
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class PluginInfo:
    """
    Metadata about a plugin.

    Attributes:
        name: Plugin name
        version: Plugin version string
        description: Plugin description
        author: Plugin author
        dependencies: List of required dependencies
        entry_point: Entry point for loading
    """
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
        }


@runtime_checkable
class AegisTwinPlugin(Protocol):
    """
    Protocol for AegisTwin plugins.

    All plugins must implement this protocol.

    Attributes:
        name: Plugin name
        version: Plugin version

    ## Non-Negotiables
    - Plugins must not access restricted resources
    - Plugins must handle errors gracefully
    - Plugins must be unloadable without side effects
    """

    name: str
    version: str

    def register(self, runtime: Any) -> None:
        """
        Register the plugin with a runtime.

        Args:
            runtime: AegisTwinRuntime instance
        """
        ...

    def unregister(self, runtime: Any) -> None:
        """
        Unregister the plugin from a runtime.

        Args:
            runtime: AegisTwinRuntime instance
        """
        ...


class BasePlugin(ABC):
    """
    Abstract base class for plugins.

    Provides default implementations for common functionality.
    """

    name: str = "base-plugin"
    version: str = "0.0.0"
    description: str = ""

    def __init__(self):
        self._registered = False
        self._runtime = None

    @abstractmethod
    def register(self, runtime: Any) -> None:
        """Register the plugin with a runtime."""
        self._runtime = runtime
        self._registered = True

    @abstractmethod
    def unregister(self, runtime: Any) -> None:
        """Unregister the plugin from a runtime."""
        self._runtime = None
        self._registered = False

    @property
    def is_registered(self) -> bool:
        """Check if plugin is registered."""
        return self._registered

    def get_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
        )


class ConnectorPlugin(BasePlugin):
    """
    Base class for connector plugins.

    Connectors handle data ingestion from external sources.

    ## Affected Components
    - aegistwin.runtime.core (EventBus subscription)
    - aegistwin.events.schema (IngestRequested events)
    """

    source_type: str = "generic"

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to data source.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from data source."""
        pass

    @abstractmethod
    def fetch(self, **kwargs) -> dict[str, Any]:
        """
        Fetch data from source.

        Args:
            **kwargs: Source-specific parameters

        Returns:
            Fetched data dictionary
        """
        pass

    def register(self, runtime: Any) -> None:
        """Register connector with runtime."""
        super().register(runtime)
        # Subclasses can add event subscriptions here

    def unregister(self, runtime: Any) -> None:
        """Unregister connector from runtime."""
        self.disconnect()
        super().unregister(runtime)


class AnalyzerPlugin(BasePlugin):
    """
    Base class for analyzer plugins.

    Analyzers process data and extract insights.

    ## Affected Components
    - aegistwin.runtime.core (EventBus subscription)
    - aegistwin.events.schema (AnalysisCompleted events)
    """

    analysis_type: str = "generic"

    @abstractmethod
    def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze data and return results.

        Args:
            data: Data to analyze

        Returns:
            Analysis results
        """
        pass

    def register(self, runtime: Any) -> None:
        """Register analyzer with runtime."""
        super().register(runtime)

    def unregister(self, runtime: Any) -> None:
        """Unregister analyzer from runtime."""
        super().unregister(runtime)


class PolicyPlugin(BasePlugin):
    """
    Base class for policy plugins.

    Policy plugins add custom authorization rules.

    ## Affected Components
    - aegistwin.governance.policy (PolicyEngine)
    """

    @abstractmethod
    def get_policies(self) -> list[Any]:
        """
        Get list of policies to add.

        Returns:
            List of Policy objects
        """
        pass

    def register(self, runtime: Any) -> None:
        """Register policies with runtime."""
        super().register(runtime)

        if hasattr(runtime, 'policy_engine'):
            for policy in self.get_policies():
                runtime.policy_engine.add_policy(policy)

    def unregister(self, runtime: Any) -> None:
        """Unregister policies from runtime."""
        if hasattr(runtime, 'policy_engine'):
            for policy in self.get_policies():
                runtime.policy_engine.remove_policy(policy.id)

        super().unregister(runtime)
