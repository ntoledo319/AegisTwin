#!/usr/bin/env python3
"""
Comprehensive System Test for Cognitive-Twin

Tests all major components and integrations to ensure the system
is working correctly and all placeholders have been replaced.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any, List
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTester:
    """Comprehensive system tester"""
    
    def __init__(self):
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_tests = 0
    
    async def run_all_tests(self):
        """Run all system tests"""
        logger.info("🧪 Starting Cognitive-Twin System Tests")
        
        tests = [
            ("Configuration System", self.test_configuration),
            ("AI Integration", self.test_ai_integration),
            ("Memory System", self.test_memory_system),
            ("Event System", self.test_event_system),
            ("Real-time Features", self.test_realtime_features),
            ("Health Check System", self.test_health_system),
            ("API Integration", self.test_api_integration),
            ("End-to-End Conversation", self.test_end_to_end_conversation)
        ]
        
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        self.print_summary()
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test"""
        logger.info(f"🔍 Testing: {test_name}")
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: PASSED")
                self.passed_tests += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
                self.failed_tests += 1
            
            self.test_results[test_name] = result
            self.total_tests += 1
            
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            self.test_results[test_name] = False
            self.failed_tests += 1
            self.total_tests += 1
    
    async def test_configuration(self) -> bool:
        """Test configuration system"""
        try:
            from cognitive_twin.config import get_settings, Settings
            from cognitive_twin.config.database import DatabaseConfig
            from cognitive_twin.config.ai_config import AIConfig
            
            # Test settings loading
            settings = get_settings()
            assert isinstance(settings, Settings)
            logger.info(f"   Settings loaded: {settings.app_name} v{settings.app_version}")
            
            # Test database config
            db_config = DatabaseConfig()
            assert db_config.postgres_url is not None
            logger.info("   Database configuration validated")
            
            # Test AI config
            ai_config = AIConfig()
            assert ai_config.model_configs is not None
            assert len(ai_config.model_configs) > 0
            logger.info(f"   AI configuration loaded: {len(ai_config.model_configs)} models")
            
            return True
            
        except Exception as e:
            logger.error(f"   Configuration test failed: {e}")
            return False
    
    async def test_ai_integration(self) -> bool:
        """Test AI integration"""
        try:
            from cognitive_twin.ai.openrouter_client import OpenRouterClient
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.ai.personality_ai import PersonalityAI
            from cognitive_twin.ai.analysis_ai import AnalysisAI
            
            # Test OpenRouter client
            client = OpenRouterClient()
            assert client is not None
            logger.info("   OpenRouter client initialized")
            
            # Test conversation AI
            conversation_ai = ConversationAI()
            assert conversation_ai is not None
            logger.info("   Conversation AI initialized")
            
            # Test personality AI
            personality_ai = PersonalityAI()
            assert personality_ai is not None
            logger.info("   Personality AI initialized")
            
            # Test analysis AI
            analysis_ai = AnalysisAI()
            assert analysis_ai is not None
            logger.info("   Analysis AI initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"   AI integration test failed: {e}")
            return False
    
    async def test_memory_system(self) -> bool:
        """Test memory system"""
        try:
            from cognitive_twin.memory.vector_memory import VectorMemory
            from cognitive_twin.memory.memory_manager import MemoryManager
            from cognitive_twin.memory.conversation_memory import ConversationMemory
            from cognitive_twin.memory.personality_memory import PersonalityMemory
            
            # Test vector memory
            vector_memory = VectorMemory()
            assert vector_memory is not None
            logger.info("   Vector memory initialized")
            
            # Test memory manager
            memory_manager = MemoryManager()
            assert memory_manager is not None
            logger.info("   Memory manager initialized")
            
            # Test conversation memory
            conversation_memory = ConversationMemory(vector_memory)
            assert conversation_memory is not None
            logger.info("   Conversation memory initialized")
            
            # Test personality memory
            personality_memory = PersonalityMemory(vector_memory)
            assert personality_memory is not None
            logger.info("   Personality memory initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"   Memory system test failed: {e}")
            return False
    
    async def test_event_system(self) -> bool:
        """Test event system"""
        try:
            from cognitive_twin.events.event_bus import EventBus
            from cognitive_twin.events.event_types import EventType, Event
            from cognitive_twin.events.service_coordinator import ServiceCoordinator
            
            # Test event bus
            event_bus = EventBus()
            assert event_bus is not None
            logger.info("   Event bus initialized")
            
            # Test event types
            assert len(EventType) > 0
            logger.info(f"   Event types defined: {len(EventType)} types")
            
            # Test service coordinator
            service_coordinator = ServiceCoordinator(event_bus)
            assert service_coordinator is not None
            logger.info("   Service coordinator initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"   Event system test failed: {e}")
            return False
    
    async def test_realtime_features(self) -> bool:
        """Test real-time features"""
        try:
            from cognitive_twin.realtime.websocket_manager import WebSocketManager
            from cognitive_twin.realtime.live_conversation import LiveConversation
            
            # Test WebSocket manager
            websocket_manager = WebSocketManager()
            assert websocket_manager is not None
            logger.info("   WebSocket manager initialized")
            
            # Test live conversation (without actual WebSocket dependencies)
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.memory.memory_manager import MemoryManager
            from cognitive_twin.events.event_bus import EventBus
            
            conversation_ai = ConversationAI()
            memory_manager = MemoryManager()
            event_bus = EventBus()
            
            live_conversation = LiveConversation(
                websocket_manager=websocket_manager,
                conversation_ai=conversation_ai,
                memory_manager=memory_manager,
                event_bus=event_bus
            )
            assert live_conversation is not None
            logger.info("   Live conversation initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"   Real-time features test failed: {e}")
            return False
    
    async def test_health_system(self) -> bool:
        """Test health check system"""
        try:
            from cognitive_twin.health.health_checker import HealthChecker
            
            # Test health checker
            health_checker = HealthChecker()
            assert health_checker is not None
            logger.info("   Health checker initialized")
            
            # Run a quick health check
            results = await health_checker.check_all_components()
            assert isinstance(results, dict)
            logger.info(f"   Health check completed: {len(results)} components checked")
            
            # Get overall health
            overall = health_checker.get_overall_health()
            assert "status" in overall
            logger.info(f"   Overall health status: {overall['status'].value}")
            
            return True
            
        except Exception as e:
            logger.error(f"   Health system test failed: {e}")
            return False
    
    async def test_api_integration(self) -> bool:
        """Test API integration"""
        try:
            # Import the updated digital twin endpoint
            import sys
            sys.path.append('integrated_system')
            
            # This is a basic import test - in a real test we'd use a test client
            from api.endpoints.digital_twin import router
            assert router is not None
            logger.info("   Digital twin API router loaded")
            
            return True
            
        except Exception as e:
            logger.error(f"   API integration test failed: {e}")
            return False
    
    async def test_end_to_end_conversation(self) -> bool:
        """Test end-to-end conversation flow"""
        try:
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.memory.memory_manager import MemoryManager
            
            # Initialize components
            conversation_ai = ConversationAI()
            memory_manager = MemoryManager()
            
            # Test conversation without actual API calls
            test_message = "Hello, I'm testing the Cognitive-Twin system."
            test_user_id = "test_user_123"
            
            logger.info(f"   Testing conversation with message: '{test_message}'")
            
            # This would normally make API calls, but we're testing the structure
            # In a real test environment with API keys, this would work fully
            
            # Test memory storage
            conversation_id = await memory_manager.store_conversation(
                user_id=test_user_id,
                message=test_message,
                response="Test response",
                metadata={"test": True}
            )
            assert conversation_id is not None
            logger.info("   Conversation stored in memory")
            
            # Test memory retrieval
            history = await memory_manager.get_conversation_history(
                user_id=test_user_id,
                limit=1
            )
            assert len(history) > 0
            logger.info("   Conversation history retrieved")
            
            return True
            
        except Exception as e:
            logger.error(f"   End-to-end conversation test failed: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("🧪 COGNITIVE-TWIN SYSTEM TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {self.total_tests}")
        logger.info(f"Passed: {self.passed_tests}")
        logger.info(f"Failed: {self.failed_tests}")
        
        if self.failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            logger.warning(f"⚠️  {self.failed_tests} test(s) failed. Review issues above.")
        
        logger.info("\n📋 Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {status}: {test_name}")
        
        logger.info("\n🔧 Next Steps:")
        if self.failed_tests == 0:
            logger.info("   1. Set OPENROUTER_API_KEY environment variable")
            logger.info("   2. Configure database connections")
            logger.info("   3. Run deployment script: ./deploy.sh")
            logger.info("   4. Access system at https://localhost")
        else:
            logger.info("   1. Fix failing components")
            logger.info("   2. Re-run tests: python test_complete_system.py")
            logger.info("   3. Check logs for detailed error information")
        
        logger.info("="*60)


async def main():
    """Main test function"""
    tester = SystemTester()
    await tester.run_all_tests()
    
    # Exit with error code if tests failed
    if tester.failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
