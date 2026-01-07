#!/usr/bin/env python3
"""
Adaptive Evolution Example

This script demonstrates the Adaptive Evolution Engine from INFINITY,
which provides self-improvement capabilities for the Digital Twin system.
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

from digital_twin.evolution.adaptive_engine import AdaptiveEvolutionEngine
from digital_twin.evolution.improvement_proposal import ImprovementProposal
from digital_twin.evolution.safety_validator import SafetyValidator


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
            }
        }
        self.performance_metrics = {
            "personality_modeling_accuracy": 0.75,
            "conversation_quality_score": 0.65,
            "memory_retrieval_speed": 0.85,
            "memory_retrieval_relevance": 0.70,
            "pattern_recognition_accuracy": 0.80,
            "recommendation_accuracy": 0.60,
            "recommendation_diversity": 0.55,
            "system_response_time": 0.90
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


class AdaptiveEvolutionDemo:
    """
    Demonstration of the Adaptive Evolution Engine.
    """
    
    def __init__(self):
        """Initialize the demo."""
        self.digital_twin = DigitalTwinSystem()
        self.evolution_engine = AdaptiveEvolutionEngine()
        logger.info("Adaptive Evolution Demo initialized")
    
    async def run_demo(self):
        """Run the demonstration."""
        logger.info("Starting Adaptive Evolution Demo")
        
        # Step 1: Add user feedback
        logger.info("\n=== Step 1: Adding User Feedback ===")
        self._add_sample_feedback()
        
        # Step 2: Generate improvement proposals
        logger.info("\n=== Step 2: Generating Improvement Proposals ===")
        proposals = await self._generate_proposals()
        
        # Step 3: Validate proposals
        logger.info("\n=== Step 3: Validating Proposals ===")
        validation_results = await self._validate_proposals(proposals)
        
        # Step 4: Implement a validated proposal
        logger.info("\n=== Step 4: Implementing a Validated Proposal ===")
        implementation_results = await self._implement_proposal(proposals)
        
        # Step 5: Evaluate the implementation
        logger.info("\n=== Step 5: Evaluating Implementation ===")
        evaluation_results = await self._evaluate_implementation(proposals)
        
        # Step 6: Show improvement history
        logger.info("\n=== Step 6: Showing Improvement History ===")
        await self._show_improvement_history()
        
        logger.info("\nAdaptive Evolution Demo completed")
    
    def _add_sample_feedback(self):
        """Add sample user feedback."""
        self.digital_twin.add_user_feedback(
            topic="conversation",
            sentiment=-0.3,
            content="Responses sometimes seem disconnected from the conversation context"
        )
        self.digital_twin.add_user_feedback(
            topic="conversation",
            sentiment=-0.2,
            content="Sometimes the system doesn't remember things I mentioned earlier"
        )
        self.digital_twin.add_user_feedback(
            topic="conversation",
            sentiment=-0.4,
            content="Responses can be repetitive in longer conversations"
        )
        self.digital_twin.add_user_feedback(
            topic="recommendations",
            sentiment=-0.5,
            content="Recommendations don't seem to match my interests very well"
        )
        self.digital_twin.add_user_feedback(
            topic="recommendations",
            sentiment=-0.3,
            content="I keep seeing the same recommendations over and over"
        )
    
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
            logger.info(f"  {i}. {proposal.component}: {proposal.description} (Priority: {proposal.priority:.2f})")
        
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
        
        return validation_results
    
    async def _implement_proposal(self, proposals: List[ImprovementProposal]) -> Dict[str, Any]:
        """
        Implement a validated proposal.
        
        Args:
            proposals: List of proposals
            
        Returns:
            Implementation results
        """
        # Find a validated proposal
        validated_proposals = [p for p in proposals if p.status == "validated"]
        if not validated_proposals:
            logger.warning("No validated proposals to implement")
            return {"success": False, "message": "No validated proposals"}
        
        # Select the highest priority validated proposal
        proposal = max(validated_proposals, key=lambda p: p.priority)
        logger.info(f"Selected proposal for implementation: {proposal.proposal_id}")
        logger.info(f"  Component: {proposal.component}")
        logger.info(f"  Description: {proposal.description}")
        logger.info(f"  Priority: {proposal.priority:.2f}")
        
        # Implement the proposal
        system_state = self.digital_twin.get_system_state()
        implementation_results = await self.evolution_engine.implement_proposal(
            proposal, system_state
        )
        
        if implementation_results["success"]:
            logger.info(f"Implementation successful: {implementation_results['steps_completed']} steps completed")
            
            # Simulate component update
            if proposal.component in system_state:
                self.digital_twin.update_component(proposal.component, {
                    "version": "1.1.0",  # Increment version
                    "last_update": datetime.now().isoformat()
                })
                
                # Simulate metric improvements
                if "conversation" in proposal.component.lower():
                    self.digital_twin.update_metrics({
                        "conversation_quality_score": 0.75  # Improved from 0.65
                    })
                elif "recommendation" in proposal.component.lower():
                    self.digital_twin.update_metrics({
                        "recommendation_accuracy": 0.70,  # Improved from 0.60
                        "recommendation_diversity": 0.65   # Improved from 0.55
                    })
        else:
            logger.warning(f"Implementation failed: {implementation_results.get('message', 'Unknown error')}")
            if implementation_results.get("errors"):
                logger.warning(f"Errors: {', '.join(implementation_results['errors'])}")
        
        return implementation_results
    
    async def _evaluate_implementation(self, proposals: List[ImprovementProposal]) -> Dict[str, Any]:
        """
        Evaluate an implemented proposal.
        
        Args:
            proposals: List of proposals
            
        Returns:
            Evaluation results
        """
        # Find an implemented proposal
        implemented_proposals = [p for p in proposals if p.status == "implemented"]
        if not implemented_proposals:
            logger.warning("No implemented proposals to evaluate")
            return {"success": False, "message": "No implemented proposals"}
        
        # Select the most recently implemented proposal
        proposal = implemented_proposals[-1]
        logger.info(f"Evaluating implementation of proposal: {proposal.proposal_id}")
        
        # Define before and after metrics based on the component
        before_metrics = {}
        after_metrics = {}
        
        if "conversation" in proposal.component.lower():
            before_metrics = {
                "conversation_quality_score": 0.65,
                "context_retention_score": 0.60,
                "response_relevance_score": 0.70
            }
            after_metrics = {
                "conversation_quality_score": 0.75,  # Improved
                "context_retention_score": 0.75,  # Improved
                "response_relevance_score": 0.80  # Improved
            }
        elif "recommendation" in proposal.component.lower():
            before_metrics = {
                "recommendation_accuracy": 0.60,
                "recommendation_diversity": 0.55
            }
            after_metrics = {
                "recommendation_accuracy": 0.70,  # Improved
                "recommendation_diversity": 0.65  # Improved
            }
        
        # Evaluate the implementation
        evaluation_results = await self.evolution_engine.evaluate_implementation(
            proposal, before_metrics, after_metrics
        )
        
        logger.info(f"Evaluation results:")
        logger.info(f"  Overall improvement: {evaluation_results['overall_improvement']:.2f}")
        logger.info(f"  Meets expectations: {evaluation_results['meets_expectations']}")
        
        # Show metric comparisons
        logger.info(f"  Metric comparisons:")
        for metric, comparison in evaluation_results["metrics_comparison"].items():
            logger.info(f"    {metric}: {comparison['before']:.2f} → {comparison['after']:.2f} ({comparison['percent_change']:.1f}%)")
        
        # Show recommendations if any
        if evaluation_results.get("recommendations"):
            logger.info(f"  Recommendations:")
            for recommendation in evaluation_results["recommendations"]:
                logger.info(f"    - {recommendation}")
        
        return evaluation_results
    
    async def _show_improvement_history(self) -> None:
        """Show the improvement history."""
        history = await self.evolution_engine.get_improvement_history()
        
        if not history:
            logger.info("No improvement history yet")
            return
        
        logger.info(f"Improvement history ({len(history)} entries):")
        for i, entry in enumerate(history, 1):
            logger.info(f"  {i}. {entry['component']}: {entry['description']}")
            logger.info(f"     Implemented: {entry['implemented_at']}")
            logger.info(f"     Overall improvement: {entry['overall_improvement']:.2f}")
            logger.info(f"     Metrics improved: {', '.join(entry['metrics_improved'])}")


async def main():
    """Main function."""
    try:
        demo = AdaptiveEvolutionDemo()
        await demo.run_demo()
    except Exception as e:
        logger.error(f"Error in Adaptive Evolution Demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())