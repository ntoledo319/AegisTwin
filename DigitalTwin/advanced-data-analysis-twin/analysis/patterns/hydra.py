"""
Enhanced PatternHydra for multi-dimensional pattern detection.

This module extends the SpiderMind Omega PatternHydra with additional capabilities
for detecting patterns across various data dimensions.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

from core.logging import get_logger
from core.utils import generate_id, timestamp_now

# Import SpiderMind Omega's PatternHydra
import sys
import os
from pathlib import Path

# Add SpiderMind Omega to path
spidermind_path = Path(os.environ.get("SPIDERMIND_DIR", "../ct_omega"))
if spidermind_path.exists():
    sys.path.append(str(spidermind_path))
    
    try:
        from core.pattern_hydra import PatternHydra as SpiderMindPatternHydra
        from core.pattern_hydra import Pattern as SpiderMindPattern
        SPIDERMIND_AVAILABLE = True
    except ImportError:
        SPIDERMIND_AVAILABLE = False
else:
    SPIDERMIND_AVAILABLE = False

logger = get_logger(__name__)

class Pattern:
    """Enhanced pattern representation with additional metadata and analysis."""
    
    def __init__(
        self,
        pattern_id: str,
        pattern_type: str,
        frequency: int,
        confidence: float,
        triggers: List[str],
        impact_areas: List[str],
        metadata: Dict[str, Any],
        source_data: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize a pattern.
        
        Args:
            pattern_id: Unique identifier for the pattern
            pattern_type: Type of pattern (behavioral, emotional, etc.)
            frequency: How often the pattern occurs
            confidence: Confidence level in the pattern (0.0-1.0)
            triggers: List of triggers that cause this pattern
            impact_areas: Areas impacted by this pattern
            metadata: Additional pattern metadata
            source_data: Source data points that contributed to this pattern
        """
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type
        self.frequency = frequency
        self.confidence = confidence
        self.triggers = triggers
        self.impact_areas = impact_areas
        self.metadata = metadata
        self.source_data = source_data or []
        self.created_at = timestamp_now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "triggers": self.triggers,
            "impact_areas": self.impact_areas,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "source_data_count": len(self.source_data)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """Create pattern from dictionary."""
        return cls(
            pattern_id=data.get("pattern_id", generate_id("pattern")),
            pattern_type=data.get("pattern_type", "unknown"),
            frequency=data.get("frequency", 0),
            confidence=data.get("confidence", 0.0),
            triggers=data.get("triggers", []),
            impact_areas=data.get("impact_areas", []),
            metadata=data.get("metadata", {}),
            source_data=data.get("source_data", [])
        )
    
    @classmethod
    def from_spidermind_pattern(cls, pattern: Any) -> 'Pattern':
        """Convert SpiderMind pattern to enhanced pattern."""
        if not SPIDERMIND_AVAILABLE:
            raise ImportError("SpiderMind Omega is not available")
        
        return cls(
            pattern_id=getattr(pattern, "pattern_id", generate_id("pattern")),
            pattern_type=getattr(pattern, "pattern_type", "unknown"),
            frequency=getattr(pattern, "frequency", 0),
            confidence=getattr(pattern, "confidence", 0.0),
            triggers=getattr(pattern, "triggers", []),
            impact_areas=getattr(pattern, "impact_areas", []),
            metadata=getattr(pattern, "metadata", {}),
            source_data=[]
        )

