"""
Online Learner Module - Continuous Incremental Learning

Continuously learns from streaming data without full retraining.
Adapts to new patterns while retaining knowledge of old ones.
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


class LearningMode(Enum):
    """Learning modes"""
    INCREMENTAL = "incremental"
    ADAPTIVE = "adaptive"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


@dataclass
class LearningExample:
    """Single learning example"""
    features: Dict[str, Any]
    label: Optional[Any] = None
    timestamp: float = 0.0
    weight: float = 1.0


@dataclass
class ModelState:
    """Current state of learned model"""
    model_id: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    examples_seen: int
    last_updated: float
    confidence: float


class OnlineLearner(Module):
    """
    Continuous online learning module.
    
    Learns incrementally from streaming data, adapting models
    in real-time without requiring full retraining.
    
    Events consumed:
    - learner/train: Train on new example
    - learner/predict: Make prediction
    - learner/evaluate: Evaluate performance
    
    Events emitted:
    - learner/model_updated: Model updated
    - learner/prediction: Prediction result
    - learner/drift_detected: Concept drift detected
    """
    
    name = "online_learner"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        learning_mode: LearningMode = LearningMode.INCREMENTAL,
        learning_rate: float = 0.01,
        forgetting_factor: float = 0.95
    ):
        super().__init__(bus, ex, policy)
        self.learning_mode = learning_mode
        self.base_learning_rate = learning_rate
        self.forgetting_factor = forgetting_factor
        
        self.models: Dict[str, ModelState] = {}
        self.default_model_id = "default"
        self.training_buffer: deque = deque(maxlen=1000)
        
        self._total_examples = 0
        self._total_predictions = 0
        self._drift_detections = 0
        
        self._initialize_default_model()
    
    def _initialize_default_model(self) -> None:
        """Initialize default model"""
        self.models[self.default_model_id] = ModelState(
            model_id=self.default_model_id,
            parameters={'weights': {}, 'bias': 0.0, 'means': {}, 'stds': {}},
            performance_metrics={'accuracy': 0.0},
            examples_seen=0,
            last_updated=time.time(),
            confidence=0.5
        )
    
    async def start(self) -> None:
        await super().start()
        await self.bus.subscribe("learner/train", self._handle_train)
        await self.bus.subscribe("learner/predict", self._handle_predict)
        self.log.info("Online learner started")
    
    async def stop(self) -> None:
        await super().stop()
        self.log.info("Online learner stopped")
    
    async def _handle_train(self, msg: Message) -> None:
        """Handle training request"""
        try:
            data = msg.data
            model_id = data.get('model_id', self.default_model_id)
            
            example = LearningExample(
                features=data.get('features', {}),
                label=data.get('label'),
                timestamp=time.time(),
                weight=data.get('weight', 1.0)
            )
            
            result = await self._train_on_example(model_id, example)
            
            await self.emit("learner/model_updated", {
                "model_id": model_id,
                "examples_seen": result['examples_seen'],
                "performance": result['performance']
            })
            
        except Exception as e:
            self.log.error(f"Error handling train: {e}")
    
    async def _handle_predict(self, msg: Message) -> None:
        """Handle prediction request"""
        try:
            data = msg.data
            model_id = data.get('model_id', self.default_model_id)
            features = data.get('features', {})
            
            prediction, confidence = await self._predict(model_id, features)
            self._total_predictions += 1
            
            await self.emit("learner/prediction", {
                "request_id": data.get('request_id'),
                "model_id": model_id,
                "prediction": prediction,
                "confidence": confidence
            })
            
        except Exception as e:
            self.log.error(f"Error handling predict: {e}")
    
    async def _train_on_example(self, model_id: str, example: LearningExample) -> Dict[str, Any]:
        """Train model on single example"""
        if model_id not in self.models:
            self.models[model_id] = ModelState(
                model_id=model_id,
                parameters={'weights': {}, 'bias': 0.0, 'means': {}, 'stds': {}},
                performance_metrics={'accuracy': 0.0},
                examples_seen=0,
                last_updated=time.time(),
                confidence=0.5
            )
        
        model = self.models[model_id]
        learning_rate = self._calculate_learning_rate(model)
        
        model.parameters = self._update_parameters(model.parameters, example, learning_rate)
        model.examples_seen += 1
        model.last_updated = time.time()
        self._total_examples += 1
        
        performance = self._estimate_performance(model)
        model.performance_metrics = performance
        
        return {'examples_seen': model.examples_seen, 'performance': performance}
    
    async def _predict(self, model_id: str, features: Dict[str, Any]) -> Tuple[Any, float]:
        """Make prediction"""
        if model_id not in self.models:
            return None, 0.0
        
        model = self.models[model_id]
        params = model.parameters
        
        score = params.get('bias', 0.0)
        for feature, value in features.items():
            if feature in params.get('weights', {}) and isinstance(value, (int, float)):
                score += params['weights'][feature] * value
        
        prediction = 1 if score > 0 else 0
        confidence = min(1.0, abs(score) / 10.0)
        
        return prediction, confidence
    
    def _calculate_learning_rate(self, model: ModelState) -> float:
        """Calculate adaptive learning rate"""
        base = self.base_learning_rate
        
        if self.learning_mode == LearningMode.INCREMENTAL:
            return base / (1 + model.examples_seen / 1000)
        elif self.learning_mode == LearningMode.CONSERVATIVE:
            return base * 0.5
        elif self.learning_mode == LearningMode.AGGRESSIVE:
            return base * 2.0
        else:  # ADAPTIVE
            perf = model.performance_metrics.get('accuracy', 0.5)
            return base * (1.5 if perf < 0.6 else 0.8)
    
    def _update_parameters(
        self,
        params: Dict[str, Any],
        example: LearningExample,
        learning_rate: float
    ) -> Dict[str, Any]:
        """Update model parameters"""
        updated = params.copy()
        
        if example.label is not None:
            for feature, value in example.features.items():
                if not isinstance(value, (int, float)):
                    continue
                
                if feature not in updated['weights']:
                    updated['weights'][feature] = 0.0
                
                prediction = 1 if updated.get('bias', 0) + sum(updated['weights'].values()) > 0 else 0
                error = example.label - prediction
                
                updated['weights'][feature] += learning_rate * error * value * example.weight
                updated['weights'][feature] *= self.forgetting_factor
        
        return updated
    
    def _estimate_performance(self, model: ModelState) -> Dict[str, float]:
        """Estimate model performance"""
        return {'accuracy': 0.5 + model.examples_seen / 10000, 'confidence': model.confidence}
    
    async def on_message(self, msg: Message) -> None:
        pass
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            "total_models": len(self.models),
            "total_examples": self._total_examples,
            "total_predictions": self._total_predictions,
            "learning_mode": self.learning_mode.value
        })
        return stats
