#!/usr/bin/env python3
"""
Final System Validation for Cognitive-Twin

Comprehensive validation of all system components with graceful handling
of missing dependencies and configuration issues.
"""

import asyncio
import logging
import sys
import os
import importlib
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "integrated_system"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Comprehensive system validation with graceful error handling"""
    
    def __init__(self):
        self.results = {}
        self.passed_tests = 0
        self.failed_tests = 0
        self.warning_tests = 0
        self.total_tests = 0
        
    def status_icon(self, status: str) -> str:
        """Get status icon"""
        icons = {
            "PASS": "✅",
            "FAIL": "❌", 
            "WARN": "⚠️",
            "INFO": "ℹ️"
        }
        return icons.get(status, "❓")
    
    def test_result(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        """Record test result"""
        self.total_tests += 1
        
        if status == "PASS":
            self.passed_tests += 1
        elif status == "WARN":
            self.warning_tests += 1
        else:
            self.failed_tests += 1
            
        self.results[name] = {
            "status": status,
            "message": message,
            "details": details or {}
        }
        
        icon = self.status_icon(status)
        logger.info(f"{icon} {name}: {message}")
    
    def check_import(self, module_name: str, optional: bool = False) -> Tuple[bool, str]:
        """Check if a module can be imported"""
        try:
            importlib.import_module(module_name)
            return True, f"Module '{module_name}' imported successfully"
        except ImportError as e:
            if optional:
                return False, f"Optional module '{module_name}' not available: {str(e)}"
            else:
                return False, f"Required module '{module_name}' not available: {str(e)}"
    
    def check_file_exists(self, file_path: str) -> Tuple[bool, str]:
        """Check if a file exists"""
        path = Path(file_path)
        if path.exists():
            return True, f"File exists: {file_path}"
        else:
            return False, f"File missing: {file_path}"
    
    def check_directory_structure(self):
        """Check project directory structure"""
        logger.info("🔍 Checking Project Structure")
        
        required_paths = [
            "src/cognitive_twin",
            "integrated_system",
            "ct_modules",
            "ct_omega",
            "advanced-data-analysis-twin"
        ]
        
        missing_paths = []
        existing_paths = []
        
        for path in required_paths:
            if Path(path).exists():
                existing_paths.append(path)
            else:
                missing_paths.append(path)
        
        if not missing_paths:
            self.test_result("project_structure", "PASS", "All required directories present")
        else:
            self.test_result("project_structure", "WARN", 
                           f"Missing directories: {missing_paths}",
                           {"missing": missing_paths, "existing": existing_paths})
    
    def check_core_modules(self):
        """Check core module imports"""
        logger.info("🔍 Checking Core Modules")
        
        core_modules = [
            ("cognitive_twin", False),
            ("cognitive_twin.config.settings", False),
            ("cognitive_twin.ai.openrouter_client", False),
            ("cognitive_twin.ai.conversation_ai", False),
            ("cognitive_twin.ai.personality_ai", False),
            ("cognitive_twin.memory.memory_manager", False),
            ("cognitive_twin.events.event_bus", False),
            ("cognitive_twin.realtime.websocket_manager", False),
            ("cognitive_twin.health.health_checker", False),
            ("integrated_system.main", False)
        ]
        
        importable = []
        failed = []
        
        for module, optional in core_modules:
            success, message = self.check_import(module, optional)
            if success:
                importable.append(module)
            else:
                failed.append((module, message))
        
        if len(failed) == 0:
            self.test_result("core_modules", "PASS", "All core modules importable")
        elif len(failed) <= 2:
            self.test_result("core_modules", "WARN", 
                           f"Some modules failed: {[f[0] for f in failed]}",
                           {"importable": importable, "failed": failed})
        else:
            self.test_result("core_modules", "FAIL", 
                           f"Many modules failed: {[f[0] for f in failed]}",
                           {"importable": importable, "failed": failed})
    
    def check_dependencies(self):
        """Check critical dependencies"""
        logger.info("🔍 Checking Dependencies")
        
        dependencies = [
            ("fastapi", False),
            ("uvicorn", False),
            ("pydantic", False),
            ("sqlalchemy", False),
            ("asyncpg", True),
            ("redis", True),
            ("motor", True),
            ("chromadb", True),
            ("psutil", True),
            ("websockets", True),
            ("aiohttp", True),
            ("httpx", True)
        ]
        
        available = []
        missing_required = []
        missing_optional = []
        
        for dep, optional in dependencies:
            success, message = self.check_import(dep, optional)
            if success:
                available.append(dep)
            else:
                if optional:
                    missing_optional.append(dep)
                else:
                    missing_required.append(dep)
        
        if not missing_required:
            if not missing_optional:
                self.test_result("dependencies", "PASS", "All dependencies available")
            else:
                self.test_result("dependencies", "WARN", 
                               f"Optional dependencies missing: {missing_optional}",
                               {"available": available, "missing_optional": missing_optional})
        else:
            self.test_result("dependencies", "FAIL", 
                           f"Required dependencies missing: {missing_required}",
                           {"available": available, "missing_required": missing_required, "missing_optional": missing_optional})
    
    def check_configuration(self):
        """Check configuration system"""
        logger.info("🔍 Checking Configuration")
        
        try:
            from cognitive_twin.config.settings import Settings, get_settings
            
            # Try to create settings instance
            settings = Settings()
            
            # Check critical configuration
            config_issues = []
            
            if not hasattr(settings, 'openrouter_api_key') or not settings.openrouter_api_key:
                config_issues.append("OpenRouter API key not configured")
            
            # Validate configuration
            try:
                validation_issues = settings.validate_configuration()
                config_issues.extend(validation_issues)
            except Exception as e:
                config_issues.append(f"Configuration validation failed: {str(e)}")
            
            if not config_issues:
                self.test_result("configuration", "PASS", "Configuration system working")
            else:
                self.test_result("configuration", "WARN", 
                               f"Configuration issues: {config_issues}",
                               {"issues": config_issues})
                
        except Exception as e:
            self.test_result("configuration", "FAIL", 
                           f"Configuration system failed: {str(e)}",
                           {"error": str(e), "traceback": traceback.format_exc()})
    
    def check_ai_system(self):
        """Check AI system"""
        logger.info("🔍 Checking AI System")
        
        try:
            from cognitive_twin.ai.openrouter_client import OpenRouterClient
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.ai.personality_ai import PersonalityAI
            
            # Try to initialize AI components
            client = OpenRouterClient()
            conversation_ai = ConversationAI()
            personality_ai = PersonalityAI()
            
            if not client.api_key:
                self.test_result("ai_system", "WARN", 
                               "AI system ready but missing API key",
                               {"api_key_configured": False})
            else:
                self.test_result("ai_system", "PASS", "AI system fully configured")
                
        except Exception as e:
            self.test_result("ai_system", "FAIL", 
                           f"AI system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_memory_system(self):
        """Check memory system"""
        logger.info("🔍 Checking Memory System")
        
        try:
            from cognitive_twin.memory.memory_manager import MemoryManager
            from cognitive_twin.memory.vector_memory import VectorMemory
            
            # Try to initialize memory components
            memory_manager = MemoryManager()
            
            # Check ChromaDB availability
            try:
                vector_memory = VectorMemory()
                chroma_available = True
            except Exception:
                chroma_available = False
            
            if chroma_available:
                self.test_result("memory_system", "PASS", "Memory system fully functional")
            else:
                self.test_result("memory_system", "WARN", 
                               "Memory system ready but ChromaDB not available",
                               {"chromadb_available": False})
                
        except Exception as e:
            self.test_result("memory_system", "FAIL", 
                           f"Memory system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_event_system(self):
        """Check event system"""
        logger.info("🔍 Checking Event System")
        
        try:
            from cognitive_twin.events.event_bus import EventBus
            from cognitive_twin.events.service_coordinator import ServiceCoordinator
            
            # Try to initialize event components
            event_bus = EventBus()
            coordinator = ServiceCoordinator()
            
            # Check Redis availability
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                redis_available = True
            except Exception:
                redis_available = False
            
            if redis_available:
                self.test_result("event_system", "PASS", "Event system fully functional")
            else:
                self.test_result("event_system", "WARN", 
                               "Event system ready but Redis not available",
                               {"redis_available": False})
                
        except Exception as e:
            self.test_result("event_system", "FAIL", 
                           f"Event system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_realtime_system(self):
        """Check real-time system"""
        logger.info("🔍 Checking Real-time System")
        
        try:
            from cognitive_twin.realtime.websocket_manager import WebSocketManager
            from cognitive_twin.realtime.live_conversation import LiveConversation
            from cognitive_twin.realtime.realtime_updates import RealtimeUpdates
            
            # Try to initialize real-time components
            websocket_manager = WebSocketManager()
            live_conversation = LiveConversation()
            realtime_updates = RealtimeUpdates()
            
            self.test_result("realtime_system", "PASS", "Real-time system ready")
                
        except Exception as e:
            self.test_result("realtime_system", "FAIL", 
                           f"Real-time system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_health_system(self):
        """Check health monitoring system"""
        logger.info("🔍 Checking Health System")
        
        try:
            from cognitive_twin.health.health_checker import HealthChecker
            from cognitive_twin.health.system_monitor import SystemMonitor
            from cognitive_twin.health.diagnostics import HealthDiagnostics
            
            # Try to initialize health components
            health_checker = HealthChecker()
            system_monitor = SystemMonitor()
            diagnostics = HealthDiagnostics()
            
            self.test_result("health_system", "PASS", "Health monitoring system ready")
                
        except Exception as e:
            self.test_result("health_system", "FAIL", 
                           f"Health system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_api_system(self):
        """Check API system"""
        logger.info("🔍 Checking API System")
        
        try:
            from integrated_system.api.endpoints.digital_twin import router as digital_twin_router
            from integrated_system.main import app
            
            # Check if API components are importable
            self.test_result("api_system", "PASS", "API system ready")
                
        except Exception as e:
            self.test_result("api_system", "FAIL", 
                           f"API system failed: {str(e)}",
                           {"error": str(e)})
    
    def check_data_processing(self):
        """Check data processing system"""
        logger.info("🔍 Checking Data Processing")
        
        try:
            from integrated_system.data_processing.connectors.email import EmailConnector
            from integrated_system.data_processing.core.pipeline import DataPipeline
            
            # Try to initialize data processing components
            email_connector = EmailConnector()
            pipeline = DataPipeline()
            
            self.test_result("data_processing", "PASS", "Data processing system ready")
                
        except Exception as e:
            self.test_result("data_processing", "FAIL", 
                           f"Data processing failed: {str(e)}",
                           {"error": str(e)})
    
    def check_digital_twin(self):
        """Check digital twin system"""
        logger.info("🔍 Checking Digital Twin System")
        
        try:
            from integrated_system.digital_twin.conversation.engine import ConversationEngine
            from integrated_system.digital_twin.personality.engine import PersonalityEngine
            from integrated_system.digital_twin.core.twin import CognitiveTwin
            
            # Try to initialize digital twin components
            conversation_engine = ConversationEngine()
            personality_engine = PersonalityEngine()
            
            self.test_result("digital_twin", "PASS", "Digital twin system ready")
                
        except Exception as e:
            self.test_result("digital_twin", "FAIL", 
                           f"Digital twin failed: {str(e)}",
                           {"error": str(e)})
    
    def check_advanced_features(self):
        """Check advanced features"""
        logger.info("🔍 Checking Advanced Features")
        
        advanced_systems = {
            "CT-Modules": "ct_modules",
            "CT-Omega": "ct_omega", 
            "Advanced Analytics": "advanced-data-analysis-twin"
        }
        
        available_systems = []
        missing_systems = []
        
        for name, path in advanced_systems.items():
            if Path(path).exists():
                available_systems.append(name)
            else:
                missing_systems.append(name)
        
        if len(available_systems) == len(advanced_systems):
            self.test_result("advanced_features", "PASS", "All advanced features available")
        elif available_systems:
            self.test_result("advanced_features", "WARN", 
                           f"Some advanced features available: {available_systems}",
                           {"available": available_systems, "missing": missing_systems})
        else:
            self.test_result("advanced_features", "FAIL", 
                           "No advanced features found",
                           {"missing": missing_systems})
    
    async def run_full_validation(self):
        """Run complete system validation"""
        logger.info("🚀 Starting Cognitive-Twin Full System Validation")
        logger.info("=" * 60)
        
        # Run all validation checks
        self.check_directory_structure()
        self.check_core_modules()
        self.check_dependencies()
        self.check_configuration()
        self.check_ai_system()
        self.check_memory_system()
        self.check_event_system()
        self.check_realtime_system()
        self.check_health_system()
        self.check_api_system()
        self.check_data_processing()
        self.check_digital_twin()
        self.check_advanced_features()
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("🧪 COGNITIVE-TWIN SYSTEM VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        # Overall statistics
        logger.info(f"Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"⚠️  Warnings: {self.warning_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        
        # Calculate completion percentage
        functional_score = self.passed_tests * 1.0 + self.warning_tests * 0.6
        completion_percentage = (functional_score / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        logger.info(f"🎯 Functional Completion: {completion_percentage:.1f}%")
        
        # Detailed results
        logger.info("")
        logger.info("📋 Detailed Results:")
        for name, result in self.results.items():
            icon = self.status_icon(result["status"])
            logger.info(f"   {icon} {name.replace('_', ' ').title()}: {result['message']}")
        
        # Recommendations
        logger.info("")
        logger.info("🔧 Recommendations:")
        
        recommendations = []
        
        if self.failed_tests > 0:
            recommendations.append("Fix critical failures before deployment")
        
        # Check specific issues
        for name, result in self.results.items():
            if result["status"] == "WARN":
                if "api_key" in result["message"].lower():
                    recommendations.append("Configure API keys (OPENROUTER_API_KEY)")
                if "chromadb" in result["message"].lower():
                    recommendations.append("Install ChromaDB: pip install chromadb")
                if "redis" in result["message"].lower():
                    recommendations.append("Install and configure Redis")
                if "missing" in result["message"].lower():
                    recommendations.append("Install missing dependencies: pip install -r requirements.txt")
        
        if not recommendations:
            recommendations.append("System appears ready for production!")
        
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"   {i}. {rec}")
        
        # Final assessment
        logger.info("")
        if completion_percentage >= 90:
            logger.info("🎉 SYSTEM STATUS: EXCELLENT - Ready for production!")
        elif completion_percentage >= 70:
            logger.info("✅ SYSTEM STATUS: GOOD - Minor configuration needed")
        elif completion_percentage >= 50:
            logger.info("⚠️  SYSTEM STATUS: PARTIAL - Significant work needed")
        else:
            logger.info("❌ SYSTEM STATUS: POOR - Major issues need resolution")
        
        logger.info("=" * 60)
        
        return {
            "completion_percentage": completion_percentage,
            "passed": self.passed_tests,
            "warnings": self.warning_tests,
            "failed": self.failed_tests,
            "total": self.total_tests,
            "recommendations": recommendations,
            "results": self.results
        }

async def main():
    """Main validation function"""
    validator = SystemValidator()
    return await validator.run_full_validation()

if __name__ == "__main__":
    asyncio.run(main())
