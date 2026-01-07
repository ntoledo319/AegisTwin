import json
from collections import Counter
from typing import Dict, Tuple

import pandas as pd

from analysis_pipeline import _build_emotional_lexicon, load_messages


def _scale(value: float, low: float, high: float, min_score: float = 0.0, max_score: float = 100.0) -> float:
    if high <= low:
        return min_score
    if value <= low:
        return min_score
    if value >= high:
        return max_score
    return min_score + (value - low) / (high - low) * (max_score - min_score)


def _tokenize(messages: pd.Series) -> Tuple[int, int, Counter]:
    words: Counter = Counter()
    total_words = 0
    total_chars = 0
    for msg in messages.dropna().astype(str):
        tokens = msg.split()
        total_words += len(tokens)
        total_chars += sum(len(t) for t in tokens)
        words.update(t.lower() for t in tokens)
    return total_words, total_chars, words


def analyze_verbal_intelligence(df: pd.DataFrame) -> Dict:
    outgoing = df[df["type"].str.lower() == "outgoing"]
    messages = outgoing["message"]

    total_words, total_chars, vocab = _tokenize(messages)
    unique_words = len(vocab)

    if total_words == 0:
        return {
            "verbal_intelligence": 0.0,
            "details": {
                "total_words": 0,
                "unique_words": 0,
                "vocabulary_richness": 0.0,
                "avg_word_length": 0.0,
                "complex_word_ratio": 0.0,
                "very_complex_word_ratio": 0.0,
            },
        }

    vocabulary_richness = unique_words / total_words
    avg_word_length = total_chars / total_words

    complex_words = sum(1 for w in vocab.elements() if len("".join(ch for ch in w if ch.isalpha())) >= 7)
    very_complex_words = sum(1 for w in vocab.elements() if len("".join(ch for ch in w if ch.isalpha())) >= 10)

    complex_ratio = complex_words / total_words
    very_complex_ratio = very_complex_words / total_words

    richness_score = _scale(vocabulary_richness, 0.04, 0.12, 20, 95)
    complexity_score = _scale(complex_ratio, 0.03, 0.18, 20, 95)
    word_len_score = _scale(avg_word_length, 3.5, 5.5, 20, 95)

    # Composite verbal intelligence: weighted average of components
    verbal_intelligence = 0.4 * richness_score + 0.3 * complexity_score + 0.3 * word_len_score

    return {
        "verbal_intelligence": round(verbal_intelligence, 1),
        "details": {
            "total_words": int(total_words),
            "unique_words": int(unique_words),
            "vocabulary_richness": round(vocabulary_richness, 4),
            "avg_word_length": round(avg_word_length, 2),
            "complex_word_ratio": round(complex_ratio, 4),
            "very_complex_word_ratio": round(very_complex_ratio, 4),
        },
    }


