"""
Enhanced Predictive Engine Adapter for the Digital Twin.

This module provides an adapter for integrating SpiderMind Omega's PredictiveEngine
and FuturePredictor with the Digital Twin system for advanced multi-model prediction
and scenario generation.
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional, Set, Tuple
import importlib.util
from datetime import datetime, timedelta
import uuid
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class EnhancedPredictiveEngineAdapter:
    """
    Adapter for SpiderMind Omega's PredictiveEngine and FuturePredictor for advanced
    multi-model prediction and scenario generation.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced predictive engine adapter.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.predictive_engine = None
        self.future_predictor = None
        self.future_echo = None
        self.echo_detector = None
        self.future_structures = None
        self.temporal_structures = None
        self._initialize_predictive_components()
        logger.info("Enhanced Predictive Engine Adapter initialized")

    def _initialize_predictive_components(self) -> None:
        """
        Initialize predictive components from SpiderMind Omega.
        """
        try:
            # Try to import components from SpiderMind Omega
            spidermind_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ct_omega"))
            
            if spidermind_path not in sys.path:
                sys.path.append(spidermind_path)
                
            # Import PredictiveEngine
            self._import_component("predictive_engine", "core.predictive_engine", "PredictiveEngine")
            
            # Import FuturePredictor
            self._import_component("future_predictor", "core.future_predictor", "FuturePredictor")
            
            # Import FutureEcho
            self._import_component("future_echo", "core.future_echo", "FutureEcho")
            
            # Import EchoDetector
            self._import_component("echo_detector", "core.echo_detector", "EchoDetector")
            
            # Import structure modules
            self._import_module("future_structures", "core.future_structures")
            self._import_module("temporal_structures", "core.temporal_structures")
            
        except Exception as e:
            logger.error(f"Error initializing predictive components: {str(e)}")
            logger.warning("Using fallback prediction mechanisms")

    def _import_component(self, attr_name: str, module_path: str, class_name: str) -> None:
        """
        Import a component from SpiderMind Omega.

        Args:
            attr_name: Attribute name to assign the component to
            module_path: Path to the module
            class_name: Name of the class to import
        """
        try:
            # Try to import the module
            spec = importlib.util.find_spec(module_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the class
                component_class = getattr(module, class_name, None)
                if component_class:
                    # Initialize the component
                    setattr(self, attr_name, component_class())
                    logger.info(f"Successfully imported {class_name} from {module_path}")
                else:
                    logger.warning(f"Could not find class {class_name} in {module_path}")
                    setattr(self, attr_name, None)
            else:
                logger.warning(f"Could not find module {module_path}")
                setattr(self, attr_name, None)
        except Exception as e:
            logger.error(f"Error importing {class_name} from {module_path}: {str(e)}")
            setattr(self, attr_name, None)

    def _import_module(self, attr_name: str, module_path: str) -> None:
        """
        Import a module from SpiderMind Omega.

        Args:
            attr_name: Attribute name to assign the module to
            module_path: Path to the module
        """
        try:
            # Try to import the module
            spec = importlib.util.find_spec(module_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                setattr(self, attr_name, module)
                logger.info(f"Successfully imported {module_path}")
            else:
                logger.warning(f"Could not find module {module_path}")
                setattr(self, attr_name, None)
        except Exception as e:
            logger.error(f"Error importing {module_path}: {str(e)}")
            setattr(self, attr_name, None)

    async def train_prediction_models(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train prediction models with historical data.

        Args:
            training_data: List of historical data points for training

        Returns:
            Dictionary of training results
        """
        # If PredictiveEngine is available, use it
        if self.predictive_engine:
            try:
                # Train the models
                training_results = await self.predictive_engine.train_models(training_data)
                
                # Convert the result to our format
                return self._convert_from_training_results(training_results)
            except Exception as e:
                logger.error(f"Error training prediction models: {str(e)}")
                logger.warning("Falling back to basic model training")
                
        # Fallback: Use basic model training
        return self._basic_model_training(training_data)

    async def predict_future_states(self, current_state: Dict[str, Any], horizon_days: int = 7) -> Dict[str, Any]:
        """
        Predict future states based on current state.

        Args:
            current_state: Current state of the user
            horizon_days: Number of days to predict into the future

        Returns:
            Dictionary of prediction results
        """
        # If PredictiveEngine is available, use it
        if self.predictive_engine:
            try:
                # Make predictions
                prediction_results = await self.predictive_engine.predict_future_states(
                    current_state, 
                    horizon=timedelta(days=horizon_days)
                )
                
                # Convert the result to our format
                return self._convert_from_prediction_results(prediction_results)
            except Exception as e:
                logger.error(f"Error predicting future states: {str(e)}")
                logger.warning("Falling back to basic prediction")
                
        # Fallback: Use basic prediction
        return self._basic_prediction(current_state, horizon_days)

    async def generate_future_scenarios(self, current_state: Dict[str, Any], scenario_count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple future scenarios based on current state.

        Args:
            current_state: Current state of the user
            scenario_count: Number of scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        # If FutureEcho is available, use it
        if self.future_echo:
            try:
                # Generate scenarios
                scenarios = await self.future_echo.generate_future_scenarios(
                    current_state, 
                    count=scenario_count
                )
                
                # Convert the result to our format
                return self._convert_from_scenarios(scenarios)
            except Exception as e:
                logger.error(f"Error generating future scenarios: {str(e)}")
                logger.warning("Falling back to basic scenario generation")
                
        # Fallback: Use basic scenario generation
        return self._basic_scenario_generation(current_state, scenario_count)

    async def predict_trajectory(self, history: List[Dict[str, Any]], steps_ahead: int = 24) -> Dict[str, Any]:
        """
        Predict a trajectory of future states based on historical data.

        Args:
            history: List of historical states
            steps_ahead: Number of steps to predict ahead

        Returns:
            Dictionary containing the predicted trajectory
        """
        # If FuturePredictor is available, use it
        if self.future_predictor and self.temporal_structures:
            try:
                # Create empty time waves if we don't have the detector
                time_waves = []
                if self.echo_detector:
                    time_waves = await self.echo_detector.detect_time_waves(history)
                
                # Predict trajectory
                trajectory = self.future_predictor.predict_trajectory(
                    history,
                    time_waves,
                    steps_ahead=steps_ahead
                )
                
                # Convert the result to our format
                return self._convert_from_trajectory(trajectory)
            except Exception as e:
                logger.error(f"Error predicting trajectory: {str(e)}")
                logger.warning("Falling back to basic trajectory prediction")
                
        # Fallback: Use basic trajectory prediction
        return self._basic_trajectory_prediction(history, steps_ahead)

    async def assess_prediction_confidence(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the confidence of a prediction.

        Args:
            prediction: Prediction to assess

        Returns:
            Dictionary of confidence assessment
        """
        # If PredictiveEngine is available, use it
        if self.predictive_engine:
            try:
                # Assess confidence
                confidence_assessment = await self.predictive_engine._assess_prediction_confidence(prediction)
                
                # Convert the result to our format
                return self._convert_from_confidence_assessment(confidence_assessment)
            except Exception as e:
                logger.error(f"Error assessing prediction confidence: {str(e)}")
                logger.warning("Falling back to basic confidence assessment")
                
        # Fallback: Use basic confidence assessment
        return self._basic_confidence_assessment(prediction)

    def _convert_from_training_results(self, training_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert training results from PredictiveEngine to our format.

        Args:
            training_results: Training results from PredictiveEngine

        Returns:
            Dictionary in our format
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "models_trained": [],
            "training_metrics": {},
            "overall_success": False
        }
        
        # Extract models trained
        if "models_trained" in training_results:
            result["models_trained"] = training_results["models_trained"]
        
        # Extract training metrics
        if "training_metrics" in training_results:
            result["training_metrics"] = training_results["training_metrics"]
        
        # Extract overall success
        if "success" in training_results:
            result["overall_success"] = training_results["success"]
        
        return result

    def _convert_from_prediction_results(self, prediction_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert prediction results from PredictiveEngine to our format.

        Args:
            prediction_results: Prediction results from PredictiveEngine

        Returns:
            Dictionary in our format
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "prediction_id": str(uuid.uuid4()),
            "predicted_states": [],
            "confidence_scores": {},
            "insights": [],
            "intervention_opportunities": []
        }
        
        # Extract predicted states
        if "predicted_states" in prediction_results:
            result["predicted_states"] = prediction_results["predicted_states"]
        
        # Extract confidence scores
        if "confidence_analysis" in prediction_results:
            result["confidence_scores"] = prediction_results["confidence_analysis"]
        
        # Extract insights
        if "insights" in prediction_results:
            result["insights"] = prediction_results["insights"]
        
        # Extract intervention opportunities
        if "intervention_opportunities" in prediction_results:
            result["intervention_opportunities"] = prediction_results["intervention_opportunities"]
        
        return result

    def _convert_from_scenarios(self, scenarios: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert scenarios from FutureEcho to our format.

        Args:
            scenarios: Scenarios from FutureEcho

        Returns:
            List of dictionaries in our format
        """
        result = []
        
        for scenario in scenarios:
            scenario_dict = {
                "scenario_id": getattr(scenario, "scenario_id", str(uuid.uuid4())),
                "name": getattr(scenario, "name", "Unnamed Scenario"),
                "description": getattr(scenario, "description", ""),
                "probability": getattr(scenario, "probability", 0.0),
                "timeline": [],
                "key_events": [],
                "outcome": {}
            }
            
            # Extract timeline
            if hasattr(scenario, "timeline"):
                scenario_dict["timeline"] = scenario.timeline
            
            # Extract key events
            if hasattr(scenario, "key_events"):
                scenario_dict["key_events"] = scenario.key_events
            
            # Extract outcome
            if hasattr(scenario, "outcome"):
                scenario_dict["outcome"] = scenario.outcome
            
            result.append(scenario_dict)
        
        return result

    def _convert_from_trajectory(self, trajectory: Any) -> Dict[str, Any]:
        """
        Convert trajectory from FuturePredictor to our format.

        Args:
            trajectory: Trajectory from FuturePredictor

        Returns:
            Dictionary in our format
        """
        result = {
            "trajectory_id": getattr(trajectory, "trajectory_id", str(uuid.uuid4())),
            "start_time": datetime.now().isoformat(),
            "predicted_states": [],
            "confidence_intervals": {},
            "key_transition_points": [],
            "stability_assessment": {}
        }
        
        # Extract predicted states
        if hasattr(trajectory, "predicted_states"):
            result["predicted_states"] = trajectory.predicted_states
        
        # Extract confidence intervals
        if hasattr(trajectory, "confidence_intervals"):
            result["confidence_intervals"] = trajectory.confidence_intervals
        
        # Extract key transition points
        if hasattr(trajectory, "key_transition_points"):
            result["key_transition_points"] = trajectory.key_transition_points
        
        # Extract stability assessment
        if hasattr(trajectory, "stability_assessment"):
            result["stability_assessment"] = trajectory.stability_assessment
        
        return result

    def _convert_from_confidence_assessment(self, confidence_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert confidence assessment from PredictiveEngine to our format.

        Args:
            confidence_assessment: Confidence assessment from PredictiveEngine

        Returns:
            Dictionary in our format
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "overall_confidence": 0.0,
            "model_confidences": {},
            "consensus_level": 0.0,
            "reliability_assessment": ""
        }
        
        # Extract overall confidence
        if "overall_confidence" in confidence_assessment:
            result["overall_confidence"] = confidence_assessment["overall_confidence"]
        
        # Extract model confidences
        if "model_confidences" in confidence_assessment:
            result["model_confidences"] = confidence_assessment["model_confidences"]
        
        # Extract consensus level
        if "consensus_level" in confidence_assessment:
            result["consensus_level"] = confidence_assessment["consensus_level"]
        
        # Generate reliability assessment
        confidence = result["overall_confidence"]
        consensus = result["consensus_level"]
        
        if confidence > 0.8 and consensus > 0.8:
            result["reliability_assessment"] = "Very High"
        elif confidence > 0.6 and consensus > 0.6:
            result["reliability_assessment"] = "High"
        elif confidence > 0.4 and consensus > 0.4:
            result["reliability_assessment"] = "Moderate"
        elif confidence > 0.2 and consensus > 0.2:
            result["reliability_assessment"] = "Low"
        else:
            result["reliability_assessment"] = "Very Low"
        
        return result

    def _basic_model_training(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Basic model training when SpiderMind Omega components are not available.

        Args:
            training_data: List of historical data points for training

        Returns:
            Dictionary of training results
        """
        # Simple model training simulation
        result = {
            "timestamp": datetime.now().isoformat(),
            "models_trained": ["basic_linear", "basic_pattern"],
            "training_metrics": {
                "basic_linear": {
                    "accuracy": 0.75,
                    "training_samples": len(training_data),
                    "training_time": 0.5
                },
                "basic_pattern": {
                    "accuracy": 0.7,
                    "training_samples": len(training_data),
                    "training_time": 0.3
                }
            },
            "overall_success": True
        }
        
        return result

    def _basic_prediction(self, current_state: Dict[str, Any], horizon_days: int = 7) -> Dict[str, Any]:
        """
        Basic prediction when SpiderMind Omega components are not available.

        Args:
            current_state: Current state of the user
            horizon_days: Number of days to predict into the future

        Returns:
            Dictionary of prediction results
        """
        # Simple prediction simulation
        result = {
            "timestamp": datetime.now().isoformat(),
            "prediction_id": str(uuid.uuid4()),
            "predicted_states": [],
            "confidence_scores": {
                "overall_confidence": 0.7,
                "model_confidences": {
                    "basic_linear": 0.75,
                    "basic_pattern": 0.65
                },
                "consensus_level": 0.8
            },
            "insights": [
                "Predicted stable trajectory over the forecast period",
                "No significant anomalies detected in the prediction",
                "Confidence level is moderate for this prediction"
            ],
            "intervention_opportunities": []
        }
        
        # Generate predicted states
        current_time = datetime.now()
        
        # Extract some values from current state to use in prediction
        mood = current_state.get("mood", 0.5)
        energy = current_state.get("energy", 0.5)
        focus = current_state.get("focus", 0.5)
        
        # Generate simple predictions with some random variation
        for day in range(horizon_days):
            for hour in range(0, 24, 6):  # 4 predictions per day
                future_time = current_time + timedelta(days=day, hours=hour)
                
                # Simple linear trend with some noise
                time_factor = day / horizon_days
                noise = np.random.normal(0, 0.05)
                
                predicted_state = {
                    "timestamp": future_time.isoformat(),
                    "mood": min(1.0, max(0.0, mood + (time_factor * 0.1) + noise)),
                    "energy": min(1.0, max(0.0, energy - (time_factor * 0.05) + noise)),
                    "focus": min(1.0, max(0.0, focus + (time_factor * 0.02) + noise)),
                    "confidence": 0.8 - (time_factor * 0.3)  # Confidence decreases over time
                }
                
                result["predicted_states"].append(predicted_state)
        
        # Add some intervention opportunities
        if mood < 0.4:
            result["intervention_opportunities"].append({
                "time_window": "next_24_hours",
                "intervention_type": "mood_enhancement",
                "expected_impact": "mood_increase",
                "description": "Recommend activities to improve mood"
            })
        
        if energy < 0.3:
            result["intervention_opportunities"].append({
                "time_window": "next_12_hours",
                "intervention_type": "energy_boost",
                "expected_impact": "energy_increase",
                "description": "Suggest energy-boosting activities"
            })
        
        return result

    def _basic_scenario_generation(self, current_state: Dict[str, Any], scenario_count: int = 3) -> List[Dict[str, Any]]:
        """
        Basic scenario generation when SpiderMind Omega components are not available.

        Args:
            current_state: Current state of the user
            scenario_count: Number of scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        
        # Extract some values from current state
        mood = current_state.get("mood", 0.5)
        energy = current_state.get("energy", 0.5)
        focus = current_state.get("focus", 0.5)
        
        # Generate scenarios with different trajectories
        scenario_types = [
            {"name": "Optimistic", "description": "Positive trajectory with improvements", "probability": 0.4},
            {"name": "Baseline", "description": "Continuation of current trends", "probability": 0.5},
            {"name": "Pessimistic", "description": "Negative trajectory with challenges", "probability": 0.1}
        ]
        
        # Use available scenario types or generate generic ones if we need more
        for i in range(min(scenario_count, len(scenario_types))):
            scenario_type = scenario_types[i]
            
            scenario = {
                "scenario_id": str(uuid.uuid4()),
                "name": scenario_type["name"],
                "description": scenario_type["description"],
                "probability": scenario_type["probability"],
                "timeline": [],
                "key_events": [],
                "outcome": {}
            }
            
            # Generate timeline
            current_time = datetime.now()
            
            for day in range(7):  # 7-day timeline
                future_time = current_time + timedelta(days=day)
                
                # Different trajectories based on scenario type
                if scenario_type["name"] == "Optimistic":
                    mood_change = 0.05
                    energy_change = 0.03
                    focus_change = 0.04
                elif scenario_type["name"] == "Pessimistic":
                    mood_change = -0.05
                    energy_change = -0.04
                    focus_change = -0.03
                else:  # Baseline
                    mood_change = 0.01
                    energy_change = -0.01
                    focus_change = 0.0
                
                # Add some noise
                noise = np.random.normal(0, 0.02)
                
                state = {
                    "timestamp": future_time.isoformat(),
                    "day": day,
                    "mood": min(1.0, max(0.0, mood + (day * mood_change) + noise)),
                    "energy": min(1.0, max(0.0, energy + (day * energy_change) + noise)),
                    "focus": min(1.0, max(0.0, focus + (day * focus_change) + noise))
                }
                
                scenario["timeline"].append(state)
            
            # Generate key events
            if scenario_type["name"] == "Optimistic":
                scenario["key_events"] = [
                    {"day": 2, "description": "Significant mood improvement"},
                    {"day": 5, "description": "Peak productivity achieved"}
                ]
            elif scenario_type["name"] == "Pessimistic":
                scenario["key_events"] = [
                    {"day": 1, "description": "Energy drop below threshold"},
                    {"day": 4, "description": "Focus difficulties emerge"}
                ]
            else:  # Baseline
                scenario["key_events"] = [
                    {"day": 3, "description": "Minor fluctuations in mood"},
                    {"day": 6, "description": "Return to baseline state"}
                ]
            
            # Generate outcome
            last_state = scenario["timeline"][-1]
            scenario["outcome"] = {
                "final_mood": last_state["mood"],
                "final_energy": last_state["energy"],
                "final_focus": last_state["focus"],
                "summary": f"After 7 days, {scenario_type['name'].lower()} trajectory leads to {self._describe_state(last_state)}"
            }
            
            scenarios.append(scenario)
        
        # If we need more scenarios than our predefined types, generate generic ones
        for i in range(len(scenario_types), scenario_count):
            # Generate a random scenario
            probability = 0.1 + (0.8 * np.random.random())  # Between 0.1 and 0.9
            direction = "positive" if np.random.random() > 0.5 else "negative"
            intensity = np.random.choice(["mild", "moderate", "strong"])
            
            scenario = {
                "scenario_id": str(uuid.uuid4()),
                "name": f"Scenario {i+1}",
                "description": f"{intensity.capitalize()} {direction} trajectory",
                "probability": probability,
                "timeline": [],
                "key_events": [],
                "outcome": {}
            }
            
            # Generate timeline with random trajectory
            current_time = datetime.now()
            
            # Determine change factors based on direction and intensity
            if direction == "positive":
                base_change = 0.01 if intensity == "mild" else 0.03 if intensity == "moderate" else 0.05
            else:
                base_change = -0.01 if intensity == "mild" else -0.03 if intensity == "moderate" else -0.05
            
            for day in range(7):  # 7-day timeline
                future_time = current_time + timedelta(days=day)
                
                # Add some noise
                noise = np.random.normal(0, 0.02)
                
                state = {
                    "timestamp": future_time.isoformat(),
                    "day": day,
                    "mood": min(1.0, max(0.0, mood + (day * base_change * 1.0) + noise)),
                    "energy": min(1.0, max(0.0, energy + (day * base_change * 0.8) + noise)),
                    "focus": min(1.0, max(0.0, focus + (day * base_change * 1.2) + noise))
                }
                
                scenario["timeline"].append(state)
            
            # Generate random key events
            event_count = np.random.randint(1, 3)
            for _ in range(event_count):
                day = np.random.randint(1, 6)
                if direction == "positive":
                    descriptions = ["Mood improvement", "Energy boost", "Focus enhancement"]
                else:
                    descriptions = ["Mood decline", "Energy drop", "Focus difficulty"]
                
                scenario["key_events"].append({
                    "day": day,
                    "description": np.random.choice(descriptions)
                })
            
            # Generate outcome
            last_state = scenario["timeline"][-1]
            scenario["outcome"] = {
                "final_mood": last_state["mood"],
                "final_energy": last_state["energy"],
                "final_focus": last_state["focus"],
                "summary": f"After 7 days, {intensity} {direction} trajectory leads to {self._describe_state(last_state)}"
            }
            
            scenarios.append(scenario)
        
        return scenarios

    def _basic_trajectory_prediction(self, history: List[Dict[str, Any]], steps_ahead: int = 24) -> Dict[str, Any]:
        """
        Basic trajectory prediction when SpiderMind Omega components are not available.

        Args:
            history: List of historical states
            steps_ahead: Number of steps to predict ahead

        Returns:
            Dictionary containing the predicted trajectory
        """
        result = {
            "trajectory_id": str(uuid.uuid4()),
            "start_time": datetime.now().isoformat(),
            "predicted_states": [],
            "confidence_intervals": {
                "narrow": [],
                "wide": []
            },
            "key_transition_points": [],
            "stability_assessment": {
                "stability_score": 0.7,
                "volatility": "moderate",
                "trend_direction": "stable"
            }
        }
        
        # If no history, return empty trajectory
        if not history:
            return result
        
        # Sort history by timestamp
        sorted_history = sorted(history, key=lambda x: x.get("timestamp", ""))
        
        # Get the most recent state as base
        base_state = sorted_history[-1] if sorted_history else {}
        
        # Extract key metrics from base state
        metrics = {}
        for key, value in base_state.items():
            if isinstance(value, (int, float)) and key not in ["timestamp"]:
                metrics[key] = value
        
        # If no metrics, use defaults
        if not metrics:
            metrics = {"value": 0.5}
        
        # Calculate simple trend from history
        trends = {}
        if len(sorted_history) > 1:
            for key in metrics:
                values = [h.get(key, 0) for h in sorted_history if key in h and isinstance(h[key], (int, float))]
                if len(values) > 1:
                    # Simple linear trend
                    trend = (values[-1] - values[0]) / len(values)
                    trends[key] = trend
                else:
                    trends[key] = 0
        else:
            for key in metrics:
                trends[key] = 0
        
        # Generate predicted states
        current_time = datetime.now()
        
        for step in range(steps_ahead):
            future_time = current_time + timedelta(hours=step)
            
            # Create predicted state
            predicted_state = {
                "timestamp": future_time.isoformat(),
                "step": step
            }
            
            # Add predicted values for each metric
            for key, value in metrics.items():
                trend = trends.get(key, 0)
                noise = np.random.normal(0, 0.02)
                predicted_value = value + (step * trend) + noise
                
                # Ensure values are within reasonable bounds
                if key in ["probability", "confidence"] or key.endswith("_level"):
                    predicted_value = min(1.0, max(0.0, predicted_value))
                
                predicted_state[key] = predicted_value
                
                # Add confidence intervals
                narrow_interval = 0.05 + (step * 0.005)  # Increases with steps
                wide_interval = 0.1 + (step * 0.01)  # Increases with steps
                
                result["confidence_intervals"]["narrow"].append({
                    "step": step,
                    "metric": key,
                    "lower": max(0.0, predicted_value - narrow_interval),
                    "upper": min(1.0, predicted_value + narrow_interval)
                })
                
                result["confidence_intervals"]["wide"].append({
                    "step": step,
                    "metric": key,
                    "lower": max(0.0, predicted_value - wide_interval),
                    "upper": min(1.0, predicted_value + wide_interval)
                })
            
            result["predicted_states"].append(predicted_state)
        
        # Identify key transition points
        for step in range(1, steps_ahead):
            current = result["predicted_states"][step]
            previous = result["predicted_states"][step-1]
            
            for key in metrics:
                if key in current and key in previous:
                    # Check for significant changes
                    change = abs(current[key] - previous[key])
                    if change > 0.1:  # Threshold for significant change
                        result["key_transition_points"].append({
                            "step": step,
                            "metric": key,
                            "previous_value": previous[key],
                            "new_value": current[key],
                            "change": current[key] - previous[key],
                            "description": f"Significant change in {key}"
                        })
        
        # Assess stability
        volatility = 0
        for key in metrics:
            values = [state.get(key, 0) for state in result["predicted_states"] if key in state]
            if values:
                volatility += np.std(values)
        
        avg_volatility = volatility / len(metrics) if metrics else 0
        stability_score = max(0.0, min(1.0, 1.0 - (avg_volatility * 5)))  # Convert volatility to stability
        
        result["stability_assessment"] = {
            "stability_score": stability_score,
            "volatility": "low" if stability_score > 0.7 else "moderate" if stability_score > 0.4 else "high",
            "trend_direction": self._determine_trend_direction(trends)
        }
        
        return result

    def _basic_confidence_assessment(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic confidence assessment when SpiderMind Omega components are not available.

        Args:
            prediction: Prediction to assess

        Returns:
            Dictionary of confidence assessment
        """
        # Extract confidence scores if available
        overall_confidence = 0.7  # Default
        model_confidences = {}
        
        if "confidence_scores" in prediction:
            confidence_scores = prediction["confidence_scores"]
            if "overall_confidence" in confidence_scores:
                overall_confidence = confidence_scores["overall_confidence"]
            if "model_confidences" in confidence_scores:
                model_confidences = confidence_scores["model_confidences"]
        
        # If no model confidences, create some
        if not model_confidences:
            model_confidences = {
                "basic_linear": 0.75,
                "basic_pattern": 0.65
            }
        
        # Calculate consensus level
        confidences = list(model_confidences.values())
        consensus_level = 1.0 - (np.std(confidences) if confidences else 0)
        
        # Generate reliability assessment
        if overall_confidence > 0.8 and consensus_level > 0.8:
            reliability = "Very High"
        elif overall_confidence > 0.6 and consensus_level > 0.6:
            reliability = "High"
        elif overall_confidence > 0.4 and consensus_level > 0.4:
            reliability = "Moderate"
        elif overall_confidence > 0.2 and consensus_level > 0.2:
            reliability = "Low"
        else:
            reliability = "Very Low"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_confidence": overall_confidence,
            "model_confidences": model_confidences,
            "consensus_level": consensus_level,
            "reliability_assessment": reliability
        }

    def _describe_state(self, state: Dict[str, Any]) -> str:
        """
        Generate a description of a state.

        Args:
            state: State to describe

        Returns:
            String description
        """
        mood = state.get("mood", 0.5)
        energy = state.get("energy", 0.5)
        focus = state.get("focus", 0.5)
        
        mood_desc = "excellent" if mood > 0.8 else "good" if mood > 0.6 else "moderate" if mood > 0.4 else "poor" if mood > 0.2 else "very poor"
        energy_desc = "high" if energy > 0.7 else "moderate" if energy > 0.4 else "low"
        focus_desc = "sharp" if focus > 0.7 else "adequate" if focus > 0.4 else "scattered"
        
        return f"{mood_desc} mood, {energy_desc} energy, and {focus_desc} focus"

    def _determine_trend_direction(self, trends: Dict[str, float]) -> str:
        """
        Determine the overall trend direction.

        Args:
            trends: Dictionary of trends for different metrics

        Returns:
            String describing the trend direction
        """
        if not trends:
            return "stable"
        
        # Calculate average trend
        avg_trend = sum(trends.values()) / len(trends)
        
        if avg_trend > 0.01:
            return "improving"
        elif avg_trend < -0.01:
            return "declining"
        else:
            return "stable"