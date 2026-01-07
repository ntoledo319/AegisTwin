"""
Pattern Learner Module - Autonomous Pattern Recognition and Learning

Learns patterns from system behavior, detects anomalies, and adapts
to changing conditions. Inspired by SEED learning capabilities.
"""

import asyncio
import logging
import time
import numpy as np
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns"""
    TEMPORAL = "temporal"  # Time-based patterns
    SEQUENTIAL = "sequential"  # Event sequences
    CORRELATION = "correlation"  # Correlated metrics
    ANOMALY = "anomaly"  # Anomalous behavior
    TREND = "trend"  # Long-term trends


@dataclass
class Pattern:
    """Detected pattern"""
    pattern_type: PatternType
    name: str
    confidence: float
    description: str
    data: Dict[str, Any]
    detected_at: float
    occurrences: int = 1
    last_seen: float = 0.0


class PatternLearner(Module):
    """
    Autonomous pattern learning and recognition module.
    
    Analyzes system behavior to detect patterns, learn from them,
    and adapt to changing conditions.
    
    Events consumed:
    - learner/analyze: Analyze data for patterns
    - collector/summary: Data summaries
    - health/telemetry: System telemetry
    - module/performance: Module performance
    
    Events emitted:
    - learner/pattern_detected: New pattern discovered
    - learner/anomaly_detected: Anomaly found
    - learner/prediction: Predicted event
    """
    
    name = "pattern_learner"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        learning_interval=120.0,
        pattern_threshold=0.7
    ):
        """
        Initialize pattern learner.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            learning_interval: Seconds between learning cycles (default: 2 min)
            pattern_threshold: Minimum confidence for pattern detection
        """
        super().__init__(bus, ex, policy)
        self.learning_interval = learning_interval
        self.pattern_threshold = pattern_threshold
        
        # Pattern storage
        self.patterns: Dict[str, Pattern] = {}
        self.temporal_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.sequence_buffer: deque = deque(maxlen=100)
        
        # Learning state
        self._learning_task: Optional[asyncio.Task] = None
        self._learning_enabled = True
        self._pattern_count = 0
        self._anomaly_count = 0
        
        # Baseline models for anomaly detection
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    async def start(self) -> None:
        """Start pattern learning"""
        await super().start()
        
        # Subscribe to data sources
        await self.bus.subscribe("learner/analyze", self._handle_analyze)
        await self.bus.subscribe("collector/summary", self._handle_summary)
        await self.bus.subscribe("health/telemetry", self._handle_telemetry)
        await self.bus.subscribe("module/performance", self._handle_performance)
        
        # Start learning loop
        self._learning_task = asyncio.create_task(self._learning_loop())
        
        self.log.info("Pattern learner started")
    
    async def stop(self) -> None:
        """Stop pattern learning"""
        self._learning_enabled = False
        
        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("Pattern learner stopped")
    
    async def _learning_loop(self) -> None:
        """Periodic learning loop"""
        while self._learning_enabled:
            try:
                await asyncio.sleep(self.learning_interval)
                
                # Run pattern detection
                patterns = await self._detect_patterns()
                
                # Emit newly detected patterns
                for pattern in patterns:
                    if pattern.confidence >= self.pattern_threshold:
                        await self.emit("learner/pattern_detected", {
                            "pattern_type": pattern.pattern_type.value,
                            "name": pattern.name,
                            "confidence": pattern.confidence,
                            "description": pattern.description,
                            "data": pattern.data
                        })
                
                # Detect anomalies
                anomalies = await self._detect_anomalies()
                
                # Emit anomalies
                for anomaly in anomalies:
                    await self.emit("learner/anomaly_detected", {
                        "anomaly": anomaly['name'],
                        "severity": anomaly['severity'],
                        "details": anomaly['details']
                    })
                
            except Exception as e:
                self.log.error(f"Learning loop error: {e}")
                await asyncio.sleep(self.learning_interval)
    
    async def _handle_analyze(self, msg: Message) -> None:
        """Handle analysis request"""
        try:
            data_type = msg.data.get('data_type')
            data = msg.data.get('data', [])
            
            # Analyze provided data
            patterns = await self._analyze_data(data_type, data)
            
            await self.emit("learner/analysis_result", {
                "request_id": msg.data.get('request_id'),
                "patterns_found": len(patterns),
                "patterns": [self._pattern_to_dict(p) for p in patterns]
            })
            
        except Exception as e:
            self.log.error(f"Error handling analyze request: {e}")
    
    async def _handle_summary(self, msg: Message) -> None:
        """Handle data summary"""
        try:
            data = msg.data
            
            # Extract time-series data
            for series_name, series_data in data.get('data_series', {}).items():
                if isinstance(series_data, dict) and 'mean' in series_data:
                    self.temporal_data[series_name].append({
                        'value': series_data['mean'],
                        'timestamp': data.get('timestamp', time.time())
                    })
            
        except Exception as e:
            self.log.error(f"Error handling summary: {e}")
    
    async def _handle_telemetry(self, msg: Message) -> None:
        """Handle telemetry data"""
        try:
            data = msg.data
            timestamp = data.get('ts', time.time())
            
            # Store telemetry in temporal data
            for key in ['cpu', 'mem', 'disk']:
                if key in data:
                    self.temporal_data[key].append({
                        'value': data[key],
                        'timestamp': timestamp
                    })
            
            # Add to sequence buffer
            self.sequence_buffer.append({
                'event': 'telemetry',
                'data': data,
                'timestamp': timestamp
            })
            
        except Exception as e:
            self.log.error(f"Error handling telemetry: {e}")
    
    async def _handle_performance(self, msg: Message) -> None:
        """Handle performance data"""
        try:
            data = msg.data
            module_name = data.get('module', 'unknown')
            
            # Store performance metrics
            key = f"perf_{module_name}_latency"
            self.temporal_data[key].append({
                'value': data.get('latency', 0),
                'timestamp': time.time()
            })
            
            # Add to sequence buffer
            self.sequence_buffer.append({
                'event': 'performance',
                'module': module_name,
                'data': data,
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.log.error(f"Error handling performance: {e}")
    
    async def _detect_patterns(self) -> List[Pattern]:
        """Detect patterns in collected data"""
        patterns = []
        
        # Detect temporal patterns
        patterns.extend(await self._detect_temporal_patterns())
        
        # Detect sequential patterns
        patterns.extend(await self._detect_sequential_patterns())
        
        # Detect correlations
        patterns.extend(await self._detect_correlations())
        
        # Detect trends
        patterns.extend(await self._detect_trends())
        
        # Store detected patterns
        for pattern in patterns:
            pattern_key = f"{pattern.pattern_type.value}_{pattern.name}"
            
            if pattern_key in self.patterns:
                # Update existing pattern
                existing = self.patterns[pattern_key]
                existing.occurrences += 1
                existing.last_seen = time.time()
                existing.confidence = (existing.confidence + pattern.confidence) / 2
            else:
                # Store new pattern
                pattern.last_seen = time.time()
                self.patterns[pattern_key] = pattern
                self._pattern_count += 1
        
        return patterns
    
    async def _detect_temporal_patterns(self) -> List[Pattern]:
        """Detect time-based patterns"""
        patterns = []
        
        try:
            # Analyze temporal data for periodicities
            for key, data in self.temporal_data.items():
                if len(data) < 20:
                    continue
                
                values = [d['value'] for d in data]
                timestamps = [d['timestamp'] for d in data]
                
                # Check for daily patterns (simplified)
                if len(values) >= 24:
                    # Calculate hourly averages
                    hourly_avg = {}
                    for i, (val, ts) in enumerate(zip(values[-24:], timestamps[-24:])):
                        hour = int(ts % 86400 / 3600)  # Hour of day
                        if hour not in hourly_avg:
                            hourly_avg[hour] = []
                        hourly_avg[hour].append(val)
                    
                    # Check if there's a clear pattern
                    if len(hourly_avg) >= 12:
                        hour_avgs = {h: sum(vals)/len(vals) for h, vals in hourly_avg.items()}
                        peak_hour = max(hour_avgs.items(), key=lambda x: x[1])[0]
                        low_hour = min(hour_avgs.items(), key=lambda x: x[1])[0]
                        
                        patterns.append(Pattern(
                            pattern_type=PatternType.TEMPORAL,
                            name=f"{key}_daily_pattern",
                            confidence=0.8,
                            description=f"{key} shows daily pattern: peak at {peak_hour}:00, low at {low_hour}:00",
                            data={
                                'peak_hour': peak_hour,
                                'low_hour': low_hour,
                                'hourly_averages': hour_avgs
                            },
                            detected_at=time.time()
                        ))
        
        except Exception as e:
            self.log.error(f"Error detecting temporal patterns: {e}")
        
        return patterns
    
    async def _detect_sequential_patterns(self) -> List[Pattern]:
        """Detect event sequence patterns"""
        patterns = []
        
        try:
            if len(self.sequence_buffer) < 10:
                return patterns
            
            # Look for repeating sequences
            events = [e['event'] for e in self.sequence_buffer]
            
            # Find common subsequences (simplified)
            for length in [2, 3, 4]:
                if len(events) < length:
                    continue
                
                sequences = defaultdict(int)
                for i in range(len(events) - length + 1):
                    seq = tuple(events[i:i+length])
                    sequences[seq] += 1
                
                # Find frequent sequences
                for seq, count in sequences.items():
                    if count >= 3:  # Occurred at least 3 times
                        patterns.append(Pattern(
                            pattern_type=PatternType.SEQUENTIAL,
                            name=f"sequence_{'-'.join(seq)}",
                            confidence=min(0.95, count / 10),
                            description=f"Frequent event sequence: {' -> '.join(seq)}",
                            data={
                                'sequence': list(seq),
                                'occurrences': count
                            },
                            detected_at=time.time()
                        ))
        
        except Exception as e:
            self.log.error(f"Error detecting sequential patterns: {e}")
        
        return patterns
    
    async def _detect_correlations(self) -> List[Pattern]:
        """Detect correlations between metrics"""
        patterns = []
        
        try:
            # Get all metric keys with sufficient data
            metric_keys = [k for k, v in self.temporal_data.items() if len(v) >= 20]
            
            # Check pairs for correlation
            for i, key1 in enumerate(metric_keys):
                for key2 in metric_keys[i+1:]:
                    correlation = self._calculate_correlation(key1, key2)
                    
                    if abs(correlation) > 0.7:  # Strong correlation
                        patterns.append(Pattern(
                            pattern_type=PatternType.CORRELATION,
                            name=f"correlation_{key1}_{key2}",
                            confidence=abs(correlation),
                            description=f"Strong {'positive' if correlation > 0 else 'negative'} correlation between {key1} and {key2}",
                            data={
                                'metric1': key1,
                                'metric2': key2,
                                'correlation': correlation
                            },
                            detected_at=time.time()
                        ))
        
        except Exception as e:
            self.log.error(f"Error detecting correlations: {e}")
        
        return patterns
    
    async def _detect_trends(self) -> List[Pattern]:
        """Detect trends in metrics"""
        patterns = []
        
        try:
            for key, data in self.temporal_data.items():
                if len(data) < 30:
                    continue
                
                values = [d['value'] for d in data]
                
                # Calculate trend (simplified linear regression)
                n = len(values)
                x = list(range(n))
                mean_x = sum(x) / n
                mean_y = sum(values) / n
                
                slope_num = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
                slope_den = sum((x[i] - mean_x) ** 2 for i in range(n))
                
                if slope_den > 0:
                    slope = slope_num / slope_den
                    
                    # Significant trend if slope is substantial
                    if abs(slope) > 0.1:
                        trend_type = "increasing" if slope > 0 else "decreasing"
                        
                        patterns.append(Pattern(
                            pattern_type=PatternType.TREND,
                            name=f"{key}_trend",
                            confidence=min(0.9, abs(slope)),
                            description=f"{key} shows {trend_type} trend",
                            data={
                                'slope': slope,
                                'trend': trend_type,
                                'start_value': values[0],
                                'end_value': values[-1]
                            },
                            detected_at=time.time()
                        ))
        
        except Exception as e:
            self.log.error(f"Error detecting trends: {e}")
        
        return patterns
    
    async def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in system behavior"""
        anomalies = []
        
        try:
            for key, data in self.temporal_data.items():
                if len(data) < 20:
                    continue
                
                values = [d['value'] for d in data]
                
                # Update baseline if needed
                if key not in self.baselines:
                    self.baselines[key] = self._calculate_baseline(values[:-1])
                
                # Check recent values against baseline
                baseline = self.baselines[key]
                recent_values = values[-5:]
                
                for value in recent_values:
                    deviation = abs(value - baseline['mean']) / max(baseline['std'], 0.1)
                    
                    if deviation > 3:  # More than 3 standard deviations
                        anomalies.append({
                            'name': f"anomaly_{key}",
                            'metric': key,
                            'value': value,
                            'baseline_mean': baseline['mean'],
                            'deviation': deviation,
                            'severity': 'high' if deviation > 5 else 'medium',
                            'details': f"{key} value {value} deviates {deviation:.1f}σ from baseline {baseline['mean']:.1f}",
                            'timestamp': time.time()
                        })
                        
                        self._anomaly_count += 1
                
                # Periodically update baseline
                if len(values) % 100 == 0:
                    self.baselines[key] = self._calculate_baseline(values)
        
        except Exception as e:
            self.log.error(f"Error detecting anomalies: {e}")
        
        return anomalies
    
    def _calculate_correlation(self, key1: str, key2: str) -> float:
        """Calculate correlation between two metrics"""
        try:
            data1 = list(self.temporal_data[key1])
            data2 = list(self.temporal_data[key2])
            
            # Align data by timestamp
            min_len = min(len(data1), len(data2))
            values1 = [d['value'] for d in data1[-min_len:]]
            values2 = [d['value'] for d in data2[-min_len:]]
            
            if min_len < 2:
                return 0.0
            
            # Calculate Pearson correlation
            mean1 = sum(values1) / len(values1)
            mean2 = sum(values2) / len(values2)
            
            numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
            denominator = (
                sum((v1 - mean1) ** 2 for v1 in values1) ** 0.5 *
                sum((v2 - mean2) ** 2 for v2 in values2) ** 0.5
            )
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception as e:
            self.log.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _calculate_baseline(self, values: List[float]) -> Dict[str, float]:
        """Calculate baseline statistics"""
        if not values:
            return {'mean': 0.0, 'std': 0.0}
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        
        return {'mean': mean, 'std': std}
    
    async def _analyze_data(self, data_type: str, data: List[Any]) -> List[Pattern]:
        """Analyze provided data for patterns"""
        # Store data temporarily and detect patterns
        temp_key = f"temp_{data_type}"
        
        for item in data:
            self.temporal_data[temp_key].append({
                'value': item if isinstance(item, (int, float)) else 0,
                'timestamp': time.time()
            })
        
        # Detect patterns in this data
        patterns = []
        
        # Add to pattern detection queue
        patterns.extend(await self._detect_temporal_patterns())
        patterns.extend(await self._detect_trends())
        
        # Clean up temporary data
        if temp_key in self.temporal_data:
            del self.temporal_data[temp_key]
        
        return patterns
    
    def _pattern_to_dict(self, pattern: Pattern) -> Dict[str, Any]:
        """Convert pattern to dictionary"""
        return {
            'pattern_type': pattern.pattern_type.value,
            'name': pattern.name,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'data': pattern.data,
            'detected_at': pattern.detected_at,
            'occurrences': pattern.occurrences,
            'last_seen': pattern.last_seen
        }
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        # Handled by specific subscribers
        pass
    
    def get_stats(self) -> dict:
        """Get learner statistics"""
        stats = super().get_stats()
        
        stats.update({
            "learning_enabled": self._learning_enabled,
            "patterns_detected": self._pattern_count,
            "anomalies_detected": self._anomaly_count,
            "patterns_stored": len(self.patterns),
            "temporal_data_series": len(self.temporal_data),
            "sequence_buffer_size": len(self.sequence_buffer),
            "baselines_established": len(self.baselines)
        })
        return stats
