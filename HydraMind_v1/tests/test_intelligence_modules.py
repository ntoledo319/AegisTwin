"""
Tests for intelligence modules.

Tests the AI/ML components including anomaly detection, data collection,
prediction, and optimization modules.
"""

import asyncio
import pytest
import time
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from hydramind.modules.intelligence.anomaly_lab import AnomalyLab, EWMA, ZScoreDetector
from hydramind.modules.intelligence.data_collector import DataCollector, CollectionType, CollectionResult, DataSeries
from hydramind.modules.intelligence.predictive_engine import PredictiveEngine, PredictionType, Prediction
from hydramind.core.bus import Message
from hydramind.core.module import ModuleState


class TestEWMA:
    """Test EWMA (Exponentially Weighted Moving Average) functionality."""

    def test_ewma_initialization(self):
        """Test EWMA initialization."""
        ewma = EWMA(alpha=0.3)

        assert ewma.alpha == 0.3
        assert ewma.mean is None

    def test_ewma_first_update(self):
        """Test first EWMA update."""
        ewma = EWMA(alpha=0.5)
        mean = ewma.update(10.0)

        assert mean == 10.0
        assert ewma.mean == 10.0

    def test_ewma_subsequent_updates(self):
        """Test subsequent EWMA updates."""
        ewma = EWMA(alpha=0.3)

        # First update
        mean1 = ewma.update(10.0)
        assert mean1 == 10.0

        # Second update
        mean2 = ewma.update(20.0)
        expected = 0.3 * 20.0 + 0.7 * 10.0  # 0.3*20 + 0.7*10 = 13.0
        assert abs(mean2 - expected) < 1e-10
        assert abs(ewma.mean - expected) < 1e-10

        # Third update
        mean3 = ewma.update(15.0)
        expected = 0.3 * 15.0 + 0.7 * 13.0  # 0.3*15 + 0.7*13 = 13.6
        assert abs(mean3 - expected) < 1e-10

    def test_ewma_smoothing_effect(self):
        """Test that EWMA provides smoothing."""
        ewma = EWMA(alpha=0.1)  # Low alpha for strong smoothing

        # Feed in noisy data
        values = [10, 20, 5, 25, 8, 22, 12]
        means = []

        for value in values:
            mean = ewma.update(value)
            means.append(mean)

        # Means should be smoother than original values
        assert len(means) == len(values)

        # First mean should equal first value
        assert means[0] == 10

        # Subsequent means should be between original values (smoothed)
        for i in range(1, len(means)):
            assert means[i] != values[i]  # Should be different due to smoothing


class TestZScoreDetector:
    """Test ZScoreDetector functionality."""

    def test_zscore_detector_initialization(self):
        """Test ZScoreDetector initialization."""
        detector = ZScoreDetector(window_size=10, threshold=2.0)

        assert detector.window_size == 10
        assert detector.threshold == 2.0
        assert len(detector.values) == 0

    def test_zscore_normal_values(self):
        """Test ZScoreDetector with normal values."""
        detector = ZScoreDetector(window_size=5, threshold=2.0)

        # Feed normal values around mean
        values = [10, 11, 9, 10, 11]
        for value in values:
            is_anomaly = detector.update(value)
            assert is_anomaly is False

    def test_zscore_anomaly_detection(self):
        """Test ZScoreDetector anomaly detection."""
        detector = ZScoreDetector(window_size=5, threshold=2.0)

        # Feed normal values first
        normal_values = [10, 11, 9, 10, 11]
        for value in normal_values:
            detector.update(value)

        # Feed anomalous value (far from mean)
        is_anomaly = detector.update(50.0)  # Should be anomaly
        assert is_anomaly is True

        # Feed another normal value
        is_normal = detector.update(10.5)
        assert is_normal is False

    def test_zscore_insufficient_data(self):
        """Test ZScoreDetector with insufficient data."""
        detector = ZScoreDetector(window_size=5, threshold=2.0)

        # Feed only one value (insufficient for Z-score)
        is_anomaly = detector.update(10.0)
        assert is_anomaly is False  # Should not detect anomaly with insufficient data


