#!/usr/bin/env python3
"""
SpiderMind Omega Integration Example

This script demonstrates the use of the SpiderMind Omega adapters in the Digital Twin system.
It shows how to use the EntanglementMatrix, VoidAnalyzer, Enhanced PredictiveEngine,
and Enhanced ConsciousnessMapper adapters to analyze user data and generate insights.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os
import random

# Add the parent directory to the path so we can import the digital_twin package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from digital_twin.adapters.entanglement_matrix import EntanglementMatrixAdapter
from digital_twin.adapters.void_analyzer import VoidAnalyzerAdapter
from digital_twin.adapters.predictive_engine import EnhancedPredictiveEngineAdapter
from digital_twin.adapters.consciousness_mapper import EnhancedConsciousnessMapperAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_sample_user_data(days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate sample user data for demonstration purposes.

    Args:
        days: Number of days of data to generate

    Returns:
        Dictionary of user data categorized by data type
    """
    now = datetime.now()
    user_data = {
        "communication": [],
        "activity": [],
        "mood": [],
        "social": [],
        "productivity": []
    }

    # Generate data for each day
    for i in range(days):
        timestamp = (now - timedelta(days=days-i)).isoformat()
        
        # Add some weekly patterns and trends
        day_of_week = i % 7
        week_progress = i / 7
        
        # Communication data
        message_count = 10 + int(5 * week_progress) + (5 if day_of_week < 5 else -5)
        response_time = 30 - int(5 * week_progress) + (5 if day_of_week >= 5 else -5)
        user_data["communication"].append({
            "timestamp": timestamp,
            "message_count": max(0, message_count + random.randint(-3, 3)),
            "response_time": max(5, response_time + random.randint(-5, 5)),
            "channels": random.randint(1, 3)
        })
        
        # Activity data
        activity_level = 0.3 + (0.1 * week_progress) + (0.2 if day_of_week < 5 else -0.1)
        duration = 45 + int(10 * week_progress) + (15 if day_of_week < 5 else -10)
        user_data["activity"].append({
            "timestamp": timestamp,
            "activity_level": min(1.0, max(0.1, activity_level + random.uniform(-0.1, 0.1))),
            "duration": max(15, duration + random.randint(-10, 10)),
            "type": random.choice(["work", "exercise", "leisure"])
        })
        
        # Mood data
        happiness = 0.6 + (0.05 * week_progress) + (0.1 if day_of_week >= 5 else -0.05)
        energy = 0.5 + (0.05 * week_progress) + (-0.1 if day_of_week == 0 else 0.05)
        user_data["mood"].append({
            "timestamp": timestamp,
            "happiness": min(1.0, max(0.1, happiness + random.uniform(-0.1, 0.1))),
            "energy": min(1.0, max(0.1, energy + random.uniform(-0.1, 0.1))),
            "stress": min(1.0, max(0.0, 0.5 - (0.05 * week_progress) + (0.2 if day_of_week < 5 else -0.1) + random.uniform(-0.1, 0.1)))
        })
        
        # Social data
        interactions = 3 + int(week_progress) + (2 if day_of_week >= 5 else -1)
        user_data["social"].append({
            "timestamp": timestamp,
            "interactions": max(0, interactions + random.randint(-1, 1)),
            "quality": min(1.0, max(0.1, 0.7 + (0.05 * week_progress) + random.uniform(-0.1, 0.1))),
            "duration": 60 + int(15 * week_progress) + (30 if day_of_week >= 5 else -15) + random.randint(-15, 15)
        })
        
        # Productivity data
        tasks_completed = 5 + int(2 * week_progress) + (2 if day_of_week < 5 else -2)
        focus_time = 180 + int(30 * week_progress) + (60 if day_of_week < 5 else -60)
        user_data["productivity"].append({
            "timestamp": timestamp,
            "tasks_completed": max(0, tasks_completed + random.randint(-2, 2)),
            "focus_time": max(30, focus_time + random.randint(-30, 30)),
            "efficiency": min(1.0, max(0.1, 0.6 + (0.05 * week_progress) + (0.1 if day_of_week < 5 else -0.05) + random.uniform(-0.1, 0.1)))
        })
    
    return user_data


