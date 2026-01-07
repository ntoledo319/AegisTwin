"""
Self-Optimizer Module - SEED-Inspired Self-Learning Optimization

Continuously optimizes system parameters based on observed performance metrics.
Learns from patterns and adapts strategies for maximum efficiency.
"""

import asyncio
import logging
import time
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


class OptimizationDomain(Enum):
    """Optimization domains"""
    PERFORMANCE = "performance"
    RESOURCE_USAGE = "resource_usage"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"


@dataclass
class OptimizationResult:
    """Result of an optimization cycle"""
    domain: OptimizationDomain
    metric_name: str
    old_value: float
    new_value: float
    improvement_pct: float
    parameters_adjusted: Dict[str, Any]
    confidence: float
    timestamp: float


class SelfOptimizer(Module):
    """
    Self-learning optimizer that continuously improves system parameters.
    
    Monitors performance metrics, identifies patterns, and adjusts parameters
    to maximize efficiency. Inspired by SEED optimization engine.
    
    Events consumed:
    - health/telemetry: System health metrics
    - module/performance: Module performance data
    - optimizer/optimize: Manual optimization trigger
    
    Events emitted:
    - optimizer/result: Optimization result
    - optimizer/recommendation: Optimization recommendation
    """
    
    name = "self_optimizer"
    
    def __init__(self, bus, ex, policy, window_size: int = 100, optimization_interval: float = 60.0):
        super().__init__(bus, ex, policy)
        self.window_size = window_size
        self.optimization_interval = optimization_interval
        
        # Metric windows for pattern analysis
        self.metric_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        
        # Current optimization parameters for each domain
        self.domain_parameters = {
            OptimizationDomain.PERFORMANCE: {
                'cpu_threshold': 80.0,
                'mem_threshold': 85.0,
                'scaling_factor': 1.0
            },
            OptimizationDomain.THROUGHPUT: {
                'batch_size': 10,
                'concurrency': 5,
                'buffer_size': 100
            },
            OptimizationDomain.LATENCY: {
                'timeout_ms': 1000,
                'retry_delay_ms': 100,
                'cache_ttl_s': 300
            },
            OptimizationDomain.ERROR_RATE: {
                'error_threshold': 0.05,
                'circuit_breaker_threshold': 0.1,
                'retry_limit': 3
            }
        }
        
        # Optimization history
        self.optimization_history: List[OptimizationResult] = []
        self._optimization_task: Optional[asyncio.Task] = None
        self._last_optimization = 0.0
        
        # Pattern detection state
        self.patterns_detected = {}
        self.baseline_metrics = {}
    
    async def start(self) -> None:
        """Start optimization loop"""
        await super().start()
        
        # Subscribe to relevant events
        await self.bus.subscribe("health/telemetry", self._handle_telemetry)
        await self.bus.subscribe("module/performance", self._handle_performance)
        await self.bus.subscribe("optimizer/optimize", self._handle_optimize_request)
        
        # Start optimization loop
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        self.log.info("Self-optimizer started")
    
    async def stop(self) -> None:
        """Stop optimization loop"""
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("Self-optimizer stopped")
    
    async def _optimization_loop(self) -> None:
        """Periodic optimization loop"""
        while self._running:
            try:
                await asyncio.sleep(self.optimization_interval)
                
                # Run optimization cycle
                results = await self._run_optimization_cycle()
                
                # Emit results
                for result in results:
                    await self.emit("optimizer/result", {
                        "domain": result.domain.value,
                        "metric": result.metric_name,
                        "old_value": result.old_value,
                        "new_value": result.new_value,
                        "improvement_pct": result.improvement_pct,
                        "confidence": result.confidence,
                        "parameters": result.parameters_adjusted
                    })
                
            except Exception as e:
                self.log.error(f"Optimization loop error: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    async def _handle_telemetry(self, msg: Message) -> None:
        """Handle incoming telemetry"""
        try:
            data = msg.data
            
            # Store metrics in windows
            self.metric_windows['cpu'].append(data.get('cpu', 0))
            self.metric_windows['memory'].append(data.get('mem', 0))
            self.metric_windows['disk'].append(data.get('disk', 0))
            
            # Update baseline if needed
            if not self.baseline_metrics:
                self._update_baseline()
            
        except Exception as e:
            self.log.error(f"Error handling telemetry: {e}")
    
    async def _handle_performance(self, msg: Message) -> None:
        """Handle module performance data"""
        try:
            data = msg.data
            module_name = data.get('module', 'unknown')
            
            # Store performance metrics
            key = f"perf_{module_name}"
            self.metric_windows[key].append({
                'latency': data.get('latency', 0),
                'throughput': data.get('throughput', 0),
                'errors': data.get('errors', 0),
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.log.error(f"Error handling performance: {e}")
    
    async def _handle_optimize_request(self, msg: Message) -> None:
        """Handle manual optimization request"""
        try:
            domain = msg.data.get('domain')
            
            if domain:
                # Optimize specific domain
                domain_enum = OptimizationDomain(domain)
                result = await self._optimize_domain(domain_enum)
                
                await self.emit("optimizer/result", {
                    "domain": result.domain.value,
                    "improvement_pct": result.improvement_pct,
                    "parameters": result.parameters_adjusted
                })
            else:
                # Full optimization
                results = await self._run_optimization_cycle()
                
                await self.emit("optimizer/result", {
                    "domains": [r.domain.value for r in results],
                    "total_improvements": len([r for r in results if r.improvement_pct > 0])
                })
                
        except Exception as e:
            self.log.error(f"Error handling optimize request: {e}")
    
    async def _run_optimization_cycle(self) -> List[OptimizationResult]:
        """Run full optimization cycle across all domains"""
        results = []
        
        try:
            # Detect patterns
            patterns = self._detect_patterns()
            
            # Optimize each domain
            for domain in OptimizationDomain:
                try:
                    result = await self._optimize_domain(domain, patterns)
                    results.append(result)
                    
                    # Store in history
                    self.optimization_history.append(result)
                    
                    # Keep history size manageable
                    if len(self.optimization_history) > 1000:
                        self.optimization_history = self.optimization_history[-500:]
                        
                except Exception as e:
                    self.log.error(f"Error optimizing domain {domain.value}: {e}")
            
            self._last_optimization = time.time()
            self.log.info(f"Optimization cycle complete: {len(results)} domains optimized")
            
        except Exception as e:
            self.log.error(f"Optimization cycle error: {e}")
        
        return results
    
    async def _optimize_domain(
        self, 
        domain: OptimizationDomain,
        patterns: Optional[Dict] = None
    ) -> OptimizationResult:
        """Optimize a specific domain"""
        if patterns is None:
            patterns = {}
        
        current_params = self.domain_parameters[domain].copy()
        
        # Domain-specific optimization logic
        if domain == OptimizationDomain.PERFORMANCE:
            result = self._optimize_performance(current_params, patterns)
        elif domain == OptimizationDomain.THROUGHPUT:
            result = self._optimize_throughput(current_params, patterns)
        elif domain == OptimizationDomain.LATENCY:
            result = self._optimize_latency(current_params, patterns)
        elif domain == OptimizationDomain.ERROR_RATE:
            result = self._optimize_error_rate(current_params, patterns)
        else:
            result = self._optimize_resource_usage(current_params, patterns)
        
        # Update parameters if improvement found
        if result.improvement_pct > 0:
            self.domain_parameters[domain] = result.parameters_adjusted
        
        return result
    
    def _optimize_performance(
        self, 
        current_params: Dict, 
        patterns: Dict
    ) -> OptimizationResult:
        """Optimize performance domain"""
        new_params = current_params.copy()
        
        # Analyze CPU utilization patterns
        cpu_metrics = list(self.metric_windows['cpu'])
        if len(cpu_metrics) >= 10:
            avg_cpu = sum(cpu_metrics[-10:]) / 10
            
            # Adjust thresholds based on utilization
            if avg_cpu > 85:
                # High CPU - lower threshold to scale earlier
                new_params['cpu_threshold'] = max(70, current_params['cpu_threshold'] - 5)
                new_params['scaling_factor'] = min(2.0, current_params['scaling_factor'] * 1.2)
            elif avg_cpu < 50:
                # Low CPU - can raise threshold
                new_params['cpu_threshold'] = min(90, current_params['cpu_threshold'] + 5)
                new_params['scaling_factor'] = max(0.5, current_params['scaling_factor'] * 0.9)
            
            improvement = self._calculate_improvement(
                current_params, new_params, 'cpu_efficiency'
            )
            
            return OptimizationResult(
                domain=OptimizationDomain.PERFORMANCE,
                metric_name='cpu_efficiency',
                old_value=avg_cpu,
                new_value=avg_cpu * (1 - improvement / 100),
                improvement_pct=improvement,
                parameters_adjusted=new_params,
                confidence=min(0.9, len(cpu_metrics) / self.window_size),
                timestamp=time.time()
            )
        
        return self._no_improvement_result(OptimizationDomain.PERFORMANCE, 'cpu_efficiency')
    
    def _optimize_throughput(
        self, 
        current_params: Dict, 
        patterns: Dict
    ) -> OptimizationResult:
        """Optimize throughput domain"""
        new_params = current_params.copy()
        
        # Analyze throughput patterns from module performance
        throughput_samples = []
        for key, window in self.metric_windows.items():
            if key.startswith('perf_'):
                throughput_samples.extend([
                    sample.get('throughput', 0) 
                    for sample in window 
                    if isinstance(sample, dict)
                ])
        
        if len(throughput_samples) >= 10:
            avg_throughput = sum(throughput_samples[-10:]) / 10
            
            # Adjust batch size and concurrency
            if avg_throughput < 100:
                # Low throughput - increase batch size and concurrency
                new_params['batch_size'] = min(100, current_params['batch_size'] + 5)
                new_params['concurrency'] = min(20, current_params['concurrency'] + 2)
            elif avg_throughput > 500:
                # High throughput - can reduce to save resources
                new_params['batch_size'] = max(5, current_params['batch_size'] - 2)
            
            improvement = self._calculate_improvement(
                current_params, new_params, 'throughput'
            )
            
            return OptimizationResult(
                domain=OptimizationDomain.THROUGHPUT,
                metric_name='throughput',
                old_value=avg_throughput,
                new_value=avg_throughput * (1 + improvement / 100),
                improvement_pct=improvement,
                parameters_adjusted=new_params,
                confidence=0.7,
                timestamp=time.time()
            )
        
        return self._no_improvement_result(OptimizationDomain.THROUGHPUT, 'throughput')
    
    def _optimize_latency(
        self, 
        current_params: Dict, 
        patterns: Dict
    ) -> OptimizationResult:
        """Optimize latency domain"""
        new_params = current_params.copy()
        
        # Analyze latency patterns
        latency_samples = []
        for key, window in self.metric_windows.items():
            if key.startswith('perf_'):
                latency_samples.extend([
                    sample.get('latency', 0) 
                    for sample in window 
                    if isinstance(sample, dict)
                ])
        
        if len(latency_samples) >= 10:
            avg_latency = sum(latency_samples[-10:]) / 10
            p95_latency = sorted(latency_samples[-20:])[-2] if len(latency_samples) >= 20 else avg_latency
            
            # Adjust timeouts based on observed latency
            if p95_latency > current_params['timeout_ms'] * 0.8:
                # Approaching timeout - increase
                new_params['timeout_ms'] = int(current_params['timeout_ms'] * 1.2)
            elif p95_latency < current_params['timeout_ms'] * 0.3:
                # Can tighten timeout
                new_params['timeout_ms'] = int(current_params['timeout_ms'] * 0.9)
            
            # Adjust cache TTL
            if avg_latency > 500:
                # High latency - increase cache TTL
                new_params['cache_ttl_s'] = min(3600, current_params['cache_ttl_s'] + 60)
            
            improvement = self._calculate_improvement(
                current_params, new_params, 'latency'
            )
            
            return OptimizationResult(
                domain=OptimizationDomain.LATENCY,
                metric_name='latency_ms',
                old_value=avg_latency,
                new_value=avg_latency * (1 - improvement / 100),
                improvement_pct=improvement,
                parameters_adjusted=new_params,
                confidence=0.75,
                timestamp=time.time()
            )
        
        return self._no_improvement_result(OptimizationDomain.LATENCY, 'latency_ms')
    
    def _optimize_error_rate(
        self, 
        current_params: Dict, 
        patterns: Dict
    ) -> OptimizationResult:
        """Optimize error rate domain"""
        new_params = current_params.copy()
        
        # Analyze error patterns
        error_samples = []
        for key, window in self.metric_windows.items():
            if key.startswith('perf_'):
                error_samples.extend([
                    sample.get('errors', 0) 
                    for sample in window 
                    if isinstance(sample, dict)
                ])
        
        if len(error_samples) >= 10:
            total_errors = sum(error_samples[-10:])
            error_rate = total_errors / 10  # Average errors per sample
            
            # Adjust error handling parameters
            if error_rate > 0.1:
                # High error rate - tighten thresholds
                new_params['error_threshold'] = max(0.01, current_params['error_threshold'] * 0.8)
                new_params['retry_limit'] = min(5, current_params['retry_limit'] + 1)
            elif error_rate < 0.01:
                # Very low errors - can relax
                new_params['error_threshold'] = min(0.1, current_params['error_threshold'] * 1.2)
            
            improvement = self._calculate_improvement(
                current_params, new_params, 'error_rate'
            )
            
            return OptimizationResult(
                domain=OptimizationDomain.ERROR_RATE,
                metric_name='error_rate',
                old_value=error_rate,
                new_value=error_rate * (1 - improvement / 100),
                improvement_pct=improvement,
                parameters_adjusted=new_params,
                confidence=0.8,
                timestamp=time.time()
            )
        
        return self._no_improvement_result(OptimizationDomain.ERROR_RATE, 'error_rate')
    
    def _optimize_resource_usage(
        self, 
        current_params: Dict, 
        patterns: Dict
    ) -> OptimizationResult:
        """Optimize resource usage domain"""
        new_params = {'resource_optimization_level': 1.0}
        
        # Analyze resource usage patterns
        mem_metrics = list(self.metric_windows['memory'])
        disk_metrics = list(self.metric_windows['disk'])
        
        if len(mem_metrics) >= 10 and len(disk_metrics) >= 10:
            avg_mem = sum(mem_metrics[-10:]) / 10
            avg_disk = sum(disk_metrics[-10:]) / 10
            
            # Calculate resource usage score
            resource_score = (avg_mem + avg_disk) / 2
            
            improvement = 5.0 if resource_score > 70 else 2.0
            
            return OptimizationResult(
                domain=OptimizationDomain.RESOURCE_USAGE,
                metric_name='resource_score',
                old_value=resource_score,
                new_value=resource_score * 0.95,
                improvement_pct=improvement,
                parameters_adjusted=new_params,
                confidence=0.65,
                timestamp=time.time()
            )
        
        return self._no_improvement_result(OptimizationDomain.RESOURCE_USAGE, 'resource_score')
    
    def _detect_patterns(self) -> Dict[str, Any]:
        """Detect patterns in metric data"""
        patterns = {}
        
        # Detect CPU patterns
        cpu_metrics = list(self.metric_windows['cpu'])
        if len(cpu_metrics) >= 20:
            # Check for trends
            first_half = sum(cpu_metrics[:10]) / 10
            second_half = sum(cpu_metrics[-10:]) / 10
            
            if second_half > first_half * 1.2:
                patterns['cpu_trend'] = 'increasing'
            elif second_half < first_half * 0.8:
                patterns['cpu_trend'] = 'decreasing'
            else:
                patterns['cpu_trend'] = 'stable'
            
            # Check for spikes
            max_cpu = max(cpu_metrics[-10:])
            avg_cpu = second_half
            if max_cpu > avg_cpu * 1.5:
                patterns['cpu_spikes'] = True
        
        return patterns
    
    def _calculate_improvement(
        self, 
        old_params: Dict, 
        new_params: Dict, 
        metric: str
    ) -> float:
        """Calculate expected improvement percentage"""
        # Simple heuristic - compare parameter changes
        changes = 0
        for key in new_params:
            if key in old_params and new_params[key] != old_params[key]:
                changes += 1
        
        # More changes = more potential improvement
        return min(15.0, changes * 3.0)
    
    def _update_baseline(self) -> None:
        """Update baseline metrics"""
        self.baseline_metrics = {
            'cpu': sum(self.metric_windows['cpu']) / max(1, len(self.metric_windows['cpu'])),
            'memory': sum(self.metric_windows['memory']) / max(1, len(self.metric_windows['memory'])),
            'disk': sum(self.metric_windows['disk']) / max(1, len(self.metric_windows['disk']))
        }
    
    def _no_improvement_result(self, domain: OptimizationDomain, metric: str) -> OptimizationResult:
        """Create a no-improvement result"""
        return OptimizationResult(
            domain=domain,
            metric_name=metric,
            old_value=0.0,
            new_value=0.0,
            improvement_pct=0.0,
            parameters_adjusted={},
            confidence=0.0,
            timestamp=time.time()
        )
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        if msg.topic == "health/telemetry":
            await self._handle_telemetry(msg)
        elif msg.topic == "module/performance":
            await self._handle_performance(msg)
        elif msg.topic == "optimizer/optimize":
            await self._handle_optimize_request(msg)
    
    def get_stats(self) -> dict:
        """Get optimizer statistics"""
        stats = super().get_stats()
        stats.update({
            "optimization_history_count": len(self.optimization_history),
            "last_optimization": self._last_optimization,
            "domain_parameters": {k.value: v for k, v in self.domain_parameters.items()},
            "patterns_detected": len(self.patterns_detected),
            "metric_windows": {k: len(v) for k, v in self.metric_windows.items()}
        })
        return stats
