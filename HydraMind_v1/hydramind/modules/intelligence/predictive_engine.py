"""
Predictive Engine Module - Behavior and Event Prediction

Predicts future events, behaviors, and system states based on learned patterns
and historical data. Inspired by predictive analytics from SEED architecture.
"""

import asyncio
import logging
import time
from collections import deque, defaultdict
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions"""
    EVENT = "event"  # Predict next event
    METRIC = "metric"  # Predict metric value
    ANOMALY = "anomaly"  # Predict anomaly
    LOAD = "load"  # Predict system load
    FAILURE = "failure"  # Predict failure


@dataclass
class Prediction:
    """A prediction"""
    prediction_type: PredictionType
    target: str  # What is being predicted
    predicted_value: Any
    confidence: float
    time_horizon: float  # Seconds into future
    rationale: str
    timestamp: float


class PredictiveEngine(Module):
    """
    Predictive engine for forecasting system behavior.
    
    Uses historical data and learned patterns to predict future events,
    metrics, and potential issues.
    
    Events consumed:
    - predictor/predict: Manual prediction request
    - learner/pattern_detected: Pattern detection
    - collector/summary: Data summaries
    
    Events emitted:
    - predictor/prediction: New prediction
    - predictor/alert: Predicted issue
    """
    
    name = "predictive_engine"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        prediction_interval=180.0,
        min_confidence=0.6
    ):
        """
        Initialize predictive engine.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            prediction_interval: Seconds between prediction cycles
            min_confidence: Minimum confidence to emit predictions
        """
        super().__init__(bus, ex, policy)
        self.prediction_interval = prediction_interval
        self.min_confidence = min_confidence
        
        # Historical data
        self.event_history: deque = deque(maxlen=1000)
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.pattern_library: Dict[str, Any] = {}
        
        # Prediction state
        self._prediction_task: Optional[asyncio.Task] = None
        self._predictions_made = 0
        self._predictions_accurate = 0
        
        # Models
        self.time_series_models: Dict[str, Dict] = {}
    
    async def start(self) -> None:
        """Start predictive engine"""
        await super().start()
        
        # Subscribe to data sources
        await self.bus.subscribe("predictor/predict", self._handle_predict_request)
        await self.bus.subscribe("learner/pattern_detected", self._handle_pattern)
        await self.bus.subscribe("collector/summary", self._handle_summary)
        await self.bus.subscribe("*", self._track_event)
        
        # Start prediction loop
        self._prediction_task = asyncio.create_task(self._prediction_loop())
        
        self.log.info("Predictive engine started")
    
    async def stop(self) -> None:
        """Stop predictive engine"""
        if self._prediction_task:
            self._prediction_task.cancel()
            try:
                await self._prediction_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("Predictive engine stopped")
    
    async def _prediction_loop(self) -> None:
        """Periodic prediction loop"""
        while self._running:
            try:
                await asyncio.sleep(self.prediction_interval)
                
                # Make predictions
                predictions = await self._make_predictions()
                
                # Emit predictions
                for prediction in predictions:
                    if prediction.confidence >= self.min_confidence:
                        await self.emit("predictor/prediction", {
                            "type": prediction.prediction_type.value,
                            "target": prediction.target,
                            "predicted_value": prediction.predicted_value,
                            "confidence": prediction.confidence,
                            "time_horizon": prediction.time_horizon,
                            "rationale": prediction.rationale
                        })
                        
                        # Emit alert for predicted issues
                        if prediction.prediction_type in [PredictionType.ANOMALY, PredictionType.FAILURE]:
                            if prediction.confidence > 0.7:
                                await self.emit("predictor/alert", {
                                    "type": prediction.prediction_type.value,
                                    "target": prediction.target,
                                    "confidence": prediction.confidence,
                                    "predicted_at": prediction.timestamp
                                })
                
            except Exception as e:
                self.log.error(f"Prediction loop error: {e}")
                await asyncio.sleep(self.prediction_interval)
    
    async def _handle_predict_request(self, msg: Message) -> None:
        """Handle manual prediction request"""
        try:
            data = msg.data
            prediction_type = data.get('type', 'metric')
            target = data.get('target')
            
            # Make specific prediction
            prediction = await self._predict_specific(PredictionType(prediction_type), target)
            
            await self.emit("predictor/prediction_result", {
                "request_id": data.get('request_id'),
                "prediction": {
                    "type": prediction.prediction_type.value,
                    "target": prediction.target,
                    "predicted_value": prediction.predicted_value,
                    "confidence": prediction.confidence,
                    "rationale": prediction.rationale
                } if prediction else None
            })
            
        except Exception as e:
            self.log.error(f"Error handling predict request: {e}")
    
    async def _handle_pattern(self, msg: Message) -> None:
        """Handle detected pattern"""
        try:
            data = msg.data
            pattern_name = data.get('name')
            pattern_data = data.get('data', {})
            
            # Store pattern in library
            self.pattern_library[pattern_name] = {
                'type': data.get('pattern_type'),
                'confidence': data.get('confidence', 0),
                'data': pattern_data,
                'detected_at': time.time()
            }
            
        except Exception as e:
            self.log.error(f"Error handling pattern: {e}")
    
    async def _handle_summary(self, msg: Message) -> None:
        """Handle data summary"""
        try:
            data = msg.data
            
            # Store metric data
            for series_name, series_data in data.get('data_series', {}).items():
                if isinstance(series_data, dict) and 'mean' in series_data:
                    self.metric_history[series_name].append({
                        'value': series_data['mean'],
                        'timestamp': data.get('timestamp', time.time())
                    })
                    
                    # Update time series model
                    await self._update_model(series_name)
            
        except Exception as e:
            self.log.error(f"Error handling summary: {e}")
    
    async def _track_event(self, msg: Message) -> None:
        """Track all events for pattern analysis"""
        try:
            self.event_history.append({
                'topic': msg.topic,
                'timestamp': time.time()
            })
        except Exception:
            pass  # Silent failure for catch-all
    
    async def _make_predictions(self) -> List[Prediction]:
        """Make all types of predictions"""
        predictions = []
        
        # Predict next events
        predictions.extend(await self._predict_events())
        
        # Predict metrics
        predictions.extend(await self._predict_metrics())
        
        # Predict anomalies
        predictions.extend(await self._predict_anomalies())
        
        # Predict system load
        predictions.extend(await self._predict_load())
        
        self._predictions_made += len(predictions)
        
        return predictions
    
    async def _predict_events(self) -> List[Prediction]:
        """Predict likely next events"""
        predictions = []
        
        try:
            if len(self.event_history) < 10:
                return predictions
            
            # Analyze recent event patterns
            recent_events = list(self.event_history)[-20:]
            event_topics = [e['topic'] for e in recent_events]
            
            # Find most common recent events
            from collections import Counter
            event_counts = Counter(event_topics)
            most_common = event_counts.most_common(3)
            
            for topic, count in most_common:
                if count >= 3:
                    confidence = min(0.9, count / 10)
                    
                    predictions.append(Prediction(
                        prediction_type=PredictionType.EVENT,
                        target=topic,
                        predicted_value=topic,
                        confidence=confidence,
                        time_horizon=60.0,  # Next minute
                        rationale=f"Event {topic} has occurred {count} times recently",
                        timestamp=time.time()
                    ))
        
        except Exception as e:
            self.log.error(f"Error predicting events: {e}")
        
        return predictions
    
    async def _predict_metrics(self) -> List[Prediction]:
        """Predict future metric values"""
        predictions = []
        
        try:
            for metric_name, history in self.metric_history.items():
                if len(history) < 10:
                    continue
                
                # Simple trend-based prediction
                values = [h['value'] for h in history]
                recent = values[-5:]
                older = values[-10:-5]
                
                if len(recent) >= 3 and len(older) >= 3:
                    recent_avg = sum(recent) / len(recent)
                    older_avg = sum(older) / len(older)
                    
                    # Calculate trend
                    trend = recent_avg - older_avg
                    
                    # Predict next value
                    predicted = recent_avg + trend
                    
                    # Calculate confidence based on trend consistency
                    confidence = 0.5
                    if abs(trend) > 0.1:
                        confidence = 0.7
                    
                    predictions.append(Prediction(
                        prediction_type=PredictionType.METRIC,
                        target=metric_name,
                        predicted_value=predicted,
                        confidence=confidence,
                        time_horizon=300.0,  # 5 minutes
                        rationale=f"Based on recent trend: {trend:+.2f}",
                        timestamp=time.time()
                    ))
        
        except Exception as e:
            self.log.error(f"Error predicting metrics: {e}")
        
        return predictions
    
    async def _predict_anomalies(self) -> List[Prediction]:
        """Predict potential anomalies"""
        predictions = []
        
        try:
            # Check for patterns that might lead to anomalies
            for pattern_name, pattern_data in self.pattern_library.items():
                if 'anomaly' in pattern_name.lower():
                    # Previous anomaly pattern detected
                    confidence = pattern_data.get('confidence', 0) * 0.8
                    
                    if confidence > 0.5:
                        predictions.append(Prediction(
                            prediction_type=PredictionType.ANOMALY,
                            target=pattern_name,
                            predicted_value=True,
                            confidence=confidence,
                            time_horizon=600.0,  # 10 minutes
                            rationale=f"Similar pattern to previous anomaly detected",
                            timestamp=time.time()
                        ))
            
            # Check for metrics approaching thresholds
            for metric_name, history in self.metric_history.items():
                if len(history) < 5:
                    continue
                
                recent_values = [h['value'] for h in list(history)[-5:]]
                avg_value = sum(recent_values) / len(recent_values)
                
                # Check if approaching dangerous levels
                if 'cpu' in metric_name.lower() and avg_value > 75:
                    predictions.append(Prediction(
                        prediction_type=PredictionType.ANOMALY,
                        target=f"{metric_name}_high",
                        predicted_value=True,
                        confidence=min(0.9, (avg_value - 75) / 25),
                        time_horizon=180.0,
                        rationale=f"{metric_name} trending high: {avg_value:.1f}",
                        timestamp=time.time()
                    ))
                
                elif 'memory' in metric_name.lower() and avg_value > 80:
                    predictions.append(Prediction(
                        prediction_type=PredictionType.ANOMALY,
                        target=f"{metric_name}_high",
                        predicted_value=True,
                        confidence=min(0.9, (avg_value - 80) / 20),
                        time_horizon=120.0,
                        rationale=f"{metric_name} approaching limit: {avg_value:.1f}%",
                        timestamp=time.time()
                    ))
        
        except Exception as e:
            self.log.error(f"Error predicting anomalies: {e}")
        
        return predictions
    
    async def _predict_load(self) -> List[Prediction]:
        """Predict system load"""
        predictions = []
        
        try:
            # Analyze event rate as proxy for load
            if len(self.event_history) >= 20:
                recent_events = list(self.event_history)[-20:]
                timestamps = [e['timestamp'] for e in recent_events]
                
                if timestamps:
                    time_span = timestamps[-1] - timestamps[0]
                    if time_span > 0:
                        event_rate = len(recent_events) / time_span
                        
                        # Predict load level
                        if event_rate > 10:
                            load_level = "high"
                            confidence = 0.8
                        elif event_rate > 5:
                            load_level = "medium"
                            confidence = 0.7
                        else:
                            load_level = "low"
                            confidence = 0.6
                        
                        predictions.append(Prediction(
                            prediction_type=PredictionType.LOAD,
                            target="system_load",
                            predicted_value=load_level,
                            confidence=confidence,
                            time_horizon=300.0,
                            rationale=f"Current event rate: {event_rate:.1f}/s",
                            timestamp=time.time()
                        ))
        
        except Exception as e:
            self.log.error(f"Error predicting load: {e}")
        
        return predictions
    
    async def _predict_specific(
        self,
        prediction_type: PredictionType,
        target: str
    ) -> Optional[Prediction]:
        """Make a specific prediction"""
        if prediction_type == PredictionType.METRIC:
            # Predict specific metric
            if target in self.metric_history:
                predictions = await self._predict_metrics()
                for pred in predictions:
                    if pred.target == target:
                        return pred
        
        elif prediction_type == PredictionType.EVENT:
            predictions = await self._predict_events()
            for pred in predictions:
                if pred.target == target:
                    return pred
        
        return None
    
    async def _update_model(self, metric_name: str) -> None:
        """Update time series model for metric"""
        try:
            history = self.metric_history[metric_name]
            
            if len(history) < 20:
                return
            
            # Simple model: store recent statistics
            values = [h['value'] for h in history]
            
            self.time_series_models[metric_name] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'last_update': time.time()
            }
        
        except Exception as e:
            self.log.error(f"Error updating model for {metric_name}: {e}")
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        # Handled by specific subscribers
        pass
    
    def get_stats(self) -> dict:
        """Get predictor statistics"""
        stats = super().get_stats()
        
        accuracy = (self._predictions_accurate / self._predictions_made * 100) if self._predictions_made > 0 else 0
        
        stats.update({
            "predictions_made": self._predictions_made,
            "predictions_accurate": self._predictions_accurate,
            "accuracy_pct": accuracy,
            "event_history_size": len(self.event_history),
            "metrics_tracked": len(self.metric_history),
            "patterns_known": len(self.pattern_library),
            "models_trained": len(self.time_series_models)
        })
        return stats
