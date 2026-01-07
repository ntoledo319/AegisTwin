"""
CrewAI Integration

Provides AegisTwin governance for CrewAI multi-agent systems.

@ai_prompt: Use AegisTwinCrewObserver with CrewAI crews
@context_boundary: aegistwin/integrations/crewai
"""

from datetime import datetime, timezone
from typing import Any

from aegistwin.governance.policy import PolicyEngine


class AegisTwinCrewObserver:
    """
    Observer for CrewAI crews with AegisTwin integration.

    Provides:
    - Agent action monitoring
    - Task execution tracing
    - Inter-agent communication logging
    - Policy enforcement for agent actions

    Usage:
        from crewai import Crew
        from aegistwin.integrations.crewai import AegisTwinCrewObserver

        observer = AegisTwinCrewObserver(runtime=my_runtime)
        crew = Crew(agents=[...], tasks=[...])
        observer.attach(crew)
        crew.kickoff()
    """

    def __init__(
        self,
        runtime: Any | None = None,
        policy_engine: PolicyEngine | None = None,
    ):
        self.runtime = runtime
        self.policy_engine = policy_engine or (runtime.policy_engine if runtime else None)
        self._events: list[dict[str, Any]] = []
        self._crew = None

    def attach(self, crew: Any) -> None:
        """Attach observer to a crew."""
        self._crew = crew

    def on_task_start(self, task: Any, agent: Any) -> None:
        """Called when a task starts."""
        self._record_event("task.start", {
            "task_id": getattr(task, "id", str(id(task))),
            "task_description": getattr(task, "description", "")[:100],
            "agent_role": getattr(agent, "role", "unknown"),
        })

    def on_task_end(self, task: Any, output: Any) -> None:
        """Called when a task ends."""
        self._record_event("task.end", {
            "task_id": getattr(task, "id", str(id(task))),
            "output_length": len(str(output)) if output else 0,
        })

    def on_agent_action(self, agent: Any, action: str, tool: str | None = None) -> bool:
        """Called before agent action - returns False to block."""
        if self.policy_engine:
            result = self.policy_engine.check(
                action=action,
                resource=tool or "agent_action",
                actor=f"agent:{getattr(agent, 'role', 'unknown')}",
            )
            if not result.allowed:
                self._record_event("agent.blocked", {
                    "agent_role": getattr(agent, "role", "unknown"),
                    "action": action,
                    "reason": result.reason,
                })
                return False

        self._record_event("agent.action", {
            "agent_role": getattr(agent, "role", "unknown"),
            "action": action,
            "tool": tool,
        })
        return True

    def on_delegation(self, from_agent: Any, to_agent: Any, task: Any) -> None:
        """Called when task is delegated between agents."""
        self._record_event("delegation", {
            "from_agent": getattr(from_agent, "role", "unknown"),
            "to_agent": getattr(to_agent, "role", "unknown"),
            "task": getattr(task, "description", "")[:100],
        })

    def _record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an event."""
        event = {
            "event_type": f"crewai.{event_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        self._events.append(event)

    def get_events(self) -> list[dict[str, Any]]:
        """Get all recorded events."""
        return self._events.copy()