def analyze_ei(df: pd.DataFrame) -> Dict:
    outgoing = df[df["type"].str.lower() == "outgoing"]
    messages = outgoing["message"].dropna().astype(str)

    total_words, _, vocab = _tokenize(messages)
    if total_words == 0:
        zero_components = {
            "emotional_expression": 0.0,
            "empathy_indicators": 0.0,
            "emotional_regulation": 0.0,
            "social_awareness": 0.0,
            "relationship_management": 0.0,
        }
        return {
            "emotional_intelligence": 0.0,
            "components": zero_components,
            "details": {
                "total_words": 0,
            },
        }

    lexicon = _build_emotional_lexicon()

    # Count emotion-related terms using the same lexicon categories
    text = " ".join(messages.str.lower())
    emotion_counts: Dict[str, int] = {}
    total_emotion_hits = 0
    for category, phrases in lexicon.items():
        c = 0
        for phrase in phrases:
            c += text.count(phrase)
        emotion_counts[category] = c
        total_emotion_hits += c

    emotion_per_1000 = total_emotion_hits / total_words * 1000

    # Empathy lexicon (perspective-taking, concern)
    empathy_phrases = [
        "how are you",
        "are you ok",
        "are you okay",
        "you okay",
        "i'm sorry",
        "im sorry",
        "sorry that",
        "tell me more",
        "how did that feel",
        "that must be hard",
        "i understand",
        "i get it",
        "makes sense",
        "thank you for sharing",
    ]
    empathy_hits = 0
    for phrase in empathy_phrases:
        empathy_hits += text.count(phrase)
    empathy_per_1000 = empathy_hits / total_words * 1000

    # Pronoun-based social awareness
    you_count = vocab.get("you", 0) + vocab.get("u", 0)
    i_count = vocab.get("i", 0) + vocab.get("im", 0) + vocab.get("i'm", 0)
    you_i_ratio = you_count / (i_count + 1e-6)

    # Conflict vs repair/support
    conflict = emotion_counts.get("conflict", 0) + emotion_counts.get("sadness", 0) + emotion_counts.get("breakup", 0)
    repair = emotion_counts.get("support", 0) + emotion_counts.get("reconciliation", 0)
    conflict_per_1000 = conflict / total_words * 1000
    repair_per_1000 = repair / total_words * 1000

    # Component scores on 0–100 scale
    emotional_expression = _scale(emotion_per_1000, 5, 40)  # richer emotional vocabulary → higher
    empathy_indicators = _scale(empathy_per_1000, 2, 25)

    # Emotional regulation: low conflict with reasonable repair language
    if conflict_per_1000 <= 2:
        base_reg = 80
    elif conflict_per_1000 <= 8:
        base_reg = 60
    else:
        base_reg = 40
    repair_bonus = _scale(repair_per_1000, 1, 15, 0, 20)
    emotional_regulation = min(100.0, base_reg + repair_bonus)

    # Social awareness: focus on "you" relative to "I"
    social_awareness = _scale(you_i_ratio, 0.4, 1.6, 20, 95)

    # Relationship management: combination of empathy and repair language
    relationship_management = 0.6 * empathy_indicators + 0.4 * _scale(repair_per_1000, 1, 15)

    components = {
        "emotional_expression": round(emotional_expression, 1),
        "empathy_indicators": round(empathy_indicators, 1),
        "emotional_regulation": round(emotional_regulation, 1),
        "social_awareness": round(social_awareness, 1),
        "relationship_management": round(relationship_management, 1),
    }

    # Overall EI: weighted average with more weight on empathy and relationship management
    emotional_intelligence = (
        0.2 * components["emotional_expression"]
        + 0.25 * components["empathy_indicators"]
        + 0.2 * components["emotional_regulation"]
        + 0.15 * components["social_awareness"]
        + 0.2 * components["relationship_management"]
    )

    return {
        "emotional_intelligence": round(emotional_intelligence, 1),
        "components": components,
        "details": {
            "total_words": int(total_words),
            "emotion_counts": emotion_counts,
            "emotion_per_1000_words": round(emotion_per_1000, 2),
            "empathy_hits": int(empathy_hits),
            "empathy_per_1000_words": round(empathy_per_1000, 2),
            "you_i_ratio": round(you_i_ratio, 3),
            "conflict_per_1000_words": round(conflict_per_1000, 2),
            "repair_per_1000_words": round(repair_per_1000, 2),
        },
    }


