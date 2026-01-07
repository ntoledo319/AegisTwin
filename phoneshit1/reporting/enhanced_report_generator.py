"""
Enhanced Report Generator
Phase 3A - Advanced Reporting

Generates comprehensive markdown reports for a single contact by
stitching together outputs from the analytics and psychology modules.

This implementation expects JSON outputs produced by:
- analytics/predictive_analysis.py      → outputs/predictions/
- analytics/pattern_detection.py       → outputs/patterns/
- analytics/topic_mining.py            → outputs/topics/
- analytics/sentiment_evolution.py     → outputs/sentiment/
- psychology/attachment_analysis.py    → outputs/attachment/
- psychology/communication_evolution.py→ outputs/communication_evolution/
- psychology/conflict_analysis.py      → outputs/conflict_analysis/
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ethics import ensure_user_consent


class EnhancedReportGenerator:
    """Generates comprehensive reports with all analytical insights."""

    def __init__(self, outputs_base: str = "outputs") -> None:
        self.outputs_base = outputs_base
        # Logical module keys mapped to their output subdirectories
        self.module_config = {
            "predictive": "predictions",
            "patterns": "patterns",
            "topics": "topics",
            "sentiment": "sentiment",
            "attachment": "attachment",
            "communication": "communication_evolution",
            "conflict": "conflict_analysis",
        }
        self.analytics_modules = list(self.module_config.keys())

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #

    def _load_all_analytics(self, contact_name: str) -> dict:
        """Load all analytical outputs for a contact from the outputs/ tree."""
        analytics = {}
        contact_safe = contact_name.replace(" ", "_")

        for module, subdir in self.module_config.items():
            module_dir = os.path.join(self.outputs_base, subdir)
            if not os.path.isdir(module_dir):
                continue

            candidates = [
                f
                for f in os.listdir(module_dir)
                if f.startswith(contact_safe) and f.endswith(".json")
            ]
            if not candidates:
                continue

            # Heuristic: last filename is usually the latest dated export
            filename = sorted(candidates)[-1]
            filepath = os.path.join(module_dir, filename)

            try:
                with open(filepath, "r") as f:
                    analytics[module] = json.load(f)
            except Exception as e:  # pragma: no cover - defensive
                print(f"Warning: Could not load {module} for {contact_name}: {e}")

        return analytics

    # ------------------------------------------------------------------ #
    # Report building
    # ------------------------------------------------------------------ #

    def generate_comprehensive_report(self, contact_name: str) -> str:
        """Generate a comprehensive markdown report for a contact."""
        analytics = self._load_all_analytics(contact_name)

        if not analytics:
            return f"# {contact_name}\n\nNo analytical data available for this contact.\n"

        report = self._build_report_header(contact_name, analytics)
        report += self._build_executive_summary(analytics)
        report += self._build_predictive_section(analytics)
        report += self._build_patterns_section(analytics)
        report += self._build_emotional_section(analytics)
        report += self._build_psychological_section(analytics)
        report += self._build_recommendations(analytics)
        report += self._build_footer()

        return report

    def _build_report_header(self, contact_name: str, analytics: dict) -> str:
        return f"""# 🔬 COMPREHENSIVE RELATIONSHIP ANALYSIS: {contact_name}

**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
**Analysis Type:** PREDICTIVE + PSYCHOLOGICAL + BEHAVIORAL  
**Data Coverage:** {len(analytics)} analytical dimensions  

---

