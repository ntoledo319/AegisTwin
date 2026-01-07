"""
Swarm Coordinator Module - Autonomous Agent Orchestration

Coordinates multiple autonomous agents (modules) working together toward
common goals. Inspired by SEED drone swarm architecture.
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles for autonomous agents"""
    WORKER = "worker"  # Performs tasks
    MONITOR = "monitor"  # Monitors system
    OPTIMIZER = "optimizer"  # Optimizes performance
    HEALER = "healer"  # Self-healing
    COLLECTOR = "collector"  # Data collection
    LEARNER = "learner"  # Pattern learning


class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    ACTIVE = "active"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Agent:
    """Autonomous agent"""
    agent_id: str
    role: AgentRole
    status: AgentStatus
    capabilities: List[str]
    workload: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: float = 0.0
    last_activity: float = 0.0


@dataclass
class Task:
    """Task to be executed by agents"""
    task_id: str
    task_type: str
    priority: int  # 1-10, higher = more urgent
    payload: Dict[str, Any]
    required_capabilities: List[str]
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: float = 0.0
    deadline: Optional[float] = None


class SwarmCoordinator(Module):
    """
    Coordinates multiple autonomous agents in a swarm.
    
    Manages agent lifecycle, task distribution, and collective intelligence.
    Inspired by SEED drone swarm orchestration.
    
    Events consumed:
    - swarm/register_agent: Register new agent
    - swarm/submit_task: Submit task for execution
    - swarm/agent_status: Agent status update
    
    Events emitted:
    - swarm/task_assigned: Task assigned to agent
    - swarm/task_completed: Task completed
    - swarm/swarm_status: Swarm status update
    """
    
    name = "swarm_coordinator"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        coordination_interval=30.0,
        max_agents_per_role=5
    ):
        """
        Initialize swarm coordinator.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            coordination_interval: Seconds between coordination cycles
            max_agents_per_role: Maximum agents per role
        """
        super().__init__(bus, ex, policy)
        self.coordination_interval = coordination_interval
        self.max_agents_per_role = max_agents_per_role
        
        # Agent registry
        self.agents: Dict[str, Agent] = {}
        self.agents_by_role: Dict[AgentRole, Set[str]] = defaultdict(set)
        
        # Task queue
        self.pending_tasks: deque = deque()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        # Coordination state
        self._coordination_task: Optional[asyncio.Task] = None
        self._swarm_active = True
        self._total_tasks_processed = 0
        
        # Performance tracking
        self.role_performance: Dict[AgentRole, Dict[str, Any]] = defaultdict(lambda: {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_completion_time': 0.0
        })
    
    async def start(self) -> None:
        """Start swarm coordination"""
        await super().start()
        
        # Subscribe to swarm events
        await self.bus.subscribe("swarm/register_agent", self._handle_register_agent)
        await self.bus.subscribe("swarm/submit_task", self._handle_submit_task)
        await self.bus.subscribe("swarm/agent_status", self._handle_agent_status)
        await self.bus.subscribe("swarm/task_result", self._handle_task_result)
        
        # Start coordination loop
        self._coordination_task = asyncio.create_task(self._coordination_loop())
        
        self.log.info("Swarm coordinator started")
    
    async def stop(self) -> None:
        """Stop swarm coordination"""
        self._swarm_active = False
        
        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("Swarm coordinator stopped")
    
    async def _coordination_loop(self) -> None:
        """Main coordination loop"""
        while self._swarm_active:
            try:
                await asyncio.sleep(self.coordination_interval)
                
                # Spawn agents if needed
                await self._spawn_agents()
                
                # Assign tasks to agents
                await self._assign_tasks()
                
                # Check agent health
                await self._check_agent_health()
                
                # Emit swarm status
                await self._emit_swarm_status()
                
            except Exception as e:
                self.log.error(f"Coordination loop error: {e}")
                await asyncio.sleep(self.coordination_interval)
    
    async def _handle_register_agent(self, msg: Message) -> None:
        """Handle agent registration"""
        try:
            data = msg.data
            
            agent_id = data.get('agent_id', str(uuid.uuid4())[:8])
            role = AgentRole(data.get('role', 'worker'))
            capabilities = data.get('capabilities', [])
            
            # Check if we can accept more agents in this role
            if len(self.agents_by_role[role]) >= self.max_agents_per_role:
                self.log.warning(f"Cannot register agent {agent_id}: role {role.value} at capacity")
                return
            
            # Create agent
            agent = Agent(
                agent_id=agent_id,
                role=role,
                status=AgentStatus.IDLE,
                capabilities=capabilities,
                created_at=time.time(),
                last_activity=time.time()
            )
            
            # Register agent
            self.agents[agent_id] = agent
            self.agents_by_role[role].add(agent_id)
            
            self.log.info(f"Registered agent {agent_id} with role {role.value}")
            
            await self.emit("swarm/agent_registered", {
                "agent_id": agent_id,
                "role": role.value
            })
            
        except Exception as e:
            self.log.error(f"Error registering agent: {e}")
    
    async def _handle_submit_task(self, msg: Message) -> None:
        """Handle task submission"""
        try:
            data = msg.data
            
            task_id = data.get('task_id', str(uuid.uuid4())[:8])
            task_type = data.get('task_type', 'generic')
            priority = data.get('priority', 5)
            payload = data.get('payload', {})
            required_capabilities = data.get('capabilities', [])
            deadline = data.get('deadline')
            
            # Create task
            task = Task(
                task_id=task_id,
                task_type=task_type,
                priority=priority,
                payload=payload,
                required_capabilities=required_capabilities,
                deadline=deadline,
                created_at=time.time()
            )
            
            # Add to queue
            self.pending_tasks.append(task)
            
            self.log.info(f"Task {task_id} submitted: type={task_type}, priority={priority}")
            
            # Try to assign immediately
            await self._assign_tasks()
            
        except Exception as e:
            self.log.error(f"Error submitting task: {e}")
    
    async def _handle_agent_status(self, msg: Message) -> None:
        """Handle agent status update"""
        try:
            data = msg.data
            agent_id = data.get('agent_id')
            status = data.get('status')
            
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.status = AgentStatus(status)
                agent.last_activity = time.time()
                
                self.log.debug(f"Agent {agent_id} status: {status}")
            
        except Exception as e:
            self.log.error(f"Error handling agent status: {e}")
    
    async def _handle_task_result(self, msg: Message) -> None:
        """Handle task completion result"""
        try:
            data = msg.data
            task_id = data.get('task_id')
            agent_id = data.get('agent_id')
            success = data.get('success', False)
            
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = "completed" if success else "failed"
                
                # Move to completed
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                
                # Keep completed tasks manageable
                if len(self.completed_tasks) > 1000:
                    self.completed_tasks = self.completed_tasks[-500:]
                
                # Update agent
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent.workload = max(0, agent.workload - 1)
                    agent.status = AgentStatus.IDLE
                    
                    if success:
                        agent.tasks_completed += 1
                        self.role_performance[agent.role]['tasks_completed'] += 1
                    else:
                        agent.tasks_failed += 1
                        self.role_performance[agent.role]['tasks_failed'] += 1
                
                self._total_tasks_processed += 1
                
                # Emit completion event
                await self.emit("swarm/task_completed", {
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "success": success,
                    "task_type": task.task_type
                })
                
                self.log.info(f"Task {task_id} {'completed' if success else 'failed'} by agent {agent_id}")
            
        except Exception as e:
            self.log.error(f"Error handling task result: {e}")
    
    async def _spawn_agents(self) -> None:
        """Spawn new agents if needed based on workload"""
        try:
            # Check workload for each role
            for role in AgentRole:
                role_agents = [self.agents[aid] for aid in self.agents_by_role[role]]
                
                if not role_agents:
                    continue
                
                # Calculate average workload
                avg_workload = sum(a.workload for a in role_agents) / len(role_agents)
                
                # Spawn if high workload and under capacity
                if avg_workload > 5 and len(role_agents) < self.max_agents_per_role:
                    # Request new agent spawn
                    await self.emit("swarm/spawn_agent", {
                        "role": role.value,
                        "reason": "high_workload"
                    })
                    
                    self.log.info(f"Requested spawn of {role.value} agent (avg workload: {avg_workload})")
        
        except Exception as e:
            self.log.error(f"Error spawning agents: {e}")
    
    async def _assign_tasks(self) -> None:
        """Assign pending tasks to available agents"""
        try:
            if not self.pending_tasks:
                return
            
            # Sort tasks by priority
            sorted_tasks = sorted(self.pending_tasks, key=lambda t: t.priority, reverse=True)
            
            assigned_count = 0
            
            for task in sorted_tasks[:]:  # Iterate over copy
                # Find suitable agent
                agent = self._find_suitable_agent(task)
                
                if agent:
                    # Assign task
                    task.assigned_agent = agent.agent_id
                    task.status = "assigned"
                    
                    # Update agent
                    agent.status = AgentStatus.WORKING
                    agent.workload += 1
                    agent.last_activity = time.time()
                    
                    # Move task to active
                    self.active_tasks[task.task_id] = task
                    self.pending_tasks.remove(task)
                    
                    # Emit assignment event
                    await self.emit("swarm/task_assigned", {
                        "task_id": task.task_id,
                        "agent_id": agent.agent_id,
                        "task_type": task.task_type,
                        "payload": task.payload
                    })
                    
                    assigned_count += 1
                    
                    self.log.info(f"Assigned task {task.task_id} to agent {agent.agent_id}")
            
            if assigned_count > 0:
                self.log.info(f"Assigned {assigned_count} tasks")
        
        except Exception as e:
            self.log.error(f"Error assigning tasks: {e}")
    
    def _find_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find suitable agent for task"""
        # Filter idle or lightly loaded agents
        available_agents = [
            agent for agent in self.agents.values()
            if agent.status in [AgentStatus.IDLE, AgentStatus.ACTIVE] and agent.workload < 3
        ]
        
        if not available_agents:
            return None
        
        # Filter by capabilities if required
        if task.required_capabilities:
            suitable_agents = [
                agent for agent in available_agents
                if all(cap in agent.capabilities for cap in task.required_capabilities)
            ]
            
            if suitable_agents:
                available_agents = suitable_agents
        
        # Select agent with lowest workload
        return min(available_agents, key=lambda a: a.workload)
    
    async def _check_agent_health(self) -> None:
        """Check health of all agents"""
        try:
            current_time = time.time()
            stale_agents = []
            
            for agent_id, agent in self.agents.items():
                # Check if agent is stale (no activity for too long)
                time_since_activity = current_time - agent.last_activity
                
                if time_since_activity > 300:  # 5 minutes
                    stale_agents.append(agent_id)
                    self.log.warning(f"Agent {agent_id} appears stale (last activity: {time_since_activity:.0f}s ago)")
            
            # Remove stale agents
            for agent_id in stale_agents:
                agent = self.agents[agent_id]
                self.agents_by_role[agent.role].discard(agent_id)
                del self.agents[agent_id]
                
                self.log.info(f"Removed stale agent {agent_id}")
        
        except Exception as e:
            self.log.error(f"Error checking agent health: {e}")
    
    async def _emit_swarm_status(self) -> None:
        """Emit comprehensive swarm status"""
        try:
            status = {
                'timestamp': time.time(),
                'agents': {
                    'total': len(self.agents),
                    'by_role': {
                        role.value: len(agents)
                        for role, agents in self.agents_by_role.items()
                    },
                    'by_status': {
                        status.value: len([a for a in self.agents.values() if a.status == status])
                        for status in AgentStatus
                    }
                },
                'tasks': {
                    'pending': len(self.pending_tasks),
                    'active': len(self.active_tasks),
                    'completed': len(self.completed_tasks),
                    'total_processed': self._total_tasks_processed
                },
                'performance': {
                    role.value: perf
                    for role, perf in self.role_performance.items()
                }
            }
            
            await self.emit("swarm/status", status)
        
        except Exception as e:
            self.log.error(f"Error emitting swarm status: {e}")
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        # Handled by specific subscribers
        pass
    
    def get_stats(self) -> dict:
        """Get swarm statistics"""
        stats = super().get_stats()
        
        stats.update({
            "swarm_active": self._swarm_active,
            "total_agents": len(self.agents),
            "agents_by_role": {
                role.value: len(agents)
                for role, agents in self.agents_by_role.items()
            },
            "pending_tasks": len(self.pending_tasks),
            "active_tasks": len(self.active_tasks),
            "total_tasks_processed": self._total_tasks_processed,
            "avg_agent_workload": sum(a.workload for a in self.agents.values()) / len(self.agents) if self.agents else 0
        })
        return stats
