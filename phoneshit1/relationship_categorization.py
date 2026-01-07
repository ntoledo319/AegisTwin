import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

from analysis_pipeline import ChatStats, build_contact_database, load_messages, rebuild_all_deep_analyses


def _load_chat_stats_from_contact_db(contact_db: Dict[str, Dict]) -> Dict[str, ChatStats]:
    stats: Dict[str, ChatStats] = {}
    for name, data in contact_db.items():
        stats[name] = ChatStats(
            name=name,
            type=data.get("type", "individual"),
            message_count=int(data.get("message_count", 0)),
            first_message=data.get("first_message", ""),
            last_message=data.get("last_message", ""),
            relationship_duration_days=int(data.get("relationship_duration_days", 0)),
            participant_names=data.get("sender_names", []),
            participant_count=len(data.get("sender_names", [])),
        )
    return stats


def _is_family_name(name: str) -> bool:
    lowered = name.lower()
    family_keywords = [
        "mom",
        "dad",
        "aunt",
        "uncle",
        "grandma",
        "grandpa",
        "brother",
        "sister",
        "cousin",
        "family",
    ]
    return any(k in lowered for k in family_keywords)


def load_deep_analyses() -> Dict[str, Dict]:
    analyses: Dict[str, Dict] = {}
    for fn in os.listdir("DATA/analysis"):
        if not fn.endswith("_deep_analysis.json"):
            continue
        path = os.path.join("DATA/analysis", fn)
        with open(path, "r") as f:
            data = json.load(f)
        name = data.get("person") or fn.replace("_deep_analysis.json", "")
        analyses[name] = data
    return analyses


def classify_individual(
    name: str,
    analysis: Dict,
    stats: ChatStats,
    romantic_seed: List[str],
) -> str:
    if _is_family_name(name):
        return "family"

    if name in romantic_seed:
        love = analysis.get("emotional_keywords", {}).get("love", 0)
        breakup = analysis.get("emotional_keywords", {}).get("breakup", 0)
        days_since = analysis.get("days_since_last", 999)
        status = analysis.get("status", "")
        if days_since <= 60 and "INACTIVE" not in status and breakup < 40:
            return "romantic_partner"
        return "ex_romantic_partner"

    total_messages = analysis.get("total_messages", stats.message_count)
    duration_days = analysis.get("duration_days", stats.relationship_duration_days)
    days_since = analysis.get("days_since_last", 999)

    # Close friend criteria: high depth, long duration, decent recency, not in romantic seed set.
    if total_messages >= 10000 and duration_days >= 365 and days_since <= 365:
        return "close_friends"

    return "acquaintances"


def build_relationship_categories(
    contact_db: Dict[str, Dict],
    deep_analyses: Dict[str, Dict],
) -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {
        "romantic_partner": [],
        "ex_romantic_partner": [],
        "close_friends": [],
        "family": [],
        "acquaintances": [],
        "group_chats": [],
        "system_accounts": [],
    }

    stats_map = _load_chat_stats_from_contact_db(contact_db)

    # Known romantic anchors (may be customized per dataset)
    romantic_seed = []

    for name, stats in stats_map.items():
        ctype = stats.type
        analysis = deep_analyses.get(name, {})

        if ctype == "system":
            categories["system_accounts"].append(name)
            continue

        # Group chats: tracked separately, but some groups (like Marisa / Julia) are also
        # primary romantic relationships and should be classified as such.
        if ctype == "group":
            categories["group_chats"].append(name)
            if _is_family_name(name):
                categories["family"].append(name)
            # For romantic_seed names, fall through to individual classification as well.
            if name not in romantic_seed:
                continue

        # Individual contact (or special-case group like Marisa / Julia)
        rel_type = classify_individual(name, analysis, stats, romantic_seed)
        categories.setdefault(rel_type, []).append(name)

    # Deduplicate and sort each category
    for key, values in categories.items():
        categories[key] = sorted(sorted(set(values)), key=lambda x: x.lower())

    return categories


