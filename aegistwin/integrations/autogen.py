"""
AutoGen Integration

Provides AegisTwin governance for Microsoft AutoGen agents.

@ai_prompt: Use AegisTwinAutoGenMonitor with AutoGen conversations
@context_boundary: aegistwin/integrations/autogen
"""

from datetime import datetime, timezone
from typing import Any

from aegistwin.governance.policy import PolicyEngine


class AegisTwinAutoGenMonitor:
    """
    Monitor for AutoGen conversations with AegisTwin integration.

    Provides:
    - Message tracking between agents
    - Code execution monitoring
    - Policy enforcement for agent actions
    - Conversation state logging

    Usage:
        from autogen import AssistantAgent, UserProxyAgent
        from aegistwin.integrations.autogen import AegisTwinAutoGenMonitor

        monitor = AegisTwinAutoGenMonitor(runtime=my_runtime)

        assistant = AssistantAgent("assistant", ...)
        user_proxy = UserProxyAgent("user", ...)

        monitor.register_agent(assistant)
        monitor.register_agent(user_proxy)

        user_proxy.initiate_chat(assistant, message="...")
    """

    def __init__(
        self,
        runtime: Any | None = None,
        policy_engine: PolicyEngine | None = None,
        block_code_execution: bool = False,
    ):
        self.runtime = runtime
        self.policy_engine = policy_engine or (runtime.policy_engine if runtime else None)
        self.block_code_execution = block_code_execution
        self._events: list[dict[str, Any]] = []
        self._agents: dict[str, Any] = {}
        self._message_count = 0

    def register_agent(self, agent: Any) -> None:
        """Register an agent for monitoring."""
        agent_name = getattr(agent, "name", str(id(agent)))
        self._agents[agent_name] = agent

        original_send = getattr(agent, "send", None)
        if original_send:
            def wrapped_send(message, recipient, *args, **kwargs):
                self._on_message(agent, recipient, message)
                return original_send(message, recipient, *args, **kwargs)
            agent.send = wrapped_send

        self._record_event("agent.registered", {
            "agent_name": agent_name,
            "agent_type": type(agent).__name__,
        })

    def _on_message(self, sender: Any, recipient: Any, message: Any) -> None:
        """Called when a message is sent between agents."""
        self._message_count += 1

        sender_name = getattr(sender, "name", "unknown")
        recipient_name = getattr(recipient, "name", "unknown")

        content = str(message) if not isinstance(message, dict) else message.get("content", "")
        has_code = "```" in content

        if has_code and self.block_code_execution:
            if self.policy_engine:
                result = self.policy_engine.check(
                    action="code.execute",
                    resource="autogen_code",
                    actor=f"agent:{sender_name}",
                )
                if not result.allowed:
                    self._record_event("code.blocked", {
                        "sender": sender_name,
                        "reason": result.reason,
                    })
                    raise PermissionError("Code execution blocked by policy")

        self._record_event("message", {
            "message_id": self._message_count,
            "sender": sender_name,
            "recipient": recipient_name,
            "content_length": len(content),
            "has_code": has_code,
        })

    def _record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an event."""
        event = {
            "event_type": f"autogen.{event_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        self._events.append(event)

    def get_events(self) -> list[dict[str, Any]]:
        """Get all recorded events."""
        return self._events.copy()

    def get_stats(self) -> dict[str, Any]:
        """Get conversation statistics."""
        return {
            "total_messages": self._message_count,
            "registered_agents": list(self._agents.keys()),
            "events_recorded": len(self._events),
        }
