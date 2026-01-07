"""
Tests for the AdaptiveEvolutionEngine.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.evolution.adaptive_engine import AdaptiveEvolutionEngine
from digital_twin.evolution.improvement_proposal import ImprovementProposal
from digital_twin.evolution.safety_validator import SafetyValidator


class TestAdaptiveEvolutionEngine:
    """Tests for the AdaptiveEvolutionEngine."""

    @pytest.fixture
    def engine(self):
        """Create an AdaptiveEvolutionEngine instance for testing."""
        return AdaptiveEvolutionEngine()

    @pytest.fixture
    def system_state(self):
        """Create a sample system state for testing."""
        return {
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

    @pytest.fixture
    def performance_metrics(self):
        """Create sample performance metrics for testing."""
        return {
            "personality_modeling_accuracy": 0.75,
            "conversation_quality_score": 0.65,
            "memory_retrieval_speed": 0.85,
            "memory_retrieval_relevance": 0.70,
            "pattern_recognition_accuracy": 0.80,
            "recommendation_accuracy": 0.60,
            "recommendation_diversity": 0.55,
            "system_response_time": 0.90
        }

    @pytest.fixture
    def user_feedback(self):
        """Create sample user feedback for testing."""
        return [
            {
                "id": "feedback_001",
                "topic": "conversation",
                "sentiment": -0.3,
                "content": "Responses sometimes seem disconnected from the conversation context",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "feedback_002",
                "topic": "conversation",
                "sentiment": -0.2,
                "content": "Sometimes the system doesn't remember things I mentioned earlier",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "feedback_003",
                "topic": "conversation",
                "sentiment": -0.4,
                "content": "Responses can be repetitive in longer conversations",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "feedback_004",
                "topic": "recommendations",
                "sentiment": -0.5,
                "content": "Recommendations don't seem to match my interests very well",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "feedback_005",
                "topic": "recommendations",
                "sentiment": -0.3,
                "content": "I keep seeing the same recommendations over and over",
                "timestamp": datetime.now().isoformat()
            }
        ]

    @pytest.mark.asyncio
    async def test_generate_improvement_proposals(self, engine, system_state, performance_metrics, user_feedback):
        """Test generate_improvement_proposals method."""
        # Call the method
        proposals = await engine.generate_improvement_proposals(system_state, performance_metrics, user_feedback)

        # Verify the result
        assert isinstance(proposals, list)
        assert len(proposals) > 0
        
        # Check that proposals were generated for low-performing areas
        proposal_components = [p.component for p in proposals]
        
        # Conversation quality is low (0.65) so should have a proposal
        assert any("conversation" in comp.lower() for comp in proposal_components)
        
        # Recommendation accuracy is low (0.60) so should have a proposal
        assert any("recommendation" in comp.lower() for comp in proposal_components)
        
        # Check that proposals have all required fields
        for proposal in proposals:
            assert proposal.proposal_id
            assert proposal.component
            assert proposal.description
            assert isinstance(proposal.implementation_plan, list)
            assert len(proposal.implementation_plan) > 0
            assert isinstance(proposal.expected_benefits, list)
            assert len(proposal.expected_benefits) > 0
            assert isinstance(proposal.risk_assessment, dict)
            assert 0.0 <= proposal.priority <= 1.0
            assert proposal.status == "proposed"

    @pytest.mark.asyncio
    async def test_validate_proposals(self, engine):
        """Test validate_proposals method."""
        # Create test proposals
        proposals = [
            ImprovementProposal(
                component="conversation_engine",
                description="Improve conversation context management",
                implementation_plan=[
                    {
                        "step_type": "analyze",
                        "description": "Analyze conversation flow patterns",
                        "action": "analyze_conversation_patterns",
                        "parameters": {"component": "conversation_engine"}
                    },
                    {
                        "step_type": "modify",
                        "description": "Enhance context management",
                        "action": "enhance_context_management",
                        "parameters": {"component": "conversation_engine"}
                    },
                    {
                        "step_type": "test",
                        "description": "Test conversation quality",
                        "action": "test_conversations",
                        "parameters": {"component": "conversation_engine"}
                    },
                    {
                        "step_type": "monitor",
                        "description": "Monitor performance after deployment",
                        "action": "monitor_performance",
                        "parameters": {"component": "conversation_engine", "duration": "24h"}
                    },
                    {
                        "step_type": "rollback",
                        "description": "Prepare rollback plan if needed",
                        "action": "prepare_rollback",
                        "parameters": {"component": "conversation_engine"}
                    }
                ],
                expected_benefits=[
                    "More coherent and contextually relevant responses",
                    "Better handling of complex conversation contexts"
                ],
                risk_assessment={
                    "data_integrity": 0.2,
                    "user_privacy": 0.1,
                    "system_stability": 0.3,
                    "behavioral_consistency": 0.4
                },
                priority=0.7
            ),
            ImprovementProposal(
                component="recommendation_engine",
                description="Improve recommendation diversity",
                implementation_plan=[
                    {
                        "step_type": "modify",
                        "description": "Modify recommendation algorithm",
                        "action": "modify_algorithm",
                        "parameters": {"component": "recommendation_engine"}
                    }
                ],
                expected_benefits=[
                    "More diverse recommendations",
                    "Higher user satisfaction"
                ],
                risk_assessment={
                    "data_integrity": 0.2,
                    "user_privacy": 0.1,
                    "system_stability": 0.7,  # High risk to system stability
                    "behavioral_consistency": 0.3
                },
                priority=0.6
            )
        ]

        # Call the method
        validation_results = await engine.validate_proposals(proposals)

        # Verify the result
        assert isinstance(validation_results, list)
        assert len(validation_results) == 2
        
        # First proposal should be safe (has testing, monitoring, and rollback)
        assert validation_results[0]["is_safe"] is True
        assert validation_results[0]["proposal_id"] == proposals[0].proposal_id
        
        # Second proposal should be unsafe (high system stability risk, no testing or rollback)
        assert validation_results[1]["is_safe"] is False
        assert validation_results[1]["proposal_id"] == proposals[1].proposal_id
        assert len(validation_results[1]["warnings"]) > 0
        
        # Check that proposal statuses were updated
        assert proposals[0].status == "validated"
        assert proposals[1].status == "rejected"

    @pytest.mark.asyncio
    async def test_implement_proposal(self, engine, system_state):
        """Test implement_proposal method."""
        # Create a test proposal
        proposal = ImprovementProposal(
            component="conversation_engine",
            description="Improve conversation context management",
            implementation_plan=[
                {
                    "step_type": "analyze",
                    "description": "Analyze conversation flow patterns",
                    "action": "analyze_conversation_patterns",
                    "parameters": {"component": "conversation_engine"}
                },
                {
                    "step_type": "modify",
                    "description": "Enhance context management",
                    "action": "enhance_context_management",
                    "parameters": {"component": "conversation_engine"}
                },
                {
                    "step_type": "test",
                    "description": "Test conversation quality",
                    "action": "test_conversations",
                    "parameters": {"component": "conversation_engine"}
                }
            ],
            expected_benefits=[
                "More coherent and contextually relevant responses",
                "Better handling of complex conversation contexts"
            ],
            risk_assessment={
                "data_integrity": 0.2,
                "user_privacy": 0.1,
                "system_stability": 0.3,
                "behavioral_consistency": 0.4
            },
            priority=0.7
        )
        
        # Set the proposal status to validated
        proposal.status = "validated"

        # Call the method
        implementation_results = await engine.implement_proposal(proposal, system_state)

        # Verify the result
        assert isinstance(implementation_results, dict)
        assert implementation_results["success"] is True
        assert implementation_results["steps_completed"] == len(proposal.implementation_plan)
        assert len(implementation_results["step_results"]) == len(proposal.implementation_plan)
        assert len(implementation_results["errors"]) == 0
        assert len(implementation_results["modified_components"]) > 0
        
        # Check that proposal status was updated
        assert proposal.status == "implemented"
        
        # Test with an unvalidated proposal
        unvalidated_proposal = ImprovementProposal(
            component="recommendation_engine",
            description="Improve recommendation diversity"
        )
        unvalidated_proposal.status = "proposed"  # Not validated
        
        # Call the method
        unvalidated_results = await engine.implement_proposal(unvalidated_proposal, system_state)
        
        # Verify the result
        assert unvalidated_results["success"] is False
        assert "must be validated" in unvalidated_results["message"]

    @pytest.mark.asyncio
    async def test_evaluate_implementation(self, engine):
        """Test evaluate_implementation method."""
        # Create a test proposal
        proposal = ImprovementProposal(
            component="conversation_engine",
            description="Improve conversation context management"
        )
        proposal.status = "implemented"
        
        # Create before and after metrics
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

        # Call the method
        evaluation_results = await engine.evaluate_implementation(proposal, before_metrics, after_metrics)

        # Verify the result
        assert isinstance(evaluation_results, dict)
        assert evaluation_results["success"] is True
        assert "metrics_comparison" in evaluation_results
        assert "improvement_scores" in evaluation_results
        assert evaluation_results["overall_improvement"] > 0
        assert evaluation_results["meets_expectations"] is True
        
        # Check that proposal status was updated
        assert proposal.status == "successful"
        
        # Test with a proposal that doesn't meet expectations
        proposal2 = ImprovementProposal(
            component="recommendation_engine",
            description="Improve recommendation diversity"
        )
        proposal2.status = "implemented"
        
        before_metrics2 = {
            "recommendation_accuracy": 0.60,
            "recommendation_diversity": 0.55
        }
        
        after_metrics2 = {
            "recommendation_accuracy": 0.61,  # Minimal improvement
            "recommendation_diversity": 0.56  # Minimal improvement
        }
        
        # Call the method
        evaluation_results2 = await engine.evaluate_implementation(proposal2, before_metrics2, after_metrics2)
        
        # Verify the result
        assert evaluation_results2["overall_improvement"] < 0.05  # Less than 5% improvement
        assert evaluation_results2["meets_expectations"] is False
        assert len(evaluation_results2["recommendations"]) > 0
        
        # Check that proposal status was updated
        assert proposal2.status == "reverted"

    @pytest.mark.asyncio
    async def test_get_improvement_history(self, engine):
        """Test get_improvement_history method."""
        # Initially, history should be empty
        history = await engine.get_improvement_history()
        assert isinstance(history, list)
        assert len(history) == 0
        
        # Add a successful improvement to history
        engine.improvement_history.append({
            "proposal_id": "test_proposal_1",
            "component": "conversation_engine",
            "description": "Improve conversation context management",
            "implemented_at": datetime.now().isoformat(),
            "overall_improvement": 0.15,
            "metrics_improved": ["conversation_quality_score", "context_retention_score"]
        })
        
        # Get history again
        history = await engine.get_improvement_history()
        assert len(history) == 1
        assert history[0]["proposal_id"] == "test_proposal_1"
        assert history[0]["component"] == "conversation_engine"
        assert history[0]["overall_improvement"] == 0.15

    @pytest.mark.asyncio
    async def test_get_proposals(self, engine):
        """Test get_proposals method."""
        # Create test proposals
        proposal1 = ImprovementProposal(
            proposal_id="test_proposal_1",
            component="conversation_engine",
            description="Improve conversation context management",
            status="validated"
        )
        
        proposal2 = ImprovementProposal(
            proposal_id="test_proposal_2",
            component="recommendation_engine",
            description="Improve recommendation diversity",
            status="rejected"
        )
        
        # Add proposals to engine
        engine.proposals = [proposal1, proposal2]
        
        # Get all proposals
        all_proposals = await engine.get_proposals()
        assert isinstance(all_proposals, list)
        assert len(all_proposals) == 2
        
        # Get validated proposals
        validated_proposals = await engine.get_proposals(status="validated")
        assert len(validated_proposals) == 1
        assert validated_proposals[0]["proposal_id"] == "test_proposal_1"
        
        # Get rejected proposals
        rejected_proposals = await engine.get_proposals(status="rejected")
        assert len(rejected_proposals) == 1
        assert rejected_proposals[0]["proposal_id"] == "test_proposal_2"