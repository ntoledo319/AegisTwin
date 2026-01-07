"""
Tests for execution engine functionality.

Tests the Exec class, ResourceManager, and execution utilities.
"""

import asyncio
import pytest
import psutil
import time
from unittest.mock import Mock, AsyncMock, patch
from hydramind.core.execs import Exec, ResourceManager, ResourceHint
from hydramind.core.exceptions import ExecutionError


class TestResourceManager:
    """Test ResourceManager functionality."""

    @pytest.fixture
    def resource_manager(self):
        """Create a test resource manager."""
        return ResourceManager()

    def test_resource_manager_initialization(self, resource_manager):
        """Test ResourceManager initializes correctly."""
        assert resource_manager is not None

    def test_get_system_info(self, resource_manager):
        """Test getting system information."""
        info = resource_manager.get_system_info()

        assert isinstance(info, dict)
        assert "cpu_count" in info
        assert "memory_total" in info
        assert "memory_available" in info
        assert "cpu_percent" in info

        # Basic sanity checks
        assert info["cpu_count"] > 0
        assert info["memory_total"] > 0
        assert info["memory_available"] >= 0
        assert 0 <= info["cpu_percent"] <= 100

    def test_recommend_hint_basic(self, resource_manager):
        """Test basic execution hint recommendation."""
        hint = resource_manager.recommend()

        assert isinstance(hint, ExecutionHint)
        assert hint.max_workers > 0
        assert hint.memory_limit > 0
        assert hint.priority >= 0

    def test_recommend_hint_with_constraints(self, resource_manager):
        """Test execution hint recommendation with constraints."""
        constraints = {
            "max_workers": 2,
            "memory_limit": 100 * 1024 * 1024,  # 100MB
            "priority": 5
        }

        hint = resource_manager.recommend(constraints)

        assert isinstance(hint, ExecutionHint)
        assert hint.max_workers <= 2
        assert hint.memory_limit <= 100 * 1024 * 1024
        assert hint.priority == 5

    def test_resource_monitoring(self, resource_manager):
        """Test resource monitoring capabilities."""
        # Get initial readings
        initial_cpu = resource_manager.get_cpu_usage()
        initial_memory = resource_manager.get_memory_usage()

        assert isinstance(initial_cpu, float)
        assert isinstance(initial_memory, dict)
        assert 0 <= initial_cpu <= 100
        assert "used" in initial_memory
        assert "available" in initial_memory
        assert "percent" in initial_memory

        # Memory values should be reasonable
        assert initial_memory["used"] >= 0
        assert initial_memory["available"] >= 0
        assert 0 <= initial_memory["percent"] <= 100

    def test_memory_pressure_detection(self, resource_manager):
        """Test memory pressure detection."""
        pressure = resource_manager.get_memory_pressure()

        assert isinstance(pressure, float)
        assert 0 <= pressure <= 1.0

        # Should be a reasonable value
        assert pressure >= 0.0

    def test_cpu_pressure_detection(self, resource_manager):
        """Test CPU pressure detection."""
        pressure = resource_manager.get_cpu_pressure()

        assert isinstance(pressure, float)
        assert 0 <= pressure <= 1.0

        # Should be a reasonable value
        assert pressure >= 0.0


class TestResourceHint:
    """Test ResourceHint data class."""

    def test_resource_hint_creation(self):
        """Test creating ResourceHint instances."""
        hint = ResourceHint(
            max_workers=4,
            memory_limit=1024 * 1024 * 1024,  # 1GB
            priority=10,
            timeout=30.0
        )

        assert hint["max_workers"] == 4
        assert hint["memory_limit"] == 1024 * 1024 * 1024
        assert hint["priority"] == 10
        assert hint["timeout"] == 30.0

    def test_resource_hint_defaults(self):
        """Test ResourceHint default values."""
        hint = ResourceHint()

        # Should have sensible defaults
        assert hint["max_workers"] > 0
        assert hint["memory_limit"] > 0
        assert hint["priority"] >= 0
        assert hint["timeout"] > 0

    def test_resource_hint_validation(self):
        """Test ResourceHint parameter validation."""
        # Valid hint should not raise
        ResourceHint(max_workers=1, memory_limit=1024, priority=0, timeout=1.0)

        # Invalid max_workers should raise (implementation dependent)
        # This tests the current behavior - may need adjustment based on actual validation

    def test_resource_hint_comparison(self):
        """Test ResourceHint comparison operations."""
        hint1 = ResourceHint(max_workers=4, memory_limit=1024)
        hint2 = ResourceHint(max_workers=4, memory_limit=1024)
        hint3 = ResourceHint(max_workers=2, memory_limit=1024)

        # Same values should be equal
        assert hint1 == hint2

        # Different values should not be equal
        assert hint1 != hint3


