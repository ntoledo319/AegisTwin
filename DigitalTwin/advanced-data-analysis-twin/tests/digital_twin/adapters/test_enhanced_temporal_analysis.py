"""
Tests for the EnhancedTemporalAnalysisEngine adapter.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.adapters.enhanced_temporal_analysis import EnhancedTemporalAnalysisEngine


class TestEnhancedTemporalAnalysisEngine:
    """Tests for the EnhancedTemporalAnalysisEngine adapter."""

    @pytest.fixture
    def engine(self):
        """Create an EnhancedTemporalAnalysisEngine instance for testing."""
        return EnhancedTemporalAnalysisEngine()

    @pytest.fixture
    def temporal_data(self):
        """Create sample temporal data for testing."""
        now = datetime.now()
        return [
            {
                "timestamp": (now - timedelta(days=30)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 480,
                "stress_level": 7,
                "productivity_score": 6,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=29)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 490,
                "stress_level": 6,
                "productivity_score": 7,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=28)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 470,
                "stress_level": 8,
                "productivity_score": 5,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=27)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 485,
                "stress_level": 7,
                "productivity_score": 6,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=26)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 460,
                "stress_level": 6,
                "productivity_score": 7,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=25)).isoformat(),
                "activity_type": "leisure",
                "duration_minutes": 240,
                "stress_level": 3,
                "productivity_score": None,
                "location": "home"
            },
            {
                "timestamp": (now - timedelta(days=24)).isoformat(),
                "activity_type": "leisure",
                "duration_minutes": 360,
                "stress_level": 2,
                "productivity_score": None,
                "location": "park"
            },
            {
                "timestamp": (now - timedelta(days=23)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 480,
                "stress_level": 6,
                "productivity_score": 7,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=22)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 485,
                "stress_level": 7,
                "productivity_score": 6,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=21)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 470,
                "stress_level": 8,
                "productivity_score": 5,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=20)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 490,
                "stress_level": 7,
                "productivity_score": 6,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=19)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 480,
                "stress_level": 6,
                "productivity_score": 7,
                "location": "office"
            },
            {
                "timestamp": (now - timedelta(days=18)).isoformat(),
                "activity_type": "leisure",
                "duration_minutes": 300,
                "stress_level": 3,
                "productivity_score": None,
                "location": "home"
            },
            {
                "timestamp": (now - timedelta(days=17)).isoformat(),
                "activity_type": "leisure",
                "duration_minutes": 360,
                "stress_level": 2,
                "productivity_score": None,
                "location": "beach"
            },
            {
                "timestamp": (now - timedelta(days=16)).isoformat(),
                "activity_type": "work",
                "duration_minutes": 480,
                "stress_level": 7,
                "productivity_score": 6,
                "location": "office"
            }
        ]

    @pytest.fixture
    def temporal_data_sets(self):
        """Create sample temporal data sets for testing."""
        now = datetime.now()
        
        # Work data
        work_data = [
            {
                "timestamp": (now - timedelta(days=i)).isoformat(),
                "duration_minutes": 480 - (i % 3) * 10,
                "stress_level": 6 + (i % 3),
                "productivity_score": 7 - (i % 3)
            } for i in range(30, 15, -1)
        ]
        
        # Sleep data
        sleep_data = [
            {
                "timestamp": (now - timedelta(days=i)).isoformat(),
                "duration_minutes": 420 + (i % 4) * 15,
                "quality_score": 7 - (i % 3),
                "interruptions": (i % 3)
            } for i in range(30, 15, -1)
        ]
        
        # Exercise data
        exercise_data = [
            {
                "timestamp": (now - timedelta(days=i)).isoformat(),
                "duration_minutes": 45 + (i % 3) * 15,
                "intensity_level": 6 + (i % 3),
                "calories_burned": 300 + (i % 3) * 50
            } for i in range(30, 15, -3)  # Exercise every 3 days
        ]
        
        return {
            "work": work_data,
            "sleep": sleep_data,
            "exercise": exercise_data
        }

    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns_with_spidermind(self, engine, temporal_data):
        """Test analyze_temporal_patterns with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        engine.time_weaver = MagicMock()
        engine.time_weaver.analyze = MagicMock(
            return_value=asyncio.Future()
        )
        engine.time_weaver.analyze.return_value.set_result({
            "patterns": [
                {
                    "pattern_id": "weekly_cycle",
                    "pattern_type": "cycle",
                    "cycle_length": 7,
                    "confidence": 0.85,
                    "description": "Weekly work-leisure cycle"
                },
                {
                    "pattern_id": "stress_productivity",
                    "pattern_type": "correlation",
                    "correlation_coefficient": -0.75,
                    "confidence": 0.9,
                    "description": "Negative correlation between stress and productivity"
                }
            ],
            "confidence": 0.88
        })

        # Call the method
        result = await engine.analyze_temporal_patterns(temporal_data)

        # Verify the result
        assert "patterns" in result
        assert len(result["patterns"]) > 0
        assert result["patterns"][0]["pattern_id"] == "weekly_cycle"
        assert result["patterns"][0]["cycle_length"] == 7
        assert "confidence" in result

        # Verify that the SpiderMind method was called
        engine.time_weaver.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns_fallback(self, engine, temporal_data):
        """Test analyze_temporal_patterns fallback implementation."""
        # Ensure SpiderMind components are not available
        engine.time_weaver = None
        engine.temporal_detector = None
        engine.temporal_structures = None

        # Call the method
        result = await engine.analyze_temporal_patterns(temporal_data)

        # Verify the result
        assert "patterns" in result
        assert isinstance(result["patterns"], list)
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_detect_cycles_with_spidermind(self, engine, temporal_data):
        """Test detect_cycles with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        engine.temporal_detector = MagicMock()
        engine.temporal_detector.detect_cycles = MagicMock(
            return_value=asyncio.Future()
        )
        engine.temporal_detector.detect_cycles.return_value.set_result([
            {
                "cycle_id": "weekly_work",
                "cycle_length": 7,
                "confidence": 0.9,
                "description": "Weekly work pattern",
                "peak_days": [0, 7, 14, 21, 28],
                "trough_days": [5, 6, 12, 13, 19, 20, 26, 27]
            },
            {
                "cycle_id": "biweekly_stress",
                "cycle_length": 14,
                "confidence": 0.75,
                "description": "Biweekly stress cycle",
                "peak_days": [7, 21],
                "trough_days": [0, 14, 28]
            }
        ])

        # Call the method
        result = await engine.detect_cycles(temporal_data, 7, 14)

        # Verify the result
        assert len(result) > 0
        assert result[0]["cycle_id"] == "weekly_work"
        assert result[0]["cycle_length"] == 7
        assert result[0]["confidence"] == 0.9
        assert len(result[0]["peak_days"]) > 0

        # Verify that the SpiderMind method was called
        engine.temporal_detector.detect_cycles.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_cycles_fallback(self, engine, temporal_data):
        """Test detect_cycles fallback implementation."""
        # Ensure SpiderMind components are not available
        engine.temporal_detector = None
        engine.temporal_structures = None

        # Call the method
        result = await engine.detect_cycles(temporal_data, 7, 14)

        # Verify the result
        assert isinstance(result, list)
        if len(result) > 0:
            assert "cycle_id" in result[0]
            assert "cycle_length" in result[0]
            assert "confidence" in result[0]

    @pytest.mark.asyncio
    async def test_predict_future_patterns_with_spidermind(self, engine, temporal_data):
        """Test predict_future_patterns with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        engine.future_echo = MagicMock()
        engine.future_echo.detect_echoes = MagicMock(
            return_value=asyncio.Future()
        )
        engine.future_echo.detect_echoes.return_value.set_result({
            "echoes": [
                {
                    "echo_id": "echo_001",
                    "echo_strength": 0.8,
                    "source_timeframe": [0, 7],
                    "target_timeframe": [30, 37],
                    "confidence": 0.75
                }
            ]
        })
        
        engine.future_predictor = MagicMock()
        engine.future_predictor.predict_future = MagicMock(
            return_value=asyncio.Future()
        )
        engine.future_predictor.predict_future.return_value.set_result({
            "predictions": [
                {
                    "day": 30,
                    "activity_type": "work",
                    "stress_level": 7,
                    "productivity_score": 6,
                    "confidence": 0.85
                },
                {
                    "day": 31,
                    "activity_type": "work",
                    "stress_level": 6,
                    "productivity_score": 7,
                    "confidence": 0.8
                }
            ],
            "confidence": 0.82,
            "prediction_horizon": 30
        })

        # Call the method
        result = await engine.predict_future_patterns(temporal_data)

        # Verify the result
        assert "predictions" in result
        assert len(result["predictions"]) > 0
        assert "confidence" in result
        assert "prediction_horizon" in result

        # Verify that the SpiderMind methods were called
        engine.future_echo.detect_echoes.assert_called_once()
        engine.future_predictor.predict_future.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_future_patterns_with_timeweaver(self, engine, temporal_data):
        """Test predict_future_patterns with TimeWeaver when FutureEcho is not available."""
        # Mock the SpiderMind Omega components
        engine.future_echo = None
        engine.future_predictor = None
        
        engine.time_weaver = MagicMock()
        engine.time_weaver.predict_future = MagicMock(
            return_value=asyncio.Future()
        )
        engine.time_weaver.predict_future.return_value.set_result({
            "predictions": [
                {
                    "day": 30,
                    "activity_type": "work",
                    "stress_level": 7,
                    "productivity_score": 6,
                    "confidence": 0.75
                }
            ],
            "confidence": 0.75,
            "prediction_horizon": 30
        })

        # Call the method
        result = await engine.predict_future_patterns(temporal_data)

        # Verify the result
        assert "predictions" in result
        assert len(result["predictions"]) > 0
        assert "confidence" in result

        # Verify that the TimeWeaver method was called
        engine.time_weaver.predict_future.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_future_patterns_fallback(self, engine, temporal_data):
        """Test predict_future_patterns fallback implementation."""
        # Ensure SpiderMind components are not available
        engine.future_echo = None
        engine.future_predictor = None
        engine.time_weaver = None

        # Call the method
        result = await engine.predict_future_patterns(temporal_data)

        # Verify the result
        assert "predictions" in result
        assert isinstance(result["predictions"], list)
        assert "confidence" in result
        assert "prediction_horizon" in result

    @pytest.mark.asyncio
    async def test_analyze_temporal_correlations(self, engine, temporal_data_sets):
        """Test analyze_temporal_correlations method."""
        # Mock the SpiderMind Omega components
        engine.time_weaver = MagicMock()
        engine.time_weaver.analyze_correlations = MagicMock(
            return_value=asyncio.Future()
        )
        engine.time_weaver.analyze_correlations.return_value.set_result({
            "correlations": [
                {
                    "source_dataset": "work",
                    "target_dataset": "sleep",
                    "correlation_type": "inverse",
                    "correlation_coefficient": -0.7,
                    "confidence": 0.85,
                    "description": "Higher work stress correlates with lower sleep quality"
                },
                {
                    "source_dataset": "exercise",
                    "target_dataset": "sleep",
                    "correlation_type": "direct",
                    "correlation_coefficient": 0.6,
                    "confidence": 0.8,
                    "description": "Exercise correlates with better sleep quality"
                }
            ],
            "confidence": 0.82
        })

        # Call the method
        result = await engine.analyze_temporal_correlations(temporal_data_sets)

        # Verify the result
        assert "correlations" in result
        assert len(result["correlations"]) > 0
        assert result["correlations"][0]["source_dataset"] in ["work", "exercise"]
        assert result["correlations"][0]["target_dataset"] in ["sleep", "work"]
        assert "confidence" in result

        # Verify that the SpiderMind method was called
        engine.time_weaver.analyze_correlations.assert_called_once()

        # If TimeWeaver is not available, test the fallback
        engine.time_weaver = None
        result = await engine.analyze_temporal_correlations(temporal_data_sets)
        
        # Verify the fallback result
        assert "correlations" in result
        assert isinstance(result["correlations"], list)
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_generate_temporal_insights(self, engine, temporal_data):
        """Test generate_temporal_insights method."""
        # Mock the SpiderMind Omega components
        engine.time_weaver = MagicMock()
        engine.time_weaver.analyze = MagicMock(
            return_value=asyncio.Future()
        )
        engine.time_weaver.analyze.return_value.set_result({
            "patterns": [
                {
                    "pattern_id": "weekly_cycle",
                    "pattern_type": "cycle",
                    "cycle_length": 7,
                    "confidence": 0.85,
                    "description": "Weekly work-leisure cycle"
                }
            ],
            "insights": [
                "User follows a consistent weekly work pattern",
                "Stress levels peak mid-week and decrease on weekends",
                "Productivity is inversely correlated with stress levels"
            ],
            "confidence": 0.88
        })

        # Call the method
        result = await engine.generate_temporal_insights(temporal_data)

        # Verify the result
        assert "insights" in result
        assert len(result["insights"]) > 0
        assert isinstance(result["insights"][0], str)
        assert "confidence" in result

        # Verify that the SpiderMind method was called
        engine.time_weaver.analyze.assert_called_once()

        # If TimeWeaver is not available, test the fallback
        engine.time_weaver = None
        result = await engine.generate_temporal_insights(temporal_data)
        
        # Verify the fallback result
        assert "insights" in result
        assert isinstance(result["insights"], list)
        assert "confidence" in result