class TestAnomalyLab:
    """Test AnomalyLab module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for AnomalyLab."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def anomaly_lab(self, mock_dependencies):
        """Create an AnomalyLab instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return AnomalyLab(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_anomaly_lab_initialization(self, anomaly_lab):
        """Test AnomalyLab initializes correctly."""
        assert anomaly_lab.name == "anomaly_lab"
        assert anomaly_lab.state == ModuleState.UNINITIALIZED
        assert isinstance(anomaly_lab.detectors, dict)
        assert len(anomaly_lab.detectors) == 0

    @pytest.mark.asyncio
    async def test_metric_data_handling(self, anomaly_lab):
        """Test handling metric data for anomaly detection."""
        await anomaly_lab.start()

        # Mock the emit method
        anomaly_lab.emit = AsyncMock()

        # Create a metric data message
        metric_msg = Message("metrics/cpu", {
            "value": 85.5,
            "timestamp": time.time(),
            "host": "server1"
        })

        # Handle the message
        await anomaly_lab.on_message(metric_msg)

        # Should have created a detector for this metric
        assert "metrics/cpu" in anomaly_lab.detectors

        # Should have emitted anomaly check result
        anomaly_lab.emit.assert_called_once()
        call_args = anomaly_lab.emit.call_args[0]

        assert call_args[0] == "anomaly/check"
        result_data = call_args[1]
        assert result_data["metric"] == "metrics/cpu"
        assert "is_anomaly" in result_data
        assert "confidence" in result_data

        await anomaly_lab.stop()

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, anomaly_lab):
        """Test actual anomaly detection."""
        await anomaly_lab.start()

        # Mock the emit method
        anomaly_lab.emit = AsyncMock()

        # Send normal values first
        normal_values = [50.0, 52.0, 48.0, 51.0, 49.0]
        for value in normal_values:
            metric_msg = Message("metrics/cpu", {
                "value": value,
                "timestamp": time.time()
            })
            await anomaly_lab.on_message(metric_msg)

        # Send anomalous value
        anomaly_msg = Message("metrics/cpu", {
            "value": 95.0,  # Significantly higher
            "timestamp": time.time()
        })
        await anomaly_lab.on_message(anomaly_msg)

        # Should detect the anomaly
        assert anomaly_lab.emit.call_count >= 6  # At least normal + anomaly checks

        # Check the last call (anomaly detection)
        last_call = anomaly_lab.emit.call_args_list[-1]
        result_data = last_call[0][1]
        assert result_data["is_anomaly"] is True
        assert result_data["confidence"] > 0.5

        await anomaly_lab.stop()

    @pytest.mark.asyncio
    async def test_multiple_metrics(self, anomaly_lab):
        """Test handling multiple different metrics."""
        await anomaly_lab.start()

        # Mock the emit method
        anomaly_lab.emit = AsyncMock()

        # Send data for different metrics
        metrics_data = [
            ("metrics/cpu", 60.0),
            ("metrics/memory", 70.0),
            ("metrics/disk", 30.0),
            ("metrics/cpu", 62.0),  # Same metric again
            ("metrics/network", 40.0)
        ]

        for metric, value in metrics_data:
            msg = Message(metric, {
                "value": value,
                "timestamp": time.time()
            })
            await anomaly_lab.on_message(msg)

        # Should have detectors for all unique metrics
        assert "metrics/cpu" in anomaly_lab.detectors
        assert "metrics/memory" in anomaly_lab.detectors
        assert "metrics/disk" in anomaly_lab.detectors
        assert "metrics/network" in anomaly_lab.detectors

        # Should have emitted checks for all data points
        assert anomaly_lab.emit.call_count >= 5

        await anomaly_lab.stop()