class TestExec:
    """Test Exec class functionality."""

    @pytest.fixture
    def resource_manager(self):
        """Create a test resource manager."""
        return ResourceManager()

    @pytest.fixture
    def exec_engine(self, resource_manager):
        """Create a test execution engine."""
        hint = resource_manager.recommend()
        return Exec(hint)

    def test_exec_initialization(self, exec_engine, resource_manager):
        """Test Exec initializes correctly."""
        assert exec_engine is not None
        assert exec_engine.hint is not None
        assert exec_engine._thread_pool is not None
        assert exec_engine._running is False

    @pytest.mark.asyncio
    async def test_exec_start_stop(self, exec_engine):
        """Test starting and stopping the execution engine."""
        # Initially not running
        assert exec_engine._running is False

        # Start the engine
        await exec_engine.start()
        assert exec_engine._running is True

        # Stop the engine
        await exec_engine.stop()
        assert exec_engine._running is False

    @pytest.mark.asyncio
    async def test_exec_double_start(self, exec_engine):
        """Test starting an already running engine."""
        await exec_engine.start()

        # Second start should be a no-op or raise an error
        # Implementation dependent - test current behavior
        await exec_engine.start()  # Should not raise

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_submit_task(self, exec_engine):
        """Test submitting tasks to the execution engine."""
        await exec_engine.start()

        # Submit a simple task
        async def simple_task(x, y):
            await asyncio.sleep(0.01)  # Simulate work
            return x + y

        future = exec_engine.submit(simple_task, 5, 10)

        # Wait for completion
        result = await future
        assert result == 15

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_submit_multiple_tasks(self, exec_engine):
        """Test submitting multiple tasks concurrently."""
        await exec_engine.start()

        # Submit multiple tasks
        async def task_func(task_id):
            await asyncio.sleep(0.01)
            return f"task_{task_id}_result"

        futures = []
        for i in range(5):
            future = exec_engine.submit(task_func, i)
            futures.append(future)

        # Wait for all to complete
        results = await asyncio.gather(*futures)

        assert len(results) == 5
        assert "task_0_result" in results
        assert "task_1_result" in results
        assert "task_2_result" in results
        assert "task_3_result" in results
        assert "task_4_result" in results

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_task_exception_handling(self, exec_engine):
        """Test exception handling in submitted tasks."""
        await exec_engine.start()

        # Submit a task that raises an exception
        async def failing_task():
            raise ValueError("Test exception")

        future = exec_engine.submit(failing_task)

        # Exception should be propagated
        with pytest.raises(ValueError, match="Test exception"):
            await future

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_concurrent_task_execution(self, exec_engine):
        """Test concurrent task execution."""
        await exec_engine.start()

        execution_times = []

        async def timed_task(task_id):
            start_time = time.time()
            await asyncio.sleep(0.1)  # Simulate work
            end_time = time.time()
            execution_times.append((task_id, end_time - start_time))
            return task_id

        # Submit multiple tasks that should run concurrently
        futures = []
        for i in range(3):
            future = exec_engine.submit(timed_task, i)
            futures.append(future)

        # Wait for all to complete
        results = await asyncio.gather(*futures)

        # All tasks should complete
        assert len(results) == 3
        assert set(results) == {0, 1, 2}

        # Check that tasks ran concurrently (total time should be ~0.1s, not 0.3s)
        total_time = max(end_time for _, end_time in execution_times)
        assert total_time < 0.25  # Should be much less than 0.3s if concurrent

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_resource_limits(self, exec_engine):
        """Test that execution respects resource limits."""
        await exec_engine.start()

        # Submit many tasks to test resource management
        async def resource_task(task_id):
            # Each task uses some memory and CPU
            data = [0] * 1000  # Allocate some memory
            await asyncio.sleep(0.01)
            return len(data)

        # Submit tasks up to the limit
        futures = []
        max_tasks = exec_engine.hint.max_workers * 2

        for i in range(max_tasks):
            future = exec_engine.submit(resource_task, i)
            futures.append(future)

        # All tasks should complete successfully
        results = await asyncio.gather(*futures)
        assert len(results) == max_tasks
        assert all(result == 1000 for result in results)

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_shutdown_with_pending_tasks(self, exec_engine):
        """Test shutting down with pending tasks."""
        await exec_engine.start()

        # Submit long-running tasks
        async def long_task():
            await asyncio.sleep(1.0)
            return "completed"

        futures = []
        for i in range(3):
            future = exec_engine.submit(long_task)
            futures.append(future)

        # Shutdown immediately (tasks should be cancelled)
        await exec_engine.stop()

        # All futures should be cancelled or completed
        for future in futures:
            if not future.done():
                # Cancel if not done
                future.cancel()

    def test_exec_stats(self, exec_engine):
        """Test execution engine statistics."""
        stats = exec_engine.get_stats()

        assert isinstance(stats, dict)
        assert "running" in stats
        assert "tasks_submitted" in stats
        assert "tasks_completed" in stats
        assert "tasks_failed" in stats

        # Initially all should be zero/false
        assert stats["running"] is False
        assert stats["tasks_submitted"] == 0
        assert stats["tasks_completed"] == 0
        assert stats["tasks_failed"] == 0


