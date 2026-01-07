"""
Tests for domain modules.

Tests the example domain modules (templates) to ensure they work correctly.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock
from hydramind.modules.domain.domain_examples import (
    DroneFleet,
    RoboticsCell,
    TradingEngine,
    DBAnalyzer
)
from hydramind.core.bus import Message
from hydramind.core.module import ModuleState


class TestDroneFleet:
    """Test DroneFleet domain module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for DroneFleet."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def drone_fleet(self, mock_dependencies):
        """Create a DroneFleet instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return DroneFleet(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_drone_fleet_initialization(self, drone_fleet):
        """Test DroneFleet initializes correctly."""
        assert drone_fleet.name == "drone_fleet"
        assert drone_fleet.state == ModuleState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_drone_command_handling(self, drone_fleet):
        """Test handling drone commands."""
        await drone_fleet.start()

        # Mock the emit method
        drone_fleet.emit = AsyncMock()

        # Create a drone command message
        command_msg = Message("drone/command", {
            "drone_id": "drone_001",
            "action": "takeoff",
            "altitude": 10.0
        })

        # Handle the message
        await drone_fleet.on_message(command_msg)

        # Should emit an acknowledgment
        drone_fleet.emit.assert_called_once()
        call_args = drone_fleet.emit.call_args[0]

        assert call_args[0] == "drone/ack"
        ack_data = call_args[1]
        assert ack_data["drone_id"] == "drone_001"
        assert ack_data["action"] == "takeoff"
        assert ack_data["ok"] is True
        assert "ts" in ack_data

        await drone_fleet.stop()

    @pytest.mark.asyncio
    async def test_drone_command_missing_fields(self, drone_fleet):
        """Test handling drone commands with missing fields."""
        await drone_fleet.start()

        # Mock the emit method
        drone_fleet.emit = AsyncMock()

        # Create a command message missing drone_id
        command_msg = Message("drone/command", {
            "action": "land"
            # Missing drone_id
        })

        # Should handle gracefully
        await drone_fleet.on_message(command_msg)

        # Should still emit acknowledgment (implementation dependent)
        drone_fleet.emit.assert_called_once()

        await drone_fleet.stop()

    @pytest.mark.asyncio
    async def test_drone_command_non_command_topic(self, drone_fleet):
        """Test handling non-command messages."""
        await drone_fleet.start()

        # Mock the emit method
        drone_fleet.emit = AsyncMock()

        # Create a message on a different topic
        other_msg = Message("drone/status", {
            "drone_id": "drone_001",
            "battery": 85
        })

        # Should not emit acknowledgment for non-command topics
        await drone_fleet.on_message(other_msg)

        # No emit should be called for non-command topics
        drone_fleet.emit.assert_not_called()

        await drone_fleet.stop()


class TestRoboticsCell:
    """Test RoboticsCell domain module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for RoboticsCell."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def robotics_cell(self, mock_dependencies):
        """Create a RoboticsCell instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return RoboticsCell(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_robotics_cell_initialization(self, robotics_cell):
        """Test RoboticsCell initializes correctly."""
        assert robotics_cell.name == "robotics_cell"
        assert robotics_cell.state == ModuleState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_robot_status_handling(self, robotics_cell):
        """Test handling robot status messages."""
        await robotics_cell.start()

        # Mock the emit method
        robotics_cell.emit = AsyncMock()

        # Create a robot status message
        status_msg = Message("robot/status", {
            "robot_id": "arm_001",
            "joint_positions": [0.1, -0.2, 0.3, 0.4, 0.5, 0.6],
            "gripper_force": 15.5,
            "temperature": 42.0
        })

        # Handle the message
        await robotics_cell.on_message(status_msg)

        # Should emit processed status
        robotics_cell.emit.assert_called_once()
        call_args = robotics_cell.emit.call_args[0]

        assert call_args[0] == "robot/processed_status"
        processed_data = call_args[1]
        assert processed_data["robot_id"] == "arm_001"
        assert "processed_at" in processed_data

        await robotics_cell.stop()

    @pytest.mark.asyncio
    async def test_robot_command_handling(self, robotics_cell):
        """Test handling robot commands."""
        await robotics_cell.start()

        # Mock the emit method
        robotics_cell.emit = AsyncMock()

        # Create a robot command message
        command_msg = Message("robot/command", {
            "robot_id": "arm_001",
            "command": "move_to",
            "position": [0.5, 0.2, 0.8],
            "speed": 0.1
        })

        # Handle the message
        await robotics_cell.on_message(command_msg)

        # Should emit command acknowledgment
        robotics_cell.emit.assert_called_once()
        call_args = robotics_cell.emit.call_args[0]

        assert call_args[0] == "robot/command_ack"
        ack_data = call_args[1]
        assert ack_data["robot_id"] == "arm_001"
        assert ack_data["command"] == "move_to"
        assert ack_data["status"] == "executing"

        await robotics_cell.stop()


class TestTradingEngine:
    """Test TradingEngine domain module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for TradingEngine."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def trading_engine(self, mock_dependencies):
        """Create a TradingEngine instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return TradingEngine(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_trading_engine_initialization(self, trading_engine):
        """Test TradingEngine initializes correctly."""
        assert trading_engine.name == "trading_engine"
        assert trading_engine.state == ModuleState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_market_data_handling(self, trading_engine):
        """Test handling market data messages."""
        await trading_engine.start()

        # Mock the emit method
        trading_engine.emit = AsyncMock()

        # Create a market data message
        market_msg = Message("market/data", {
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 1000000,
            "timestamp": time.time()
        })

        # Handle the message
        await trading_engine.on_message(market_msg)

        # Should emit processed market data
        trading_engine.emit.assert_called_once()
        call_args = trading_engine.emit.call_args[0]

        assert call_args[0] == "market/processed"
        processed_data = call_args[1]
        assert processed_data["symbol"] == "AAPL"
        assert processed_data["price"] == 150.25
        assert "analysis" in processed_data

        await trading_engine.stop()

    @pytest.mark.asyncio
    async def test_trading_signal_handling(self, trading_engine):
        """Test handling trading signals."""
        await trading_engine.start()

        # Mock the emit method
        trading_engine.emit = AsyncMock()

        # Create a trading signal message
        signal_msg = Message("trading/signal", {
            "signal": "BUY",
            "symbol": "GOOGL",
            "price": 2800.50,
            "confidence": 0.85,
            "reason": "Technical breakout"
        })

        # Handle the message
        await trading_engine.on_message(signal_msg)

        # Should emit trade execution
        trading_engine.emit.assert_called_once()
        call_args = trading_engine.emit.call_args[0]

        assert call_args[0] == "trading/execution"
        execution_data = call_args[1]
        assert execution_data["signal"] == "BUY"
        assert execution_data["symbol"] == "GOOGL"
        assert execution_data["executed"] is True

        await trading_engine.stop()


class TestDBAnalyzer:
    """Test DBAnalyzer domain module."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for DBAnalyzer."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def db_analyzer(self, mock_dependencies):
        """Create a DBAnalyzer instance."""
        bus, exec_engine, policy_guard = mock_dependencies
        return DBAnalyzer(bus, exec_engine, policy_guard)

    @pytest.mark.asyncio
    async def test_db_analyzer_initialization(self, db_analyzer):
        """Test DBAnalyzer initializes correctly."""
        assert db_analyzer.name == "db_analyzer"
        assert db_analyzer.state == ModuleState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_query_request_handling(self, db_analyzer):
        """Test handling database query requests."""
        await db_analyzer.start()

        # Mock the emit method
        db_analyzer.emit = AsyncMock()

        # Create a query request message
        query_msg = Message("db/query", {
            "query_id": "query_001",
            "sql": "SELECT * FROM users WHERE active = true",
            "timeout": 30.0
        })

        # Handle the message
        await db_analyzer.on_message(query_msg)

        # Should emit query result
        db_analyzer.emit.assert_called_once()
        call_args = db_analyzer.emit.call_args[0]

        assert call_args[0] == "db/result"
        result_data = call_args[1]
        assert result_data["query_id"] == "query_001"
        assert "results" in result_data
        assert "execution_time" in result_data

        await db_analyzer.stop()

    @pytest.mark.asyncio
    async def test_analytics_request_handling(self, db_analyzer):
        """Test handling analytics requests."""
        await db_analyzer.start()

        # Mock the emit method
        db_analyzer.emit = AsyncMock()

        # Create an analytics request message
        analytics_msg = Message("db/analytics", {
            "request_id": "analytics_001",
            "metric": "user_engagement",
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
        })

        # Handle the message
        await db_analyzer.on_message(analytics_msg)

        # Should emit analytics result
        db_analyzer.emit.assert_called_once()
        call_args = db_analyzer.emit.call_args[0]

        assert call_args[0] == "db/analytics_result"
        result_data = call_args[1]
        assert result_data["request_id"] == "analytics_001"
        assert result_data["metric"] == "user_engagement"
        assert "data" in result_data

        await db_analyzer.stop()


