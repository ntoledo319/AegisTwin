import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Literal, Optional, Tuple

import pandas as pd


ContactType = Literal["individual", "group", "system"]


@dataclass
class ChatStats:
    name: str
    type: ContactType
    message_count: int
    first_message: str
    last_message: str
    relationship_duration_days: int
    participant_names: List[str]
    participant_count: int


def load_messages(path: str = "DATA/raw/messages.csv") -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = df.rename(
        columns={
            "Chat Session": "chat_session",
            "Message Date": "timestamp",
            "Sender Name": "sender_name",
            "Text": "message",
            "Type": "type",
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Normalize sender: outgoing = "You", otherwise original sender name
    df["sender"] = df.apply(
        lambda row: "You" if str(row.get("type", "")).lower() == "outgoing" else row.get("sender_name", ""),
        axis=1,
    )
    return df


def _looks_like_system_chat(name: str) -> bool:
    n = name.strip()
    if not n:
        return True
    # iOS filtered / smsfp / smsft markers
    lowered = n.lower()
    if any(s in lowered for s in ["(smsfp)", "(smsft)", "(filtered)"]):
        return True
    # Short codes and generic numeric senders
    if n.startswith("+") and n[1:].isdigit() and 4 <= len(n[1:]) <= 12:
        return True
    if n.isdigit() and 4 <= len(n) <= 9:
        return True
    # Some known non-person sources by name
    system_like_keywords = [
        "yale study",
        "lululemon",
        "craftd",
        "study",
        "uber",
        "lyft",
        "doordash",
        "bank",
        "verification",
        "auth",
    ]
    if any(k in lowered for k in system_like_keywords):
        return True
    return False


def _infer_contact_type(
    chat_name: str, participant_names: List[str], message_count: int
) -> ContactType:
    # System / service detection first
    if _looks_like_system_chat(chat_name):
        return "system"
    if len(participant_names) == 0:
        # No other visible participants almost always means a system/sender code
        if message_count <= 50:
            return "system"
    # Group detection
    # If there are 2+ distinct non-you participants or the name clearly looks like a group
    non_you = [p for p in participant_names if p and p != "You"]
    if len(set(non_you)) >= 2:
        return "group"
    if "&" in chat_name or "," in chat_name:
        return "group"
    # Default: individual person
    return "individual"


def build_contact_database(df: pd.DataFrame) -> Tuple[Dict[str, Dict], Dict[str, ChatStats]]:
    """
    Rebuild a clean contact_database-style mapping and per-chat stats.

    This is the foundation for all other analysis. We treat each chat_session as
    a relationship with either a single person, a group, or a system/service.
    """
    contact_db: Dict[str, Dict] = {}
    chat_stats: Dict[str, ChatStats] = {}

    global_end = df["timestamp"].max()

    for chat_name, group in df.groupby("chat_session"):
        group = group.sort_values("timestamp")
        message_count = len(group)
        first_ts = group["timestamp"].iloc[0]
        last_ts = group["timestamp"].iloc[-1]
        duration_days = max((last_ts - first_ts).days, 0)

        # Participants: unique senders excluding "You"
        participant_names = []
        for s in group["sender"].unique():
            s_str = str(s).strip()
            if not s_str:
                continue
            lowered = s_str.lower()
            if lowered in ("you", "nan"):
                continue
            participant_names.append(s_str)
        participant_names = sorted(set(participant_names))

        ctype = _infer_contact_type(chat_name, participant_names, message_count)

        contact_db[chat_name] = {
            "chat_sessions": [chat_name],
            "sender_names": participant_names,
            "message_count": int(message_count),
            "first_message": first_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "last_message": last_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "relationship_duration_days": int(duration_days),
            "type": ctype,
        }

        chat_stats[chat_name] = ChatStats(
            name=chat_name,
            type=ctype,
            message_count=int(message_count),
            first_message=first_ts.strftime("%Y-%m-%d %H:%M:%S"),
            last_message=last_ts.strftime("%Y-%m-%d %H:%M:%S"),
            relationship_duration_days=int(duration_days),
            participant_names=participant_names,
            participant_count=len(participant_names),
        )

    return contact_db, chat_stats


def compute_basic_stats(df: pd.DataFrame, chat_stats: Dict[str, ChatStats]) -> Dict:
    total_messages = int(len(df))
    date_range = {
        "start": df["timestamp"].min().strftime("%Y-%m-%d %H:%M:%S"),
        "end": df["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S"),
    }

    messages_by_year = (
        df["timestamp"].dt.year.value_counts().sort_index().to_dict()
    )

    outgoing_mask = df["type"].str.lower() == "outgoing"
    outgoing_messages = int(outgoing_mask.sum())
    incoming_messages = int(total_messages - outgoing_messages)

    df["message_length"] = df["message"].astype(str).str.len()
    avg_message_length = {
        "outgoing": float(df.loc[outgoing_mask, "message_length"].mean()),
        "incoming": float(df.loc[~outgoing_mask, "message_length"].mean()),
    }

    # Top contacts by message count, using our clean classification
    counts = Counter()
    for name, stats in chat_stats.items():
        if stats.type == "system":
            continue
        counts[name] = stats.message_count
    top_20_contacts = dict(counts.most_common(20))

    return {
        "total_messages": total_messages,
        "date_range": date_range,
        "unique_chat_sessions": int(df["chat_session"].nunique()),
        "outgoing_messages": outgoing_messages,
        "incoming_messages": incoming_messages,
        "messages_by_year": {str(k): int(v) for k, v in messages_by_year.items()},
        "top_20_contacts": top_20_contacts,
        "avg_message_length": avg_message_length,
    }


def build_all_individuals_and_groups(chat_stats: Dict[str, ChatStats]) -> Tuple[List[Dict], List[Dict]]:
    individuals: List[Dict] = []
    groups: List[Dict] = []

    for stats in chat_stats.values():
        if stats.type == "system":
            continue
        entry = {"name": stats.name, "message_count": stats.message_count}
        if stats.type == "group":
            groups.append(entry)
        else:
            individuals.append(entry)

    # Sort descending by message_count
    individuals.sort(key=lambda x: x["message_count"], reverse=True)
    groups.sort(key=lambda x: x["message_count"], reverse=True)

    return individuals, groups


def _build_emotional_lexicon() -> Dict[str, List[str]]:
    # Simple but explicit lexicon; can be tuned further.
    return {
        "love": [
            "love",
            "loved",
            "loving",
            "in love",
            "adore",
            "adored",
            "adoring",
            "miss you",
            "miss u",
            "i miss",
            "i care",
        ],
        "conflict": [
            "angry",
            "mad",
            "upset",
            "pissed",
            "fight",
            "fighting",
            "argue",
            "argument",
            "annoyed",
            "frustrated",
            "hurt",
        ],
        "breakup": [
            "break up",
            "breakup",
            "broke up",
            "ending this",
            "we are done",
            "we're done",
            "its over",
            "it's over",
            "over between us",
        ],
        "reconciliation": [
            "work it out",
            "work this out",
            "fix this",
            "start over",
            "try again",
            "give us another chance",
            "i'm sorry",
            "im sorry",
            "sorry for",
            "forgive me",
        ],
        "intimacy": [
            "intimate",
            "kiss",
            "kissed",
            "kissing",
            "sex",
            "sexy",
            "in bed",
            "cuddle",
            "cuddling",
            "make out",
            "making out",
        ],
        "support": [
            "i'm here for you",
            "im here for you",
            "here for you",
            "you got this",
            "you've got this",
            "proud of you",
            "i support you",
            "support you",
            "how can i help",
            "let me help",
            "talk to me",
        ],
        "excitement": [
            "so excited",
            "excited for",
            "cant wait",
            "can't wait",
            "hype",
            "stoked",
            "pumped",
            "this is huge",
            "amazing",
            "incredible",
        ],
        "sadness": [
            "sad",
            "depressed",
            "depression",
            "down",
            "lonely",
            "alone",
            "crying",
            "cried",
            "tears",
            "heartbroken",
            "heartbroken",
        ],
    }


def _count_emotional_keywords(messages: pd.Series, lexicon: Dict[str, List[str]]) -> Dict[str, int]:
    text = " ".join(messages.astype(str).str.lower())
    counts: Dict[str, int] = {}
    for category, phrases in lexicon.items():
        total = 0
        for phrase in phrases:
            total += text.count(phrase)
        counts[category] = int(total)
    return counts


def _build_phases(
    timestamps: pd.Series, total_messages: int
) -> List[Dict]:
    if total_messages == 0:
        return []
    timestamps = timestamps.sort_values()
    start = timestamps.iloc[0]
    end = timestamps.iloc[-1]
    total_days = max((end - start).days, 1)

    # Use up to 4 phases, but reduce for very short spans
    if total_days <= 60:
        phase_count = 2
    elif total_days <= 180:
        phase_count = 3
    else:
        phase_count = 4

    phases: List[Dict] = []
    for i in range(phase_count):
        phase_start = start + (end - start) * (i / phase_count)
        if i == phase_count - 1:
            phase_end = end
        else:
            phase_end = start + (end - start) * ((i + 1) / phase_count)

        mask = (timestamps >= phase_start) & (timestamps <= phase_end)
        msg_count = int(mask.sum())
        duration_days = max((phase_end - phase_start).days, 1)
        daily_avg = msg_count / duration_days

        if daily_avg < 2:
            characteristics = "Low intensity"
        elif daily_avg < 10:
            characteristics = "Low-moderate intensity"
        elif daily_avg < 25:
            characteristics = "Moderate intensity"
        else:
            characteristics = "High intensity"

        phases.append(
            {
                "start_date": phase_start.date().isoformat(),
                "end_date": phase_end.date().isoformat(),
                "duration_days": int(duration_days),
                "message_count": msg_count,
                "daily_avg": float(daily_avg),
                "characteristics": characteristics,
            }
        )
    return phases


def build_deep_analysis_for_chat(
    df: pd.DataFrame, chat_name: str, stats: ChatStats, global_end: datetime, lexicon: Dict[str, List[str]]
) -> Dict:
    subset = df[df["chat_session"] == chat_name].copy()
    subset = subset.sort_values("timestamp")
    if subset.empty:
        return {}

    total_messages = int(len(subset))
    first_ts = subset["timestamp"].iloc[0]
    last_ts = subset["timestamp"].iloc[-1]
    duration_days = max((last_ts - first_ts).days, 0)

    your_messages = int((subset["type"].str.lower() == "outgoing").sum())
    their_messages = total_messages - your_messages
    balance = (your_messages / total_messages * 100.0) if total_messages > 0 else 0.0

    emotional_keywords = _count_emotional_keywords(subset["message"], lexicon)

    phases = _build_phases(subset["timestamp"], total_messages)

    days_since_last = max((global_end - last_ts).days, 0)

    if days_since_last <= 30:
        status = "ACTIVE"
    elif days_since_last <= 90:
        status = "RECENTLY_ACTIVE"
    else:
        status = "INACTIVE"

    return {
        "person": chat_name,
        "type": stats.type,
        "total_messages": total_messages,
        "first_message": first_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "last_message": last_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_days": int(duration_days),
        "days_since_last": int(days_since_last),
        "your_messages": your_messages,
        "their_messages": their_messages,
        "balance": float(balance),
        "emotional_keywords": emotional_keywords,
        "phases": phases,
        "status": status,
    }


def rebuild_all_deep_analyses(df: pd.DataFrame, chat_stats: Dict[str, ChatStats]) -> Dict[str, Dict]:
    lexicon = _build_emotional_lexicon()
    global_end = df["timestamp"].max()

    analyses: Dict[str, Dict] = {}
    for name, stats in chat_stats.items():
        if stats.type == "system":
            continue
        analyses[name] = build_deep_analysis_for_chat(df, name, stats, global_end, lexicon)
    return analyses


def save_json(obj: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def main():
    df = load_messages()
    contact_db, chat_stats = build_contact_database(df)
    basic_stats = compute_basic_stats(df, chat_stats)
    individuals, groups = build_all_individuals_and_groups(chat_stats)
    deep_analyses = rebuild_all_deep_analyses(df, chat_stats)

    # Persist core analysis artifacts as v2 to keep legacy files intact.
    save_json(contact_db, "DATA/analysis/contact_database_v2.json")
    save_json(basic_stats, "DATA/analysis/basic_stats_v2.json")
    # Keep original all_relationships_summary.json (narrative) intact; write a v2 index instead.
    save_json({"individuals": individuals, "groups": groups}, "DATA/analysis/all_relationships_summary_v2.json")
    save_json(individuals, "DATA/analysis/all_individuals_v2.json")
    save_json(groups, "DATA/analysis/all_groups_v2.json")

    for name, analysis in deep_analyses.items():
        safe = name.replace("/", "_")[:200]
        path = f"DATA/analysis/{safe}_deep_analysis.json"
        save_json(analysis, path)

    print(f"Rebuilt core analysis for {len(deep_analyses)} chats (deep_analysis files updated, summary indices saved as *_v2).")


if __name__ == "__main__":
    main()