def build_intelligence_profile(df: pd.DataFrame) -> Dict:
    verbal = analyze_verbal_intelligence(df)
    ei = analyze_ei(df)

    verbal_score = verbal["verbal_intelligence"]
    ei_score = ei["emotional_intelligence"]

    # Synthetic but transparent "social_intelligence" and "communication_effectiveness"
    outgoing = df[df["type"].str.lower() == "outgoing"].copy()
    outgoing["msg_len"] = outgoing["message"].astype(str).str.len()
    avg_len = float(outgoing["msg_len"].mean()) if not outgoing.empty else 0.0

    # Question and exclamation rates
    msgs = outgoing["message"].astype(str)
    total_msgs = len(msgs)
    if total_msgs > 0:
        q_rate = sum("?" in m for m in msgs) / total_msgs * 100
        excl_rate = sum("!" in m for m in msgs) / total_msgs * 100
    else:
        q_rate = 0.0
        excl_rate = 0.0

    # Communication effectiveness: moderate length, some questions, not too spammy with punctuation
    len_score = _scale(avg_len, 18, 80, 40, 95)
    q_score = _scale(q_rate, 2, 15, 30, 95)
    excl_score = _scale(excl_rate, 0.5, 8, 20, 90)

    communication_effectiveness = 0.5 * len_score + 0.3 * q_score + 0.2 * excl_score

    # Social intelligence: blend of EI social components and engagement
    social_intelligence = 0.6 * ei["components"]["social_awareness"] + 0.4 * q_score

    composite_intelligence = 0.4 * verbal_score + 0.2 * ei_score + 0.2 * social_intelligence + 0.2 * communication_effectiveness

    strengths = []
    growth_areas = []
    if verbal_score >= 65:
        strengths.append("Verbal Intelligence")
    else:
        growth_areas.append("Verbal Intelligence")
    if ei_score >= 65:
        strengths.append("Emotional Intelligence")
    else:
        growth_areas.append("Emotional Intelligence")
    if social_intelligence >= 65:
        strengths.append("Social Intelligence")
    else:
        growth_areas.append("Social Intelligence")
    if communication_effectiveness >= 65:
        strengths.append("Communication Effectiveness")
    else:
        growth_areas.append("Communication Effectiveness")

    profile = {
        "verbal_intelligence": round(verbal_score, 1),
        "emotional_intelligence": round(ei_score, 1),
        "social_intelligence": round(social_intelligence, 1),
        "communication_effectiveness": round(communication_effectiveness, 1),
        "composite_intelligence": round(composite_intelligence, 1),
        "strengths": strengths,
        "growth_areas": growth_areas,
        "details": {
            "verbal": verbal["details"],
            "ei": ei["details"],
            "avg_outgoing_message_length": round(avg_len, 2),
            "outgoing_question_rate_pct": round(q_rate, 2),
            "outgoing_exclamation_rate_pct": round(excl_rate, 2),
        },
        "methodology_version": "3.0_structured_heuristic",
        "methodology_notes": "Scores are derived from transparent linguistic heuristics on outgoing messages; they are relative indicators, not clinical IQ/EQ measurements.",
    }
    return profile


def save_intelligence_profile(profile: Dict, path: str = "DATA/analysis/intelligence_scores_v2.json") -> None:
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)


def save_methodology(profile: Dict, path: str = "DATA/analysis/enhanced_iq_ei_methodology_v3.json") -> None:
    methodology = {
        "version": "3.0_structured_heuristic",
        "description": "Transparent heuristic-based IQ/EI proxy metrics computed from full outgoing message history.",
        "components": {
            "verbal_intelligence": {
                "inputs": [
                    "vocabulary_richness",
                    "average_word_length",
                    "complex_word_ratio",
                ],
                "notes": "Higher scores indicate richer and more complex language use in text messages.",
            },
            "emotional_intelligence": {
                "inputs": [
                    "emotion_per_1000_words",
                    "empathy_per_1000_words",
                    "you_i_ratio",
                    "conflict_per_1000_words",
                    "repair_per_1000_words",
                ],
                "notes": "EI is inferred only from language patterns; real-world EI also depends on non-verbal behavior and context.",
            },
            "social_intelligence": {
                "inputs": [
                    "social_awareness_component",
                    "outgoing_question_rate_pct",
                ],
            },
            "communication_effectiveness": {
                "inputs": [
                    "avg_outgoing_message_length",
                    "outgoing_question_rate_pct",
                    "outgoing_exclamation_rate_pct",
                ],
            },
        },
        "disclaimer": "These scores are data-driven heuristics from text messages only. They are not substitutes for standardized IQ or clinical EI assessments, but are designed for relative comparison within this dataset.",
        "derived_from_profile_file": "intelligence_scores_v2.json",
    }
    with open(path, "w") as f:
        json.dump(methodology, f, indent=2)


def main():
    df = load_messages()
    profile = build_intelligence_profile(df)
    save_intelligence_profile(profile)
    save_methodology(profile)
    print("Saved updated intelligence profile to DATA/analysis/intelligence_scores_v2.json")


if __name__ == "__main__":
    main()

