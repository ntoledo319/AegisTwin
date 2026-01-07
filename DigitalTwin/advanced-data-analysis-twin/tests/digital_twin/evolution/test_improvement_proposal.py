"""
Tests for the ImprovementProposal class.
"""

import pytest
import sys
import os
from datetime import datetime
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.evolution.improvement_proposal import ImprovementProposal


class TestImprovementProposal:
    """Tests for the ImprovementProposal class."""

    @pytest.fixture
    def proposal(self):
        """Create an ImprovementProposal instance for testing."""
        return ImprovementProposal(
            proposal_id="test_proposal_1",
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

    def test_initialization(self, proposal):
        """Test initialization of ImprovementProposal."""
        assert proposal.proposal_id == "test_proposal_1"
        assert proposal.component == "conversation_engine"
        assert proposal.description == "Improve conversation context management"
        assert len(proposal.implementation_plan) == 2
        assert len(proposal.expected_benefits) == 2
        assert proposal.risk_assessment["data_integrity"] == 0.2
        assert proposal.priority == 0.7
        assert proposal.status == "proposed"
        assert proposal.created_at is not None
        assert proposal.updated_at is not None
        assert proposal.evaluation_results == {}
        assert proposal.implementation_results == {}
        assert proposal.metadata == {}

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        proposal = ImprovementProposal()
        assert proposal.proposal_id is not None
        assert proposal.proposal_id.startswith("proposal_")
        assert proposal.component == ""
        assert proposal.description == ""
        assert proposal.implementation_plan == []
        assert proposal.expected_benefits == []
        assert proposal.risk_assessment == {}
        assert proposal.priority == 0.5
        assert proposal.status == "proposed"
        assert proposal.created_at is not None
        assert proposal.updated_at is not None
        assert proposal.evaluation_results == {}
        assert proposal.implementation_results == {}
        assert proposal.metadata == {}

    def test_to_dict(self, proposal):
        """Test to_dict method."""
        proposal_dict = proposal.to_dict()
        assert proposal_dict["proposal_id"] == "test_proposal_1"
        assert proposal_dict["component"] == "conversation_engine"
        assert proposal_dict["description"] == "Improve conversation context management"
        assert len(proposal_dict["implementation_plan"]) == 2
        assert len(proposal_dict["expected_benefits"]) == 2
        assert proposal_dict["risk_assessment"]["data_integrity"] == 0.2
        assert proposal_dict["priority"] == 0.7
        assert proposal_dict["status"] == "proposed"
        assert proposal_dict["created_at"] is not None
        assert proposal_dict["updated_at"] is not None
        assert proposal_dict["evaluation_results"] == {}
        assert proposal_dict["implementation_results"] == {}
        assert proposal_dict["metadata"] == {}

    def test_from_dict(self):
        """Test from_dict method."""
        proposal_dict = {
            "proposal_id": "test_proposal_2",
            "component": "recommendation_engine",
            "description": "Improve recommendation diversity",
            "implementation_plan": [
                {
                    "step_type": "modify",
                    "description": "Modify recommendation algorithm",
                    "action": "modify_algorithm",
                    "parameters": {"component": "recommendation_engine"}
                }
            ],
            "expected_benefits": [
                "More diverse recommendations",
                "Higher user satisfaction"
            ],
            "risk_assessment": {
                "data_integrity": 0.2,
                "user_privacy": 0.1,
                "system_stability": 0.3,
                "behavioral_consistency": 0.2
            },
            "priority": 0.6,
            "status": "validated",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "evaluation_results": {
                "safety_validation": {
                    "is_safe": True,
                    "safety_score": 0.8
                }
            },
            "implementation_results": {
                "success": True,
                "steps_completed": 1
            },
            "metadata": {
                "source": "user_feedback"
            }
        }
        
        proposal = ImprovementProposal.from_dict(proposal_dict)
        assert proposal.proposal_id == "test_proposal_2"
        assert proposal.component == "recommendation_engine"
        assert proposal.description == "Improve recommendation diversity"
        assert len(proposal.implementation_plan) == 1
        assert len(proposal.expected_benefits) == 2
        assert proposal.risk_assessment["data_integrity"] == 0.2
        assert proposal.priority == 0.6
        assert proposal.status == "validated"
        assert proposal.created_at == "2025-01-01T00:00:00"
        assert proposal.updated_at == "2025-01-02T00:00:00"
        assert proposal.evaluation_results["safety_validation"]["is_safe"] is True
        assert proposal.implementation_results["success"] is True
        assert proposal.metadata["source"] == "user_feedback"

    def test_update_status(self, proposal):
        """Test update_status method."""
        original_updated_at = proposal.updated_at
        time.sleep(0.001)  # Ensure timestamp changes
        
        proposal.update_status("validated")
        assert proposal.status == "validated"
        assert proposal.updated_at > original_updated_at

    def test_add_evaluation_result(self, proposal):
        """Test add_evaluation_result method."""
        original_updated_at = proposal.updated_at
        time.sleep(0.001)  # Ensure timestamp changes
        
        safety_validation = {
            "is_safe": True,
            "safety_score": 0.8,
            "warnings": []
        }
        
        proposal.add_evaluation_result("safety_validation", safety_validation)
        assert "safety_validation" in proposal.evaluation_results
        assert proposal.evaluation_results["safety_validation"] == safety_validation
        assert proposal.updated_at > original_updated_at

    def test_add_implementation_result(self, proposal):
        """Test add_implementation_result method."""
        original_updated_at = proposal.updated_at
        time.sleep(0.001)  # Ensure timestamp changes
        
        implementation_result = {
            "success": True,
            "steps_completed": 2,
            "errors": []
        }
        
        proposal.add_implementation_result(implementation_result)
        assert proposal.implementation_results == implementation_result
        assert proposal.updated_at > original_updated_at

    def test_add_metadata(self, proposal):
        """Test add_metadata method."""
        original_updated_at = proposal.updated_at
        time.sleep(0.001)  # Ensure timestamp changes
        
        proposal.add_metadata("source", "user_feedback")
        assert "source" in proposal.metadata
        assert proposal.metadata["source"] == "user_feedback"
        assert proposal.updated_at > original_updated_at

    def test_is_safe(self, proposal):
        """Test is_safe method."""
        # Initially, proposal has no safety validation
        assert proposal.is_safe() is False
        
        # Add safety validation with is_safe=True
        proposal.add_evaluation_result("safety_validation", {"is_safe": True})
        assert proposal.is_safe() is True
        
        # Add safety validation with is_safe=False
        proposal.add_evaluation_result("safety_validation", {"is_safe": False})
        assert proposal.is_safe() is False

    def test_get_safety_score(self, proposal):
        """Test get_safety_score method."""
        # Initially, proposal has no safety validation
        assert proposal.get_safety_score() == 0.0
        
        # Add safety validation with safety_score=0.8
        proposal.add_evaluation_result("safety_validation", {"safety_score": 0.8})
        assert proposal.get_safety_score() == 0.8
        
        # Add safety validation with safety_score=0.5
        proposal.add_evaluation_result("safety_validation", {"safety_score": 0.5})
        assert proposal.get_safety_score() == 0.5

    def test_get_implementation_success(self, proposal):
        """Test get_implementation_success method."""
        # Initially, proposal has no implementation results
        assert proposal.get_implementation_success() is False
        
        # Add implementation results with success=True
        proposal.add_implementation_result({"success": True})
        assert proposal.get_implementation_success() is True
        
        # Add implementation results with success=False
        proposal.add_implementation_result({"success": False})
        assert proposal.get_implementation_success() is False

    def test_get_warnings(self, proposal):
        """Test get_warnings method."""
        # Initially, proposal has no warnings
        assert proposal.get_warnings() == []
        
        # Add safety validation with warnings
        proposal.add_evaluation_result("safety_validation", {
            "warnings": ["Warning 1", "Warning 2"]
        })
        assert len(proposal.get_warnings()) == 2
        assert "Warning 1" in proposal.get_warnings()
        assert "Warning 2" in proposal.get_warnings()
        
        # Add implementation results with errors
        proposal.add_implementation_result({
            "errors": ["Error 1", "Error 2"]
        })
        assert len(proposal.get_warnings()) == 4
        assert "Error 1" in proposal.get_warnings()
        assert "Error 2" in proposal.get_warnings()

    def test_get_recommendations(self, proposal):
        """Test get_recommendations method."""
        # Initially, proposal has no recommendations
        assert proposal.get_recommendations() == []
        
        # Add safety validation with recommendations
        proposal.add_evaluation_result("safety_validation", {
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        })
        assert len(proposal.get_recommendations()) == 2
        assert "Recommendation 1" in proposal.get_recommendations()
        assert "Recommendation 2" in proposal.get_recommendations()
        
        # Add implementation evaluation with recommendations
        proposal.add_evaluation_result("implementation_evaluation", {
            "recommendations": ["Recommendation 3", "Recommendation 4"]
        })
        assert len(proposal.get_recommendations()) == 4
        assert "Recommendation 3" in proposal.get_recommendations()
        assert "Recommendation 4" in proposal.get_recommendations()