class EnhancedPatternHydra:
    """
    Enhanced multi-headed pattern detection engine.
    
    This class extends SpiderMind Omega's PatternHydra with additional capabilities:
    - Relationship pattern detection
    - Communication pattern analysis
    - Productivity pattern recognition
    - Health and wellness pattern detection
    - Cross-dimensional pattern correlation
    - Temporal pattern evolution tracking
    """
    
    def __init__(self, data_dir=None, config: Dict[str, Any] = None):
        """
        Initialize the enhanced pattern hydra.
        
        Args:
            data_dir: Directory for storing pattern data
            config: Configuration dictionary
        """
        self.config = config or {}
        self.data_dir = data_dir
        self.pattern_cache = defaultdict(list)
        self.hydra_id = generate_id("pattern_hydra")
        
        # Initialize SpiderMind PatternHydra if available
        self.spidermind_hydra = None
        if SPIDERMIND_AVAILABLE:
            try:
                self.spidermind_hydra = SpiderMindPatternHydra(data_dir)
                logger.info("SpiderMind PatternHydra initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize SpiderMind PatternHydra: {str(e)}")
        
        # Initialize detection heads
        self.detection_heads = {
            'behavioral': self._detect_behavioral_patterns,
            'emotional': self._detect_emotional_patterns,
            'temporal': self._detect_temporal_patterns,
            'relationship': self._detect_relationship_patterns,
            'communication': self._detect_communication_patterns,
            'productivity': self._detect_productivity_patterns,
            'health': self._detect_health_patterns,
        }
    
    async def detect_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect patterns across all dimensions.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of detected patterns
        """
        all_patterns = []
        
        # Use SpiderMind PatternHydra if available
        if self.spidermind_hydra:
            try:
                spidermind_patterns = await self.spidermind_hydra.detect_emergent_patterns(data)
                
                # Convert SpiderMind patterns to enhanced patterns
                for pattern in spidermind_patterns:
                    all_patterns.append(Pattern.from_spidermind_pattern(pattern))
                
                logger.info(f"Detected {len(spidermind_patterns)} patterns using SpiderMind PatternHydra")
            except Exception as e:
                logger.warning(f"Failed to use SpiderMind PatternHydra: {str(e)}")
        
        # Run enhanced detection heads
        for head_name, detector in self.detection_heads.items():
            try:
                patterns = await detector(data)
                all_patterns.extend(patterns)
                logger.debug(f"Detected {len(patterns)} patterns with {head_name} head")
            except Exception as e:
                logger.warning(f"Pattern detection head {head_name} failed: {str(e)}")
        
        # Cross-correlate patterns between heads
        cross_patterns = await self._identify_cross_dimensional_patterns(all_patterns)
        all_patterns.extend(cross_patterns)
        
        # Deduplicate patterns
        unique_patterns = await self._deduplicate_patterns(all_patterns)
        
        logger.info(f"Detected {len(unique_patterns)} unique patterns across all dimensions")
        return unique_patterns
    
    async def _detect_behavioral_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect behavioral patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of behavioral patterns
        """
        patterns = []
        
        # Extract behavior sequences
        behaviors = []
        for item in data:
            if "metadata" in item and "behaviors" in item["metadata"]:
                behaviors.append(item["metadata"]["behaviors"])
            elif "behaviors" in item:
                behaviors.append(item["behaviors"])
        
        # Analyze behavior sequences
        behavior_sequences = self._extract_sequences(behaviors)
        
        for seq, freq in behavior_sequences.items():
            if freq > 2:  # Pattern threshold
                patterns.append(Pattern(
                    pattern_id=generate_id("behavior"),
                    pattern_type="behavioral_sequence",
                    frequency=freq,
                    confidence=min(1.0, freq / 10.0),
                    triggers=[],
                    impact_areas=["behavior"],
                    metadata={"sequence": seq},
                    source_data=[item for item in data if self._contains_sequence(item, seq)]
                ))
        
        return patterns
    
    async def _detect_emotional_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect emotional patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of emotional patterns
        """
        patterns = []
        
        # Extract emotional data
        emotional_data = []
        for item in data:
            if "analysis" in item and "sentiment" in item["analysis"]:
                emotional_data.append({
                    "timestamp": item.get("timestamp", ""),
                    "sentiment": item["analysis"]["sentiment"],
                    "item": item
                })
            elif "sentiment" in item:
                emotional_data.append({
                    "timestamp": item.get("timestamp", ""),
                    "sentiment": item["sentiment"],
                    "item": item
                })
        
        # Sort by timestamp if available
        emotional_data.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "")
        
        # Extract sentiment values
        sentiment_values = [item["sentiment"] for item in emotional_data]
        
        if len(sentiment_values) > 5:
            # Detect cyclical patterns
            cycles = self._detect_cycles(sentiment_values)
            for cycle in cycles:
                patterns.append(Pattern(
                    pattern_id=generate_id("emotion"),
                    pattern_type="emotional_cycle",
                    frequency=len(cycle),
                    confidence=0.7,
                    triggers=[],
                    impact_areas=["emotional", "cognitive"],
                    metadata={"cycle_length": len(cycle), "cycle_values": cycle},
                    source_data=[item["item"] for item in emotional_data[:len(cycle)]]
                ))
            
            # Detect sentiment shifts
            shifts = self._detect_shifts(sentiment_values, threshold=0.3)
            for shift in shifts:
                patterns.append(Pattern(
                    pattern_id=generate_id("emotion"),
                    pattern_type="sentiment_shift",
                    frequency=1,
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["emotional"],
                    metadata={
                        "shift_index": shift["index"],
                        "shift_magnitude": shift["magnitude"],
                        "shift_direction": shift["direction"]
                    },
                    source_data=[
                        emotional_data[shift["index"] - 1]["item"] if shift["index"] > 0 else None,
                        emotional_data[shift["index"]]["item"] if shift["index"] < len(emotional_data) else None
                    ]
                ))
        
        return patterns
    
    async def _detect_temporal_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect time-based patterns in data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of temporal patterns
        """
        patterns = []
        
        # Group by time of day, day of week, etc.
        temporal_groups = defaultdict(list)
        for item in data:
            timestamp = item.get("timestamp", "")
            if not timestamp:
                continue
            
            try:
                dt = datetime.fromisoformat(timestamp)
                hour_group = f"hour_{dt.hour // 4 * 4}"  # 4-hour blocks
                day_group = f"day_{dt.weekday()}"
                
                temporal_groups[hour_group].append(item)
                temporal_groups[day_group].append(item)
            except (ValueError, TypeError):
                continue
        
        # Identify temporal correlations
        for time_block, block_data in temporal_groups.items():
            if len(block_data) > 3:
                # Calculate average sentiment if available
                sentiments = []
                for item in block_data:
                    if "analysis" in item and "sentiment" in item["analysis"]:
                        sentiments.append(item["analysis"]["sentiment"])
                    elif "sentiment" in item:
                        sentiments.append(item["sentiment"])
                
                if sentiments:
                    avg_sentiment = np.mean(sentiments)
                    if avg_sentiment > 0.7 or avg_sentiment < 0.3:
                        patterns.append(Pattern(
                            pattern_id=generate_id("temporal"),
                            pattern_type="temporal_sentiment",
                            frequency=len(block_data),
                            confidence=abs(avg_sentiment - 0.5) * 2,
                            triggers=[time_block],
                            impact_areas=["temporal", "emotional"],
                            metadata={
                                "time_block": time_block,
                                "avg_sentiment": avg_sentiment,
                                "sentiment_direction": "positive" if avg_sentiment > 0.5 else "negative"
                            },
                            source_data=block_data
                        ))
        
        return patterns
    
    async def _detect_relationship_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect relationship patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of relationship patterns
        """
        patterns = []
        
        # Extract relationship data
        relationship_data = defaultdict(list)
        for item in data:
            # Extract sender and recipient for communication data
            sender = None
            recipient = None
            
            if "from" in item:
                sender = item["from"]
            elif "sender" in item:
                sender = item["sender"]
            
            if "to" in item:
                recipient = item["to"]
            elif "recipient" in item:
                recipient = item["recipient"]
            
            if sender and recipient:
                relationship_key = f"{sender}_{recipient}"
                relationship_data[relationship_key].append(item)
        
        # Analyze relationship patterns
        for relationship, rel_data in relationship_data.items():
            if len(rel_data) > 3:
                # Calculate communication frequency
                timestamps = []
                for item in rel_data:
                    if "timestamp" in item:
                        try:
                            dt = datetime.fromisoformat(item["timestamp"])
                            timestamps.append(dt)
                        except (ValueError, TypeError):
                            continue
                
                if timestamps:
                    # Sort timestamps
                    timestamps.sort()
                    
                    # Calculate average time between communications
                    time_diffs = []
                    for i in range(1, len(timestamps)):
                        diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # hours
                        time_diffs.append(diff)
                    
                    if time_diffs:
                        avg_time_diff = np.mean(time_diffs)
                        
                        patterns.append(Pattern(
                            pattern_id=generate_id("relationship"),
                            pattern_type="communication_frequency",
                            frequency=len(rel_data),
                            confidence=min(1.0, len(rel_data) / 10.0),
                            triggers=[relationship.split("_")[0]],  # Sender as trigger
                            impact_areas=["relationship", "communication"],
                            metadata={
                                "relationship": relationship,
                                "avg_hours_between_comm": avg_time_diff,
                                "total_communications": len(rel_data)
                            },
                            source_data=rel_data
                        ))
        
        return patterns
    
    async def _detect_communication_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect communication patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of communication patterns
        """
        patterns = []
        
        # Extract communication content
        communication_data = []
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
                communication_data.append({
                    "content": content,
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
        
        # Analyze communication length patterns
        if communication_data:
            content_lengths = [len(item["content"]) for item in communication_data]
            avg_length = np.mean(content_lengths)
            std_length = np.std(content_lengths)
            
            # Identify unusually long or short communications
            outliers = []
            for i, length in enumerate(content_lengths):
                z_score = (length - avg_length) / std_length if std_length > 0 else 0
                if abs(z_score) > 2:
                    outliers.append({
                        "index": i,
                        "z_score": z_score,
                        "length": length,
                        "type": "long" if z_score > 0 else "short"
                    })
            
            if outliers:
                patterns.append(Pattern(
                    pattern_id=generate_id("communication"),
                    pattern_type="content_length_variation",
                    frequency=len(outliers),
                    confidence=0.8,
                    triggers=[],
                    impact_areas=["communication"],
                    metadata={
                        "avg_length": avg_length,
                        "std_length": std_length,
                        "outliers": outliers
                    },
                    source_data=[communication_data[o["index"]]["item"] for o in outliers]
                ))
        
        return patterns
    
    async def _detect_productivity_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect productivity patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of productivity patterns
        """
        patterns = []
        
        # Extract productivity data
        productivity_data = []
        for item in data:
            if "metadata" in item and "productivity" in item["metadata"]:
                productivity_data.append({
                    "productivity": item["metadata"]["productivity"],
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
            elif "productivity" in item:
                productivity_data.append({
                    "productivity": item["productivity"],
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
        
        # Sort by timestamp if available
        productivity_data.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "")
        
        # Analyze productivity patterns
        if len(productivity_data) > 5:
            productivity_values = [item["productivity"] for item in productivity_data if isinstance(item["productivity"], (int, float))]
            
            if productivity_values:
                # Detect productivity cycles
                cycles = self._detect_cycles(productivity_values)
                for cycle in cycles:
                    patterns.append(Pattern(
                        pattern_id=generate_id("productivity"),
                        pattern_type="productivity_cycle",
                        frequency=len(cycle),
                        confidence=0.7,
                        triggers=[],
                        impact_areas=["productivity"],
                        metadata={"cycle_length": len(cycle), "cycle_values": cycle},
                        source_data=[item["item"] for item in productivity_data[:len(cycle)]]
                    ))
        
        return patterns
    
    async def _detect_health_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Detect health and wellness patterns from data.
        
        Args:
            data: List of data points to analyze
            
        Returns:
            List of health patterns
        """
        patterns = []
        
        # Extract health data
        health_data = []
        for item in data:
            if "metadata" in item and "health" in item["metadata"]:
                health_data.append({
                    "health": item["metadata"]["health"],
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
            elif "health" in item:
                health_data.append({
                    "health": item["health"],
                    "timestamp": item.get("timestamp", ""),
                    "item": item
                })
        
        # Sort by timestamp if available
        health_data.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "")
        
        # Analyze health patterns
        if len(health_data) > 5:
            # Extract sleep data if available
            sleep_data = []
            for item in health_data:
                if isinstance(item["health"], dict) and "sleep" in item["health"]:
                    sleep_data.append({
                        "sleep": item["health"]["sleep"],
                        "timestamp": item["timestamp"],
                        "item": item["item"]
                    })
            
            if sleep_data:
                sleep_values = [item["sleep"] for item in sleep_data if isinstance(item["sleep"], (int, float))]
                
                if sleep_values:
                    # Detect sleep cycles
                    cycles = self._detect_cycles(sleep_values)
                    for cycle in cycles:
                        patterns.append(Pattern(
                            pattern_id=generate_id("health"),
                            pattern_type="sleep_cycle",
                            frequency=len(cycle),
                            confidence=0.7,
                            triggers=[],
                            impact_areas=["health", "sleep"],
                            metadata={"cycle_length": len(cycle), "cycle_values": cycle},
                            source_data=[item["item"] for item in sleep_data[:len(cycle)]]
                        ))
        
        return patterns
    
    async def _identify_cross_dimensional_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """
        Identify patterns that span multiple dimensions.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of cross-dimensional patterns
        """
        cross_patterns = []
        
        # Group patterns by type
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern.pattern_type].append(pattern)
        
        # Look for correlations between different pattern types
        for type1, patterns1 in pattern_groups.items():
            for type2, patterns2 in pattern_groups.items():
                if type1 != type2:
                    correlations = self._find_pattern_correlations(patterns1, patterns2)
                    for correlation in correlations:
                        cross_patterns.append(Pattern(
                            pattern_id=generate_id("cross"),
                            pattern_type="cross_dimensional",
                            frequency=correlation["frequency"],
                            confidence=correlation["confidence"],
                            triggers=correlation["triggers"],
                            impact_areas=[type1, type2],
                            metadata=correlation,
                            source_data=correlation.get("source_data", [])
                        ))
        
        return cross_patterns
    
    async def _deduplicate_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """
        Deduplicate patterns based on similarity.
        
        Args:
            patterns: List of patterns to deduplicate
            
        Returns:
            List of unique patterns
        """
        if not patterns:
            return []
        
        # Group patterns by type
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern.pattern_type].append(pattern)
        
        unique_patterns = []
        
        # Process each pattern type separately
        for pattern_type, type_patterns in pattern_groups.items():
            # Sort by confidence (highest first)
            sorted_patterns = sorted(type_patterns, key=lambda p: p.confidence, reverse=True)
            
            # Keep track of patterns we've already seen
            seen_patterns = set()
            
            for pattern in sorted_patterns:
                # Create a simple hash of the pattern
                pattern_hash = self._create_pattern_hash(pattern)
                
                if pattern_hash not in seen_patterns:
                    unique_patterns.append(pattern)
                    seen_patterns.add(pattern_hash)
        
        return unique_patterns
    
    def _extract_sequences(self, data_list: List[List]) -> Dict[str, int]:
        """
        Extract recurring sequences from data.
        
        Args:
            data_list: List of data sequences
            
        Returns:
            Dictionary mapping sequences to frequencies
        """
        sequences = defaultdict(int)
        
        for data in data_list:
            if isinstance(data, list) and len(data) > 1:
                for i in range(len(data) - 1):
                    seq = f"{data[i]}->{data[i+1]}"
                    sequences[seq] += 1
        
        return dict(sequences)
    
    def _detect_cycles(self, values: List[float], min_cycle_length: int = 3) -> List[List[float]]:
        """
        Detect cyclical patterns in numerical data.
        
        Args:
            values: List of numerical values
            min_cycle_length: Minimum length for a cycle
            
        Returns:
            List of detected cycles
        """
        cycles = []
        
        if len(values) < min_cycle_length * 2:
            return cycles
        
        # Simple cycle detection using autocorrelation
        for cycle_len in range(min_cycle_length, len(values) // 2):
            correlation = self._calculate_autocorrelation(values, cycle_len)
            if correlation > 0.6:  # Strong correlation threshold
                cycles.append(values[:cycle_len])
        
        return cycles
    
    def _detect_shifts(self, values: List[float], threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Detect significant shifts in numerical data.
        
        Args:
            values: List of numerical values
            threshold: Threshold for significant shift
            
        Returns:
            List of detected shifts
        """
        shifts = []
        
        if len(values) < 2:
            return shifts
        
        for i in range(1, len(values)):
            diff = values[i] - values[i-1]
            if abs(diff) > threshold:
                shifts.append({
                    "index": i,
                    "magnitude": abs(diff),
                    "direction": "increase" if diff > 0 else "decrease"
                })
        
        return shifts
    
    def _calculate_autocorrelation(self, values: List[float], lag: int) -> float:
        """
        Calculate autocorrelation at given lag.
        
        Args:
            values: List of numerical values
            lag: Lag value
            
        Returns:
            Autocorrelation value
        """
        if len(values) <= lag:
            return 0.0
        
        n = len(values) - lag
        if n == 0:
            return 0.0
        
        mean_val = np.mean(values)
        numerator = sum((values[i] - mean_val) * (values[i + lag] - mean_val) for i in range(n))
        denominator = sum((val - mean_val) ** 2 for val in values)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _find_pattern_correlations(self, patterns1: List[Pattern], patterns2: List[Pattern]) -> List[Dict[str, Any]]:
        """
        Find correlations between different pattern types.
        
        Args:
            patterns1: First list of patterns
            patterns2: Second list of patterns
            
        Returns:
            List of correlation dictionaries
        """
        correlations = []
        
        # Simple correlation based on trigger overlap
        for p1 in patterns1:
            for p2 in patterns2:
                trigger_overlap = set(p1.triggers) & set(p2.triggers)
                
                # Check for source data overlap
                source_overlap = []
                if p1.source_data and p2.source_data:
                    # This is a simplification - in a real system, you'd need a more sophisticated
                    # way to identify the same data points across different patterns
                    p1_ids = {self._get_item_id(item) for item in p1.source_data if self._get_item_id(item)}
                    p2_ids = {self._get_item_id(item) for item in p2.source_data if self._get_item_id(item)}
                    source_overlap = list(p1_ids & p2_ids)
                
                if trigger_overlap or source_overlap:
                    correlation = {
                        'frequency': min(p1.frequency, p2.frequency),
                        'confidence': (p1.confidence + p2.confidence) / 2,
                        'triggers': list(trigger_overlap),
                        'pattern1': p1.pattern_id,
                        'pattern2': p2.pattern_id,
                        'pattern1_type': p1.pattern_type,
                        'pattern2_type': p2.pattern_type,
                        'source_overlap_count': len(source_overlap),
                        'source_data': []  # Would include overlapping source data in a real implementation
                    }
                    correlations.append(correlation)
        
        return correlations
    
    def _contains_sequence(self, item: Dict[str, Any], sequence: str) -> bool:
        """
        Check if an item contains a specific sequence.
        
        Args:
            item: Data item
            sequence: Sequence to check for
            
        Returns:
            True if the item contains the sequence, False otherwise
        """
        if "metadata" in item and "behaviors" in item["metadata"]:
            behaviors = item["metadata"]["behaviors"]
            if isinstance(behaviors, list) and len(behaviors) > 1:
                for i in range(len(behaviors) - 1):
                    seq = f"{behaviors[i]}->{behaviors[i+1]}"
                    if seq == sequence:
                        return True
        
        elif "behaviors" in item:
            behaviors = item["behaviors"]
            if isinstance(behaviors, list) and len(behaviors) > 1:
                for i in range(len(behaviors) - 1):
                    seq = f"{behaviors[i]}->{behaviors[i+1]}"
                    if seq == sequence:
                        return True
        
        return False
    
    def _get_item_id(self, item: Dict[str, Any]) -> str:
        """
        Get a unique identifier for a data item.
        
        Args:
            item: Data item
            
        Returns:
            Unique identifier string
        """
        if "id" in item:
            return str(item["id"])
        elif "source_id" in item:
            return str(item["source_id"])
        elif "timestamp" in item and ("content" in item or "body" in item or "text" in item):
            content = item.get("content", item.get("body", item.get("text", "")))
            return f"{item['timestamp']}_{hash(content)}"
        else:
            return ""
    
    def _create_pattern_hash(self, pattern: Pattern) -> str:
        """
        Create a simple hash for a pattern to identify duplicates.
        
        Args:
            pattern: Pattern to hash
            
        Returns:
            Hash string
        """
        components = [
            pattern.pattern_type,
            ",".join(sorted(pattern.triggers)),
            ",".join(sorted(pattern.impact_areas)),
            str(pattern.frequency)
        ]
        
        return "_".join(components)