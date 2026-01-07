"""
System Verifier Module - Autonomous Health Verification

Continuously scans the system for errors, inconsistencies, and degradation.
Inspired by verification drones from SEED swarm architecture.
"""

import asyncio
import logging
import time
import psutil
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a verification check"""
    check_name: str
    passed: bool
    severity: str  # 'low', 'medium', 'high', 'critical'
    issues: List[str]
    recommendations: List[str]
    health_score: float  # 0-100
    timestamp: float


class SystemVerifier(Module):
    """
    Autonomous system verification and health checking.
    
    Continuously runs health checks, detects issues, and provides
    recommendations for system improvements.
    
    Events consumed:
    - verifier/check: Manual verification trigger
    - verifier/register_check: Register custom check
    
    Events emitted:
    - verifier/result: Verification result
    - verifier/alert: Critical issue detected
    - verifier/recommendation: System recommendation
    """
    
    name = "system_verifier"
    
    def __init__(self, bus, ex, policy, check_interval: float = 300.0):
        """
        Initialize system verifier.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            check_interval: Seconds between full system checks (default: 5 min)
        """
        super().__init__(bus, ex, policy)
        self.check_interval = check_interval
        self._verification_task: Optional[asyncio.Task] = None
        self._checks = []
        self._results_history: List[VerificationResult] = []
        self._last_check_time = 0.0
        
        # Register default checks
        self._register_default_checks()
    
    async def start(self) -> None:
        """Start verification loop"""
        await super().start()
        
        # Subscribe to events
        await self.bus.subscribe("verifier/check", self._handle_check_request)
        await self.bus.subscribe("verifier/register_check", self._handle_register_check)
        
        # Start verification loop
        self._verification_task = asyncio.create_task(self._verification_loop())
        self.log.info("System verifier started")
    
    async def stop(self) -> None:
        """Stop verification loop"""
        if self._verification_task:
            self._verification_task.cancel()
            try:
                await self._verification_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("System verifier stopped")
    
    def _register_default_checks(self) -> None:
        """Register default health checks"""
        self._checks = [
            ('memory_usage', self._check_memory_usage),
            ('disk_space', self._check_disk_space),
            ('cpu_usage', self._check_cpu_usage),
            ('file_handles', self._check_file_handles),
            ('event_bus_health', self._check_event_bus),
        ]
    
    async def _verification_loop(self) -> None:
        """Periodic verification loop"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Run full system check
                results = await self._run_full_verification()
                
                # Calculate overall health score
                overall_health = self._calculate_overall_health(results)
                
                # Emit results
                await self.emit("verifier/result", {
                    "checks_completed": len(results),
                    "checks_passed": len([r for r in results if r.passed]),
                    "overall_health": overall_health,
                    "issues": self._collect_all_issues(results),
                    "recommendations": self._collect_all_recommendations(results),
                    "timestamp": time.time()
                })
                
                # Emit alerts for critical issues
                critical_results = [r for r in results if r.severity == 'critical' and not r.passed]
                for result in critical_results:
                    await self.emit("verifier/alert", {
                        "check": result.check_name,
                        "issues": result.issues,
                        "severity": result.severity,
                        "timestamp": result.timestamp
                    })
                
                self._last_check_time = time.time()
                
            except Exception as e:
                self.log.error(f"Verification loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _handle_check_request(self, msg: Message) -> None:
        """Handle manual verification request"""
        try:
            check_type = msg.data.get('check_type', 'full')
            
            if check_type == 'full':
                results = await self._run_full_verification()
            else:
                # Run specific check
                results = []
                for check_name, check_fn in self._checks:
                    if check_name == check_type:
                        result = await check_fn()
                        results.append(result)
                        break
            
            # Emit results
            overall_health = self._calculate_overall_health(results)
            
            await self.emit("verifier/result", {
                "request_id": msg.data.get('request_id'),
                "check_type": check_type,
                "overall_health": overall_health,
                "results": [self._result_to_dict(r) for r in results]
            })
            
        except Exception as e:
            self.log.error(f"Error handling check request: {e}")
    
    async def _handle_register_check(self, msg: Message) -> None:
        """Handle custom check registration"""
        try:
            check_name = msg.data.get('name')
            # In a real implementation, this would accept a callable
            # For now, just acknowledge
            self.log.info(f"Custom check registration request: {check_name}")
            
        except Exception as e:
            self.log.error(f"Error handling register check: {e}")
    
    async def _run_full_verification(self) -> List[VerificationResult]:
        """Run all verification checks"""
        results = []
        
        for check_name, check_fn in self._checks:
            try:
                result = await check_fn()
                results.append(result)
                
                # Store in history
                self._results_history.append(result)
                
                # Keep history size manageable
                if len(self._results_history) > 1000:
                    self._results_history = self._results_history[-500:]
                
            except Exception as e:
                self.log.error(f"Check {check_name} failed: {e}")
                results.append(VerificationResult(
                    check_name=check_name,
                    passed=False,
                    severity='high',
                    issues=[f"Check execution failed: {str(e)}"],
                    recommendations=["Investigate check implementation"],
                    health_score=0.0,
                    timestamp=time.time()
                ))
        
        return results
    
    async def _check_memory_usage(self) -> VerificationResult:
        """Check system memory usage"""
        try:
            mem = psutil.virtual_memory()
            issues = []
            recommendations = []
            
            if mem.percent > 90:
                issues.append(f"Critical memory usage: {mem.percent:.1f}%")
                recommendations.append("Immediate memory cleanup required")
                severity = 'critical'
                health_score = 10.0
            elif mem.percent > 85:
                issues.append(f"High memory usage: {mem.percent:.1f}%")
                recommendations.append("Consider memory cleanup or scaling")
                severity = 'high'
                health_score = 40.0
            elif mem.percent > 75:
                issues.append(f"Elevated memory usage: {mem.percent:.1f}%")
                recommendations.append("Monitor memory trends")
                severity = 'medium'
                health_score = 70.0
            else:
                severity = 'low'
                health_score = 100.0 - mem.percent
            
            return VerificationResult(
                check_name='memory_usage',
                passed=mem.percent < 85,
                severity=severity,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.log.error(f"Memory check error: {e}")
            return self._error_result('memory_usage', str(e))
    
    async def _check_disk_space(self) -> VerificationResult:
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_pct = (disk.free / disk.total) * 100
            issues = []
            recommendations = []
            
            if free_pct < 10:
                issues.append(f"Critical: Only {free_pct:.1f}% disk space remaining")
                recommendations.append("Urgent: Free up disk space immediately")
                severity = 'critical'
                health_score = 10.0
            elif free_pct < 20:
                issues.append(f"Low disk space: {free_pct:.1f}% remaining")
                recommendations.append("Clean up logs, temporary files, or archives")
                severity = 'high'
                health_score = 50.0
            elif free_pct < 30:
                issues.append(f"Disk space getting low: {free_pct:.1f}% remaining")
                recommendations.append("Plan for disk cleanup soon")
                severity = 'medium'
                health_score = 75.0
            else:
                severity = 'low'
                health_score = min(100.0, free_pct)
            
            return VerificationResult(
                check_name='disk_space',
                passed=free_pct >= 20,
                severity=severity,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.log.error(f"Disk check error: {e}")
            return self._error_result('disk_space', str(e))
    
    async def _check_cpu_usage(self) -> VerificationResult:
        """Check CPU usage patterns"""
        try:
            # Get CPU usage over 1 second interval
            cpu_pct = psutil.cpu_percent(interval=1.0)
            issues = []
            recommendations = []
            
            if cpu_pct > 95:
                issues.append(f"Critical CPU usage: {cpu_pct:.1f}%")
                recommendations.append("System may be overloaded - consider scaling")
                severity = 'critical'
                health_score = 5.0
            elif cpu_pct > 85:
                issues.append(f"High CPU usage: {cpu_pct:.1f}%")
                recommendations.append("Monitor for sustained high CPU usage")
                severity = 'high'
                health_score = 30.0
            elif cpu_pct > 70:
                issues.append(f"Elevated CPU usage: {cpu_pct:.1f}%")
                recommendations.append("Normal under load, but monitor trends")
                severity = 'medium'
                health_score = 60.0
            else:
                severity = 'low'
                health_score = 100.0 - cpu_pct
            
            return VerificationResult(
                check_name='cpu_usage',
                passed=cpu_pct < 85,
                severity=severity,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.log.error(f"CPU check error: {e}")
            return self._error_result('cpu_usage', str(e))
    
    async def _check_file_handles(self) -> VerificationResult:
        """Check file handle usage"""
        try:
            process = psutil.Process()
            num_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
            
            # Typical limit is 1024 or 4096
            issues = []
            recommendations = []
            
            if num_fds > 800:
                issues.append(f"High file descriptor usage: {num_fds}")
                recommendations.append("Check for file descriptor leaks")
                severity = 'high'
                health_score = 40.0
            elif num_fds > 500:
                issues.append(f"Moderate file descriptor usage: {num_fds}")
                recommendations.append("Monitor file handle usage")
                severity = 'medium'
                health_score = 70.0
            else:
                severity = 'low'
                health_score = 100.0
            
            return VerificationResult(
                check_name='file_handles',
                passed=num_fds < 800,
                severity=severity,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.log.error(f"File handles check error: {e}")
            return self._error_result('file_handles', str(e))
    
    async def _check_event_bus(self) -> VerificationResult:
        """Check event bus health"""
        try:
            # Get bus statistics
            bus_stats = self.bus.get_stats()
            
            messages_published = bus_stats.get('messages_published', 0)
            messages_delivered = bus_stats.get('messages_delivered', 0)
            
            issues = []
            recommendations = []
            
            # Check delivery rate
            if messages_published > 0:
                delivery_rate = messages_delivered / messages_published
                
                if delivery_rate < 0.8:
                    issues.append(f"Low message delivery rate: {delivery_rate:.1%}")
                    recommendations.append("Investigate subscriber health")
                    severity = 'medium'
                    health_score = delivery_rate * 100
                else:
                    severity = 'low'
                    health_score = 100.0
            else:
                severity = 'low'
                health_score = 100.0
            
            return VerificationResult(
                check_name='event_bus_health',
                passed=True,
                severity=severity,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.log.error(f"Event bus check error: {e}")
            return self._error_result('event_bus_health', str(e))
    
    def _calculate_overall_health(self, results: List[VerificationResult]) -> float:
        """Calculate overall system health score"""
        if not results:
            return 100.0
        
        # Weight by severity
        weights = {'critical': 0.4, 'high': 0.3, 'medium': 0.2, 'low': 0.1}
        total_weight = 0.0
        weighted_sum = 0.0
        
        for result in results:
            weight = weights.get(result.severity, 0.1)
            total_weight += weight
            weighted_sum += result.health_score * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 100.0
    
    def _collect_all_issues(self, results: List[VerificationResult]) -> List[str]:
        """Collect all issues from results"""
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        return all_issues
    
    def _collect_all_recommendations(self, results: List[VerificationResult]) -> List[str]:
        """Collect all recommendations from results"""
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        return all_recommendations
    
    def _error_result(self, check_name: str, error: str) -> VerificationResult:
        """Create error result for failed check"""
        return VerificationResult(
            check_name=check_name,
            passed=False,
            severity='high',
            issues=[f"Check failed: {error}"],
            recommendations=["Investigate check implementation"],
            health_score=0.0,
            timestamp=time.time()
        )
    
    def _result_to_dict(self, result: VerificationResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'check_name': result.check_name,
            'passed': result.passed,
            'severity': result.severity,
            'issues': result.issues,
            'recommendations': result.recommendations,
            'health_score': result.health_score,
            'timestamp': result.timestamp
        }
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        if msg.topic == "verifier/check":
            await self._handle_check_request(msg)
        elif msg.topic == "verifier/register_check":
            await self._handle_register_check(msg)
    
    def get_stats(self) -> dict:
        """Get verifier statistics"""
        stats = super().get_stats()
        
        recent_results = self._results_history[-10:] if self._results_history else []
        
        stats.update({
            "total_checks": len(self._checks),
            "results_history_count": len(self._results_history),
            "last_check_time": self._last_check_time,
            "recent_health_scores": [r.health_score for r in recent_results],
            "recent_average_health": sum(r.health_score for r in recent_results) / len(recent_results) if recent_results else 100.0
        })
        return stats
