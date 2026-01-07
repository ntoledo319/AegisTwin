"""
Tests for infrastructure modules (sensors).

Tests the sensor hub and related infrastructure components.
"""

import asyncio
import pytest
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from hydramind.modules.infrastructure.sensors import SensorHub
from hydramind.core.bus import Message
from hydramind.core.data import RingBuffer, MMapSnapshot, TTLCache
from hydramind.core.module import ModuleState


class TestSensorHub:
    """Test SensorHub infrastructure module."""

    @pytest.fixture
    def mock_ring_buffer(self):
        """Create a mock ring buffer."""
        ring = Mock(spec=RingBuffer)
        ring.write = Mock()
        ring.read = Mock(return_value=None)  # No data initially
        ring.capacity = 1000
        return ring

    @pytest.fixture
    def mock_snapshot(self):
        """Create a mock memory-mapped snapshot."""
        snap = Mock(spec=MMapSnapshot)
        snap.write = Mock()
        snap.read = Mock(return_value={})
        return snap

    @pytest.fixture
    def mock_cache(self):
        """Create a mock TTL cache."""
        cache = Mock(spec=TTLCache)
        cache.get = Mock(return_value=None)
        cache.set = Mock()
        cache.size = 0
        return cache

    @pytest.fixture
    def mock_dependencies(self, mock_ring_buffer, mock_snapshot, mock_cache):
        """Create mock dependencies for SensorHub."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard, mock_ring_buffer, mock_snapshot, mock_cache

    @pytest.fixture
    def sensor_hub(self, mock_dependencies):
        """Create a SensorHub instance."""
        bus, exec_engine, policy_guard, ring, snap, cache = mock_dependencies
        return SensorHub(bus, exec_engine, policy_guard, ring, snap, cache)

    def test_sensor_hub_initialization(self, sensor_hub, mock_dependencies):
        """Test SensorHub initializes correctly."""
        _, _, _, ring, snap, cache = mock_dependencies

        assert sensor_hub.name == "sensors"
        assert sensor_hub.state == ModuleState.UNINITIALIZED
        assert sensor_hub.ring is ring
        assert sensor_hub.snap is snap
        assert sensor_hub.cache is cache
        assert sensor_hub.produce_interval == 0.05
        assert sensor_hub.consume_interval == 0.01

    def test_sensor_hub_custom_intervals(self, mock_dependencies):
        """Test SensorHub with custom intervals."""
        bus, exec_engine, policy_guard, ring, snap, cache = mock_dependencies

        custom_hub = SensorHub(
            bus, exec_engine, policy_guard, ring, snap, cache,
            produce_interval=0.1,
            consume_interval=0.02
        )

        assert custom_hub.produce_interval == 0.1
        assert custom_hub.consume_interval == 0.02

    @pytest.mark.asyncio
    async def test_sensor_hub_start_stop(self, sensor_hub):
        """Test starting and stopping the sensor hub."""
        # Initially no tasks
        assert sensor_hub._produce_task is None
        assert sensor_hub._consume_task is None

        # Start the hub
        await sensor_hub.start()

        # Should have running tasks
        assert sensor_hub._produce_task is not None
        assert not sensor_hub._produce_task.done()
        assert sensor_hub._consume_task is not None
        assert not sensor_hub._consume_task.done()

        # Stop the hub
        await sensor_hub.stop()

        # Tasks should be cancelled
        assert sensor_hub._produce_task.done()
        assert sensor_hub._consume_task.done()

    @pytest.mark.asyncio
    async def test_produce_loop(self, sensor_hub):
        """Test the sensor data production loop."""
        # Mock system metrics
        with patch('psutil.cpu_percent', return_value=45.5), \
             patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.disk_usage') as mock_disk:

            mock_mem.return_value = Mock(percent=60.2, used=8589934592, available=4294967296)
            mock_disk.return_value = Mock(percent=30.1, used=107374182400, free=214748364800)

            # Start the hub
            await sensor_hub.start()

            # Let it run for a short time to produce data
            await asyncio.sleep(0.1)

            # Should have written to ring buffer
            assert sensor_hub.ring.write.called

            # Should have written to snapshot
            assert sensor_hub.snap.write.called

            await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_consume_loop(self, sensor_hub):
        """Test the sensor data consumption loop."""
        # Add some mock data to the ring buffer
        test_data = {
            "timestamp": time.time(),
            "cpu_percent": 50.0,
            "memory_percent": 65.0,
            "disk_percent": 35.0
        }

        sensor_hub.ring.read = Mock(return_value=json.dumps(test_data).encode())

        # Mock the emit method
        sensor_hub.emit = AsyncMock()

        # Start the hub
        await sensor_hub.start()

        # Let it run for a short time to consume data
        await asyncio.sleep(0.05)

        # Should have emitted sensor data
        assert sensor_hub.emit.called

        await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_sensor_query_handling(self, sensor_hub):
        """Test handling sensor query messages."""
        await sensor_hub.start()

        # Mock cache to return cached data
        cached_data = {
            "timestamp": time.time(),
            "cpu_percent": 42.0,
            "memory_percent": 58.0
        }
        sensor_hub.cache.get = Mock(return_value=cached_data)

        # Mock the emit method
        sensor_hub.emit = AsyncMock()

        # Create a sensor query message
        query_msg = Message("sensors/get_last", {
            "sensor_type": "system_metrics"
        })

        # Handle the message
        await sensor_hub.on_message(query_msg)

        # Should emit cached sensor data
        sensor_hub.emit.assert_called_once()
        call_args = sensor_hub.emit.call_args[0]

        assert call_args[0] == "sensors/last_reading"
        response_data = call_args[1]
        assert response_data["sensor_type"] == "system_metrics"
        assert "data" in response_data
        assert "timestamp" in response_data

        await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_sensor_query_no_cache(self, sensor_hub):
        """Test handling sensor query when no cached data."""
        await sensor_hub.start()

        # Mock cache to return None (no cached data)
        sensor_hub.cache.get = Mock(return_value=None)

        # Mock the emit method
        sensor_hub.emit = AsyncMock()

        # Create a sensor query message
        query_msg = Message("sensors/get_last", {
            "sensor_type": "system_metrics"
        })

        # Handle the message
        await sensor_hub.on_message(query_msg)

        # Should emit error response
        sensor_hub.emit.assert_called_once()
        call_args = sensor_hub.emit.call_args[0]

        assert call_args[0] == "sensors/last_reading"
        response_data = call_args[1]
        assert response_data["error"] == "No cached data available"

        await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_sensor_hub_stats(self, sensor_hub):
        """Test sensor hub statistics."""
        await sensor_hub.start()

        # Mock some activity
        sensor_hub.ring.write = Mock()
        sensor_hub.snap.write = Mock()
        sensor_hub.cache.set = Mock()

        # Let it run briefly
        await asyncio.sleep(0.05)

        # Get stats
        stats = sensor_hub.get_stats()

        # Should include base module stats plus sensor-specific stats
        assert "ring_buffer_size" in stats
        assert "snapshot_size" in stats
        assert "cache_size" in stats
        assert "produce_count" in stats
        assert "consume_count" in stats

        await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_producer_consumer_coordination(self, sensor_hub):
        """Test coordination between producer and consumer loops."""
        # Mock realistic data flow
        data_items = []
        sensor_hub.ring.write = Mock(side_effect=lambda data: data_items.append(data))
        sensor_hub.ring.read = Mock(side_effect=[
            json.dumps({"test": "data1"}).encode(),
            json.dumps({"test": "data2"}).encode(),
            None  # End of data
        ])

        sensor_hub.snap.write = Mock()
        sensor_hub.cache.set = Mock()

        # Mock emit method
        sensor_hub.emit = AsyncMock()

        # Start the hub
        await sensor_hub.start()

        # Let it run for a short time
        await asyncio.sleep(0.1)

        # Should have processed data items
        assert len(data_items) > 0
        assert sensor_hub.emit.called

        await sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_error_handling_in_loops(self, sensor_hub):
        """Test error handling in producer/consumer loops."""
        # Mock ring buffer to raise exceptions
        sensor_hub.ring.write = Mock(side_effect=Exception("Ring buffer full"))
        sensor_hub.ring.read = Mock(side_effect=Exception("Ring buffer empty"))

        # Mock other components to work normally
        sensor_hub.snap.write = Mock()
        sensor_hub.cache.set = Mock()
        sensor_hub.emit = AsyncMock()

        # Start the hub (should handle errors gracefully)
        await sensor_hub.start()

        # Let it run briefly (errors should be logged but not crash)
        await asyncio.sleep(0.05)

        # Hub should still be running despite errors
        assert sensor_hub.state == ModuleState.RUNNING

        await sensor_hub.stop()


class TestSensorHubIntegration:
    """Test SensorHub integration scenarios."""

    @pytest.fixture
    def real_ring_buffer(self):
        """Create a real ring buffer for integration testing."""
        return RingBuffer(capacity=100, item_size=1024)

    @pytest.fixture
    def real_snapshot(self, tmp_path):
        """Create a real memory-mapped snapshot."""
        snap_file = tmp_path / "test_snapshot.mmap"
        return MMapSnapshot(str(snap_file), size=4096)

    @pytest.fixture
    def real_cache(self):
        """Create a real TTL cache."""
        return TTLCache(max_size=100, ttl=60.0)

    @pytest.fixture
    def integration_dependencies(self, real_ring_buffer, real_snapshot, real_cache):
        """Create real dependencies for integration testing."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard, real_ring_buffer, real_snapshot, real_cache

    @pytest.fixture
    def integration_sensor_hub(self, integration_dependencies):
        """Create a SensorHub with real dependencies."""
        bus, exec_engine, policy_guard, ring, snap, cache = integration_dependencies
        return SensorHub(bus, exec_engine, policy_guard, ring, snap, cache)

    @pytest.mark.asyncio
    async def test_real_data_flow(self, integration_sensor_hub):
        """Test real data flow through the sensor hub."""
        await integration_sensor_hub.start()

        # Let it run to produce some data
        await asyncio.sleep(0.1)

        # Should have written to ring buffer
        assert integration_sensor_hub.ring.size > 0

        # Should have written to snapshot
        snapshot_data = integration_sensor_hub.snap.read()
        assert snapshot_data is not None

        # Should have cached data
        assert integration_sensor_hub.cache.size > 0

        await integration_sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_performance_under_load(self, integration_sensor_hub):
        """Test sensor hub performance under high-frequency load."""
        await integration_sensor_hub.start()

        # Run for a longer period to test performance
        start_time = time.time()
        await asyncio.sleep(0.5)
        end_time = time.time()

        # Should complete within reasonable time
        duration = end_time - start_time
        assert duration < 1.0  # Should complete in under 1 second

        # Should have processed many data points
        stats = integration_sensor_hub.get_stats()
        assert stats["produce_count"] > 0
        assert stats["consume_count"] > 0

        await integration_sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self, integration_sensor_hub):
        """Test memory usage tracking in sensor hub."""
        await integration_sensor_hub.start()

        # Get initial memory usage
        initial_stats = integration_sensor_hub.get_stats()

        # Let it run and accumulate data
        await asyncio.sleep(0.2)

        # Get final memory usage
        final_stats = integration_sensor_hub.get_stats()

        # Memory usage should be tracked
        assert "memory_usage" in final_stats or "ring_buffer_size" in final_stats

        await integration_sensor_hub.stop()


