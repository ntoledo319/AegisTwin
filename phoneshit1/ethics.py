"""
Ethics and safety layer for the relationship analysis system.

This module is intentionally simple and transparent. It provides:
- A small, configurable set of heuristics to assess ethical risk for
  analyzing a given contact.
- A consent handshake for CLI entrypoints so users explicitly agree
  to use the system for self-reflection, not harm.

The goal is not perfect enforcement, but to make everyday misuse
harder and to keep the primary use-case pointed at self-awareness.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional


def _project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


DEFAULT_CONFIG: Dict[str, Any] = {
    "min_total_messages_for_analysis": 50,
    "max_recent_days_full_detail": 365,
    "one_sided_threshold_pct": 85.0,
    "high_breakup_keyword_threshold": 100,
    "high_conflict_keyword_threshold": 200,
    "limited_detail_risk_threshold": 40,
    "block_detail_risk_threshold": 75,
}


def load_ethics_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load ethics configuration from JSON, with sane defaults."""
    if path is None:
        path = os.path.join(_project_root(), "ethics_config.json")

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update({k: v for k, v in data.items() if k in cfg})
            return cfg
        except Exception:
            # Fall back to defaults on any parse error
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


@dataclass
class ContactEthicsAssessment:
    contact: str
    risk_score: float
    risk_level: str
    detail_level: str  # "full", "limited", "blocked"
    reasons: list

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _risk_level(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 40:
        return "MODERATE"
    return "LOW"


def assess_contact_from_deep_analysis(
    contact_name: str,
    deep_analyses: Dict[str, Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Assess ethical risk for analyzing a contact using deep analysis data.

    Heuristics (tunable via config):
    - Very one-sided communication patterns
    - Very old / ended relationships being re-analyzed
    - Extremely high breakup/conflict keyword counts
    """
    if config is None:
        config = load_ethics_config()

    analysis = deep_analyses.get(contact_name)
    if not analysis:
        assessment = ContactEthicsAssessment(
            contact=contact_name,
            risk_score=0.0,
            risk_level="LOW",
            detail_level="full",
            reasons=["no_deep_analysis_available"],
        )
        return assessment.to_dict()

    reasons = []
    risk = 0.0

    total_messages = float(analysis.get("total_messages", 0))
    days_since = float(analysis.get("days_since_last", 9999))
    balance_pct = float(analysis.get("balance", 50.0))
    status = str(analysis.get("status", "")).upper()
    emotional = analysis.get("emotional_keywords", {}) or {}
    breakup = float(emotional.get("breakup", 0))
    conflict = float(emotional.get("conflict", 0))

    # Very small conversations: low risk but low insight; keep full detail but log.
    if total_messages < config["min_total_messages_for_analysis"]:
        reasons.append("very_few_messages")

    # One-sided patterns
    if balance_pct >= config["one_sided_threshold_pct"]:
        risk += 20
        reasons.append("highly_one_sided_outgoing")
    elif balance_pct <= (100.0 - config["one_sided_threshold_pct"]):
        risk += 20
        reasons.append("highly_one_sided_incoming")

    # Very old / ended relationships
    if days_since > config["max_recent_days_full_detail"]:
        risk += 10
        reasons.append("very_old_relationship")

    if "ENDED" in status or "INACTIVE" in status:
        risk += 10
        reasons.append("ended_relationship")

    # High breakup / conflict content
    if breakup >= config["high_breakup_keyword_threshold"]:
        risk += 30
        reasons.append("high_breakup_content")

    if conflict >= config["high_conflict_keyword_threshold"]:
        risk += 30
        reasons.append("high_conflict_content")

    # Clamp to [0, 100]
    risk = max(0.0, min(100.0, risk))

    if risk >= config["block_detail_risk_threshold"]:
        detail_level = "blocked"
    elif risk >= config["limited_detail_risk_threshold"]:
        detail_level = "limited"
    else:
        detail_level = "full"

    assessment = ContactEthicsAssessment(
        contact=contact_name,
        risk_score=round(risk, 1),
        risk_level=_risk_level(risk),
        detail_level=detail_level,
        reasons=reasons,
    )
    return assessment.to_dict()


def ensure_user_consent() -> None:
    """
    Ensure the user has acknowledged the ethical terms in CLI mode.

    - If ETHICS_AUTO_ACCEPT=1 is set, consent is assumed (for automation/testing).
    - Otherwise, the first CLI run writes a small marker file after explicit consent.
    """
    if os.environ.get("ETHICS_AUTO_ACCEPT") == "1":
        return

    marker_path = os.path.join(_project_root(), ".ethics_consent")
    if os.path.exists(marker_path):
        return

    message = """
Before running this analysis, please acknowledge the intended use:

- This tool is for self-reflection and understanding your own patterns.
- It must not be used for stalking, harassment, retaliation, or coercive control.
- Analyses are about your behavior and patterns, not about diagnosing or punishing others.

Type YES to confirm you will use this tool responsibly: """

    try:
        response = input(message)
    except EOFError:
        # Non-interactive environment: fail closed
        raise SystemExit(
            "Ethics consent could not be obtained (non-interactive environment). "
            "Set ETHICS_AUTO_ACCEPT=1 only for automated, responsible usage."
        )

    if response.strip().upper() != "YES":
        raise SystemExit(
            "Consent not confirmed. Aborting analysis. "
            "If you change your mind, re-run and type YES."
        )

    with open(marker_path, "w") as f:
        f.write(
            json.dumps(
                {
                    "consented_at": datetime.now().isoformat(),
                    "version": 1,
                }
            )
        )