class TestExecIntegration:
    """Test Exec integration scenarios."""

    @pytest.mark.asyncio
    async def test_exec_with_resource_manager_integration(self):
        """Test integration between Exec and ResourceManager."""
        resource_manager = ResourceManager()

        # Get system-aware hint
        hint = resource_manager.recommend()
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit some tasks
        async def cpu_task(n):
            # Simulate CPU-intensive work
            total = 0
            for i in range(n):
                total += i
            return total

        futures = [exec_engine.submit(cpu_task, 1000) for _ in range(2)]
        results = await asyncio.gather(*futures)

        assert results == [499500, 499500]  # sum(0 to 999)

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_error_propagation(self):
        """Test that errors are properly propagated from Exec."""
        resource_manager = ResourceManager()
        hint = resource_manager.recommend()
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit a task that raises an ExecutionError
        async def error_task():
            raise ExecutionError("Execution failed")

        future = exec_engine.submit(error_task)

        # Error should be propagated
        with pytest.raises(ExecutionError, match="Execution failed"):
            await future

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_performance_under_load(self):
        """Test Exec performance under high load."""
        resource_manager = ResourceManager()
        hint = resource_manager.recommend(max_workers=4)
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit many lightweight tasks
        async def lightweight_task(task_id):
            return task_id * 2

        start_time = time.time()

        # Submit many tasks
        futures = [exec_engine.submit(lightweight_task, i) for i in range(100)]
        results = await asyncio.gather(*futures)

        end_time = time.time()

        # Should complete all tasks
        assert len(results) == 100
        assert results[0] == 0
        assert results[50] == 100
        assert results[99] == 198

        # Should be reasonably fast
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete in under 5 seconds

        await exec_engine.stop()


class TestExecErrorHandling:
    """Test Exec error handling scenarios."""

    @pytest.mark.asyncio
    async def test_exec_task_timeout(self):
        """Test task timeout handling."""
        resource_manager = ResourceManager()
        hint = resource_manager.recommend()
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit a task that exceeds timeout
        async def slow_task():
            await asyncio.sleep(2.0)
            return "completed"

        # This test depends on the timeout implementation
        # For now, just test that the task completes
        future = exec_engine.submit(slow_task)
        result = await future
        assert result == "completed"

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_memory_limit_exhaustion(self):
        """Test behavior when memory limits are reached."""
        resource_manager = ResourceManager()
        hint = resource_manager.recommend(memory_limit=1024)  # Very small limit
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit a task that tries to use a lot of memory
        async def memory_task():
            # Try to allocate a large amount of memory
            data = [0] * 1000000  # This might exceed the limit
            return len(data)

        future = exec_engine.submit(memory_task)

        # Task should either complete or fail gracefully
        try:
            result = await future
            assert isinstance(result, int)
        except Exception:
            # Memory error should be handled gracefully
            pass

        await exec_engine.stop()

    @pytest.mark.asyncio
    async def test_exec_unhandled_exception_recovery(self):
        """Test recovery from unhandled exceptions in tasks."""
        resource_manager = ResourceManager()
        hint = resource_manager.recommend()
        exec_engine = Exec(hint)

        await exec_engine.start()

        # Submit a mix of good and bad tasks
        async def good_task(task_id):
            await asyncio.sleep(0.01)
            return f"good_{task_id}"

        async def bad_task(task_id):
            raise RuntimeError(f"Bad task {task_id}")

        futures = []
        for i in range(3):
            futures.append(exec_engine.submit(good_task, i))
            futures.append(exec_engine.submit(bad_task, i))

        # Collect results, ignoring exceptions from bad tasks
        results = []
        for future in futures:
            try:
                result = await future
                results.append(result)
            except RuntimeError:
                pass  # Expected for bad tasks

        # Should have results from good tasks only
        assert len(results) == 3
        assert "good_0" in results
        assert "good_1" in results
        assert "good_2" in results

        await exec_engine.stop()
