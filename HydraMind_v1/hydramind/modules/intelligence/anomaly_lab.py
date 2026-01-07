"""
Real-time anomaly detection using EWMA and Z-score analysis.

Automatically detects unusual patterns in telemetry streams without
requiring training data or configuration.
"""

from __future__ import annotations
import numpy as np
import time
from collections import deque
from typing import Dict, Tuple
from ...core.module import Module
from ...core.bus import Message


class EWMA:
    """
    Exponentially Weighted Moving Average.
    
    Tracks the smoothed average of a signal, giving more weight to recent values.
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize EWMA.
        
        Args:
            alpha: Smoothing factor (0-1, higher = more weight to recent)
        """
        self.alpha = alpha
        self.mean: float | None = None
    
    def update(self, x: float) -> float:
        """
        Update EWMA with new value.
        
        Args:
            x: New value
            
        Returns:
            Updated mean
        """
        if self.mean is None:
            self.mean = x
        else:
            self.mean = self.alpha * x + (1 - self.alpha) * self.mean
        
        return self.mean
    
    def reset(self) -> None:
        """Reset EWMA."""
        self.mean = None


class ZScoreDetector:
    """
    Z-score based anomaly detector.
    
    Maintains a sliding window of values and flags outliers based on
    standard deviations from the mean.
    """
    
    def __init__(self, window: int = 200, threshold: float = 3.0):
        """
        Initialize Z-score detector.
        
        Args:
            window: Size of sliding window
            threshold: Number of standard deviations for anomaly
        """
        self.window = window
        self.buffer = deque(maxlen=window)
        self.threshold = threshold
        self._anomaly_count = 0
    
    def update(self, x: float) -> Tuple[bool, float]:
        """
        Update detector with new value.
        
        Args:
            x: New value
            
        Returns:
            Tuple of (is_anomaly, z_score)
        """
        self.buffer.append(x)
        
        # Need minimum samples for statistics
        if len(self.buffer) < 30:
            return False, 0.0
        
        # Calculate Z-score
        arr = np.array(self.buffer)
        mu = arr.mean()
        sd = arr.std() + 1e-9  # Avoid division by zero
        z = abs((x - mu) / sd)
        
        is_anomaly = z > self.threshold
        
        if is_anomaly:
            self._anomaly_count += 1
        
        return is_anomaly, z
    
    def reset(self) -> None:
        """Reset detector."""
        self.buffer.clear()
        self._anomaly_count = 0


