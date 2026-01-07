"""
HydraMind Intelligence Modules

This package contains cognitive and learning modules for intelligent
system behavior, pattern recognition, and autonomous optimization.
"""

# Core cognitive modules - SEED-inspired
from .self_optimizer import SelfOptimizer
from .system_verifier import SystemVerifier
from .data_collector import DataCollector
from .pattern_learner import PatternLearner
from .swarm_coordinator import SwarmCoordinator
from .predictive_engine import PredictiveEngine
from .online_learner import OnlineLearner

# Specialized optimization modules
from .seed_optimizer import SeedOptimizer
from .anomaly_lab import AnomalyLab
from .meta_planner import MetaPlanner
from .optimizer_suite import OptimizerSuite
from .replay_service import ReplayService

__all__ = [
    # Core cognitive modules
    'SelfOptimizer',
    'SystemVerifier',
    'DataCollector',
    'PatternLearner',
    'SwarmCoordinator',
    'PredictiveEngine',
    'OnlineLearner',

    # Specialized optimization
    'SeedOptimizer',
    'AnomalyLab',
    'MetaPlanner',
    'OptimizerSuite',
    'ReplayService',
]
