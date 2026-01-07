"""
Unit tests for the Enhanced Predictive Engine adapter.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from digital_twin.adapters.predictive_engine import EnhancedPredictiveEngineAdapter


@pytest.fixture
def predictive_engine_adapter():
    """Create an Enhanced Predictive Engine adapter for testing."""
    return EnhancedPredictiveEngineAdapter()


@pytest.fixture
def sample_training_data():
    """Create sample training data for testing."""
    # Create timestamps
    now = datetime.now()
    training_data = []
    
    # Generate 20 data points
    for i in range(20):
        timestamp = (now - timedelta(days=20-i)).isoformat()
        
        # Create a data point with some patterns
        data_point = {
            "timestamp": timestamp,
            "mood": 0.5 + (i * 0.01) + (0.1 * (i % 7 == 0)),  # Slight upward trend with weekly spike
            "energy": 0.6 - (i * 0.005) + (0.05 * (i % 3 == 0)),  # Slight downward trend with periodic boost
            "focus": 0.7 + (0.1 * ((i % 5) / 5)),  # Cyclic pattern
            "productivity": 0.5 + (i * 0.015),  # Linear increase
            "social_interaction": 0.4 + (0.2 * (i % 2 == 0))  # Alternating pattern
        }
        
        training_data.append(data_point)
    
    return training_data


@pytest.fixture
def sample_current_state():
    """Create a sample current state for testing."""
    return {
        "timestamp": datetime.now().isoformat(),
        "mood": 0.7,
        "energy": 0.6,
        "focus": 0.8,
        "productivity": 0.75,
        "social_interaction": 0.5
    }


@pytest.fixture
def sample_history():
    """Create sample history data for testing."""
    # Create timestamps
    now = datetime.now()
    history = []
    
    # Generate 10 data points
    for i in range(10):
        timestamp = (now - timedelta(days=10-i)).isoformat()
        
        # Create a data point with some patterns
        data_point = {
            "timestamp": timestamp,
            "mood": 0.5 + (i * 0.02),  # Upward trend
            "energy": 0.6 - (i * 0.01),  # Downward trend
            "focus": 0.7 + (0.1 * ((i % 5) / 5))  # Cyclic pattern
        }
        
        history.append(data_point)
    
    return history


@pytest.mark.asyncio
async def test_train_prediction_models(predictive_engine_adapter, sample_training_data):
    """Test train_prediction_models method."""
    # Call the method
    result = await predictive_engine_adapter.train_prediction_models(sample_training_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "models_trained" in result
    assert "training_metrics" in result
    assert "overall_success" in result
    
    # Check that models were trained
    assert len(result["models_trained"]) > 0
    
    # Check that training metrics were generated
    assert len(result["training_metrics"]) > 0


@pytest.mark.asyncio
async def test_predict_future_states(predictive_engine_adapter, sample_current_state):
    """Test predict_future_states method."""
    # Call the method
    result = await predictive_engine_adapter.predict_future_states(sample_current_state, horizon_days=7)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "prediction_id" in result
    assert "predicted_states" in result
    assert "confidence_scores" in result
    assert "insights" in result
    
    # Check that predicted states were generated
    assert len(result["predicted_states"]) > 0
    
    # Check that each predicted state has the expected fields
    for state in result["predicted_states"]:
        assert "timestamp" in state
        assert "mood" in state
        assert "energy" in state
        assert "focus" in state
        
    # Check that confidence scores were generated
    assert "overall_confidence" in result["confidence_scores"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_generate_future_scenarios(predictive_engine_adapter, sample_current_state):
    """Test generate_future_scenarios method."""
    # Call the method
    result = await predictive_engine_adapter.generate_future_scenarios(sample_current_state, scenario_count=3)
    
    # Check the result structure
    assert isinstance(result, list)
    assert len(result) == 3
    
    # Check that each scenario has the expected fields
    for scenario in result:
        assert "scenario_id" in scenario
        assert "name" in scenario
        assert "description" in scenario
        assert "probability" in scenario
        assert "timeline" in scenario
        assert "key_events" in scenario
        assert "outcome" in scenario
        
        # Check that the timeline has entries
        assert len(scenario["timeline"]) > 0
        
        # Check that key events were generated
        assert len(scenario["key_events"]) > 0
        
        # Check that the outcome has the expected fields
        assert "summary" in scenario["outcome"]


@pytest.mark.asyncio
async def test_predict_trajectory(predictive_engine_adapter, sample_history):
    """Test predict_trajectory method."""
    # Call the method
    result = await predictive_engine_adapter.predict_trajectory(sample_history, steps_ahead=24)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "trajectory_id" in result
    assert "start_time" in result
    assert "predicted_states" in result
    assert "confidence_intervals" in result
    assert "key_transition_points" in result
    assert "stability_assessment" in result
    
    # Check that predicted states were generated
    assert len(result["predicted_states"]) == 24
    
    # Check that confidence intervals were generated
    assert "narrow" in result["confidence_intervals"]
    assert "wide" in result["confidence_intervals"]
    
    # Check that stability assessment has the expected fields
    assert "stability_score" in result["stability_assessment"]
    assert "volatility" in result["stability_assessment"]
    assert "trend_direction" in result["stability_assessment"]


@pytest.mark.asyncio
async def test_assess_prediction_confidence(predictive_engine_adapter):
    """Test assess_prediction_confidence method."""
    # Create a sample prediction
    prediction = {
        "prediction_id": "test_prediction",
        "confidence_scores": {
            "overall_confidence": 0.7,
            "model_confidences": {
                "model1": 0.8,
                "model2": 0.6
            }
        }
    }
    
    # Call the method
    result = await predictive_engine_adapter.assess_prediction_confidence(prediction)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "overall_confidence" in result
    assert "model_confidences" in result
    assert "consensus_level" in result
    assert "reliability_assessment" in result
    
    # Check that the overall confidence matches the input
    assert result["overall_confidence"] == prediction["confidence_scores"]["overall_confidence"]
    
    # Check that model confidences match the input
    for model, confidence in prediction["confidence_scores"]["model_confidences"].items():
        assert model in result["model_confidences"]
        assert result["model_confidences"][model] == confidence


@pytest.mark.asyncio
async def test_basic_model_training(predictive_engine_adapter, sample_training_data):
    """Test _basic_model_training method."""
    # Call the method
    result = predictive_engine_adapter._basic_model_training(sample_training_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "models_trained" in result
    assert "training_metrics" in result
    assert "overall_success" in result
    
    # Check that models were trained
    assert len(result["models_trained"]) > 0
    
    # Check that training metrics were generated
    assert len(result["training_metrics"]) > 0
    
    # Check that overall success is a boolean
    assert isinstance(result["overall_success"], bool)


@pytest.mark.asyncio
async def test_basic_prediction(predictive_engine_adapter, sample_current_state):
    """Test _basic_prediction method."""
    # Call the method
    result = predictive_engine_adapter._basic_prediction(sample_current_state, horizon_days=7)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "prediction_id" in result
    assert "predicted_states" in result
    assert "confidence_scores" in result
    assert "insights" in result
    
    # Check that predicted states were generated
    assert len(result["predicted_states"]) > 0
    
    # Check that each predicted state has the expected fields
    for state in result["predicted_states"]:
        assert "timestamp" in state
        assert "mood" in state
        assert "energy" in state
        assert "focus" in state
        
    # Check that confidence scores were generated
    assert "overall_confidence" in result["confidence_scores"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_basic_scenario_generation(predictive_engine_adapter, sample_current_state):
    """Test _basic_scenario_generation method."""
    # Call the method
    result = predictive_engine_adapter._basic_scenario_generation(sample_current_state, scenario_count=3)
    
    # Check the result structure
    assert isinstance(result, list)
    assert len(result) == 3
    
    # Check that each scenario has the expected fields
    for scenario in result:
        assert "scenario_id" in scenario
        assert "name" in scenario
        assert "description" in scenario
        assert "probability" in scenario
        assert "timeline" in scenario
        assert "key_events" in scenario
        assert "outcome" in scenario
        
        # Check that the timeline has entries
        assert len(scenario["timeline"]) > 0
        
        # Check that key events were generated
        assert len(scenario["key_events"]) > 0
        
        # Check that the outcome has the expected fields
        assert "summary" in scenario["outcome"]


@pytest.mark.asyncio
async def test_basic_trajectory_prediction(predictive_engine_adapter, sample_history):
    """Test _basic_trajectory_prediction method."""
    # Call the method
    result = predictive_engine_adapter._basic_trajectory_prediction(sample_history, steps_ahead=24)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "trajectory_id" in result
    assert "start_time" in result
    assert "predicted_states" in result
    assert "confidence_intervals" in result
    assert "key_transition_points" in result
    assert "stability_assessment" in result
    
    # Check that predicted states were generated
    assert len(result["predicted_states"]) == 24
    
    # Check that confidence intervals were generated
    assert "narrow" in result["confidence_intervals"]
    assert "wide" in result["confidence_intervals"]
    
    # Check that stability assessment has the expected fields
    assert "stability_score" in result["stability_assessment"]
    assert "volatility" in result["stability_assessment"]
    assert "trend_direction" in result["stability_assessment"]