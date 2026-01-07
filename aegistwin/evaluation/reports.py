"""
Evaluation Report Generator

Generates reports from evaluation results.

@ai_prompt: Use ReportGenerator to create Markdown or JSON reports
@context_boundary: aegistwin/evaluation/reports
"""

import json
from datetime import datetime
from pathlib import Path

from aegistwin.evaluation.harness import EvaluationResult, EvaluationStatus


class ReportGenerator:
    """
    Generates evaluation reports in various formats.

    Supported formats:
    - Markdown
    - JSON
    - HTML (future)
    """

    def __init__(self, result: EvaluationResult):
        self.result = result

    def to_markdown(self) -> str:
        """Generate Markdown report."""
        r = self.result

        lines = [
            f"# Evaluation Report: {r.benchmark_id}",
            "",
            f"**Evaluation ID:** {r.evaluation_id}",
            f"**Agent ID:** {r.agent_id}",
            f"**Started:** {r.started_at.isoformat()}",
            f"**Completed:** {r.completed_at.isoformat()}",
            f"**Duration:** {(r.completed_at - r.started_at).total_seconds():.2f}s",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Tests | {r.total_tests} |",
            f"| Passed | {r.passed_tests} |",
            f"| Failed | {r.failed_tests} |",
            f"| Errors | {r.error_tests} |",
            f"| Skipped | {r.skipped_tests} |",
            f"| **Pass Rate** | **{r.pass_rate:.1f}%** |",
            "",
            "## Test Results",
            "",
        ]

        for status in EvaluationStatus:
            tests = [t for t in r.test_results if t.status == status]
            if not tests:
                continue

            status_emoji = {
                EvaluationStatus.PASSED: "✅",
                EvaluationStatus.FAILED: "❌",
                EvaluationStatus.ERROR: "⚠️",
                EvaluationStatus.SKIPPED: "⏭️",
            }.get(status, "•")

            lines.append(f"### {status_emoji} {status.value.title()} ({len(tests)})")
            lines.append("")

            for test in tests:
                lines.append(f"- **{test.test_id}** ({test.duration_ms:.1f}ms)")
                if test.error_message:
                    lines.append(f"  - Error: {test.error_message}")

            lines.append("")

        if r.aggregate_metrics:
            lines.append("## Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for name, value in sorted(r.aggregate_metrics.items()):
                lines.append(f"| {name} | {value:.3f} |")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated: {datetime.now().isoformat()}*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON report."""
        return json.dumps({
            "evaluation_id": self.result.evaluation_id,
            "agent_id": self.result.agent_id,
            "benchmark_id": self.result.benchmark_id,
            "started_at": self.result.started_at.isoformat(),
            "completed_at": self.result.completed_at.isoformat(),
            "summary": {
                "total": self.result.total_tests,
                "passed": self.result.passed_tests,
                "failed": self.result.failed_tests,
                "errors": self.result.error_tests,
                "skipped": self.result.skipped_tests,
                "pass_rate": self.result.pass_rate,
            },
            "test_results": [
                {
                    "test_id": t.test_id,
                    "status": t.status.value,
                    "duration_ms": t.duration_ms,
                    "error_message": t.error_message,
                }
                for t in self.result.test_results
            ],
            "aggregate_metrics": self.result.aggregate_metrics,
        }, indent=2)

    def save(self, path: Path, format: str = "markdown") -> None:
        """Save report to file."""
        if format == "markdown":
            content = self.to_markdown()
            suffix = ".md"
        elif format == "json":
            content = self.to_json()
            suffix = ".json"
        else:
            raise ValueError(f"Unknown format: {format}")

        output_path = path.with_suffix(suffix) if not str(path).endswith(suffix) else path
        output_path.write_text(content)