"""

    def _build_executive_summary(self, analytics: dict) -> str:
        summary = "## 📊 EXECUTIVE SUMMARY\n\n"
        key_insights = []

        # Predictive
        pred = analytics.get("predictive")
        if isinstance(pred, dict):
            risk_block = pred.get("breakup_risk_assessment", pred)
            risk_score = risk_block.get("risk_score", "N/A")
            risk_level = risk_block.get("risk_level", "UNKNOWN")
            key_insights.append(
                f"**Relationship Risk:** {risk_score}/100 ({risk_level})"
            )

            trajectory = pred.get("trajectory_forecast", {})
            trend_direction = trajectory.get("trend_direction", "stable")
            key_insights.append(f"**Trajectory Direction:** {trend_direction}")

        # Conflict
        conf = analytics.get("conflict")
        if isinstance(conf, dict):
            profile = conf.get("conflict_profile", "Unknown")
            key_insights.append(f"**Conflict Profile:** {profile}")

        # Attachment
        att = analytics.get("attachment")
        if isinstance(att, dict) and isinstance(att.get("relationship_specific"), dict):
            rel_spec = att["relationship_specific"]
            style = rel_spec.get("your_style_with_them", "Unknown")
            key_insights.append(f"**Your Attachment Style:** {style}")

        # Sentiment
        sent = analytics.get("sentiment")
        if isinstance(sent, dict):
            progression = sent.get("sentiment_progression", {})
            overall = progression.get("overall_sentiment", {})
            if overall:
                score = overall.get("mean", 0.0)
                vol_block = sent.get("emotional_volatility", {})
                volatility = vol_block.get("volatility_score", 0.0)
                key_insights.append(
                    f"**Sentiment Score:** {score:.2f} (Volatility: {volatility}/100)"
                )

        for insight in key_insights:
            summary += f"- {insight}\n"

        summary += "\n---\n\n"
        return summary

    def _build_predictive_section(self, analytics: dict) -> str:
        pred = analytics.get("predictive")
        if not isinstance(pred, dict):
            return ""

        section = "## 🔮 PREDICTIVE ANALYSIS\n\n"

        risk_block = pred.get("breakup_risk_assessment", {})
        risk_score = risk_block.get("risk_score", 0)
        risk_level = risk_block.get("risk_level", "UNKNOWN")
        section += "### Risk Assessment\n\n"
        section += f"**Overall Risk Score:** {risk_score}/100 ({risk_level})\n\n"

        # Indicators
        indicators = {
            "positive": risk_block.get("positive_indicators", []),
            "concerning": risk_block.get("warning_signs", []),
        }
        if indicators["positive"]:
            section += "**Positive Indicators:**\n"
            for ind in indicators["positive"]:
                section += f"- ✅ {ind.replace('_', ' ').title()}\n"
            section += "\n"
        if indicators["concerning"]:
            section += "**Concerning Indicators:**\n"
            for ind in indicators["concerning"]:
                section += f"- ⚠️ {ind.replace('_', ' ').title()}\n"
            section += "\n"

        # Trajectory
        trajectory = pred.get("trajectory_forecast", {})
        projections = trajectory.get("trajectory_forecast", [])
        if projections:
            section += "### Relationship Trajectory\n\n"
            section += (
                "| Timeframe | Stability Probability | Trend | Assessment |\n"
                "|-----------|---------------------|-------|------------|\n"
            )
            for projection in projections:
                for period_key, details in projection.items():
                    prob = details.get("probability_stable", 0.0) * 100
                    trend = details.get("trend", "unknown")
                    label = period_key.replace("_", " ").title()
                    if prob > 80:
                        assessment = "Strong"
                    elif prob > 60:
                        assessment = "Good"
                    elif prob > 40:
                        assessment = "Uncertain"
                    else:
                        assessment = "At Risk"
                    section += (
                        f"| {label} | {prob:.0f}% | {trend} | {assessment} |\n"
                    )
            section += "\n"

        # Recommendations
        recs = pred.get("recommendations", [])
        if recs:
            section += "### Predictive Recommendations\n\n"
            for rec in recs:
                section += f"- {rec}\n"
            section += "\n"

        section += "---\n\n"
        return section

    def _build_patterns_section(self, analytics: dict) -> str:
        patt = analytics.get("patterns")
        if not isinstance(patt, dict):
            return ""

        section = "## 🔍 PATTERN ANALYSIS\n\n"

        anomalies = patt.get("anomaly_detection", {})
        if anomalies:
            section += "### Detected Anomalies\n\n"
            section += (
                f"**Total Anomalies:** {anomalies.get('anomalies_detected', 0)}\n\n"
            )
            gaps = anomalies.get("communication_gaps", [])
            spikes = anomalies.get("message_spikes", [])
            for anomaly in (gaps[:3] + spikes[:3]):
                label = anomaly.get("date", anomaly.get("start_date", "Unknown Date"))
                section += f"**{label}** - {anomaly.get('type', 'Unknown Type')}\n"
                if "severity" in anomaly:
                    section += f"- Severity: {anomaly.get('severity', 'unknown')}\n"
                if "vs_median" in anomaly:
                    section += f"- Magnitude: {anomaly.get('vs_median')}\n"
                section += "\n"

        turning = patt.get("turning_points", {})
        if turning and turning.get("turning_points"):
            section += "### Major Turning Points\n\n"
            for tp in turning["turning_points"][:5]:
                section += f"**{tp.get('date', 'Unknown')}** - "
                section += f"{tp.get('type', 'Change').title()}\n"
                if "impact" in tp:
                    section += f"- Impact: {tp['impact']}\n"
                section += "\n"

        cycles = patt.get("communication_cycles", {})
        rc = cycles.get("recurring_cycles", {}) if cycles else {}
        if rc:
            section += "### Recurring Patterns\n\n"
            section += f"**Detected:** {rc.get('interpretation', 'No recurring cycles detected')}\n\n"
            if rc.get("cycle_periods_days"):
                periods = ", ".join(str(d) for d in rc["cycle_periods_days"])
                section += f"**Cycle Periods (days):** {periods}\n\n"

        section += "---\n\n"
        return section

    def _build_emotional_section(self, analytics: dict) -> str:
        section = ""

        # Topics
        topics_report = analytics.get("topics")
        if isinstance(topics_report, dict):
            section += "## 💬 CONVERSATION THEMES\n\n"
            extraction = topics_report.get("topic_extraction", {})
            topics = extraction.get("topics", [])
            if topics:
                section += "### Primary Discussion Topics\n\n"
                for topic in topics[:7]:
                    label = topic.get("label", "Unknown")
                    prevalence = topic.get("prevalence", 0.0) * 100
                    section += (
                        f"**{label}** ({prevalence:.1f}% of conversations)\n"
                    )
                    if "keywords" in topic:
                        section += (
                            f"- Keywords: {', '.join(topic['keywords'][:8])}\n"
                        )
                    section += "\n"

            conflicts = topics_report.get("conflict_topics", {})
            if conflicts and conflicts.get("conflict_detected"):
                triggers = conflicts.get("common_conflict_topics", [])
                section += "### ⚠️ Conflict Triggers\n\n"
                section += (
                    f"Topics that tend to cause tension: "
                    f"{', '.join(triggers[:5])}\n\n"
                )

            section += "---\n\n"

        # Sentiment
        sent = analytics.get("sentiment")
        if isinstance(sent, dict):
            section += "## 📈 SENTIMENT ANALYSIS\n\n"
            progression = sent.get("sentiment_progression", {})
            overall = progression.get("overall_sentiment", {})
            if overall:
                section += f"**Overall Sentiment:** {overall.get('mean', 0):.2f}\n"
                section += f"**Trend:** {overall.get('trend', 'unknown')}\n"
                section += f"**Change from Peak:** {overall.get('current_vs_peak', 0):.2f}\n\n"

            phases = progression.get("sentiment_progression", [])
            if phases:
                section += "### Sentiment Over Time\n\n"
                section += (
                    "| Phase | Average Sentiment | Volatility | Assessment |\n"
                    "|-------|------------------|------------|------------|\n"
                )
                for phase_data in phases:
                    phase = phase_data.get("phase", 0)
                    avg = phase_data.get("avg_sentiment", 0.0)
                    vol = phase_data.get("sentiment_std", 0.0)
                    if avg > 0.3 and vol < 0.2:
                        assessment = "Stable Positive"
                    elif vol > 0.3:
                        assessment = "Volatile"
                    elif avg < 0:
                        assessment = "Declining"
                    else:
                        assessment = "Neutral"
                    section += (
                        f"| Phase {phase} | {avg:.2f} | {vol:.2f} | {assessment} |\n"
                    )
                section += "\n"

            vol_block = sent.get("emotional_volatility", {})
            volatility = vol_block.get("volatility_score", 0.0)
            section += f"**Emotional Volatility:** {volatility}/100 - "
            if volatility > 70:
                section += "High instability\n\n"
            elif volatility > 40:
                section += "Moderate fluctuation\n\n"
            else:
                section += "Stable emotions\n\n"

            section += "---\n\n"

        return section

    def _build_psychological_section(self, analytics: dict) -> str:
        section = ""

        # Attachment
        att = analytics.get("attachment")
        if isinstance(att, dict):
            section += "## 🧠 PSYCHOLOGICAL PROFILE\n\n"
            section += "### Attachment Dynamics\n\n"

            rel_spec = att.get("relationship_specific") or {}
            if rel_spec:
                your_style = rel_spec.get("your_style_with_them", "Unknown")
                their_style = rel_spec.get("their_inferred_style", "Unknown")
                compat = rel_spec.get("compatibility", {})
                compat_text = (
                    compat.get("assessment", "Unknown")
                    if isinstance(compat, dict)
                    else str(compat)
                )
                section += f"**Your Attachment Style:** {your_style}\n"
                section += f"**Their Inferred Style:** {their_style}\n"
                section += f"**Compatibility:** {compat_text}\n\n"

                recs = rel_spec.get("recommendations", [])
                if recs:
                    section += "**Attachment-Based Recommendations:**\n"
                    for rec in recs[:3]:
                        section += f"- {rec}\n"
                    section += "\n"

        # Communication evolution
        comm = analytics.get("communication")
        if isinstance(comm, dict):
            section += "### Communication Evolution\n\n"

            form = comm.get("formality_evolution")
            if form:
                section += f"**Communication Trend:** {form.get('trend', 'unknown')}\n"
                section += f"**Interpretation:** {form.get('interpretation', 'N/A')}\n\n"

            express = comm.get("emotional_expressiveness")
            if express:
                growth = express.get("vocabulary_growth_percent", 0.0)
                section += f"**Emotional Vocabulary Growth:** {growth:.1f}%\n"
                section += f"**Assessment:** {express.get('assessment', 'N/A')}\n\n"

            sync = comm.get("style_synchronization")
            if isinstance(sync, dict) and "synchronization_score" in sync:
                score = sync.get("synchronization_score", 0.0)
                section += f"**Communication Sync Score:** {score:.2f}\n"
                section += f"**Interpretation:** {sync.get('interpretation', 'N/A')}\n\n"

        # Conflict analysis
        conf = analytics.get("conflict")
        if isinstance(conf, dict):
            section += "### Conflict Patterns\n\n"
            section += f"**Conflict Profile:** {conf.get('conflict_profile', 'Unknown')}\n\n"

            stats = conf.get("statistics") or {}
            if stats:
                section += f"- Total Conflicts: {stats.get('total_conflicts', 0)}\n"
                section += (
                    f"- Average Duration: {stats.get('avg_duration_days', 0)} days\n"
                )
                section += (
                    f"- Average Severity: {stats.get('avg_severity', 0):.2f}/10\n"
                )
                section += (
                    f"- Conflict Frequency: Every "
                    f"{stats.get('conflict_frequency_days', 0):.0f} days\n\n"
                )

            triggers = conf.get("triggers") or []
            if triggers:
                section += "**Primary Conflict Triggers:**\n"
                for trigger in triggers[:5]:
                    topic = trigger.get("topic", "unknown").title()
                    freq = trigger.get("frequency", 0)
                    sev = trigger.get("severity", "unknown")
                    section += f"- {topic}: {freq} occurrences ({sev})\n"
                section += "\n"

            maturity = conf.get("conflict_maturity") or {}
            if maturity:
                section += f"**Conflict Maturity Trend:** {maturity.get('trend', 'UNKNOWN')}\n"
                section += f"**Assessment:** {maturity.get('assessment', 'N/A')}\n\n"

        if section:
            section += "---\n\n"
        return section

    def _build_recommendations(self, analytics: dict) -> str:
        section = "## 💡 CONSOLIDATED RECOMMENDATIONS\n\n"
        all_recs = []

        for module_name, module_data in analytics.items():
            if not isinstance(module_data, dict):
                continue

            if "recommendations" in module_data:
                recs = module_data["recommendations"]
                if isinstance(recs, list):
                    all_recs.extend([f"[{module_name.title()}] {r}" for r in recs])
                elif isinstance(recs, str):
                    all_recs.append(f"[{module_name.title()}] {recs}")

            # Attachment nested recommendations
            if module_name == "attachment":
                overall = module_data.get("overall_attachment_profile") or {}
                if "recommendations" in overall:
                    for r in overall["recommendations"]:
                        all_recs.append(f"[Attachment] {r}")

        if all_recs:
            for idx, rec in enumerate(all_recs[:10], 1):
                section += f"{idx}. {rec}\n"
        else:
            section += "No specific recommendations generated.\n"

        section += "\n---\n\n"
        return section

    def _build_footer(self) -> str:
        return f"""---

