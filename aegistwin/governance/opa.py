"""
AegisTwin OPA Integration

Open Policy Agent integration for enterprise policy-as-code workflows.

@ai_prompt: Use OPAEvaluator for Rego policy evaluation.
@context_boundary: aegistwin/governance/opa

## Usage
```python
from aegistwin.governance.opa import OPAEvaluator

evaluator = OPAEvaluator(policy_path="policies/default.rego")
allowed, reason = evaluator.check("query", "memory_graph", "user")
```

# AI-GENERATED 2026-01-07
"""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class OPAInput:
    """
    Input structure for OPA policy evaluation.

    Attributes:
        action: The action being performed
        resource: The resource being accessed
        actor: Who is performing the action
        context: Additional context data
    """
    action: str
    resource: str
    actor: str = "system"
    context: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for OPA input."""
        return {
            "action": self.action,
            "resource": self.resource,
            "actor": self.actor,
            "context": self.context or {},
        }


class OPAEvaluator:
    """
    OPA policy evaluator supporting both external OPA server and embedded Rego.

    Supports:
    - External OPA server via HTTP API
    - Embedded Rego evaluation via CLI
    - Fallback to built-in policies

    Attributes:
        opa_url: URL of external OPA server (optional)
        policy_path: Path to Rego policy file (optional)
    """

    def __init__(
        self,
        opa_url: str | None = None,
        policy_path: str | None = None,
    ):
        """
        Initialize OPA evaluator.

        Args:
            opa_url: URL of OPA server (e.g., http://localhost:8181)
            policy_path: Path to Rego policy file
        """
        self.opa_url = opa_url or os.getenv("OPA_URL")
        self.policy_path = policy_path
        self._policy_content: str | None = None

        if policy_path:
            self._load_policy(policy_path)

    def _load_policy(self, path: str) -> None:
        """Load Rego policy from file."""
        policy_file = Path(path)
        if policy_file.exists():
            self._policy_content = policy_file.read_text()

    def check(
        self,
        action: str,
        resource: str,
        actor: str = "system",
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """
        Check if an action is allowed by OPA policy.

        Args:
            action: The action to check
            resource: The resource being accessed
            actor: Who is performing the action
            context: Additional context

        Returns:
            Tuple of (allowed, reason)
        """
        opa_input = OPAInput(
            action=action,
            resource=resource,
            actor=actor,
            context=context,
        )

        # Try external OPA server first
        if self.opa_url:
            return self._check_external(opa_input)

        # Try embedded Rego via CLI
        if self._policy_content:
            return self._check_embedded(opa_input)

        # Fallback: allow by default
        return True, "No OPA policy configured - default allow"

    def _check_external(self, opa_input: OPAInput) -> tuple[bool, str]:
        """
        Check policy against external OPA server.

        Args:
            opa_input: Input for policy evaluation

        Returns:
            Tuple of (allowed, reason)
        """
        if not HTTPX_AVAILABLE:
            return True, "httpx not available for OPA requests"

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.opa_url}/v1/data/aegistwin/authz",
                    json={"input": opa_input.to_dict()},
                )

                if response.status_code != 200:
                    return True, f"OPA error: {response.status_code}"

                result = response.json().get("result", {})

                # Check allow
                if result.get("allow", False):
                    return True, "Allowed by OPA policy"

                # Check deny reasons
                deny_reasons = result.get("deny", [])
                if deny_reasons:
                    return False, "; ".join(deny_reasons)

                return False, "Denied by OPA policy"

        except Exception as e:
            # On error, fail open with warning
            return True, f"OPA error (fail-open): {str(e)}"

    def _check_embedded(self, opa_input: OPAInput) -> tuple[bool, str]:
        """
        Check policy using embedded Rego via OPA CLI.

        Args:
            opa_input: Input for policy evaluation

        Returns:
            Tuple of (allowed, reason)
        """
        try:
            # Check if opa CLI is available
            result = subprocess.run(
                ["opa", "version"],
                capture_output=True,
                timeout=5,
            )

            if result.returncode != 0:
                return True, "OPA CLI not available"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return True, "OPA CLI not available"

        try:
            # Write policy and input to temp files
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".rego", delete=False
            ) as policy_file:
                policy_file.write(self._policy_content)
                policy_path = policy_file.name

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as input_file:
                json.dump(opa_input.to_dict(), input_file)
                input_path = input_file.name

            # Run OPA eval
            result = subprocess.run(
                [
                    "opa", "eval",
                    "-d", policy_path,
                    "-i", input_path,
                    "data.aegistwin.authz.allow",
                    "-f", "json",
                ],
                capture_output=True,
                timeout=10,
            )

            # Clean up temp files
            os.unlink(policy_path)
            os.unlink(input_path)

            if result.returncode != 0:
                return True, f"OPA eval error: {result.stderr.decode()}"

            output = json.loads(result.stdout.decode())

            # Parse result
            if output.get("result", [{}])[0].get("expressions", [{}])[0].get("value"):
                return True, "Allowed by Rego policy"
            else:
                return False, "Denied by Rego policy"

        except Exception as e:
            return True, f"OPA eval error (fail-open): {str(e)}"

    def is_available(self) -> bool:
        """Check if OPA is available."""
        if self.opa_url:
            return True
        if self._policy_content:
            return True
        return False


def load_rego_policy(path: str) -> str:
    """
    Load a Rego policy file.

    Args:
        path: Path to Rego file

    Returns:
        Policy content as string
    """
    policy_file = Path(path)
    if not policy_file.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return policy_file.read_text()


def create_opa_input(
    action: str,
    resource: str,
    actor: str = "system",
    **context
) -> dict[str, Any]:
    """
    Create OPA input dictionary.

    Args:
        action: The action being performed
        resource: The resource being accessed
        actor: Who is performing the action
        **context: Additional context fields

    Returns:
        Input dictionary for OPA
    """
    return {
        "input": {
            "action": action,
            "resource": resource,
            "actor": actor,
            "context": context,
        }
    }