async def generate_sample_personality_data() -> Dict[str, Any]:
    """
    Generate sample personality data for demonstration purposes.

    Returns:
        Dictionary of personality data
    """
    return {
        "traits": {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
            "creativity": 0.8,
            "resilience": 0.7,
            "adaptability": 0.6,
            "empathy": 0.9,
            "curiosity": 0.8
        },
        "states": [
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "dimensions": {
                    "mood": 0.7,
                    "energy": 0.6,
                    "focus": 0.5
                },
                "patterns": ["morning_routine", "work_focus"],
                "transitions": ["sleep_to_wake"]
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "dimensions": {
                    "mood": 0.6,
                    "energy": 0.5,
                    "focus": 0.7
                },
                "patterns": ["problem_solving", "creative_flow"],
                "transitions": ["work_to_rest"]
            },
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "dimensions": {
                    "mood": 0.8,
                    "energy": 0.7,
                    "focus": 0.6
                },
                "patterns": ["social_engagement", "relaxation"],
                "transitions": ["work_to_play"]
            }
        ],
        "preferences": {
            "music": 0.8,
            "reading": 0.7,
            "outdoor_activities": 0.6,
            "social_gatherings": 0.5,
            "technology": 0.9
        }
    }


async def convert_user_data_to_consciousness_data(user_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Convert user data to consciousness data format for ConsciousnessMapper.

    Args:
        user_data: Dictionary of user data categorized by data type

    Returns:
        List of consciousness state data points
    """
    consciousness_data = []
    
    # Get all timestamps from all categories
    all_timestamps = set()
    for category, data_points in user_data.items():
        for data_point in data_points:
            all_timestamps.add(data_point.get("timestamp", ""))
    
    # Sort timestamps
    sorted_timestamps = sorted(all_timestamps)
    
    # For each timestamp, create a consciousness state
    for timestamp in sorted_timestamps:
        # Find data points for this timestamp
        dimensions = {}
        patterns = []
        transitions = []
        
        for category, data_points in user_data.items():
            for data_point in data_points:
                if data_point.get("timestamp") == timestamp:
                    # Extract dimensions based on category
                    if category == "mood":
                        dimensions.update({
                            "happiness": data_point.get("happiness", 0.5),
                            "energy": data_point.get("energy", 0.5),
                            "stress": data_point.get("stress", 0.5)
                        })
                        patterns.append("mood_pattern")
                    elif category == "activity":
                        dimensions.update({
                            "activity_level": data_point.get("activity_level", 0.5),
                            "duration": min(1.0, data_point.get("duration", 30) / 120)  # Normalize
                        })
                        patterns.append(f"activity_{data_point.get('type', 'general')}")
                    elif category == "productivity":
                        dimensions.update({
                            "productivity": min(1.0, data_point.get("tasks_completed", 0) / 10),  # Normalize
                            "focus": min(1.0, data_point.get("focus_time", 0) / 240),  # Normalize
                            "efficiency": data_point.get("efficiency", 0.5)
                        })
                        patterns.append("productivity_pattern")
                    elif category == "social":
                        dimensions.update({
                            "social_activity": min(1.0, data_point.get("interactions", 0) / 10),  # Normalize
                            "social_quality": data_point.get("quality", 0.5)
                        })
                        patterns.append("social_pattern")
                    elif category == "communication":
                        dimensions.update({
                            "communication_volume": min(1.0, data_point.get("message_count", 0) / 20),  # Normalize
                            "response_time": min(1.0, data_point.get("response_time", 30) / 60)  # Normalize
                        })
                        patterns.append("communication_pattern")
        
        # Create consciousness state
        consciousness_state = {
            "timestamp": timestamp,
            "dimensions": dimensions,
            "patterns": patterns,
            "transitions": transitions
        }
        
        consciousness_data.append(consciousness_state)
    
    return consciousness_data


async def demonstrate_entanglement_matrix(user_data: Dict[str, List[Dict[str, Any]]]):
    """
    Demonstrate the EntanglementMatrix adapter.

    Args:
        user_data: Dictionary of user data categorized by data type
    """
    logger.info("Demonstrating EntanglementMatrix adapter...")
    
    # Initialize the adapter
    adapter = EntanglementMatrixAdapter()
    
    # Analyze entanglements
    entanglement_analysis = await adapter.analyze_entanglements(user_data)
    
    # Print results
    logger.info("Entanglement Analysis Results:")
    logger.info(f"  Network Density: {entanglement_analysis.get('network_density', 0):.2f}")
    logger.info(f"  Entanglement Count: {entanglement_analysis.get('entanglement_count', 0)}")
    logger.info(f"  Node Count: {entanglement_analysis.get('node_count', 0)}")
    
    # Print insights
    logger.info("Entanglement Insights:")
    for insight in entanglement_analysis.get("insights", []):
        logger.info(f"  - {insight}")
    
    # Detect relationship patterns
    relationship_patterns = await adapter.detect_relationship_patterns(user_data)
    
    # Print relationship patterns
    logger.info("Relationship Patterns:")
    for pattern in relationship_patterns:
        logger.info(f"  - {pattern.get('name', '')}: {pattern.get('description', '')}")
        logger.info(f"    Strength: {pattern.get('strength', 0):.2f}")
        logger.info(f"    Dimensions: {', '.join(pattern.get('dimensions', []))}")
    
    # Visualize entanglement network
    visualization = await adapter.visualize_entanglement_network(user_data)
    
    # Print visualization info
    logger.info("Entanglement Network Visualization:")
    logger.info(f"  Nodes: {len(visualization.get('nodes', []))}")
    logger.info(f"  Edges: {len(visualization.get('edges', []))}")
    logger.info(f"  Clusters: {len(visualization.get('clusters', []))}")


async def demonstrate_void_analyzer(user_data: Dict[str, List[Dict[str, Any]]], personality_data: Dict[str, Any]):
    """
    Demonstrate the VoidAnalyzer adapter.

    Args:
        user_data: Dictionary of user data categorized by data type
        personality_data: Dictionary of personality data
    """
    logger.info("Demonstrating VoidAnalyzer adapter...")
    
    # Initialize the adapter
    adapter = VoidAnalyzerAdapter()
    
    # Analyze understanding gaps
    void_analysis = await adapter.analyze_understanding_gaps(user_data)
    
    # Print results
    logger.info("Understanding Gaps Analysis Results:")
    logger.info(f"  Detected Voids: {len(void_analysis.get('detected_voids', []))}")
    logger.info(f"  Void Clusters: {len(void_analysis.get('void_clusters', []))}")
    
    # Print insights
    logger.info("Understanding Gaps Insights:")
    for insight in void_analysis.get("insights", []):
        logger.info(f"  - {insight}")
    
    # Detect knowledge gaps
    knowledge_gaps = await adapter.detect_knowledge_gaps(personality_data)
    
    # Print knowledge gaps
    logger.info("Knowledge Gaps:")
    for gap in knowledge_gaps:
        logger.info(f"  - Type: {gap.get('type', '')}")
        logger.info(f"    Severity: {gap.get('severity', 0):.2f}")
        logger.info(f"    Affected Dimensions: {', '.join(gap.get('affected_dimensions', []))}")
    
    # Generate recovery recommendations
    recovery_recommendations = await adapter.generate_void_recovery_recommendations(knowledge_gaps)
    
    # Print recovery recommendations
    logger.info("Recovery Recommendations:")
    for recommendation in recovery_recommendations.get("recommendations", []):
        logger.info(f"  - {recommendation.get('description', '')}")
        logger.info(f"    Method: {recommendation.get('method', '')}")
        logger.info(f"    Priority: {recommendation.get('priority', 0):.2f}")


async def demonstrate_predictive_engine(user_data: Dict[str, List[Dict[str, Any]]]):
    """
    Demonstrate the Enhanced PredictiveEngine adapter.

    Args:
        user_data: Dictionary of user data categorized by data type
    """
    logger.info("Demonstrating Enhanced PredictiveEngine adapter...")
    
    # Initialize the adapter
    adapter = EnhancedPredictiveEngineAdapter()
    
    # Prepare training data
    training_data = []
    for category, data_points in user_data.items():
        for data_point in data_points:
            training_data.append(data_point)
    
    # Train prediction models
    training_results = await adapter.train_prediction_models(training_data)
    
    # Print training results
    logger.info("Model Training Results:")
    logger.info(f"  Models Trained: {', '.join(training_results.get('models_trained', []))}")
    logger.info(f"  Overall Success: {training_results.get('overall_success', False)}")
    
    # Get current state (most recent data points)
    current_state = {}
    for category, data_points in user_data.items():
        if data_points:
            # Sort by timestamp and get the most recent
            sorted_points = sorted(data_points, key=lambda x: x.get("timestamp", ""))
            most_recent = sorted_points[-1]
            
            # Extract relevant metrics
            if category == "mood":
                current_state["mood"] = most_recent.get("happiness", 0.5)
                current_state["energy"] = most_recent.get("energy", 0.5)
            elif category == "activity":
                current_state["activity_level"] = most_recent.get("activity_level", 0.5)
            elif category == "productivity":
                current_state["focus"] = most_recent.get("efficiency", 0.5)
    
    # Predict future states
    prediction_results = await adapter.predict_future_states(current_state, horizon_days=7)
    
    # Print prediction results
    logger.info("Future State Prediction Results:")
    logger.info(f"  Prediction ID: {prediction_results.get('prediction_id', '')}")
    logger.info(f"  Predicted States: {len(prediction_results.get('predicted_states', []))}")
    logger.info(f"  Overall Confidence: {prediction_results.get('confidence_scores', {}).get('overall_confidence', 0):.2f}")
    
    # Print insights
    logger.info("Prediction Insights:")
    for insight in prediction_results.get("insights", []):
        logger.info(f"  - {insight}")
    
    # Generate future scenarios
    scenarios = await adapter.generate_future_scenarios(current_state, scenario_count=3)
    
    # Print scenarios
    logger.info("Future Scenarios:")
    for scenario in scenarios:
        logger.info(f"  - {scenario.get('name', '')}: {scenario.get('description', '')}")
        logger.info(f"    Probability: {scenario.get('probability', 0):.2f}")
        logger.info(f"    Outcome: {scenario.get('outcome', {}).get('summary', '')}")
    
    # Predict trajectory
    history = []
    for category, data_points in user_data.items():
        if category == "mood":
            for data_point in data_points:
                history.append({
                    "timestamp": data_point.get("timestamp", ""),
                    "mood": data_point.get("happiness", 0.5),
                    "energy": data_point.get("energy", 0.5)
                })
    
    # Sort history by timestamp
    history = sorted(history, key=lambda x: x.get("timestamp", ""))
    
    # Predict trajectory
    trajectory = await adapter.predict_trajectory(history, steps_ahead=24)
    
    # Print trajectory results
    logger.info("Trajectory Prediction Results:")
    logger.info(f"  Trajectory ID: {trajectory.get('trajectory_id', '')}")
    logger.info(f"  Predicted States: {len(trajectory.get('predicted_states', []))}")
    logger.info(f"  Key Transition Points: {len(trajectory.get('key_transition_points', []))}")
    logger.info(f"  Stability Score: {trajectory.get('stability_assessment', {}).get('stability_score', 0):.2f}")
    logger.info(f"  Trend Direction: {trajectory.get('stability_assessment', {}).get('trend_direction', '')}")


async def demonstrate_consciousness_mapper(user_data: Dict[str, List[Dict[str, Any]]], personality_data: Dict[str, Any]):
    """
    Demonstrate the Enhanced ConsciousnessMapper adapter.

    Args:
        user_data: Dictionary of user data categorized by data type
        personality_data: Dictionary of personality data
    """
    logger.info("Demonstrating Enhanced ConsciousnessMapper adapter...")
    
    # Initialize the adapter
    adapter = EnhancedConsciousnessMapperAdapter()
    
    # Convert user data to consciousness data
    consciousness_data = await convert_user_data_to_consciousness_data(user_data)
    
    # Map consciousness topology
    topology_map = await adapter.map_consciousness_topology(consciousness_data)
    
    # Print topology map results
    logger.info("Consciousness Topology Map Results:")
    logger.info(f"  Map ID: {topology_map.get('map_id', '')}")
    logger.info(f"  Regions: {len(topology_map.get('regions', []))}")
    logger.info(f"  Dominant Topologies: {topology_map.get('dominant_topologies', {})}")
    
    # Print insights
    logger.info("Topology Map Insights:")
    for insight in topology_map.get("insights", []):
        logger.info(f"  - {insight}")
    
    # Analyze consciousness structure
    structure_analysis = await adapter.analyze_consciousness_structure(personality_data)
    
    # Print structure analysis results
    logger.info("Consciousness Structure Analysis Results:")
    logger.info(f"  Analysis ID: {structure_analysis.get('analysis_id', '')}")
    logger.info(f"  Layers: {len(structure_analysis.get('layers', []))}")
    logger.info(f"  Core Elements: {len(structure_analysis.get('core_elements', []))}")
    logger.info(f"  Peripheral Elements: {len(structure_analysis.get('peripheral_elements', []))}")
    
    # Print insights
    logger.info("Structure Analysis Insights:")
    for insight in structure_analysis.get("insights", []):
        logger.info(f"  - {insight}")
    
    # Detect emergent properties
    emergent_properties = await adapter.detect_emergent_properties(consciousness_data)
    
    # Print emergent properties
    logger.info("Emergent Properties:")
    for property in emergent_properties:
        logger.info(f"  - {property.get('name', '')}: {property.get('description', '')}")
        logger.info(f"    Emergence Level: {property.get('emergence_level', 0):.2f}")
        logger.info(f"    Contributing Elements: {', '.join(property.get('contributing_elements', []))}")
    
    # Generate navigation guide
    navigation_guide = await adapter.generate_navigation_guide(topology_map)
    
    # Print navigation guide
    logger.info("Navigation Guide:")
    logger.info(f"  Guide ID: {navigation_guide.get('guide_id', '')}")
    logger.info(f"  Stability Anchors: {len(navigation_guide.get('stability_anchors', []))}")
    logger.info(f"  Warning Zones: {len(navigation_guide.get('warning_zones', []))}")
    
    # Print recommendations
    logger.info("Navigation Recommendations:")
    for recommendation in navigation_guide.get("recommendations", []):
        logger.info(f"  - Type: {recommendation.get('type', '')}")
        logger.info(f"    Description: {recommendation.get('description', '')}")


async def main():
    """Main function to demonstrate the SpiderMind Omega adapters."""
    logger.info("Starting SpiderMind Omega Integration Example...")
    
    # Generate sample data
    logger.info("Generating sample data...")
    user_data = await generate_sample_user_data(days=30)
    personality_data = await generate_sample_personality_data()
    
    # Demonstrate EntanglementMatrix adapter
    await demonstrate_entanglement_matrix(user_data)
    
    # Demonstrate VoidAnalyzer adapter
    await demonstrate_void_analyzer(user_data, personality_data)
    
    # Demonstrate Enhanced PredictiveEngine adapter
    await demonstrate_predictive_engine(user_data)
    
    # Demonstrate Enhanced ConsciousnessMapper adapter
    await demonstrate_consciousness_mapper(user_data, personality_data)
    
    logger.info("SpiderMind Omega Integration Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())