**Report Type:** Enhanced Comprehensive Analysis  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**System Version:** v3.0 - Predictive + Psychological  
**Confidence Level:** Based on multi-dimensional analytical framework  

*This report integrates predictive analytics, pattern detection, topic mining, sentiment analysis, attachment theory, communication evolution, and conflict resolution insights.*
"""

    # ------------------------------------------------------------------ #
    # Batch generation
    # ------------------------------------------------------------------ #

    def _auto_detect_contacts(self) -> list[str]:
        """Infer contact names from filenames in outputs/."""
        contacts = set()

        for module, subdir in self.module_config.items():
            module_dir = os.path.join(self.outputs_base, subdir)
            if not os.path.isdir(module_dir):
                continue

            for filename in os.listdir(module_dir):
                if not filename.endswith(".json"):
                    continue

                stem = filename[:-5]

                # Module-specific filename patterns
                if module == "predictive" and "_prediction_" in stem:
                    contact_safe = stem.split("_prediction_")[0]
                elif module == "patterns" and "_patterns_" in stem:
                    contact_safe = stem.split("_patterns_")[0]
                elif module == "topics" and "_topics_" in stem:
                    contact_safe = stem.split("_topics_")[0]
                elif module == "sentiment" and "_sentiment_" in stem:
                    contact_safe = stem.split("_sentiment_")[0]
                elif module == "attachment" and "_attachment_" in stem:
                    contact_safe = stem.split("_attachment_")[0]
                elif module == "communication" and stem.endswith("_communication_evolution"):
                    contact_safe = stem[: -len("_communication_evolution")]
                elif module == "conflict" and stem.endswith("_conflict"):
                    contact_safe = stem[: -len("_conflict")]
                else:
                    continue

                contacts.add(contact_safe.replace("_", " "))

        return sorted(contacts)

    def generate_all_reports(self, contacts=None, output_dir: str = "REPORTS/05_ENHANCED") -> None:
        """Generate enhanced reports for all contacts."""
        os.makedirs(output_dir, exist_ok=True)

        if contacts is None:
            contacts = self._auto_detect_contacts()

        print(f"🔄 Generating {len(contacts)} enhanced reports...")
        print("=" * 70)

        for idx, contact in enumerate(contacts, 1):
            print(f"\n[{idx}/{len(contacts)}] {contact}")
            try:
                report = self.generate_comprehensive_report(contact)
                filename = os.path.join(
                    output_dir, f"{contact.replace(' ', '_')}_ENHANCED.md"
                )
                with open(filename, "w") as f:
                    f.write(report)
                word_count = len(report.split())
                print(f"  ✅ Saved ({word_count:,} words)")
            except Exception as e:  # pragma: no cover - defensive
                print(f"  ❌ Error generating report for {contact}: {e}")

        print(f"\n{'=' * 70}")
        print(f"✅ Generated {len(contacts)} enhanced reports")
        print(f"📁 Location: {output_dir}/")


def main() -> None:
    """CLI entrypoint."""
    ensure_user_consent()
    generator = EnhancedReportGenerator()
    generator.generate_all_reports()


if __name__ == "__main__":
    main()
