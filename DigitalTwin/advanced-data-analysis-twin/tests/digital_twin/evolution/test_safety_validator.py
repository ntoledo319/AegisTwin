"""
Tests for the SafetyValidator.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.evolution.safety_validator import SafetyValidator
from digital_twin.evolution.improvement_proposal import ImprovementProposal


class TestSafetyValidator:
    """Tests for the SafetyValidator."""

    @pytest.fixture
    def validator(self):
        """Create a SafetyValidator instance for testing."""
        return SafetyValidator()

    @pytest.fixture
    def safe_proposal(self):
        """Create a safe proposal for testing."""
        return {
            "proposal_id": "test_proposal_1",
            "component": "conversation_engine",
            "description": "Improve conversation context management",
            "implementation_plan": [
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
                    "step_type": "validate",
                    "description": "Validate behavioral consistency",
                    "action": "validate_consistency",
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
            "expected_benefits": [
                "More coherent and contextually relevant responses",
                "Better handling of complex conversation contexts"
            ],
            "risk_assessment": {
                "data_integrity": 0.2,
                "user_privacy": 0.1,
                "system_stability": 0.3,
                "behavioral_consistency": 0.4
            },
            "priority": 0.7
        }

    @pytest.fixture
    def unsafe_proposal(self):
        """Create an unsafe proposal for testing."""
        return {
            "proposal_id": "test_proposal_2",
            "component": "memory_system",
            "description": "Optimize memory storage and retrieval",
            "implementation_plan": [
                {
                    "step_type": "modify",
                    "description": "Modify memory storage format",
                    "action": "modify_storage_format",
                    "parameters": {"component": "memory_system"}
                },
                {
                    "step_type": "modify",
                    "description": "Update retrieval algorithms",
                    "action": "update_algorithms",
                    "parameters": {"component": "memory_system"}
                },
                {
                    "step_type": "deploy",
                    "description": "Deploy changes to production",
                    "action": "deploy_changes",
                    "parameters": {"component": "memory_system"}
                }
                # Missing testing, validation, monitoring, and rollback steps
            ],
            "expected_benefits": [
                "Faster memory retrieval",
                "More efficient storage"
            ],
            "risk_assessment": {
                "data_integrity": 0.7,  # High risk to data integrity
                "user_privacy": 0.6,    # High risk to user privacy
                "system_stability": 0.5,
                "behavioral_consistency": 0.3
            },
            "priority": 0.8
        }

    @pytest.mark.asyncio
    async def test_validate_proposal_safe(self, validator, safe_proposal):
        """Test validate_proposal with a safe proposal."""
        # Call the method
        validation_results = await validator.validate_proposal(safe_proposal)

        # Verify the result
        assert isinstance(validation_results, dict)
        assert validation_results["is_safe"] is True
        assert "safety_score" in validation_results
        assert validation_results["safety_score"] >= 0.7  # Should be reasonably safe
        assert "safety_aspects" in validation_results
        assert len(validation_results["warnings"]) == 0
        assert "validation_id" in validation_results
        assert "timestamp" in validation_results

        # Check that all required safety aspects are present
        assert "data_integrity" in validation_results["safety_aspects"]
        assert "user_privacy" in validation_results["safety_aspects"]
        assert "system_stability" in validation_results["safety_aspects"]
        assert "behavioral_consistency" in validation_results["safety_aspects"]

        # Check that the validation was added to history
        assert len(validator.validation_history) == 1
        assert validator.validation_history[0]["proposal_id"] == safe_proposal["proposal_id"]
        assert validator.validation_history[0]["is_safe"] is True

    @pytest.mark.asyncio
    async def test_validate_proposal_unsafe(self, validator, unsafe_proposal):
        """Test validate_proposal with an unsafe proposal."""
        # Call the method
        validation_results = await validator.validate_proposal(unsafe_proposal)

        # Verify the result
        assert isinstance(validation_results, dict)
        assert validation_results["is_safe"] is False
        assert "safety_score" in validation_results
        assert validation_results["safety_score"] < 0.7  # Should be unsafe
        assert "safety_aspects" in validation_results
        assert len(validation_results["warnings"]) > 0
        assert len(validation_results["recommendations"]) > 0
        assert "validation_id" in validation_results
        assert "timestamp" in validation_results

        # Check that the validation was added to history
        assert len(validator.validation_history) == 1
        assert validator.validation_history[0]["proposal_id"] == unsafe_proposal["proposal_id"]
        assert validator.validation_history[0]["is_safe"] is False

    @pytest.mark.asyncio
    async def test_validate_implementation(self, validator, safe_proposal):
        """Test validate_implementation method."""
        # Extract implementation plan
        implementation_plan = safe_proposal["implementation_plan"]

        # Call the method
        validation_results = await validator.validate_implementation(safe_proposal, implementation_plan)

        # Verify the result
        assert isinstance(validation_results, dict)
        assert validation_results["is_safe"] is True
        assert "safety_score" in validation_results
        assert "step_validations" in validation_results
        assert len(validation_results["step_validations"]) == len(implementation_plan)
        assert len(validation_results["warnings"]) == 0
        assert "validation_id" in validation_results
        assert "timestamp" in validation_results

        # Check that each step has a validation result
        for i, step_validation in enumerate(validation_results["step_validations"]):
            assert step_validation["step_index"] == i
            assert "step_description" in step_validation
            assert "is_safe" in step_validation
            assert "safety_score" in step_validation

        # Check that the validation was added to history
        assert len(validator.validation_history) == 1
        assert validator.validation_history[0]["proposal_id"] == safe_proposal["proposal_id"]
        assert validator.validation_history[0]["is_safe"] is True
        assert validator.validation_history[0]["type"] == "implementation"

    @pytest.mark.asyncio
    async def test_validate_implementation_unsafe(self, validator, unsafe_proposal):
        """Test validate_implementation with an unsafe implementation plan."""
        # Extract implementation plan
        implementation_plan = unsafe_proposal["implementation_plan"]

        # Call the method
        validation_results = await validator.validate_implementation(unsafe_proposal, implementation_plan)

        # Verify the result
        assert isinstance(validation_results, dict)
        assert validation_results["is_safe"] is False
        assert "safety_score" in validation_results
        assert "step_validations" in validation_results
        assert len(validation_results["step_validations"]) == len(implementation_plan)
        assert len(validation_results["warnings"]) > 0
        assert len(validation_results["recommendations"]) > 0
        assert "validation_id" in validation_results
        assert "timestamp" in validation_results

        # Check that the validation was added to history
        assert len(validator.validation_history) == 1
        assert validator.validation_history[0]["proposal_id"] == unsafe_proposal["proposal_id"]
        assert validator.validation_history[0]["is_safe"] is False
        assert validator.validation_history[0]["type"] == "implementation"

    @pytest.mark.asyncio
    async def test_get_validation_history(self, validator, safe_proposal, unsafe_proposal):
        """Test get_validation_history method."""
        # Initially, history should be empty
        history = await validator.get_validation_history()
        assert isinstance(history, list)
        assert len(history) == 0

        # Add validations
        await validator.validate_proposal(safe_proposal)
        await validator.validate_proposal(unsafe_proposal)

        # Get history again
        history = await validator.get_validation_history()
        assert len(history) == 2
        assert history[0]["proposal_id"] == safe_proposal["proposal_id"]
        assert history[1]["proposal_id"] == unsafe_proposal["proposal_id"]
        assert history[0]["is_safe"] is True
        assert history[1]["is_safe"] is False

    @pytest.mark.asyncio
    async def test_validate_data_integrity(self, validator):
        """Test _validate_data_integrity method."""
        # Create proposals with different data integrity risks
        low_risk_proposal = {
            "component": "conversation_engine",
            "description": "Improve conversation flow",
            "implementation_plan": [
                {"step_type": "test", "description": "Test changes"},
                {"step_type": "rollback", "description": "Prepare rollback plan"}
            ],
            "risk_assessment": {"data_integrity": 0.2}
        }

        high_risk_proposal = {
            "component": "memory_system",
            "description": "Modify data storage format",
            "implementation_plan": [
                {"step_type": "modify", "description": "Modify storage format"}
                # Missing validation and rollback steps
            ],
            "risk_assessment": {"data_integrity": 0.7}
        }

        # Call the method directly
        low_risk_score = await validator._validate_data_integrity(low_risk_proposal)
        high_risk_score = await validator._validate_data_integrity(high_risk_proposal)

        # Verify the results
        assert low_risk_score > 0.7  # Should be safe
        assert high_risk_score < 0.5  # Should be unsafe

    @pytest.mark.asyncio
    async def test_validate_user_privacy(self, validator):
        """Test _validate_user_privacy method."""
        # Create proposals with different user privacy risks
        low_risk_proposal = {
            "component": "conversation_engine",
            "description": "Improve conversation flow",
            "implementation_plan": [
                {"step_type": "test", "description": "Test changes"},
                {"step_type": "privacy", "description": "Ensure privacy protection"}
            ],
            "risk_assessment": {"user_privacy": 0.1}
        }

        high_risk_proposal = {
            "component": "user_data",
            "description": "Enhance user data processing",
            "implementation_plan": [
                {"step_type": "modify", "description": "Modify data processing"}
                # Missing privacy protection steps
            ],
            "risk_assessment": {"user_privacy": 0.6}
        }

        # Call the method directly
        low_risk_score = await validator._validate_user_privacy(low_risk_proposal)
        high_risk_score = await validator._validate_user_privacy(high_risk_proposal)

        # Verify the results
        assert low_risk_score > 0.7  # Should be safe
        assert high_risk_score < 0.5  # Should be unsafe

    @pytest.mark.asyncio
    async def test_validate_system_stability(self, validator):
        """Test _validate_system_stability method."""
        # Create proposals with different system stability risks
        low_risk_proposal = {
            "component": "utility",
            "description": "Add new utility function",
            "implementation_plan": [
                {"step_type": "test", "description": "Test changes"},
                {"step_type": "monitor", "description": "Monitor system stability"},
                {"step_type": "rollback", "description": "Prepare rollback plan"}
            ],
            "risk_assessment": {"system_stability": 0.2}
        }

        high_risk_proposal = {
            "component": "core_engine",
            "description": "Modify core processing logic",
            "implementation_plan": [
                {"step_type": "modify", "description": "Modify core logic"}
                # Missing testing, monitoring, and rollback steps
            ],
            "risk_assessment": {"system_stability": 0.7}
        }

        # Call the method directly
        low_risk_score = await validator._validate_system_stability(low_risk_proposal)
        high_risk_score = await validator._validate_system_stability(high_risk_proposal)

        # Verify the results
        assert low_risk_score > 0.7  # Should be safe
        assert high_risk_score < 0.5  # Should be unsafe

    @pytest.mark.asyncio
    async def test_validate_behavioral_consistency(self, validator):
        """Test _validate_behavioral_consistency method."""
        # Create proposals with different behavioral consistency risks
        low_risk_proposal = {
            "component": "utility",
            "description": "Add new utility function",
            "implementation_plan": [
                {"step_type": "test", "description": "Test changes"},
                {"step_type": "consistency", "description": "Check behavioral consistency"}
            ],
            "risk_assessment": {"behavioral_consistency": 0.2}
        }

        high_risk_proposal = {
            "component": "conversation_engine",
            "description": "Modify response generation",
            "implementation_plan": [
                {"step_type": "modify", "description": "Modify response generation"}
                # Missing consistency validation steps
            ],
            "risk_assessment": {"behavioral_consistency": 0.6}
        }

        # Call the method directly
        low_risk_score = await validator._validate_behavioral_consistency(low_risk_proposal)
        high_risk_score = await validator._validate_behavioral_consistency(high_risk_proposal)

        # Verify the results
        assert low_risk_score > 0.6  # Should be safe
        assert high_risk_score < 0.5  # Should be unsafe