class AnomalyLab(Module):
    """
    Real-time anomaly detection for system telemetry.
    
    Monitors telemetry streams and automatically detects anomalies using:
    - EWMA for trend tracking
    - Z-score for statistical outlier detection
    
    Inspired by SONAR's detection and reporting patterns.
    
    Protocol:
        Input events:
            - telemetry/host: System telemetry (cpu, mem, etc)
            - telemetry/custom: Custom metric streams
        
        Output events:
            - anomaly/cpu: CPU anomaly detected
            - anomaly/mem: Memory anomaly detected
            - anomaly/<metric>: Custom metric anomaly
    
    Example:
        # Telemetry automatically monitored
        await bus.publish(Message("telemetry/host", {
            "cpu": 95.2,
            "mem": 87.3,
            "ts": time.time()
        }))
        
        # Anomaly emitted if detected
        # -> anomaly/cpu: {"ts": ..., "value": 95.2, "z": 4.2, "mean": 35.0}
    """
    
    name = "anomaly"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        ema_alpha: float = 0.2,
        z_window: int = 200,
        z_threshold: float = 3.0
    ):
        """
        Initialize anomaly lab.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            ema_alpha: EWMA smoothing factor
            z_window: Z-score window size
            z_threshold: Z-score threshold for anomaly
        """
        super().__init__(bus, ex, policy)
        
        self.ema_alpha = ema_alpha
        self.z_window = z_window
        self.z_threshold = z_threshold
        
        # Separate detectors per metric
        self.ewma: Dict[str, EWMA] = {}
        self.zscore: Dict[str, ZScoreDetector] = {}
        
        self._anomalies_detected = 0
        
        self.log.info(
            f"AnomalyLab initialized: alpha={ema_alpha}, "
            f"window={z_window}, threshold={z_threshold}"
        )
    
    def _get_detectors(self, metric: str) -> Tuple[EWMA, ZScoreDetector]:
        """Get or create detectors for metric."""
        if metric not in self.ewma:
            self.ewma[metric] = EWMA(self.ema_alpha)
            self.zscore[metric] = ZScoreDetector(self.z_window, self.z_threshold)
            self.log.debug(f"Created detectors for metric '{metric}'")
        
        return self.ewma[metric], self.zscore[metric]
    
    async def on_message(self, msg: Message) -> None:
        """Handle telemetry events."""
        
        if msg.topic == "telemetry/host":
            await self._handle_host_telemetry(msg)
        
        elif msg.topic.startswith("telemetry/"):
            await self._handle_custom_telemetry(msg)
    
    async def _handle_host_telemetry(self, msg: Message) -> None:
        """Handle system telemetry."""
        cpu = msg.data.get("cpu")
        mem = msg.data.get("mem")
        ts = msg.data.get("ts", time.time())
        
        # Check CPU
        if cpu is not None:
            await self._check_metric("cpu", float(cpu), ts)
        
        # Check memory
        if mem is not None:
            await self._check_metric("mem", float(mem), ts)
    
    async def _handle_custom_telemetry(self, msg: Message) -> None:
        """Handle custom telemetry metrics."""
        # Extract metric name from topic
        metric = msg.topic.split("/", 1)[1] if "/" in msg.topic else "unknown"
        
        # Check all numeric values in data
        for key, value in msg.data.items():
            if isinstance(value, (int, float)) and key != "ts":
                full_metric = f"{metric}/{key}"
                ts = msg.data.get("ts", time.time())
                await self._check_metric(full_metric, float(value), ts)
    
    async def _check_metric(
        self,
        metric: str,
        value: float,
        ts: float
    ) -> None:
        """
        Check metric for anomalies.
        
        Args:
            metric: Metric name
            value: Metric value
            ts: Timestamp
        """
        try:
            ewma, zscore = self._get_detectors(metric)
            
            # Update EWMA
            mean = ewma.update(value)
            
            # Update Z-score detector
            is_anomaly, z = zscore.update(value)
            
            if is_anomaly:
                self._anomalies_detected += 1
                
                self.log.warning(
                    f"Anomaly detected in '{metric}': "
                    f"value={value:.2f}, z={z:.2f}, mean={mean:.2f}"
                )
                
                await self.emit(f"anomaly/{metric}", {
                    "ts": ts,
                    "value": value,
                    "z": z,
                    "mean": mean,
                    "metric": metric
                })
        
        except Exception as e:
            self.log.error(f"Error checking metric '{metric}': {e}")
    
    async def reset_metric(self, metric: str) -> None:
        """
        Reset detectors for a metric.
        
        Args:
            metric: Metric name (or "*" for all)
        """
        if metric == "*":
            for m in list(self.ewma.keys()):
                self.ewma[m].reset()
                self.zscore[m].reset()
            self.log.info("Reset all anomaly detectors")
        
        elif metric in self.ewma:
            self.ewma[metric].reset()
            self.zscore[metric].reset()
            self.log.info(f"Reset detector for '{metric}'")
    
    def get_stats(self) -> dict:
        """Get anomaly detection statistics."""
        stats = super().get_stats()
        
        detector_stats = {}
        for metric, detector in self.zscore.items():
            detector_stats[metric] = {
                "buffer_size": len(detector.buffer),
                "anomalies": detector._anomaly_count
            }
        
        stats.update({
            "ema_alpha": self.ema_alpha,
            "z_window": self.z_window,
            "z_threshold": self.z_threshold,
            "metrics_tracked": len(self.ewma),
            "total_anomalies": self._anomalies_detected,
            "detectors": detector_stats
        })
        
        return stats
