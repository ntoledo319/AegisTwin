"""
AegisTwin Integrations

Adapters for popular AI agent frameworks.
"""

from aegistwin.integrations.autogen import AegisTwinAutoGenMonitor
from aegistwin.integrations.crewai import AegisTwinCrewObserver
from aegistwin.integrations.langchain import AegisTwinCallbackHandler, wrap_langchain_agent

__all__ = [
    "AegisTwinCallbackHandler",
    "wrap_langchain_agent",
    "AegisTwinCrewObserver",
    "AegisTwinAutoGenMonitor",
]
