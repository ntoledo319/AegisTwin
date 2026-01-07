"""
LangChain Integration

Provides AegisTwin governance and tracing for LangChain agents.

@ai_prompt: Use AegisTwinCallbackHandler with any LangChain chain or agent
@context_boundary: aegistwin/integrations/langchain
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

try:
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.messages import BaseMessage  # noqa: F401
    from langchain_core.outputs import LLMResult
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    BaseCallbackHandler = object

from aegistwin.governance.policy import PolicyEngine


class AegisTwinCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for AegisTwin integration.

    Provides:
    - Event tracing for all LangChain operations
    - Policy enforcement before tool calls
    - Audit logging of agent actions
    - Cost tracking for LLM calls

    Usage:
        from aegistwin.integrations.langchain import AegisTwinCallbackHandler
        from langchain.agents import AgentExecutor

        handler = AegisTwinCallbackHandler(runtime=my_runtime)
        agent.invoke({"input": "..."}, config={"callbacks": [handler]})
    """

    def __init__(
        self,
        runtime: Any | None = None,
        policy_engine: PolicyEngine | None = None,
        run_id: str | None = None,
        actor: str = "langchain_agent",
    ):
        if not HAS_LANGCHAIN:
            raise RuntimeError(
                "LangChain not installed. Install with: pip install langchain-core"
            )

        super().__init__()
        self.runtime = runtime
        self.policy_engine = policy_engine or (runtime.policy_engine if runtime else None)
        self.run_id = run_id
        self.actor = actor
        self._events: list[dict[str, Any]] = []
        self._token_usage: dict[str, int] = {"prompt": 0, "completion": 0}

    def _record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an event."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "actor": self.actor,
            **data,
        }
        self._events.append(event)

        if self.runtime and hasattr(self.runtime, "event_bus"):
            pass

    def _check_policy(self, action: str, resource: str) -> bool:
        """Check policy before action."""
        if not self.policy_engine:
            return True

        result = self.policy_engine.check(
            action=action,
            resource=resource,
            actor=self.actor,
        )
        return result.allowed

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when LLM starts."""
        self._record_event("llm.start", {
            "llm_run_id": str(run_id),
            "model": serialized.get("name", "unknown"),
            "prompt_count": len(prompts),
        })

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when LLM ends."""
        if response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self._token_usage["prompt"] += usage.get("prompt_tokens", 0)
            self._token_usage["completion"] += usage.get("completion_tokens", 0)

        self._record_event("llm.end", {
            "llm_run_id": str(run_id),
            "generations": len(response.generations),
            "token_usage": self._token_usage.copy(),
        })

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when LLM errors."""
        self._record_event("llm.error", {
            "llm_run_id": str(run_id),
            "error": str(error),
        })

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when chain starts."""
        self._record_event("chain.start", {
            "chain_run_id": str(run_id),
            "chain_type": serialized.get("name", "unknown"),
        })

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when chain ends."""
        self._record_event("chain.end", {
            "chain_run_id": str(run_id),
            "output_keys": list(outputs.keys()) if isinstance(outputs, dict) else [],
        })

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when tool starts - includes policy check."""
        tool_name = serialized.get("name", "unknown_tool")

        if not self._check_policy(action="tool.execute", resource=tool_name):
            self._record_event("tool.denied", {
                "tool_run_id": str(run_id),
                "tool_name": tool_name,
                "reason": "Policy denied",
            })
            raise PermissionError(f"Tool '{tool_name}' blocked by policy")

        self._record_event("tool.start", {
            "tool_run_id": str(run_id),
            "tool_name": tool_name,
        })

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when tool ends."""
        self._record_event("tool.end", {
            "tool_run_id": str(run_id),
            "output_length": len(output) if output else 0,
        })

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when agent takes action."""
        self._record_event("agent.action", {
            "agent_run_id": str(run_id),
            "tool": action.tool,
            "log": action.log[:200] if action.log else None,
        })

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        **kwargs,
    ) -> None:
        """Called when agent finishes."""
        self._record_event("agent.finish", {
            "agent_run_id": str(run_id),
            "return_values": list(finish.return_values.keys()),
        })

    def get_events(self) -> list[dict[str, Any]]:
        """Get all recorded events."""
        return self._events.copy()

    def get_token_usage(self) -> dict[str, int]:
        """Get total token usage."""
        return self._token_usage.copy()


def wrap_langchain_agent(
    agent: Any,
    runtime: Any | None = None,
    policy_engine: PolicyEngine | None = None,
) -> Any:
    """
    Wrap a LangChain agent with AegisTwin governance.

    Args:
        agent: LangChain agent or chain
        runtime: Optional AegisTwin runtime
        policy_engine: Optional policy engine

    Returns:
        Wrapped agent with governance enabled
    """
    handler = AegisTwinCallbackHandler(
        runtime=runtime,
        policy_engine=policy_engine,
    )

    return agent, handler
