"""
Pattern detectors for specific pattern types.

This module provides specialized detectors for various pattern types,
complementing the EnhancedPatternHydra's capabilities.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np
import re

from core.logging import get_logger
from core.utils import generate_id, timestamp_now
from .hydra import Pattern

logger = get_logger(__name__)

class PatternDetectorBase:
    """Base class for pattern detectors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the pattern detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.detector_id = generate_id("detector")
        self.detector_type = self.__class__.__name__
    
    async def detect(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect patterns in data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of detected patterns
        """
        raise NotImplementedError("Subclasses must implement detect method")

class TextPatternDetector(PatternDetectorBase):
    """Detector for patterns in text content."""
    
    async def detect(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect patterns in text content.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Extract text content
        text_data = []
        for item in data:
            content = None
            
            if "content" in item:
                content = item["content"]
            elif "body" in item:
                content = item["body"]
            elif "body_text" in item:
                content = item["body_text"]
            elif "text" in item:
                content = item["text"]
            
            if content:
                text_data.append({
                    "content": content,
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
        
        if not text_data:
            return patterns
        
        # Detect phrase patterns
        phrase_patterns = await self._detect_phrase_patterns(text_data)
        patterns.extend(phrase_patterns)
        
        # Detect topic patterns
        topic_patterns = await self._detect_topic_patterns(text_data)
        patterns.extend(topic_patterns)
        
        # Detect writing style patterns
        style_patterns = await self._detect_style_patterns(text_data)
        patterns.extend(style_patterns)
        
        return patterns
    
    async def _detect_phrase_patterns(self, text_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect recurring phrases in text.
        
        Args:
            text_data: List of text data points
            
        Returns:
            List of phrase patterns
        """
        patterns = []
        
        # Extract all content
        all_content = " ".join([item["content"] for item in text_data])
        
        # Find common phrases (3-5 words)
        phrase_patterns = []
        for phrase_length in range(3, 6):
            phrases = self._extract_phrases(all_content, phrase_length)
            phrase_counts = defaultdict(int)
            
            for phrase in phrases:
                phrase_counts[phrase] += 1
            
            # Filter for frequent phrases
            for phrase, count in phrase_counts.items():
                if count >= 3:  # Threshold for pattern
                    # Find items containing this phrase
                    matching_items = [
                        item["item"] for item in text_data
                        if phrase.lower() in item["content"].lower()
                    ]
                    
                    patterns.append(Pattern(
                        pattern_id=generate_id("phrase"),
                        pattern_type="recurring_phrase",
                        frequency=count,
                        confidence=min(1.0, count / 10.0),
                        triggers=[],
                        impact_areas=["communication", "language"],
                        metadata={"phrase": phrase},
                        source_data=matching_items
                    ))
        
        return patterns
    
    async def _detect_topic_patterns(self, text_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect topic patterns in text.
        
        Args:
            text_data: List of text data points
            
        Returns:
            List of topic patterns
        """
        patterns = []
        
        # Simple keyword-based topic detection
        topics = {
            "work": ["work", "job", "office", "project", "meeting", "deadline", "client", "boss", "colleague"],
            "family": ["family", "mom", "dad", "parent", "child", "kid", "brother", "sister", "husband", "wife"],
            "health": ["health", "doctor", "exercise", "workout", "gym", "diet", "sick", "illness", "medicine"],
            "finance": ["money", "finance", "bank", "invest", "budget", "expense", "income", "loan", "debt"],
            "technology": ["tech", "computer", "software", "app", "phone", "device", "internet", "digital", "online"],
            "education": ["school", "study", "learn", "class", "course", "teacher", "student", "education", "degree"],
            "travel": ["travel", "trip", "vacation", "flight", "hotel", "tour", "visit", "journey", "destination"],
            "entertainment": ["movie", "show", "music", "game", "book", "concert", "festival", "party", "entertainment"]
        }
        
        # Count topic mentions
        topic_counts = defaultdict(int)
        topic_items = defaultdict(list)
        
        for item in text_data:
            content = item["content"].lower()
            
            for topic, keywords in topics.items():
                for keyword in keywords:
                    if re.search(r'\b' + keyword + r'\b', content):
                        topic_counts[topic] += 1
                        topic_items[topic].append(item["item"])
                        break  # Count each topic only once per item
        
        # Create patterns for frequent topics
        for topic, count in topic_counts.items():
            if count >= 3:  # Threshold for pattern
                patterns.append(Pattern(
                    pattern_id=generate_id("topic"),
                    pattern_type="recurring_topic",
                    frequency=count,
                    confidence=min(1.0, count / len(text_data)),
                    triggers=[],
                    impact_areas=["communication", "interests"],
                    metadata={"topic": topic},
                    source_data=topic_items[topic]
                ))
        
        return patterns
    
    async def _detect_style_patterns(self, text_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect writing style patterns.
        
        Args:
            text_data: List of text data points
            
        Returns:
            List of style patterns
        """
        patterns = []
        
        # Calculate style metrics
        avg_sentence_length = []
        question_frequency = []
        exclamation_frequency = []
        emoji_frequency = []
        
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        
        for item in text_data:
            content = item["content"]
            
            # Sentence length
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
                avg_sentence_length.append(avg_length)
            
            # Question frequency
            questions = len(re.findall(r'\?', content))
            question_frequency.append(questions / max(1, len(sentences)))
            
            # Exclamation frequency
            exclamations = len(re.findall(r'!', content))
            exclamation_frequency.append(exclamations / max(1, len(sentences)))
            
            # Emoji frequency
            emojis = len(emoji_pattern.findall(content))
            emoji_frequency.append(emojis / max(1, len(content.split())))
        
        # Detect style patterns
        if avg_sentence_length:
            avg_length = np.mean(avg_sentence_length)
            if avg_length > 20:  # Long sentences
                patterns.append(Pattern(
                    pattern_id=generate_id("style"),
                    pattern_type="writing_style",
                    frequency=len(text_data),
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["communication", "expression"],
                    metadata={
                        "style_aspect": "sentence_length",
                        "characteristic": "long_sentences",
                        "avg_length": avg_length
                    },
                    source_data=[item["item"] for item in text_data]
                ))
            elif avg_length < 8:  # Short sentences
                patterns.append(Pattern(
                    pattern_id=generate_id("style"),
                    pattern_type="writing_style",
                    frequency=len(text_data),
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["communication", "expression"],
                    metadata={
                        "style_aspect": "sentence_length",
                        "characteristic": "short_sentences",
                        "avg_length": avg_length
                    },
                    source_data=[item["item"] for item in text_data]
                ))
        
        # Question frequency pattern
        if question_frequency:
            avg_questions = np.mean(question_frequency)
            if avg_questions > 0.3:  # High question frequency
                patterns.append(Pattern(
                    pattern_id=generate_id("style"),
                    pattern_type="writing_style",
                    frequency=len(text_data),
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["communication", "expression"],
                    metadata={
                        "style_aspect": "question_frequency",
                        "characteristic": "inquisitive",
                        "avg_frequency": avg_questions
                    },
                    source_data=[item["item"] for item in text_data]
                ))
        
        # Emoji usage pattern
        if emoji_frequency:
            avg_emojis = np.mean(emoji_frequency)
            if avg_emojis > 0.05:  # High emoji usage
                patterns.append(Pattern(
                    pattern_id=generate_id("style"),
                    pattern_type="writing_style",
                    frequency=len(text_data),
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["communication", "expression"],
                    metadata={
                        "style_aspect": "emoji_usage",
                        "characteristic": "emoji_heavy",
                        "avg_frequency": avg_emojis
                    },
                    source_data=[item["item"] for item in text_data]
                ))
        
        return patterns
    
    def _extract_phrases(self, text: str, phrase_length: int) -> List[str]:
        """
        Extract phrases of a specific length from text.
        
        Args:
            text: Input text
            phrase_length: Number of words in each phrase
            
        Returns:
            List of phrases
        """
        words = text.split()
        phrases = []
        
        for i in range(len(words) - phrase_length + 1):
            phrase = " ".join(words[i:i + phrase_length])
            phrases.append(phrase)
        
        return phrases

class TimePatternDetector(PatternDetectorBase):
    """Detector for time-based patterns."""
    
    async def detect(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect time-based patterns.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Extract timestamp data
        time_data = []
        for item in data:
            if "timestamp" in item:
                try:
                    dt = datetime.fromisoformat(item["timestamp"])
                    time_data.append({
                        "datetime": dt,
                        "hour": dt.hour,
                        "day": dt.weekday(),
                        "month": dt.month,
                        "item": item
                    })
                except (ValueError, TypeError):
                    continue
        
        if not time_data:
            return patterns
        
        # Detect daily patterns
        daily_patterns = await self._detect_daily_patterns(time_data)
        patterns.extend(daily_patterns)
        
        # Detect weekly patterns
        weekly_patterns = await self._detect_weekly_patterns(time_data)
        patterns.extend(weekly_patterns)
        
        # Detect activity bursts
        burst_patterns = await self._detect_activity_bursts(time_data)
        patterns.extend(burst_patterns)
        
        return patterns
    
    async def _detect_daily_patterns(self, time_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect daily patterns in activity.
        
        Args:
            time_data: List of time data points
            
        Returns:
            List of daily patterns
        """
        patterns = []
        
        # Group by hour
        hour_counts = defaultdict(int)
        hour_items = defaultdict(list)
        
        for item in time_data:
            hour = item["hour"]
            hour_counts[hour] += 1
            hour_items[hour].append(item["item"])
        
        # Find peak hours
        if hour_counts:
            avg_count = sum(hour_counts.values()) / len(hour_counts)
            peak_hours = []
            
            for hour, count in hour_counts.items():
                if count > avg_count * 1.5:  # Threshold for peak
                    peak_hours.append({
                        "hour": hour,
                        "count": count,
                        "items": hour_items[hour]
                    })
            
            if peak_hours:
                # Sort by count (highest first)
                peak_hours.sort(key=lambda x: x["count"], reverse=True)
                
                # Create pattern for peak activity hours
                patterns.append(Pattern(
                    pattern_id=generate_id("time"),
                    pattern_type="daily_activity",
                    frequency=sum(p["count"] for p in peak_hours),
                    confidence=0.9,
                    triggers=[],
                    impact_areas=["temporal", "behavior"],
                    metadata={
                        "peak_hours": [p["hour"] for p in peak_hours],
                        "peak_counts": [p["count"] for p in peak_hours],
                        "avg_count": avg_count
                    },
                    source_data=sum([p["items"] for p in peak_hours], [])
                ))
                
                # Create patterns for specific time periods
                time_periods = {
                    "morning": list(range(5, 12)),
                    "afternoon": list(range(12, 18)),
                    "evening": list(range(18, 23)),
                    "night": list(range(23, 24)) + list(range(0, 5))
                }
                
                for period, hours in time_periods.items():
                    period_count = sum(hour_counts.get(h, 0) for h in hours)
                    period_items = sum([hour_items.get(h, []) for h in hours], [])
                    
                    if period_count > avg_count * len(hours) * 1.2:  # Threshold for period pattern
                        patterns.append(Pattern(
                            pattern_id=generate_id("time"),
                            pattern_type="time_period_activity",
                            frequency=period_count,
                            confidence=0.8,
                            triggers=[period],
                            impact_areas=["temporal", "behavior"],
                            metadata={
                                "time_period": period,
                                "count": period_count,
                                "hours": hours
                            },
                            source_data=period_items
                        ))
        
        return patterns
    
    async def _detect_weekly_patterns(self, time_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect weekly patterns in activity.
        
        Args:
            time_data: List of time data points
            
        Returns:
            List of weekly patterns
        """
        patterns = []
        
        # Group by day of week
        day_counts = defaultdict(int)
        day_items = defaultdict(list)
        
        for item in time_data:
            day = item["day"]
            day_counts[day] += 1
            day_items[day].append(item["item"])
        
        # Find peak days
        if day_counts:
            avg_count = sum(day_counts.values()) / len(day_counts)
            peak_days = []
            
            for day, count in day_counts.items():
                if count > avg_count * 1.5:  # Threshold for peak
                    peak_days.append({
                        "day": day,
                        "count": count,
                        "items": day_items[day]
                    })
            
            if peak_days:
                # Sort by count (highest first)
                peak_days.sort(key=lambda x: x["count"], reverse=True)
                
                # Map day numbers to names
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                # Create pattern for peak activity days
                patterns.append(Pattern(
                    pattern_id=generate_id("time"),
                    pattern_type="weekly_activity",
                    frequency=sum(p["count"] for p in peak_days),
                    confidence=0.9,
                    triggers=[],
                    impact_areas=["temporal", "behavior"],
                    metadata={
                        "peak_days": [day_names[p["day"]] for p in peak_days],
                        "peak_counts": [p["count"] for p in peak_days],
                        "avg_count": avg_count
                    },
                    source_data=sum([p["items"] for p in peak_days], [])
                ))
                
                # Create patterns for weekday vs weekend
                weekday_count = sum(day_counts.get(d, 0) for d in range(0, 5))  # Monday-Friday
                weekend_count = sum(day_counts.get(d, 0) for d in range(5, 7))  # Saturday-Sunday
                
                weekday_items = sum([day_items.get(d, []) for d in range(0, 5)], [])
                weekend_items = sum([day_items.get(d, []) for d in range(5, 7)], [])
                
                # Normalize by number of days
                weekday_avg = weekday_count / 5
                weekend_avg = weekend_count / 2
                
                if weekday_avg > weekend_avg * 1.5:
                    patterns.append(Pattern(
                        pattern_id=generate_id("time"),
                        pattern_type="weekday_preference",
                        frequency=weekday_count,
                        confidence=0.8,
                        triggers=["weekday"],
                        impact_areas=["temporal", "behavior"],
                        metadata={
                            "weekday_count": weekday_count,
                            "weekend_count": weekend_count,
                            "weekday_avg": weekday_avg,
                            "weekend_avg": weekend_avg
                        },
                        source_data=weekday_items
                    ))
                elif weekend_avg > weekday_avg * 1.5:
                    patterns.append(Pattern(
                        pattern_id=generate_id("time"),
                        pattern_type="weekend_preference",
                        frequency=weekend_count,
                        confidence=0.8,
                        triggers=["weekend"],
                        impact_areas=["temporal", "behavior"],
                        metadata={
                            "weekday_count": weekday_count,
                            "weekend_count": weekend_count,
                            "weekday_avg": weekday_avg,
                            "weekend_avg": weekend_avg
                        },
                        source_data=weekend_items
                    ))
        
        return patterns
    
    async def _detect_activity_bursts(self, time_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect bursts of activity.
        
        Args:
            time_data: List of time data points
            
        Returns:
            List of burst patterns
        """
        patterns = []
        
        if len(time_data) < 3:
            return patterns
        
        # Sort by timestamp
        sorted_data = sorted(time_data, key=lambda x: x["datetime"])
        
        # Calculate time differences between consecutive items
        time_diffs = []
        for i in range(1, len(sorted_data)):
            diff = (sorted_data[i]["datetime"] - sorted_data[i-1]["datetime"]).total_seconds() / 60  # minutes
            time_diffs.append(diff)
        
        # Find bursts (clusters of activity with small time differences)
        bursts = []
        current_burst = []
        burst_threshold = 30  # minutes
        
        for i, diff in enumerate(time_diffs):
            if diff <= burst_threshold:
                if not current_burst:
                    current_burst = [sorted_data[i]["item"], sorted_data[i+1]["item"]]
                else:
                    current_burst.append(sorted_data[i+1]["item"])
            else:
                if len(current_burst) >= 3:  # Minimum burst size
                    bursts.append(current_burst)
                current_burst = []
        
        # Add the last burst if it exists
        if len(current_burst) >= 3:
            bursts.append(current_burst)
        
        # Create patterns for bursts
        for i, burst in enumerate(bursts):
            patterns.append(Pattern(
                pattern_id=generate_id("time"),
                pattern_type="activity_burst",
                frequency=len(burst),
                confidence=0.9,
                triggers=[],
                impact_areas=["temporal", "behavior"],
                metadata={
                    "burst_id": i,
                    "burst_size": len(burst),
                    "burst_duration_minutes": burst_threshold * (len(burst) - 1)
                },
                source_data=burst
            ))
        
        return patterns

class BehaviorPatternDetector(PatternDetectorBase):
    """Detector for behavioral patterns."""
    
    async def detect(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect behavioral patterns.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Extract behavior data
        behavior_data = []
        for item in data:
            behaviors = None
            
            if "metadata" in item and "behaviors" in item["metadata"]:
                behaviors = item["metadata"]["behaviors"]
            elif "behaviors" in item:
                behaviors = item["behaviors"]
            
            if behaviors:
                behavior_data.append({
                    "behaviors": behaviors,
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
        
        if not behavior_data:
            return patterns
        
        # Detect behavior sequences
        sequence_patterns = await self._detect_behavior_sequences(behavior_data)
        patterns.extend(sequence_patterns)
        
        # Detect behavior frequencies
        frequency_patterns = await self._detect_behavior_frequencies(behavior_data)
        patterns.extend(frequency_patterns)
        
        # Detect behavior co-occurrences
        cooccurrence_patterns = await self._detect_behavior_cooccurrences(behavior_data)
        patterns.extend(cooccurrence_patterns)
        
        return patterns
    
    async def _detect_behavior_sequences(self, behavior_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect sequences in behaviors.
        
        Args:
            behavior_data: List of behavior data points
            
        Returns:
            List of sequence patterns
        """
        patterns = []
        
        # Extract all behavior sequences
        sequences = []
        for item in behavior_data:
            behaviors = item["behaviors"]
            if isinstance(behaviors, list) and len(behaviors) > 1:
                sequences.append(behaviors)
        
        if not sequences:
            return patterns
        
        # Find common subsequences
        subsequences = defaultdict(int)
        
        for sequence in sequences:
            for i in range(len(sequence) - 1):
                for j in range(i + 2, min(i + 5, len(sequence) + 1)):
                    subsequence = tuple(sequence[i:j])
                    subsequences[subsequence] += 1
        
        # Create patterns for common subsequences
        for subsequence, count in subsequences.items():
            if count >= 2:  # Threshold for pattern
                # Find items containing this subsequence
                matching_items = []
                for item in behavior_data:
                    behaviors = item["behaviors"]
                    if isinstance(behaviors, list):
                        for i in range(len(behaviors) - len(subsequence) + 1):
                            if tuple(behaviors[i:i + len(subsequence)]) == subsequence:
                                matching_items.append(item["item"])
                                break
                
                patterns.append(Pattern(
                    pattern_id=generate_id("behavior"),
                    pattern_type="behavior_sequence",
                    frequency=count,
                    confidence=min(1.0, count / 10.0),
                    triggers=[],
                    impact_areas=["behavior"],
                    metadata={
                        "sequence": subsequence,
                        "sequence_length": len(subsequence)
                    },
                    source_data=matching_items
                ))
        
        return patterns
    
    async def _detect_behavior_frequencies(self, behavior_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect frequencies of specific behaviors.
        
        Args:
            behavior_data: List of behavior data points
            
        Returns:
            List of frequency patterns
        """
        patterns = []
        
        # Count behavior frequencies
        behavior_counts = defaultdict(int)
        behavior_items = defaultdict(list)
        
        for item in behavior_data:
            behaviors = item["behaviors"]
            if isinstance(behaviors, list):
                for behavior in behaviors:
                    behavior_counts[behavior] += 1
                    behavior_items[behavior].append(item["item"])
        
        # Create patterns for frequent behaviors
        for behavior, count in behavior_counts.items():
            if count >= 3:  # Threshold for pattern
                patterns.append(Pattern(
                    pattern_id=generate_id("behavior"),
                    pattern_type="behavior_frequency",
                    frequency=count,
                    confidence=min(1.0, count / len(behavior_data)),
                    triggers=[behavior],
                    impact_areas=["behavior"],
                    metadata={
                        "behavior": behavior,
                        "count": count
                    },
                    source_data=behavior_items[behavior]
                ))
        
        return patterns
    
    async def _detect_behavior_cooccurrences(self, behavior_data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect co-occurrences of behaviors.
        
        Args:
            behavior_data: List of behavior data points
            
        Returns:
            List of co-occurrence patterns
        """
        patterns = []
        
        # Count behavior co-occurrences
        cooccurrences = defaultdict(int)
        cooccurrence_items = defaultdict(list)
        
        for item in behavior_data:
            behaviors = item["behaviors"]
            if isinstance(behaviors, list) and len(behaviors) > 1:
                # Check all pairs of behaviors
                for i in range(len(behaviors)):
                    for j in range(i + 1, len(behaviors)):
                        pair = tuple(sorted([behaviors[i], behaviors[j]]))
                        cooccurrences[pair] += 1
                        cooccurrence_items[pair].append(item["item"])
        
        # Create patterns for frequent co-occurrences
        for pair, count in cooccurrences.items():
            if count >= 2:  # Threshold for pattern
                patterns.append(Pattern(
                    pattern_id=generate_id("behavior"),
                    pattern_type="behavior_cooccurrence",
                    frequency=count,
                    confidence=min(1.0, count / 10.0),
                    triggers=list(pair),
                    impact_areas=["behavior"],
                    metadata={
                        "behaviors": pair,
                        "count": count
                    },
                    source_data=cooccurrence_items[pair]
                ))
        
        return patterns

# Register all detectors
DETECTOR_REGISTRY = {
    "text": TextPatternDetector,
    "time": TimePatternDetector,
    "behavior": BehaviorPatternDetector,
}

def get_detector_class(detector_type: str):
    """
    Get detector class by type.
    
    Args:
        detector_type: Type of detector
        
    Returns:
        Detector class
        
    Raises:
        ValueError: If detector type is not found
    """
    if detector_type not in DETECTOR_REGISTRY:
        raise ValueError(f"Detector type not found: {detector_type}")
    
    return DETECTOR_REGISTRY[detector_type]

async def create_detector(detector_type: str, config: Dict[str, Any] = None):
    """
    Create a detector instance.
    
    Args:
        detector_type: Type of detector
        config: Configuration dictionary
        
    Returns:
        Detector instance
    """
    detector_class = get_detector_class(detector_type)
    return detector_class(config or {})