class TestDataSeries:
    """Test DataSeries functionality."""

    def test_data_series_creation(self):
        """Test creating DataSeries."""
        series = DataSeries(name="cpu_usage", metadata={"unit": "percent"})

        assert series.name == "cpu_usage"
        assert series.metadata == {"unit": "percent"}
        assert len(series.values) == 0

    def test_data_series_add_values(self):
        """Test adding values to DataSeries."""
        series = DataSeries(name="test_series")

        # Add values with timestamps
        series.add(10.0, 1000.0)
        series.add(20.0, 1001.0)
        series.add(15.0, 1000.5)  # Between existing timestamps

        assert len(series.values) == 3

        # Values should be stored (implementation dependent)
        # This tests that values are added without error

    def test_data_series_maxlen(self):
        """Test DataSeries maxlen behavior."""
        series = DataSeries(name="test_series")

        # Add more values than maxlen
        for i in range(5):  # maxlen is 1000, so this shouldn't trigger maxlen behavior yet
            series.add(float(i))

        assert len(series.values) == 5


class TestDataCollector:
    """Test DataCollector module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for DataCollector."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def data_collector(self, mock_dependencies):
        """Create a DataCollector instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return DataCollector(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_data_collector_initialization(self, data_collector):
        """Test DataCollector initializes correctly."""
        assert data_collector.name == "data_collector"
        assert data_collector.state == ModuleState.UNINITIALIZED
        assert isinstance(data_collector.series, dict)
        assert len(data_collector.series) == 0

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, data_collector):
        """Test collecting system metrics."""
        await data_collector.start()

        # Mock the emit method
        data_collector.emit = AsyncMock()

        # Create a system metrics message
        metrics_msg = Message("system/metrics", {
            "cpu_percent": 45.5,
            "memory_percent": 62.0,
            "disk_percent": 28.0,
            "timestamp": time.time()
        })

        # Handle the message
        await data_collector.on_message(metrics_msg)

        # Should have stored the data series
        assert "cpu_percent" in data_collector.series
        assert "memory_percent" in data_collector.series
        assert "disk_percent" in data_collector.series

        # Should have emitted collection result
        data_collector.emit.assert_called_once()
        call_args = data_collector.emit.call_args[0]

        assert call_args[0] == "data/collection_result"
        result_data = call_args[1]
        assert result_data["collection_type"] == CollectionType.SYSTEM_METRICS
        assert result_data["records_collected"] > 0

        await data_collector.stop()

    @pytest.mark.asyncio
    async def test_module_performance_collection(self, data_collector):
        """Test collecting module performance data."""
        await data_collector.start()

        # Mock the emit method
        data_collector.emit = AsyncMock()

        # Create a module performance message
        perf_msg = Message("module/performance", {
            "module_name": "anomaly_lab",
            "response_time": 0.025,
            "memory_usage": 45.2,
            "error_count": 0,
            "timestamp": time.time()
        })

        # Handle the message
        await data_collector.on_message(perf_msg)

        # Should have stored performance data
        assert "anomaly_lab_response_time" in data_collector.series
        assert "anomaly_lab_memory_usage" in data_collector.series

        # Should have emitted collection result
        data_collector.emit.assert_called_once()
        call_args = data_collector.emit.call_args[0]

        assert call_args[0] == "data/collection_result"
        result_data = call_args[1]
        assert result_data["collection_type"] == CollectionType.MODULE_PERFORMANCE

        await data_collector.stop()