class TestDomainModuleIntegration:
    """Test integration between domain modules."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for all domain modules."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.fixture
    def all_modules(self, mock_dependencies):
        """Create instances of all domain modules."""
        bus, exec_engine, policy_guard = mock_dependencies

        return {
            "drone_fleet": DroneFleet(bus, exec_engine, policy_guard),
            "robotics_cell": RoboticsCell(bus, exec_engine, policy_guard),
            "trading_engine": TradingEngine(bus, exec_engine, policy_guard),
            "db_analyzer": DBAnalyzer(bus, exec_engine, policy_guard)
        }

    @pytest.mark.asyncio
    async def test_domain_module_lifecycle(self, all_modules):
        """Test lifecycle management for all domain modules."""
        # Start all modules
        for module in all_modules.values():
            await module.start()
            assert module.state == ModuleState.RUNNING

        # Stop all modules
        for module in all_modules.values():
            await module.stop()
            assert module.state == ModuleState.STOPPED

    @pytest.mark.asyncio
    async def test_domain_module_message_routing(self, all_modules):
        """Test message routing between domain modules."""
        # Start all modules
        for module in all_modules.values():
            await module.start()

        # Mock emit methods
        for module in all_modules.values():
            module.emit = AsyncMock()

        # Test cross-module communication
        # Drone fleet sends status to robotics cell
        drone_status = Message("drone/status", {
            "drone_id": "drone_001",
            "position": [1.0, 2.0, 3.0]
        })

        # This would typically be handled by the bus routing to appropriate modules
        # For this test, we verify each module handles its own message types
        await all_modules["drone_fleet"].on_message(drone_status)

        # Should not affect other modules (each handles its own topics)
        for name, module in all_modules.items():
            if name != "drone_fleet":
                module.emit.assert_not_called()

        # Stop all modules
        for module in all_modules.values():
            await module.stop()

    @pytest.mark.asyncio
    async def test_domain_module_error_handling(self, all_modules):
        """Test error handling in domain modules."""
        # Start all modules
        for module in all_modules.values():
            await module.start()

        # Test error handling for malformed messages
        malformed_msg = Message("test/topic", "not_a_dict")  # Invalid data type

        for module in all_modules.values():
            # Should handle malformed messages gracefully
            try:
                await module.on_message(malformed_msg)
                # Should not raise an exception
            except Exception as e:
                # If an exception is raised, it should be a known type
                assert isinstance(e, (TypeError, ValueError))

        # Stop all modules
        for module in all_modules.values():
            await module.stop()


class TestDomainModulePerformance:
    """Test domain module performance."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for performance testing."""
        bus = Mock()
        exec_engine = Mock()
        policy_guard = Mock()

        return bus, exec_engine, policy_guard

    @pytest.mark.asyncio
    async def test_drone_fleet_performance(self, mock_dependencies):
        """Test DroneFleet performance under load."""
        bus, exec_engine, policy_guard = mock_dependencies
        drone_fleet = DroneFleet(bus, exec_engine, policy_guard)

        await drone_fleet.start()

        # Mock emit method
        drone_fleet.emit = AsyncMock()

        # Send many drone commands
        start_time = time.time()

        commands = []
        for i in range(100):
            command = Message("drone/command", {
                "drone_id": f"drone_{i:03d}",
                "action": "move",
                "position": [i, i*0.1, i*0.01]
            })
            commands.append(command)

        # Process all commands
        for command in commands:
            await drone_fleet.on_message(command)

        end_time = time.time()

        # Should complete reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should complete in under 2 seconds

        # Should have emitted responses for all commands
        assert drone_fleet.emit.call_count == 100

        await drone_fleet.stop()

    @pytest.mark.asyncio
    async def test_robotics_cell_performance(self, mock_dependencies):
        """Test RoboticsCell performance under load."""
        bus, exec_engine, policy_guard = mock_dependencies
        robotics_cell = RoboticsCell(bus, exec_engine, policy_guard)

        await robotics_cell.start()

        # Mock emit method
        robotics_cell.emit = AsyncMock()

        # Send many status messages
        start_time = time.time()

        for i in range(50):
            status_msg = Message("robot/status", {
                "robot_id": f"arm_{i:03d}",
                "joint_positions": [0.1 * j for j in range(6)],
                "gripper_force": 10.0 + i,
                "temperature": 40.0 + i * 0.1
            })
            await robotics_cell.on_message(status_msg)

        end_time = time.time()

        # Should complete reasonably quickly
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should complete in under 1 second

        # Should have emitted responses for all status messages
        assert robotics_cell.emit.call_count == 50

        await robotics_cell.stop()
