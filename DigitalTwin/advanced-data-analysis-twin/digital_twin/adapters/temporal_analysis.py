"""
Temporal Analysis Engine for the Digital Twin.

This module provides functionality for analyzing temporal patterns in user data,
integrating with SpiderMind Omega's TimeWeaver for advanced temporal analysis.
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import importlib.util
from collections import defaultdict

logger = logging.getLogger(__name__)


class TemporalAnalysisEngine:
    """
    Engine for analyzing temporal patterns in user data.
    
    Integrates with SpiderMind Omega's TimeWeaver for advanced temporal analysis
    and provides fallback implementations when SpiderMind components are not available.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the temporal analysis engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.time_weaver = None
        self.temporal_detector = None
        self.temporal_structures = None
        self._initialize_time_weaver()
        logger.info("Temporal Analysis Engine initialized")

    def _initialize_time_weaver(self) -> None:
        """
        Initialize TimeWeaver from SpiderMind Omega.
        """
        try:
            # Try to import TimeWeaver from SpiderMind Omega
            spidermind_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ct_omega"))
            
            if spidermind_path not in sys.path:
                sys.path.append(spidermind_path)
                
            # Try to import the TimeWeaver class
            spec = importlib.util.find_spec("core.time_weaver")
            if spec:
                time_weaver_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(time_weaver_module)
                self.time_weaver = time_weaver_module.TimeWeaver()
                logger.info("Successfully imported TimeWeaver from SpiderMind Omega")
            else:
                logger.warning("Could not find TimeWeaver module in SpiderMind Omega")
                self.time_weaver = None
                
            # Try to import the TemporalDetector class
            spec = importlib.util.find_spec("core.temporal_detector")
            if spec:
                temporal_detector_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(temporal_detector_module)
                self.temporal_detector = temporal_detector_module.TemporalDetector()
                logger.info("Successfully imported TemporalDetector from SpiderMind Omega")
            else:
                logger.warning("Could not find TemporalDetector module in SpiderMind Omega")
                self.temporal_detector = None
                
            # Try to import the temporal_structures module
            spec = importlib.util.find_spec("core.temporal_structures")
            if spec:
                temporal_structures_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(temporal_structures_module)
                self.temporal_structures = temporal_structures_module
                logger.info("Successfully imported temporal_structures from SpiderMind Omega")
            else:
                logger.warning("Could not find temporal_structures module in SpiderMind Omega")
                self.temporal_structures = None
                
        except Exception as e:
            logger.error(f"Error initializing TimeWeaver: {str(e)}")
            logger.warning("Using fallback temporal analysis")
            self.time_weaver = None
            self.temporal_detector = None
            self.temporal_structures = None

    async def analyze_temporal_patterns(self, temporal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in user data.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            Dictionary of temporal patterns and analysis results
        """
        # If TimeWeaver is available, use it
        if self.time_weaver:
            try:
                # Convert data to TimeWeaver format
                weaver_input = self._convert_to_weaver_format(temporal_data)
                
                # Analyze temporal patterns
                patterns = await self.time_weaver.analyze(weaver_input)
                
                # Convert results to our format
                return self._convert_from_weaver_format(patterns)
            except Exception as e:
                logger.error(f"Error using TimeWeaver: {str(e)}")
                logger.warning("Falling back to basic temporal analysis")
                
        # Fallback: Use basic temporal analysis
        return self._basic_temporal_analysis(temporal_data)

    async def detect_cycles(self, temporal_data: List[Dict[str, Any]], 
                          min_cycle_length: int = 1, 
                          max_cycle_length: int = 30) -> List[Dict[str, Any]]:
        """
        Detect cycles in temporal data.

        Args:
            temporal_data: List of timestamped data points
            min_cycle_length: Minimum cycle length in days
            max_cycle_length: Maximum cycle length in days

        Returns:
            List of detected cycles with metadata
        """
        # If TemporalDetector is available, use it
        if self.temporal_detector:
            try:
                # Convert data to TemporalDetector format
                detector_input = self._convert_to_detector_format(temporal_data)
                
                # Detect cycles
                cycles = await self.temporal_detector.detect_cycles(
                    detector_input, 
                    min_cycle_length=min_cycle_length,
                    max_cycle_length=max_cycle_length
                )
                
                # Convert results to our format
                return self._convert_cycles_from_detector_format(cycles)
            except Exception as e:
                logger.error(f"Error using TemporalDetector: {str(e)}")
                logger.warning("Falling back to basic cycle detection")
                
        # Fallback: Use basic cycle detection
        return self._basic_cycle_detection(temporal_data, min_cycle_length, max_cycle_length)

    async def predict_future_patterns(self, temporal_data: List[Dict[str, Any]], 
                                    prediction_days: int = 7) -> List[Dict[str, Any]]:
        """
        Predict future patterns based on historical data.

        Args:
            temporal_data: List of timestamped data points
            prediction_days: Number of days to predict into the future

        Returns:
            List of predicted data points
        """
        # If TimeWeaver is available, use it
        if self.time_weaver:
            try:
                # Convert data to TimeWeaver format
                weaver_input = self._convert_to_weaver_format(temporal_data)
                
                # Add prediction parameters
                weaver_input['prediction_horizon'] = prediction_days
                
                # Predict future patterns
                predictions = await self.time_weaver.predict_future(weaver_input)
                
                # Convert results to our format
                return self._convert_predictions_from_weaver_format(predictions)
            except Exception as e:
                logger.error(f"Error using TimeWeaver for prediction: {str(e)}")
                logger.warning("Falling back to basic pattern prediction")
                
        # Fallback: Use basic pattern prediction
        return self._basic_pattern_prediction(temporal_data, prediction_days)

    async def analyze_behavior_changes(self, temporal_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze significant changes in behavior over time.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            List of detected behavior changes with metadata
        """
        # If TemporalDetector is available, use it
        if self.temporal_detector:
            try:
                # Convert data to TemporalDetector format
                detector_input = self._convert_to_detector_format(temporal_data)
                
                # Detect behavior changes
                changes = await self.temporal_detector.detect_changes(detector_input)
                
                # Convert results to our format
                return self._convert_changes_from_detector_format(changes)
            except Exception as e:
                logger.error(f"Error using TemporalDetector for change detection: {str(e)}")
                logger.warning("Falling back to basic change detection")
                
        # Fallback: Use basic change detection
        return self._basic_change_detection(temporal_data)

    async def generate_temporal_insights(self, temporal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate insights from temporal data analysis.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            Dictionary of insights derived from temporal analysis
        """
        insights = {}
        
        # Analyze patterns
        patterns = await self.analyze_temporal_patterns(temporal_data)
        insights['patterns'] = patterns
        
        # Detect cycles
        cycles = await self.detect_cycles(temporal_data)
        insights['cycles'] = cycles
        
        # Detect behavior changes
        changes = await self.analyze_behavior_changes(temporal_data)
        insights['behavior_changes'] = changes
        
        # Generate summary insights
        insights['summary'] = self._generate_summary_insights(patterns, cycles, changes)
        
        return insights

    def _convert_to_weaver_format(self, temporal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert temporal data to TimeWeaver format.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            Data in TimeWeaver format
        """
        # Extract time range
        timestamps = [self._parse_timestamp(item.get('timestamp')) for item in temporal_data if 'timestamp' in item]
        
        if not timestamps:
            return {
                'temporal_data': temporal_data,
                'analysis_types': ['patterns', 'cycles', 'trends'],
                'time_range': {
                    'start': datetime.now().isoformat(),
                    'end': datetime.now().isoformat()
                },
                'resolution': 'day'
            }
        
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Determine appropriate resolution
        time_span = (end_time - start_time).total_seconds()
        if time_span < 86400:  # Less than a day
            resolution = 'hour'
        elif time_span < 604800:  # Less than a week
            resolution = 'day'
        elif time_span < 2592000:  # Less than a month
            resolution = 'week'
        else:
            resolution = 'month'
        
        return {
            'temporal_data': temporal_data,
            'analysis_types': ['patterns', 'cycles', 'trends'],
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'resolution': resolution
        }

    def _convert_from_weaver_format(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert TimeWeaver results to our format.

        Args:
            patterns: TimeWeaver analysis results

        Returns:
            Results in our format
        """
        return {
            'temporal_patterns': patterns.get('patterns', []),
            'cycles': patterns.get('cycles', []),
            'trends': patterns.get('trends', []),
            'stability': patterns.get('stability', 0.5),
            'periodicity': patterns.get('periodicity', 0.0),
            'consistency': patterns.get('consistency', 0.5),
            'anomalies': patterns.get('anomalies', [])
        }

    def _convert_to_detector_format(self, temporal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert temporal data to TemporalDetector format.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            Data in TemporalDetector format
        """
        # Extract time series data
        time_series = []
        
        for item in temporal_data:
            if 'timestamp' in item and 'value' in item:
                timestamp = self._parse_timestamp(item['timestamp'])
                time_series.append({
                    'timestamp': timestamp.isoformat(),
                    'value': item['value'],
                    'metadata': {k: v for k, v in item.items() if k not in ['timestamp', 'value']}
                })
        
        return {
            'time_series': time_series,
            'detection_params': {
                'sensitivity': 0.7,
                'min_confidence': 0.5,
                'anomaly_threshold': 2.0
            }
        }

    def _convert_cycles_from_detector_format(self, cycles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert TemporalDetector cycle results to our format.

        Args:
            cycles: TemporalDetector cycle results

        Returns:
            Cycles in our format
        """
        converted_cycles = []
        
        for cycle in cycles:
            converted_cycle = {
                'period': cycle.get('period', 0),
                'period_unit': cycle.get('period_unit', 'days'),
                'confidence': cycle.get('confidence', 0.0),
                'strength': cycle.get('strength', 0.0),
                'phase': cycle.get('phase', 0.0),
                'description': cycle.get('description', ''),
                'detected_occurrences': cycle.get('occurrences', 0)
            }
            converted_cycles.append(converted_cycle)
        
        return converted_cycles

    def _convert_changes_from_detector_format(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert TemporalDetector change results to our format.

        Args:
            changes: TemporalDetector change results

        Returns:
            Changes in our format
        """
        converted_changes = []
        
        for change in changes:
            converted_change = {
                'timestamp': change.get('timestamp', ''),
                'change_type': change.get('type', 'unknown'),
                'magnitude': change.get('magnitude', 0.0),
                'confidence': change.get('confidence', 0.0),
                'before_value': change.get('before', 0.0),
                'after_value': change.get('after', 0.0),
                'description': change.get('description', '')
            }
            converted_changes.append(converted_change)
        
        return converted_changes

    def _convert_predictions_from_weaver_format(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert TimeWeaver prediction results to our format.

        Args:
            predictions: TimeWeaver prediction results

        Returns:
            Predictions in our format
        """
        converted_predictions = []
        
        for prediction in predictions.get('predictions', []):
            converted_prediction = {
                'timestamp': prediction.get('timestamp', ''),
                'value': prediction.get('value', 0.0),
                'confidence': prediction.get('confidence', 0.0),
                'prediction_basis': prediction.get('basis', 'pattern'),
                'upper_bound': prediction.get('upper_bound', prediction.get('value', 0.0) * 1.2),
                'lower_bound': prediction.get('lower_bound', prediction.get('value', 0.0) * 0.8)
            }
            converted_predictions.append(converted_prediction)
        
        return converted_predictions

    def _basic_temporal_analysis(self, temporal_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform basic temporal analysis without SpiderMind components.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            Basic temporal analysis results
        """
        # Extract time series data
        time_series = []
        
        for item in temporal_data:
            if 'timestamp' in item and 'value' in item:
                timestamp = self._parse_timestamp(item['timestamp'])
                time_series.append((timestamp, item['value']))
        
        if not time_series:
            return {
                'temporal_patterns': [],
                'cycles': [],
                'trends': [],
                'stability': 0.5,
                'periodicity': 0.0,
                'consistency': 0.5,
                'anomalies': []
            }
        
        # Sort by timestamp
        time_series.sort(key=lambda x: x[0])
        
        # Calculate basic statistics
        values = [value for _, value in time_series]
        mean_value = sum(values) / len(values)
        
        # Detect trend
        trend = self._calculate_basic_trend(time_series)
        
        # Detect basic patterns
        patterns = self._detect_basic_patterns(time_series)
        
        # Calculate stability
        stability = self._calculate_stability(values)
        
        # Detect anomalies
        anomalies = self._detect_basic_anomalies(time_series, mean_value)
        
        return {
            'temporal_patterns': patterns,
            'cycles': [],  # Basic analysis doesn't detect cycles
            'trends': [trend] if trend['strength'] > 0.1 else [],
            'stability': stability,
            'periodicity': 0.0,  # Basic analysis doesn't calculate periodicity
            'consistency': stability,
            'anomalies': anomalies
        }

    def _basic_cycle_detection(self, temporal_data: List[Dict[str, Any]], 
                             min_cycle_length: int, 
                             max_cycle_length: int) -> List[Dict[str, Any]]:
        """
        Perform basic cycle detection without SpiderMind components.

        Args:
            temporal_data: List of timestamped data points
            min_cycle_length: Minimum cycle length in days
            max_cycle_length: Maximum cycle length in days

        Returns:
            List of detected cycles
        """
        # Extract time series data
        time_series = []
        
        for item in temporal_data:
            if 'timestamp' in item and 'value' in item:
                timestamp = self._parse_timestamp(item['timestamp'])
                time_series.append((timestamp, item['value']))
        
        if not time_series:
            return []
        
        # Sort by timestamp
        time_series.sort(key=lambda x: x[0])
        
        # Very basic cycle detection - look for repeating patterns in daily data
        # This is a simplified approach and won't detect complex cycles
        
        # Group by day of week
        day_of_week_values = defaultdict(list)
        
        for timestamp, value in time_series:
            day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
            day_of_week_values[day_of_week].append(value)
        
        # Calculate average value for each day of week
        day_averages = {}
        for day, values in day_of_week_values.items():
            if values:
                day_averages[day] = sum(values) / len(values)
        
        # Check if there's a weekly pattern
        if len(day_averages) >= 3:  # Need at least 3 days to detect a pattern
            # Calculate variance between days
            values = list(day_averages.values())
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            
            # If variance is significant, there might be a weekly cycle
            if variance > 0.1 * mean:
                return [{
                    'period': 7,
                    'period_unit': 'days',
                    'confidence': min(variance / mean, 0.9),  # Higher variance = higher confidence
                    'strength': min(variance / mean, 0.9),
                    'phase': min(day_averages.items(), key=lambda x: x[1])[0],  # Day with minimum value
                    'description': 'Weekly cycle detected',
                    'detected_occurrences': len(time_series) // 7
                }]
        
        return []

    def _basic_pattern_prediction(self, temporal_data: List[Dict[str, Any]], 
                                prediction_days: int) -> List[Dict[str, Any]]:
        """
        Perform basic pattern prediction without SpiderMind components.

        Args:
            temporal_data: List of timestamped data points
            prediction_days: Number of days to predict into the future

        Returns:
            List of predicted data points
        """
        # Extract time series data
        time_series = []
        
        for item in temporal_data:
            if 'timestamp' in item and 'value' in item:
                timestamp = self._parse_timestamp(item['timestamp'])
                time_series.append((timestamp, item['value']))
        
        if not time_series:
            return []
        
        # Sort by timestamp
        time_series.sort(key=lambda x: x[0])
        
        # Calculate average and trend
        values = [value for _, value in time_series]
        mean_value = sum(values) / len(values)
        
        # Simple linear trend
        if len(time_series) >= 2:
            first_timestamp, first_value = time_series[0]
            last_timestamp, last_value = time_series[-1]
            
            time_diff = (last_timestamp - first_timestamp).total_seconds() / 86400  # Convert to days
            if time_diff > 0:
                value_diff = last_value - first_value
                daily_trend = value_diff / time_diff
            else:
                daily_trend = 0
        else:
            daily_trend = 0
        
        # Generate predictions
        predictions = []
        last_timestamp = time_series[-1][0]
        
        for i in range(1, prediction_days + 1):
            prediction_timestamp = last_timestamp + timedelta(days=i)
            predicted_value = time_series[-1][1] + (daily_trend * i)
            
            # Add some weekly pattern if detected
            day_of_week = prediction_timestamp.weekday()
            
            # Group historical data by day of week
            day_values = defaultdict(list)
            for ts, val in time_series:
                day_values[ts.weekday()].append(val)
            
            # Calculate day of week adjustment
            if day_of_week in day_values and len(day_values[day_of_week]) > 0:
                day_avg = sum(day_values[day_of_week]) / len(day_values[day_of_week])
                day_factor = day_avg / mean_value if mean_value > 0 else 1.0
                predicted_value *= day_factor
            
            # Calculate confidence (decreases with prediction distance)
            confidence = max(0.1, 1.0 - (i * 0.05))
            
            predictions.append({
                'timestamp': prediction_timestamp.isoformat(),
                'value': predicted_value,
                'confidence': confidence,
                'prediction_basis': 'trend',
                'upper_bound': predicted_value * (1 + (i * 0.05)),  # Increase uncertainty with time
                'lower_bound': predicted_value * (1 - (i * 0.05))
            })
        
        return predictions

    def _basic_change_detection(self, temporal_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform basic change detection without SpiderMind components.

        Args:
            temporal_data: List of timestamped data points

        Returns:
            List of detected changes
        """
        # Extract time series data
        time_series = []
        
        for item in temporal_data:
            if 'timestamp' in item and 'value' in item:
                timestamp = self._parse_timestamp(item['timestamp'])
                time_series.append((timestamp, item['value']))
        
        if not time_series:
            return []
        
        # Sort by timestamp
        time_series.sort(key=lambda x: x[0])
        
        # Need at least 3 points to detect changes
        if len(time_series) < 3:
            return []
        
        # Calculate moving average
        window_size = min(5, len(time_series) // 3)
        if window_size < 2:
            window_size = 2
            
        moving_averages = []
        for i in range(len(time_series) - window_size + 1):
            window_values = [time_series[i+j][1] for j in range(window_size)]
            moving_averages.append((time_series[i+window_size-1][0], sum(window_values) / window_size))
        
        # Detect significant changes
        changes = []
        threshold = 0.2  # 20% change threshold
        
        for i in range(1, len(moving_averages)):
            prev_timestamp, prev_value = moving_averages[i-1]
            curr_timestamp, curr_value = moving_averages[i]
            
            if prev_value > 0:
                change_pct = abs(curr_value - prev_value) / prev_value
                
                if change_pct > threshold:
                    change_type = 'increase' if curr_value > prev_value else 'decrease'
                    
                    changes.append({
                        'timestamp': curr_timestamp.isoformat(),
                        'change_type': change_type,
                        'magnitude': change_pct,
                        'confidence': min(change_pct, 0.9),  # Higher change = higher confidence
                        'before_value': prev_value,
                        'after_value': curr_value,
                        'description': f'Significant {change_type} detected'
                    })
        
        return changes

    def _calculate_basic_trend(self, time_series: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """
        Calculate basic trend from time series data.

        Args:
            time_series: List of (timestamp, value) tuples

        Returns:
            Trend information
        """
        if len(time_series) < 2:
            return {
                'direction': 'stable',
                'strength': 0.0,
                'description': 'Insufficient data for trend analysis'
            }
        
        first_timestamp, first_value = time_series[0]
        last_timestamp, last_value = time_series[-1]
        
        time_diff = (last_timestamp - first_timestamp).total_seconds() / 86400  # Convert to days
        if time_diff == 0:
            return {
                'direction': 'stable',
                'strength': 0.0,
                'description': 'Insufficient time span for trend analysis'
            }
        
        value_diff = last_value - first_value
        daily_change = value_diff / time_diff
        
        # Calculate average value for normalization
        values = [value for _, value in time_series]
        mean_value = sum(values) / len(values)
        
        if mean_value == 0:
            normalized_change = 0.0
        else:
            normalized_change = daily_change / mean_value
        
        # Determine trend direction and strength
        if abs(normalized_change) < 0.01:
            direction = 'stable'
            strength = 0.0
            description = 'No significant trend detected'
        elif normalized_change > 0:
            direction = 'increasing'
            strength = min(abs(normalized_change) * 10, 1.0)  # Scale for better readability
            description = f'Increasing trend ({strength:.1%} per day)'
        else:
            direction = 'decreasing'
            strength = min(abs(normalized_change) * 10, 1.0)  # Scale for better readability
            description = f'Decreasing trend ({strength:.1%} per day)'
        
        return {
            'direction': direction,
            'strength': strength,
            'description': description,
            'daily_change': daily_change,
            'normalized_change': normalized_change
        }

    def _detect_basic_patterns(self, time_series: List[Tuple[datetime, float]]) -> List[Dict[str, Any]]:
        """
        Detect basic patterns in time series data.

        Args:
            time_series: List of (timestamp, value) tuples

        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Need at least 7 days of data for basic pattern detection
        if len(time_series) < 7:
            return patterns
        
        # Group by day of week
        day_of_week_values = defaultdict(list)
        
        for timestamp, value in time_series:
            day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
            day_of_week_values[day_of_week].append(value)
        
        # Calculate average value for each day of week
        day_averages = {}
        for day, values in day_of_week_values.items():
            if values:
                day_averages[day] = sum(values) / len(values)
        
        # Find day with maximum and minimum average
        if day_averages:
            max_day = max(day_averages.items(), key=lambda x: x[1])
            min_day = min(day_averages.items(), key=lambda x: x[1])
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Add patterns if there's a significant difference
            if max_day[1] > 0 and (max_day[1] - min_day[1]) / max_day[1] > 0.2:
                patterns.append({
                    'pattern_type': 'weekly_high',
                    'description': f'Activity peaks on {day_names[max_day[0]]}',
                    'confidence': 0.7,
                    'metadata': {
                        'day_of_week': max_day[0],
                        'day_name': day_names[max_day[0]],
                        'average_value': max_day[1]
                    }
                })
                
                patterns.append({
                    'pattern_type': 'weekly_low',
                    'description': f'Activity is lowest on {day_names[min_day[0]]}',
                    'confidence': 0.7,
                    'metadata': {
                        'day_of_week': min_day[0],
                        'day_name': day_names[min_day[0]],
                        'average_value': min_day[1]
                    }
                })
        
        # Check for weekend vs weekday pattern
        weekday_values = []
        weekend_values = []
        
        for day, values in day_of_week_values.items():
            if day < 5:  # Monday to Friday
                weekday_values.extend(values)
            else:  # Saturday and Sunday
                weekend_values.extend(values)
        
        if weekday_values and weekend_values:
            weekday_avg = sum(weekday_values) / len(weekday_values)
            weekend_avg = sum(weekend_values) / len(weekend_values)
            
            # If there's a significant difference between weekdays and weekends
            if max(weekday_avg, weekend_avg) > 0:
                diff_pct = abs(weekday_avg - weekend_avg) / max(weekday_avg, weekend_avg)
                
                if diff_pct > 0.2:
                    if weekday_avg > weekend_avg:
                        patterns.append({
                            'pattern_type': 'weekday_weekend',
                            'description': 'Activity is higher on weekdays than weekends',
                            'confidence': min(diff_pct, 0.9),
                            'metadata': {
                                'weekday_avg': weekday_avg,
                                'weekend_avg': weekend_avg,
                                'difference_pct': diff_pct
                            }
                        })
                    else:
                        patterns.append({
                            'pattern_type': 'weekend_weekday',
                            'description': 'Activity is higher on weekends than weekdays',
                            'confidence': min(diff_pct, 0.9),
                            'metadata': {
                                'weekday_avg': weekday_avg,
                                'weekend_avg': weekend_avg,
                                'difference_pct': diff_pct
                            }
                        })
        
        return patterns

    def _calculate_stability(self, values: List[float]) -> float:
        """
        Calculate stability score from a list of values.

        Args:
            values: List of numeric values

        Returns:
            Stability score between 0 and 1
        """
        if not values or len(values) < 2:
            return 0.5  # Default stability
        
        # Calculate coefficient of variation
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.5  # Default stability
            
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / mean
        
        # Convert to stability score (0-1)
        # Lower CV means higher stability
        stability = max(0.0, min(1.0, 1.0 - (cv / 2.0)))
        
        return stability

    def _detect_basic_anomalies(self, time_series: List[Tuple[datetime, float]], 
                              mean_value: float) -> List[Dict[str, Any]]:
        """
        Detect basic anomalies in time series data.

        Args:
            time_series: List of (timestamp, value) tuples
            mean_value: Mean value of the time series

        Returns:
            List of detected anomalies
        """
        if not time_series or len(time_series) < 3:
            return []
        
        # Calculate standard deviation
        values = [value for _, value in time_series]
        variance = sum((x - mean_value) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Detect values outside 2 standard deviations
        anomalies = []
        threshold = 2.0 * std_dev
        
        for timestamp, value in time_series:
            deviation = abs(value - mean_value)
            if deviation > threshold:
                anomaly_type = 'spike' if value > mean_value else 'drop'
                z_score = deviation / std_dev if std_dev > 0 else 0
                
                anomalies.append({
                    'timestamp': timestamp.isoformat(),
                    'value': value,
                    'anomaly_type': anomaly_type,
                    'z_score': z_score,
                    'confidence': min(z_score / 4.0, 0.95),  # Higher z-score = higher confidence
                    'description': f'Anomalous {anomaly_type} detected'
                })
        
        return anomalies

    def _generate_summary_insights(self, patterns: Dict[str, Any], 
                                 cycles: List[Dict[str, Any]], 
                                 changes: List[Dict[str, Any]]) -> List[str]:
        """
        Generate summary insights from temporal analysis results.

        Args:
            patterns: Temporal patterns
            cycles: Detected cycles
            changes: Detected behavior changes

        Returns:
            List of insight statements
        """
        insights = []
        
        # Add pattern insights
        if patterns.get('stability', 0) > 0.7:
            insights.append("Behavior shows high stability and consistency over time.")
        elif patterns.get('stability', 0) < 0.3:
            insights.append("Behavior shows significant variability and unpredictability.")
            
        for pattern in patterns.get('temporal_patterns', []):
            if pattern.get('confidence', 0) > 0.6:
                insights.append(pattern.get('description', ''))
                
        for trend in patterns.get('trends', []):
            if trend.get('strength', 0) > 0.3:
                insights.append(trend.get('description', ''))
        
        # Add cycle insights
        if cycles:
            for cycle in cycles:
                if cycle.get('confidence', 0) > 0.6:
                    period = cycle.get('period', 0)
                    unit = cycle.get('period_unit', 'days')
                    insights.append(f"Detected a {period} {unit} cycle in behavior patterns.")
        
        # Add change insights
        if changes:
            recent_changes = sorted(changes, key=lambda x: x.get('timestamp', ''), reverse=True)[:3]
            for change in recent_changes:
                if change.get('confidence', 0) > 0.6:
                    change_type = change.get('change_type', 'unknown')
                    timestamp = change.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d')
                            insights.append(f"Significant {change_type} in behavior detected on {date_str}.")
                        except:
                            insights.append(f"Significant {change_type} in behavior detected recently.")
        
        return insights

    def _parse_timestamp(self, timestamp) -> datetime:
        """
        Parse timestamp string to datetime object.

        Args:
            timestamp: Timestamp string or datetime object

        Returns:
            Datetime object
        """
        if isinstance(timestamp, datetime):
            return timestamp
            
        if isinstance(timestamp, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                try:
                    # Try common format
                    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        # Try date only
                        return datetime.strptime(timestamp, '%Y-%m-%d')
                    except:
                        # Default to current time
                        return datetime.now()
        
        # Default to current time
        return datetime.now()