def compute_relationship_health(
    deep_analyses: Dict[str, Dict],
    categories: Dict[str, List[str]],
) -> Dict[str, Dict]:
    scores: Dict[str, Dict] = {}

    for name, analysis in deep_analyses.items():
        total_messages = analysis.get("total_messages", 0)
        duration_days = analysis.get("duration_days", 1) or 1
        days_since = analysis.get("days_since_last", 999)
        balance = analysis.get("balance", 50.0)
        phases = analysis.get("phases", [])

        daily_avg = total_messages / duration_days

        # Depth: more messages and longer relationships score higher, up to a cap.
        depth_score = min(100.0, (total_messages / 20000.0) * 100.0)

        # Recency: 0 days → 100, 365+ days → 0
        recency_score = max(0.0, 100.0 - min(days_since, 365) / 365.0 * 100.0)

        # Balance: 50/50 is ideal, extremes penalized
        balance_score = max(0.0, 100.0 - abs(balance - 50.0) * 2.0)

        # Growth: compare last phase daily_avg to earlier average
        if len(phases) >= 2:
            early_avg = sum(p["daily_avg"] for p in phases[:-1]) / (len(phases) - 1)
            last_avg = phases[-1]["daily_avg"]
            if early_avg <= 0:
                growth_score = 50.0
            else:
                change_ratio = (last_avg - early_avg) / early_avg
                if change_ratio >= 0.5:
                    growth_score = 90.0
                elif change_ratio >= 0.1:
                    growth_score = 75.0
                elif change_ratio >= -0.1:
                    growth_score = 60.0
                elif change_ratio >= -0.4:
                    growth_score = 40.0
                else:
                    growth_score = 25.0
        else:
            growth_score = 50.0

        # Consistency: dispersion of phase daily_avgs
        if len(phases) >= 2:
            vals = [p["daily_avg"] for p in phases]
            mean_v = sum(vals) / len(vals)
            if mean_v == 0:
                consistency_score = 50.0
            else:
                variance = sum((v - mean_v) ** 2 for v in vals) / len(vals)
                rel_var = variance / (mean_v**2 + 1e-6)
                if rel_var <= 0.1:
                    consistency_score = 90.0
                elif rel_var <= 0.3:
                    consistency_score = 75.0
                elif rel_var <= 0.7:
                    consistency_score = 55.0
                else:
                    consistency_score = 35.0
        else:
            consistency_score = 50.0

        # Engagement score from daily average messages
        if daily_avg >= 40:
            engagement_score = 100.0
        elif daily_avg >= 10:
            engagement_score = 80.0
        elif daily_avg >= 3:
            engagement_score = 60.0
        elif daily_avg >= 1:
            engagement_score = 40.0
        else:
            engagement_score = 20.0

        composite = (
            0.25 * depth_score
            + 0.2 * recency_score
            + 0.2 * balance_score
            + 0.15 * growth_score
            + 0.1 * consistency_score
            + 0.1 * engagement_score
        )

        if composite >= 85:
            grade = "A"
            status = "EXCELLENT"
        elif composite >= 75:
            grade = "B"
            status = "STRONG"
        elif composite >= 65:
            grade = "C"
            status = "GROWING"
        elif composite >= 50:
            grade = "D"
            status = "DECLINING"
        else:
            grade = "F"
            status = "CRITICAL"

        scores[name] = {
            "composite_score": round(composite, 1),
            "component_scores": {
                "depth": round(depth_score, 1),
                "recency": round(recency_score, 1),
                "balance": round(balance_score, 1),
                "growth": round(growth_score, 1),
                "consistency": round(consistency_score, 1),
                "engagement": round(engagement_score, 1),
            },
            "grade": grade,
            "status": status,
        }

    return scores


def save_json(obj: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def main():
    df = load_messages()
    contact_db, chat_stats = build_contact_database(df)
    deep_analyses = rebuild_all_deep_analyses(df, chat_stats)

    categories = build_relationship_categories(contact_db, deep_analyses)
    health_scores = compute_relationship_health(deep_analyses, categories)

    save_json(categories, "DATA/analysis/relationship_categories_v2.json")
    save_json(health_scores, "DATA/analysis/relationship_health_scores_v2.json")
    print("Saved relationship_categories_v2.json and relationship_health_scores_v2.json")


if __name__ == "__main__":
    main()