class TestPredictiveEngine:
    """Test PredictiveEngine module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for PredictiveEngine."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def predictive_engine(self, mock_dependencies):
        """Create a PredictiveEngine instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return PredictiveEngine(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_predictive_engine_initialization(self, predictive_engine):
        """Test PredictiveEngine initializes correctly."""
        assert predictive_engine.name == "predictive_engine"
        assert predictive_engine.state == ModuleState.UNINITIALIZED
        assert isinstance(predictive_engine.history, dict)
        assert len(predictive_engine.history) == 0

    @pytest.mark.asyncio
    async def test_event_prediction(self, predictive_engine):
        """Test event prediction functionality."""
        await predictive_engine.start()

        # Mock the emit method
        predictive_engine.emit = AsyncMock()

        # Create an event prediction request
        predict_msg = Message("predict/event", {
            "target": "system/failure",
            "time_horizon": 3600,  # 1 hour
            "context": {
                "current_load": 0.8,
                "error_rate": 0.02
            }
        })

        # Handle the message
        await predictive_engine.on_message(predict_msg)

        # Should have emitted prediction
        predictive_engine.emit.assert_called_once()
        call_args = predictive_engine.emit.call_args[0]

        assert call_args[0] == "prediction/result"
        prediction_data = call_args[1]
        assert prediction_data["prediction_type"] == PredictionType.EVENT
        assert prediction_data["target"] == "system/failure"
        assert prediction_data["time_horizon"] == 3600
        assert "predicted_value" in prediction_data
        assert "confidence" in prediction_data

        await predictive_engine.stop()

    @pytest.mark.asyncio
    async def test_metric_prediction(self, predictive_engine):
        """Test metric value prediction."""
        await predictive_engine.start()

        # Mock the emit method
        predictive_engine.emit = AsyncMock()

        # Create a metric prediction request
        predict_msg = Message("predict/metric", {
            "target": "cpu_usage",
            "time_horizon": 300,  # 5 minutes
            "historical_window": 3600  # 1 hour of history
        })

        # Handle the message
        await predictive_engine.on_message(predict_msg)

        # Should have emitted prediction
        predictive_engine.emit.assert_called_once()
        call_args = predictive_engine.emit.call_args[0]

        assert call_args[0] == "prediction/result"
        prediction_data = call_args[1]
        assert prediction_data["prediction_type"] == PredictionType.METRIC
        assert prediction_data["target"] == "cpu_usage"
        assert prediction_data["time_horizon"] == 300

        await predictive_engine.stop()


class TestIntelligenceModuleIntegration:
    """Test integration between intelligence modules."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for intelligence modules."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def intelligence_modules(self, mock_dependencies):
        """Create instances of key intelligence modules."""
        bus, exec_engine, policy_guard = mock_dependencies

        from hydramind.modules.intelligence.anomaly_lab import AnomalyLab
        from hydramind.modules.intelligence.data_collector import DataCollector
        from hydramind.modules.intelligence.predictive_engine import PredictiveEngine

        return {
            "anomaly_lab": AnomalyLab(bus, exec_engine, policy_guard),
            "data_collector": DataCollector(bus, exec_engine, policy_guard),
            "predictive_engine": PredictiveEngine(bus, exec_engine, policy_guard)
        }

    @pytest.mark.asyncio
    async def test_cross_module_data_flow(self, intelligence_modules):
        """Test data flow between intelligence modules."""
        # Start all modules
        for module in intelligence_modules.values():
            await module.start()

        # Mock emit methods
        for module in intelligence_modules.values():
            module.emit = AsyncMock()

        # Simulate data collection -> anomaly detection -> prediction
        # 1. Data collector receives system metrics
        metrics_msg = Message("system/metrics", {
            "cpu_percent": 75.0,
            "memory_percent": 80.0,
            "timestamp": time.time()
        })

        await intelligence_modules["data_collector"].on_message(metrics_msg)

        # 2. Anomaly lab receives the same metrics for anomaly detection
        await intelligence_modules["anomaly_lab"].on_message(metrics_msg)

        # 3. Predictive engine uses the data for prediction
        predict_msg = Message("predict/metric", {
            "target": "cpu_usage",
            "time_horizon": 300
        })
        await intelligence_modules["predictive_engine"].on_message(predict_msg)

        # Verify all modules processed their messages
        for module_name, module in intelligence_modules.items():
            assert module.emit.called, f"{module_name} should have emitted results"

        # Stop all modules
        for module in intelligence_modules.values():
            await module.stop()

    @pytest.mark.asyncio
    async def test_error_propagation_handling(self, intelligence_modules):
        """Test error handling across intelligence modules."""
        # Start all modules
        for module in intelligence_modules.values():
            await module.start()

        # Send malformed data that might cause errors
        malformed_msg = Message("test/topic", "not_a_dict")

        for module in intelligence_modules.values():
            try:
                await module.on_message(malformed_msg)
                # Should handle gracefully
            except Exception as e:
                # If an exception occurs, it should be a known type
                assert isinstance(e, (TypeError, ValueError))

        # Modules should still be running
        for module in intelligence_modules.values():
            assert module.state == ModuleState.RUNNING

        # Stop all modules
        for module in intelligence_modules.values():
            await module.stop()


class TestIntelligenceModulePerformance:
    """Test intelligence module performance."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for performance testing."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.mark.asyncio
    async def test_anomaly_detection_performance(self, mock_dependencies):
        """Test AnomalyLab performance under high-frequency data."""
        bus, exec_engine, policy_guard = mock_dependencies

        from hydramind.modules.intelligence.anomaly_lab import AnomalyLab

        anomaly_lab = AnomalyLab(bus, exec_engine, policy_guard)
        await anomaly_lab.start()

        # Mock emit method
        anomaly_lab.emit = AsyncMock()

        # Send high-frequency metric data
        start_time = time.time()

        for i in range(100):
            metric_msg = Message("metrics/cpu", {
                "value": 50.0 + np.sin(i * 0.1) * 10,  # Sinusoidal pattern
                "timestamp": time.time()
            })
            await anomaly_lab.on_message(metric_msg)

        end_time = time.time()

        # Should complete reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should complete in under 2 seconds

        # Should have processed all data points
        assert anomaly_lab.emit.call_count >= 100

        await anomaly_lab.stop()

    @pytest.mark.asyncio
    async def test_data_collection_performance(self, mock_dependencies):
        """Test DataCollector performance under load."""
        bus, exec_engine, policy_guard = mock_dependencies

        from hydramind.modules.intelligence.data_collector import DataCollector

        data_collector = DataCollector(bus, exec_engine, policy_guard)
        await data_collector.start()

        # Mock emit method
        data_collector.emit = AsyncMock()

        # Send many metrics for collection
        start_time = time.time()

        metrics_data = []
        for i in range(50):
            metrics = {
                "cpu_percent": 40.0 + i * 0.5,
                "memory_percent": 60.0 + i * 0.3,
                "disk_percent": 20.0 + i * 0.2,
                "network_rx": 1000 + i * 10,
                "network_tx": 800 + i * 8,
                "timestamp": time.time()
            }
            metrics_data.append(metrics)

        # Send all metrics
        for metrics in metrics_data:
            msg = Message("system/metrics", metrics)
            await data_collector.on_message(msg)

        end_time = time.time()

        # Should complete reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should complete in under 1 second

        # Should have stored all metrics
        assert len(data_collector.series) > 0

        await data_collector.stop()

    @pytest.mark.asyncio
    async def test_prediction_performance(self, mock_dependencies):
        """Test PredictiveEngine performance."""
        bus, exec_engine, policy_guard = mock_dependencies

        from hydramind.modules.intelligence.predictive_engine import PredictiveEngine

        predictive_engine = PredictiveEngine(bus, exec_engine, policy_guard)
        await predictive_engine.start()

        # Mock emit method
        predictive_engine.emit = AsyncMock()

        # Send multiple prediction requests
        start_time = time.time()

        for i in range(20):
            predict_msg = Message("predict/metric", {
                "target": f"metric_{i}",
                "time_horizon": 300,
                "historical_window": 3600
            })
            await predictive_engine.on_message(predict_msg)

        end_time = time.time()

        # Should complete reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should complete in under 1 second

        # Should have emitted predictions for all requests
        assert predictive_engine.emit.call_count == 20

        await predictive_engine.stop()

