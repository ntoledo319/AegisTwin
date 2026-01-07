"""
Tests for the TraumaPatternAnalyzer adapter.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.adapters.trauma_archaeologist import TraumaPatternAnalyzer


class TestTraumaPatternAnalyzer:
    """Tests for the TraumaPatternAnalyzer adapter."""

    @pytest.fixture
    def analyzer(self):
        """Create a TraumaPatternAnalyzer instance for testing."""
        return TraumaPatternAnalyzer()

    @pytest.fixture
    def consciousness_states(self):
        """Create sample consciousness states for testing."""
        return [
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=30)).isoformat(),
                "mood_level": 2,
                "anxiety_level": 4,
                "focus_level": 3,
                "triggers": ["work_stress", "deadline_pressure"],
                "metadata": {"location": "office", "time": "morning"}
            },
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=25)).isoformat(),
                "mood_level": 3,
                "anxiety_level": 3,
                "focus_level": 4,
                "triggers": ["work_stress", "team_meeting"],
                "metadata": {"location": "office", "time": "afternoon"}
            },
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=20)).isoformat(),
                "mood_level": 2,
                "anxiety_level": 5,
                "focus_level": 2,
                "triggers": ["performance_review", "criticism"],
                "metadata": {"location": "office", "time": "morning"}
            },
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=15)).isoformat(),
                "mood_level": 4,
                "anxiety_level": 2,
                "focus_level": 4,
                "triggers": ["weekend", "relaxation"],
                "metadata": {"location": "home", "time": "morning"}
            },
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=10)).isoformat(),
                "mood_level": 3,
                "anxiety_level": 3,
                "focus_level": 3,
                "triggers": ["work_stress", "new_project"],
                "metadata": {"location": "office", "time": "morning"}
            },
            {
                "timestamp": (datetime.now() - asyncio.timedelta(days=5)).isoformat(),
                "mood_level": 2,
                "anxiety_level": 4,
                "focus_level": 3,
                "triggers": ["performance_review", "criticism"],
                "metadata": {"location": "office", "time": "afternoon"}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "mood_level": 3,
                "anxiety_level": 3,
                "focus_level": 4,
                "triggers": ["work_stress", "deadline_pressure"],
                "metadata": {"location": "office", "time": "morning"}
            }
        ]

    @pytest.fixture
    def trauma_signatures(self):
        """Create sample trauma signatures for testing."""
        return [
            {
                "signature_id": "trauma_001",
                "trauma_type": "relational",
                "severity": 0.7,
                "age_estimate": 20,
                "affected_dimensions": ["emotional", "social"],
                "core_wound": "fear of criticism",
                "protective_mechanisms": ["avoidance", "perfectionism"],
                "trigger_patterns": ["performance_review", "criticism"]
            },
            {
                "signature_id": "trauma_002",
                "trauma_type": "chronic",
                "severity": 0.6,
                "age_estimate": 30,
                "affected_dimensions": ["emotional", "cognitive"],
                "core_wound": "work-related stress",
                "protective_mechanisms": ["procrastination", "distraction"],
                "trigger_patterns": ["work_stress", "deadline_pressure"]
            }
        ]

    @pytest.mark.asyncio
    async def test_analyze_trauma_patterns_with_spidermind(self, analyzer, consciousness_states):
        """Test analyze_trauma_patterns with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        analyzer.trauma_archaeologist = MagicMock()
        analyzer.trauma_archaeologist.excavate_trauma_patterns = MagicMock(
            return_value=asyncio.Future()
        )
        analyzer.trauma_archaeologist.excavate_trauma_patterns.return_value.set_result({
            "trauma_signatures": [
                {
                    "signature_id": "trauma_001",
                    "trauma_type": "relational",
                    "severity": 0.7,
                    "age_estimate": 20,
                    "affected_dimensions": ["emotional", "social"],
                    "core_wound": "fear of criticism",
                    "protective_mechanisms": ["avoidance", "perfectionism"],
                    "trigger_patterns": ["performance_review", "criticism"]
                }
            ],
            "excavation_depth": 5,
            "confidence": 0.8
        })

        # Call the method
        result = await analyzer.analyze_trauma_patterns(consciousness_states)

        # Verify the result
        assert "trauma_patterns" in result
        assert len(result["trauma_patterns"]) > 0
        assert result["trauma_patterns"][0]["signature_id"] == "trauma_001"
        assert result["trauma_patterns"][0]["severity"] == 0.7
        assert "confidence" in result

        # Verify that the SpiderMind method was called
        analyzer.trauma_archaeologist.excavate_trauma_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_trauma_patterns_fallback(self, analyzer, consciousness_states):
        """Test analyze_trauma_patterns fallback implementation."""
        # Ensure SpiderMind components are not available
        analyzer.trauma_archaeologist = None
        analyzer.trauma_structures = None

        # Call the method
        result = await analyzer.analyze_trauma_patterns(consciousness_states)

        # Verify the result
        assert "trauma_patterns" in result
        assert isinstance(result["trauma_patterns"], list)
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_generate_healing_pathways_with_spidermind(self, analyzer, trauma_signatures):
        """Test generate_healing_pathways with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        analyzer.trauma_archaeologist = MagicMock()
        analyzer.trauma_archaeologist.generate_healing_pathways = MagicMock(
            return_value=asyncio.Future()
        )
        analyzer.trauma_archaeologist.generate_healing_pathways.return_value.set_result([
            {
                "pathway_id": "pathway_001",
                "trauma_signature_id": "trauma_001",
                "healing_approach": "cognitive behavioral therapy",
                "estimated_duration": 90,
                "success_probability": 0.8,
                "healing_stages": [
                    {"stage": 1, "focus": "awareness", "duration": 30},
                    {"stage": 2, "focus": "processing", "duration": 30},
                    {"stage": 3, "focus": "integration", "duration": 30}
                ]
            }
        ])

        # Call the method
        result = await analyzer.generate_healing_pathways(trauma_signatures)

        # Verify the result
        assert len(result) > 0
        assert result[0]["pathway_id"] == "pathway_001"
        assert result[0]["trauma_signature_id"] == "trauma_001"
        assert result[0]["success_probability"] == 0.8
        assert len(result[0]["healing_stages"]) == 3

        # Verify that the SpiderMind method was called
        analyzer.trauma_archaeologist.generate_healing_pathways.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_healing_pathways_fallback(self, analyzer, trauma_signatures):
        """Test generate_healing_pathways fallback implementation."""
        # Ensure SpiderMind components are not available
        analyzer.trauma_archaeologist = None
        analyzer.trauma_structures = None

        # Call the method
        result = await analyzer.generate_healing_pathways(trauma_signatures)

        # Verify the result
        assert len(result) > 0
        assert "pathway_id" in result[0]
        assert "trauma_signature_id" in result[0]
        assert "healing_approach" in result[0]
        assert "healing_stages" in result[0]

    @pytest.mark.asyncio
    async def test_analyze_trigger_patterns(self, analyzer, consciousness_states):
        """Test analyze_trigger_patterns method."""
        # Mock the SpiderMind Omega components
        analyzer.trauma_archaeologist = MagicMock()
        analyzer.trauma_archaeologist.analyze_trigger_patterns = MagicMock(
            return_value=asyncio.Future()
        )
        analyzer.trauma_archaeologist.analyze_trigger_patterns.return_value.set_result({
            "triggers": [
                {
                    "trigger": "criticism",
                    "frequency": 2,
                    "impact_score": 0.8,
                    "associated_emotions": ["anxiety", "fear"]
                },
                {
                    "trigger": "work_stress",
                    "frequency": 3,
                    "impact_score": 0.7,
                    "associated_emotions": ["anxiety", "frustration"]
                }
            ],
            "confidence": 0.85
        })

        # Call the method
        result = await analyzer.analyze_trigger_patterns(consciousness_states)

        # Verify the result
        assert "triggers" in result
        assert len(result["triggers"]) > 0
        assert result["triggers"][0]["trigger"] in ["criticism", "work_stress"]
        assert "confidence" in result

        # If SpiderMind is not available, test the fallback
        analyzer.trauma_archaeologist = None
        result = await analyzer.analyze_trigger_patterns(consciousness_states)
        
        # Verify the fallback result
        assert "triggers" in result
        assert isinstance(result["triggers"], list)
        assert "confidence" in result