class TestSensorHubErrorScenarios:
    """Test error scenarios in sensor hub."""

    @pytest.fixture
    def mock_dependencies_error(self):
        """Create mock dependencies that can fail."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        # Ring buffer that fails
        ring = Mock(spec=RingBuffer)
        ring.write = Mock(side_effect=Exception("Ring buffer write failed"))
        ring.read = Mock(side_effect=Exception("Ring buffer read failed"))

        # Snapshot that fails
        snap = Mock(spec=MMapSnapshot)
        snap.write = Mock(side_effect=Exception("Snapshot write failed"))

        # Cache that fails
        cache = Mock(spec=TTLCache)
        cache.set = Mock(side_effect=Exception("Cache set failed"))

        return bus, exec_engine, policy_guard, ring, snap, cache

    @pytest.fixture
    def error_sensor_hub(self, mock_dependencies_error):
        """Create a SensorHub with error-prone dependencies."""
        bus, exec_engine, policy_guard, ring, snap, cache = mock_dependencies_error
        return SensorHub(bus, exec_engine, policy_guard, ring, snap, cache)

    @pytest.mark.asyncio
    async def test_graceful_error_handling(self, error_sensor_hub):
        """Test graceful handling of component failures."""
        # Should start despite component errors
        await error_sensor_hub.start()

        # Let it run briefly
        await asyncio.sleep(0.05)

        # Should still be running (errors should be logged but not crash)
        assert error_sensor_hub.state == ModuleState.RUNNING

        await error_sensor_hub.stop()

    @pytest.mark.asyncio
    async def test_recovery_from_errors(self, error_sensor_hub):
        """Test recovery from temporary errors."""
        await error_sensor_hub.start()

        # Simulate recovery by making components work again
        error_sensor_hub.ring.write = Mock()  # Fixed
        error_sensor_hub.snap.write = Mock()  # Fixed
        error_sensor_hub.cache.set = Mock()  # Fixed

        # Let it continue running
        await asyncio.sleep(0.05)

        # Should continue operating normally after errors
        assert error_sensor_hub.state == ModuleState.RUNNING

        await error_sensor_hub.stop()

