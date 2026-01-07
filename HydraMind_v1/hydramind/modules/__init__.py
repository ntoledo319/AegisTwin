"""
HydraMind Modules - Intelligence and Domain Modules

This package contains all HydraMind modules for cognitive operations,
optimization, pattern recognition, and autonomous agent coordination.
"""

from typing import List

# Intelligence/Cognitive modules
from .intelligence.self_optimizer import SelfOptimizer
from .intelligence.system_verifier import SystemVerifier
from .intelligence.data_collector import DataCollector
from .intelligence.pattern_learner import PatternLearner
from .intelligence.swarm_coordinator import SwarmCoordinator
from .intelligence.predictive_engine import PredictiveEngine
from .intelligence.online_learner import OnlineLearner

# Specialized optimization modules
from .intelligence.seed_optimizer import SeedOptimizer
from .intelligence.anomaly_lab import AnomalyLab
from .intelligence.meta_planner import MetaPlanner
from .intelligence.optimizer_suite import OptimizerSuite
from .intelligence.replay_service import ReplayService

# Domain-specific modules
from .domain.domain_examples import DroneFleet, RoboticsCell, TradingEngine, DBAnalyzer

# Infrastructure modules
from .infrastructure.sensors import SensorHub


__all__ = [
    # Core cognitive modules - SEED-inspired
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

    # Domain-specific
    'DroneFleet',
    'RoboticsCell',
    'TradingEngine',
    'DBAnalyzer',

    # Infrastructure
    'SensorHub',
]


# Module categories for easy reference
COGNITIVE_MODULES = [
    'SelfOptimizer',
    'SystemVerifier',
    'DataCollector',
    'PatternLearner',
    'SwarmCoordinator',
    'PredictiveEngine',
    'OnlineLearner',
]

OPTIMIZATION_MODULES = [
    'SeedOptimizer',
    'OptimizerSuite',
    'AnomalyLab',
]

COORDINATION_MODULES = [
    'SwarmCoordinator',
    'MetaPlanner',
]

ANALYSIS_MODULES = [
    'DBAnalyzer',
    'PatternLearner',
    'PredictiveEngine',
]

DOMAIN_MODULES = [
    'DroneFleet',
    'RoboticsCell',
    'TradingEngine',
]

INFRASTRUCTURE_MODULES = [
    'SensorHub',
]


def get_available_modules() -> List[str]:
    """Get list of all available modules"""
    return __all__


def get_modules_by_category(category: str) -> List[str]:
    """
    Get modules by category.
    
    Args:
        category: One of 'cognitive', 'optimization', 'coordination', 'analysis', 'domain', 'infrastructure'
        
    Returns:
        List of module names in that category
    """
    categories = {
        'cognitive': COGNITIVE_MODULES,
        'optimization': OPTIMIZATION_MODULES,
        'coordination': COORDINATION_MODULES,
        'analysis': ANALYSIS_MODULES,
        'domain': DOMAIN_MODULES,
        'infrastructure': INFRASTRUCTURE_MODULES,
    }
    
    return categories.get(category.lower(), [])
