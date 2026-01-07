"""
AegisTwin Custom Plugin Example

Demonstrates creating and registering a custom plugin.

Usage:
    python examples/08_custom_plugin.py

@ai_prompt: Shows how to create custom analyzer and connector plugins.
@context_boundary: examples/08_custom_plugin

# AI-GENERATED 2026-01-07
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegistwin import AegisTwinRuntime
from aegistwin.plugins import PluginRegistry, discover_plugins
from aegistwin.plugins.base import AnalyzerPlugin, ConnectorPlugin
from aegistwin.events.schema import EventType


class SentimentAnalyzerPlugin(AnalyzerPlugin):
    """
    Example analyzer plugin that performs sentiment analysis.
    """
    
    name = "sentiment-analyzer"
    version = "1.0.0"
    description = "Analyzes text sentiment"
    analysis_type = "sentiment"
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of text data.
        
        Args:
            data: Data containing 'text' field
            
        Returns:
            Sentiment analysis results
        """
        text = data.get("text", "")
        
        # Simple mock sentiment analysis
        positive_words = ["good", "great", "excellent", "happy", "love"]
        negative_words = ["bad", "terrible", "awful", "sad", "hate"]
        
        text_lower = text.lower()
        positive_count = sum(1 for w in positive_words if w in text_lower)
        negative_count = sum(1 for w in negative_words if w in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = 0.7 + (positive_count * 0.05)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = 0.7 + (negative_count * 0.05)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": min(confidence, 1.0),
            "positive_signals": positive_count,
            "negative_signals": negative_count,
        }
    
    def register(self, runtime: Any) -> None:
        """Register analyzer with runtime."""
        super().register(runtime)
        print(f"  ✓ {self.name} registered")
    
    def unregister(self, runtime: Any) -> None:
        """Unregister analyzer from runtime."""
        super().unregister(runtime)
        print(f"  ✓ {self.name} unregistered")


class MockDataConnectorPlugin(ConnectorPlugin):
    """
    Example connector plugin for mock data source.
    """
    
    name = "mock-data-connector"
    version = "1.0.0"
    description = "Connects to mock data source"
    source_type = "mock"
    
    def __init__(self):
        super().__init__()
        self._connected = False
        self._data_counter = 0
    
    def connect(self) -> bool:
        """Establish connection to mock source."""
        print("  📡 Connecting to mock data source...")
        self._connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from mock source."""
        print("  📡 Disconnecting from mock data source...")
        self._connected = False
    
    def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch mock data."""
        if not self._connected:
            raise RuntimeError("Not connected")
        
        self._data_counter += 1
        count = kwargs.get("count", 5)
        
        return {
            "records": [
                {
                    "id": f"mock-{self._data_counter}-{i}",
                    "type": "mock",
                    "value": f"Mock data item {i}",
                }
                for i in range(count)
            ],
            "source": "mock-connector",
            "batch": self._data_counter,
        }
    
    def register(self, runtime: Any) -> None:
        """Register connector with runtime."""
        super().register(runtime)
        self.connect()
        print(f"  ✓ {self.name} registered and connected")
    
    def unregister(self, runtime: Any) -> None:
        """Unregister connector from runtime."""
        super().unregister(runtime)
        print(f"  ✓ {self.name} unregistered and disconnected")


def demo_plugin_registration():
    """Demonstrate plugin registration."""
    print("=" * 50)
    print("Demo 1: Plugin Registration")
    print("=" * 50)
    
    # Create runtime and registry
    runtime = AegisTwinRuntime()
    registry = PluginRegistry(runtime)
    
    # Create plugins
    analyzer = SentimentAnalyzerPlugin()
    connector = MockDataConnectorPlugin()
    
    print("\n📦 Registering plugins...")
    registry.register(analyzer)
    registry.register(connector)
    
    print(f"\n📋 Registered plugins: {registry.count}")
    for info in registry.list_plugins():
        print(f"   - {info.name} v{info.version}")
    
    return runtime, registry


def demo_plugin_usage(runtime: AegisTwinRuntime, registry: PluginRegistry):
    """Demonstrate using registered plugins."""
    print("\n" + "=" * 50)
    print("Demo 2: Plugin Usage")
    print("=" * 50)
    
    # Get analyzer plugin
    analyzer = registry.get("sentiment-analyzer")
    
    # Analyze some text
    texts = [
        "This is a great product, I love it!",
        "Terrible experience, very bad service.",
        "The weather is okay today.",
    ]
    
    print("\n🔍 Sentiment Analysis Results:")
    for text in texts:
        result = analyzer.analyze({"text": text})
        print(f"\n   Text: {text[:40]}...")
        print(f"   Sentiment: {result['sentiment']} ({result['confidence']:.0%})")
    
    # Get connector plugin
    connector = registry.get("mock-data-connector")
    
    # Fetch data
    print("\n📥 Fetching data from connector...")
    data = connector.fetch(count=3)
    print(f"   Fetched {len(data['records'])} records from batch {data['batch']}")


def demo_plugin_discovery():
    """Demonstrate plugin discovery."""
    print("\n" + "=" * 50)
    print("Demo 3: Plugin Discovery")
    print("=" * 50)
    
    print("\n🔍 Discovering installed plugins...")
    plugins = discover_plugins()
    
    if plugins:
        print(f"   Found {len(plugins)} plugins:")
        for plugin in plugins:
            print(f"   - {plugin.name} v{plugin.version}")
    else:
        print("   No plugins discovered via entry points.")
        print("   (Install plugins to see them here)")


def demo_plugin_cleanup(registry: PluginRegistry):
    """Demonstrate plugin cleanup."""
    print("\n" + "=" * 50)
    print("Demo 4: Plugin Cleanup")
    print("=" * 50)
    
    print("\n🧹 Unregistering plugins...")
    registry.clear()
    
    print(f"   Remaining plugins: {registry.count}")


def main():
    """Main entry point."""
    print("\n🔌 AegisTwin Plugin System Example\n")
    
    runtime, registry = demo_plugin_registration()
    demo_plugin_usage(runtime, registry)
    demo_plugin_discovery()
    demo_plugin_cleanup(registry)
    
    print("\n" + "=" * 50)
    print("✅ Plugin Example Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
