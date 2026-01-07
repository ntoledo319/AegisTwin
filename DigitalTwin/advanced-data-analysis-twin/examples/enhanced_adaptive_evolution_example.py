#!/usr/bin/env python3
"""
Enhanced Adaptive Evolution Example

This script demonstrates the Enhanced Adaptive Evolution Engine from INFINITY,
which provides advanced self-improvement capabilities for the Digital Twin system
with bottleneck detection, multi-model ensemble proposal generation, and
evolution strategy selection.
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from digital_twin.evolution.enhanced_adaptive_engine import EnhancedAdaptiveEvolutionEngine
from digital_twin.evolution.bottleneck_detector import BottleneckDetector
from digital_twin.evolution.ensemble_proposal_generator import EnsembleProposalGenerator
from digital_twin.evolution.evolution_strategy_selector import EvolutionStrategySelector
from digital_twin.evolution.improvement_proposal import ImprovementProposal


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DigitalTwinSystem:
    """
    Simplified Digital Twin system for demonstration purposes.
    """
    
    def __init__(self):
        """Initialize the Digital Twin system."""
        self.components = {
            "personality_engine": {
                "version": "1.0.0",
                "traits_extracted": 1000,
                "last_update": datetime.now().isoformat()
            },
            "conversation_engine": {
                "version": "1.0.0",
                "conversations_processed": 500,
                "last_update": datetime.now().isoformat()
            },
            "memory_system": {
                "version": "1.0.0",
                "memories_stored": 2000,
                "last_update": datetime.now().isoformat()
            },
            "recommendation_engine": {
                "version": "1.0.0",
                "recommendations_generated": 300,
                "last_update": datetime.now().isoformat()
            },
            "pattern_analyzer": {
                "version": "1.0.0",
                "patterns_detected": 150,
                "last_update": datetime.now().isoformat()
            }
        }
        self.performance_metrics = {
            "personality_modeling_accuracy": 0.75,
            "conversation_quality_score": 0.65,
            "memory_retrieval_speed": 0.55,  # Bottleneck
            "memory_retrieval_relevance": 0.70,
            "pattern_recognition_accuracy": 0.80,
            "recommendation_accuracy": 0.60,
            "recommendation_diversity": 0.55,
            "system_response_time": 0.90,
            "data_quality_score": 0.85
        }
        self.user_feedback = []
        
    def add_user_feedback(self, topic: str, sentiment: float, content: str) -> None:
        """
        Add user feedback to the system.
        
        Args:
            topic: Feedback topic
            sentiment: Sentiment score (-1.0 to 1.0)
            content: Feedback content
        """
        feedback = {
            "id": f"feedback_{len(self.user_feedback) + 1:03d}",
            "topic": topic,
            "sentiment": sentiment,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.user_feedback.append(feedback)
        logger.info(f"Added user feedback: {feedback['id']} on topic '{topic}'")
    
    def get_system_state(self) -> Dict[str, Any]:
        """
        Get the current system state.
        
        Returns:
            System state dictionary
        """
        return self.components
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get the current performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics
    
    def get_user_feedback(self) -> List[Dict[str, Any]]:
        """
        Get the user feedback.
        
        Returns:
            List of user feedback items
        """
        return self.user_feedback
    
    def update_component(self, component_name: str, updates: Dict[str, Any]) -> None:
        """
        Update a component with new values.
        
        Args:
            component_name: Name of the component to update
            updates: Dictionary of updates to apply
        """
        if component_name in self.components:
            self.components[component_name].update(updates)
            self.components[component_name]["last_update"] = datetime.now().isoformat()
            logger.info(f"Updated component: {component_name}")
        else:
            logger.warning(f"Component not found: {component_name}")
    
    def update_metrics(self, updates: Dict[str, Any]) -> None:
        """
        Update performance metrics.
        
        Args:
            updates: Dictionary of metric updates to apply
        """
        self.performance_metrics.update(updates)
        logger.info(f"Updated performance metrics: {list(updates.keys())}")


class EnhancedAdaptiveEvolutionDemo:
    """
    Demonstration of the Enhanced Adaptive Evolution Engine.
    """
    
    def __init__(self):
        """Initialize the demo."""
        self.digital_twin = DigitalTwinSystem()
        self.evolution_engine = EnhancedAdaptiveEvolutionEngine()
        logger.info("Enhanced Adaptive Evolution Demo initialized")
    
    async def run_demo(self):
        """Run the demonstration."""
        logger.info("Starting Enhanced Adaptive Evolution Demo")
        
        # Step 1: Add user feedback
        logger.info("\n=== Step 1: Adding User Feedback ===")
        self._add_sample_feedback()
        
        # Step 2: Analyze system
        logger.info("\n=== Step 2: Analyzing System ===")
        analysis_results = await self._analyze_system()
        
        # Step 3: Generate improvement proposals
        logger.info("\n=== Step 3: Generating Improvement Proposals ===")
        proposals = await self._generate_proposals()
        
        # Step 4: Validate proposals
        logger.info("\n=== Step 4: Validating Proposals ===")
        validation_results = await self._validate_proposals(proposals)
        
        # Step 5: Run evolution cycle
        logger.info("\n=== Step 5: Running Evolution Cycle ===")
        cycle_results = await self._run_evolution_cycle()
        
        # Step 6: Generate system health report
        logger.info("\n=== Step 6: Generating System Health Report ===")
        health_report = await self._generate_health_report()
        
        logger.info("\nEnhanced Adaptive Evolution Demo completed")
    
    def _add_sample_feedback(self):
        """Add sample user feedback."""
        self.digital_twin.add_user_feedback(
            topic="memory",
            sentiment=-0.6,
            content="Memory retrieval is too slow, it takes a long time to find relevant information"
        )
        self.digital_twin.add_user_feedback(
            topic="memory",
            sentiment=-0.4,
            content="Sometimes the system doesn't remember important details from previous conversations"
        )
        self.digital_twin.add_user_feedback(
            topic="memory",
            sentiment=-0.5,
            content="The memory system seems to prioritize recent information too much"
        )
        self.digital_twin.add_user_feedback(
            topic="conversation",
            sentiment=-0.3,
            content="Responses sometimes seem disconnected from the conversation context"
        )
        self.digital_twin.add_user_feedback(
            topic="recommendation",
            sentiment=-0.2,
            content="Recommendations don't seem to match my interests very well"
        )
    
    async def _analyze_system(self) -> Dict[str, Any]:
        """
        Analyze the system to identify bottlenecks and improvement opportunities.
        
        Returns:
            Analysis results
        """
        system_state = self.digital_twin.get_system_state()
        performance_metrics = self.digital_twin.get_performance_metrics()
        
        analysis_results = await self.evolution_engine.analyze_system(system_state, performance_metrics)
        
        logger.info(f"System analysis detected {len(analysis_results['bottlenecks'])} bottlenecks:")
        for i, bottleneck in enumerate(analysis_results["bottlenecks"], 1):
            logger.info(f"  {i}. {bottleneck['type']} in {bottleneck['component']}: {bottleneck['description']}")
            logger.info(f"     Severity: {bottleneck['severity']:.2f}")
            logger.info(f"     Solutions: {', '.join(bottleneck['solutions'])}")
        
        if analysis_results["bottleneck_patterns"]["patterns"]:
            logger.info(f"\nDetected {len(analysis_results['bottleneck_patterns']['patterns'])} bottleneck patterns:")
            for i, pattern in enumerate(analysis_results["bottleneck_patterns"]["patterns"], 1):
                logger.info(f"  {i}. {pattern['type']}: {pattern['description']}")
        
        if analysis_results["optimization_plan"]["steps"]:
            logger.info(f"\nOptimization plan ({analysis_results['optimization_plan']['priority']} priority):")
            for i, step in enumerate(analysis_results["optimization_plan"]["steps"], 1):
                logger.info(f"  {i}. {step['description']} ({step['priority']} priority)")
        
        return analysis_results
    
    async def _generate_proposals(self) -> List[ImprovementProposal]:
        """
        Generate improvement proposals.
        
        Returns:
            List of generated proposals
        """
        system_state = self.digital_twin.get_system_state()
        performance_metrics = self.digital_twin.get_performance_metrics()
        user_feedback = self.digital_twin.get_user_feedback()
        
        proposals = await self.evolution_engine.generate_improvement_proposals(
            system_state, performance_metrics, user_feedback
        )
        
        logger.info(f"Generated {len(proposals)} improvement proposals:")
        for i, proposal in enumerate(proposals, 1):
            logger.info(f"  {i}. {proposal.component}: {proposal.description}")
            logger.info(f"     Priority: {proposal.priority:.2f}")
            
            # Show evolution strategy if available
            if hasattr(proposal, "metadata") and "evolution_strategy" in proposal.metadata:
                strategy = proposal.metadata["evolution_strategy"]
                logger.info(f"     Evolution Strategy: {strategy['name']}")
            
            # Show confidence if available
            if hasattr(proposal, "metadata") and "confidence" in proposal.metadata:
                logger.info(f"     Confidence: {proposal.metadata['confidence']:.2f}")
            
            # Show implementation plan
            if proposal.implementation_plan:
                logger.info(f"     Implementation Plan: {len(proposal.implementation_plan)} steps")
        
        return proposals
    
    async def _validate_proposals(self, proposals: List[ImprovementProposal]) -> List[Dict[str, Any]]:
        """
        Validate improvement proposals.
        
        Args:
            proposals: List of proposals to validate
            
        Returns:
            List of validation results
        """
        validation_results = await self.evolution_engine.validate_proposals(proposals)
        
        logger.info(f"Validated {len(validation_results)} proposals:")
        for i, result in enumerate(validation_results, 1):
            safety_status = "SAFE" if result["is_safe"] else "UNSAFE"
            logger.info(f"  {i}. Proposal {result['proposal_id']}: {safety_status} (Score: {result['safety_score']:.2f})")
            
            if not result["is_safe"]:
                logger.info(f"     Warnings: {', '.join(result['warnings'])}")
            
            # Show strategy notes if available
            if "strategy_notes" in result:
                logger.info(f"     Strategy Notes: {', '.join(result['strategy_notes'])}")
        
        return validation_results
    
    async def _run_evolution_cycle(self) -> Dict[str, Any]:
        """
        Run a complete evolution cycle.
        
        Returns:
            Evolution cycle results
        """
        system_state = self.digital_twin.get_system_state()
        performance_metrics = self.digital_twin.get_performance_metrics()
        user_feedback = self.digital_twin.get_user_feedback()
        
        cycle_results = await self.evolution_engine.run_evolution_cycle(
            system_state, performance_metrics, user_feedback
        )
        
        logger.info(f"Evolution cycle {cycle_results['cycle_id']} completed in {cycle_results['duration_seconds']:.2f} seconds")
        logger.info(f"Completed {len(cycle_results['steps'])} steps:")
        
        for i, step in enumerate(cycle_results["steps"], 1):
            logger.info(f"  {i}. {step['step']}: {step['status']}")
            
            if "results" in step:
                for key, value in step["results"].items():
                    logger.info(f"     {key}: {value}")
        
        # Check if a proposal was implemented
        implementation_step = next((s for s in cycle_results["steps"] if s["step"] == "implement_proposal"), None)
        if implementation_step and implementation_step["status"] == "completed" and implementation_step["results"]["success"]:
            # Simulate component update
            component = implementation_step["results"].get("component", "memory_system")
            self.digital_twin.update_component(component, {
                "version": "1.1.0",  # Increment version
                "last_update": datetime.now().isoformat()
            })
            
            # Simulate metric improvements
            if "memory" in component.lower():
                self.digital_twin.update_metrics({
                    "memory_retrieval_speed": 0.75  # Improved from 0.55
                })
        
        return cycle_results
    
    async def _generate_health_report(self) -> Dict[str, Any]:
        """
        Generate a system health report.
        
        Returns:
            System health report
        """
        system_state = self.digital_twin.get_system_state()
        performance_metrics = self.digital_twin.get_performance_metrics()
        
        health_report = await self.evolution_engine.get_system_health_report(
            system_state, performance_metrics
        )
        
        logger.info(f"System Health Report:")
        logger.info(f"  Overall Health: {health_report['overall_health_status']} ({health_report['overall_health_score']:.2f})")
        logger.info(f"  Bottlenecks: {health_report['bottlenecks']}")
        
        logger.info(f"\nComponent Health:")
        for component, health in health_report["component_health"].items():
            logger.info(f"  {component}: {health['health_status']} ({health['health_score']:.2f})")
            logger.info(f"    Bottlenecks: {health['bottlenecks']}")
        
        logger.info(f"\nRecommendations:")
        for i, recommendation in enumerate(health_report["recommendations"], 1):
            logger.info(f"  {i}. {recommendation}")
        
        return health_report


async def main():
    """Main function."""
    try:
        demo = EnhancedAdaptiveEvolutionDemo()
        await demo.run_demo()
    except Exception as e:
        logger.error(f"Error in Enhanced Adaptive Evolution Demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())