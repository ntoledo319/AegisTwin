#!/usr/bin/env python3
"""
Cognitive-Twin UI Test Script

Tests the web UI functionality, templates, and integrations
to ensure everything is working correctly.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "integrated_system"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UITester:
    """Test the Cognitive-Twin UI components"""
    
    def __init__(self):
        self.test_results = {}
        self.passed = 0
        self.failed = 0
        
    def test_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        self.test_results[test_name] = {
            "passed": passed,
            "message": message
        }
        
        if passed:
            self.passed += 1
            logger.info(f"✅ {test_name}: PASS {message}")
        else:
            self.failed += 1
            logger.error(f"❌ {test_name}: FAIL {message}")
    
    def test_template_files(self):
        """Test that all template files exist and are valid"""
        logger.info("🔍 Testing Template Files")
        
        template_dir = project_root / "integrated_system" / "web" / "templates"
        required_templates = [
            "base.html",
            "index.html", 
            "dashboard.html",
            "digital_twin.html",
            "data.html",
            "error.html",
            "analysis.html",
            "knowledge_graph.html",
            "settings.html"
        ]
        
        for template in required_templates:
            template_path = template_dir / template
            exists = template_path.exists()
            
            if exists:
                # Check for basic HTML structure
                try:
                    content = template_path.read_text()
                    has_structure = (
                        "{% extends" in content or "<!DOCTYPE html" in content
                    ) and "{% block" in content
                    self.test_result(f"template_{template}", has_structure, 
                                   "Valid template structure" if has_structure else "Invalid structure")
                except Exception as e:
                    self.test_result(f"template_{template}", False, f"Read error: {e}")
            else:
                self.test_result(f"template_{template}", False, "File not found")
    
    def test_static_files(self):
        """Test that static files exist and are valid"""
        logger.info("🔍 Testing Static Files")
        
        static_dir = project_root / "integrated_system" / "web" / "static"
        
        # Test CSS file
        css_file = static_dir / "css" / "main.css"
        css_exists = css_file.exists()
        if css_exists:
            try:
                css_content = css_file.read_text()
                has_css_rules = len(css_content) > 1000 and "{" in css_content
                self.test_result("css_main", has_css_rules, 
                               f"CSS file is valid ({len(css_content)} chars)")
            except Exception as e:
                self.test_result("css_main", False, f"CSS read error: {e}")
        else:
            self.test_result("css_main", False, "CSS file not found")
        
        # Test JavaScript file
        js_file = static_dir / "js" / "main.js"
        js_exists = js_file.exists()
        if js_exists:
            try:
                js_content = js_file.read_text()
                has_js_functions = len(js_content) > 1000 and "function" in js_content
                self.test_result("js_main", has_js_functions,
                               f"JavaScript file is valid ({len(js_content)} chars)")
            except Exception as e:
                self.test_result("js_main", False, f"JavaScript read error: {e}")
        else:
            self.test_result("js_main", False, "JavaScript file not found")
    
    def test_fastapi_integration(self):
        """Test FastAPI integration"""
        logger.info("🔍 Testing FastAPI Integration")
        
        try:
            # Import FastAPI integration
            from integrated_system.web.fastapi_integration import WebIntegration
            from fastapi import FastAPI
            
            # Create test app
            test_app = FastAPI()
            integration = WebIntegration(test_app)
            
            # Test basic functionality
            has_templates = hasattr(integration, 'templates')
            has_routes = len(test_app.routes) > 0
            
            self.test_result("fastapi_integration", has_templates and has_routes,
                           f"Integration working, {len(test_app.routes)} routes registered")
            
        except Exception as e:
            self.test_result("fastapi_integration", False, f"Integration error: {e}")
    
    def test_main_app(self):
        """Test main application setup"""
        logger.info("🔍 Testing Main Application")
        
        try:
            # Import main app
            sys.path.insert(0, str(project_root / "integrated_system"))
            import main
            
            # Test app creation
            app_exists = hasattr(main, 'app')
            has_routes = len(main.app.routes) > 5 if app_exists else False
            
            self.test_result("main_app", app_exists and has_routes,
                           f"Main app created with {len(main.app.routes) if app_exists else 0} routes")
            
        except Exception as e:
            self.test_result("main_app", False, f"Main app error: {e}")
    
    def test_security_fixes(self):
        """Test that security issues have been fixed"""
        logger.info("🔍 Testing Security Fixes")
        
        # Check for malicious scripts in templates
        template_dir = project_root / "integrated_system" / "web" / "templates"
        malicious_patterns = [
            "sites.super.myninja.ai",
            "ninja-daytona-script"
        ]
        
        security_clean = True
        for template_file in template_dir.glob("*.html"):
            try:
                content = template_file.read_text()
                for pattern in malicious_patterns:
                    if pattern in content:
                        security_clean = False
                        logger.warning(f"Found suspicious pattern '{pattern}' in {template_file}")
            except Exception as e:
                logger.warning(f"Could not check {template_file}: {e}")
        
        self.test_result("security_fixes", security_clean,
                        "No malicious scripts found" if security_clean else "Suspicious patterns detected")
    
    def test_branding_update(self):
        """Test that branding has been updated"""
        logger.info("🔍 Testing Branding Updates")
        
        # Check base template for correct branding
        base_template = project_root / "integrated_system" / "web" / "templates" / "base.html"
        
        if base_template.exists():
            try:
                content = base_template.read_text()
                has_cognitive_twin = "Cognitive-Twin" in content
                no_old_branding = "Integrated System" not in content.replace("Cognitive-Twin", "")
                
                self.test_result("branding_update", has_cognitive_twin and no_old_branding,
                               "Branding successfully updated to Cognitive-Twin")
            except Exception as e:
                self.test_result("branding_update", False, f"Could not check branding: {e}")
        else:
            self.test_result("branding_update", False, "Base template not found")
    
    def test_responsive_design(self):
        """Test responsive design elements"""
        logger.info("🔍 Testing Responsive Design")
        
        css_file = project_root / "integrated_system" / "web" / "static" / "css" / "main.css"
        
        if css_file.exists():
            try:
                css_content = css_file.read_text()
                
                # Check for responsive features
                has_media_queries = "@media" in css_content
                has_flexbox = "flex" in css_content
                has_grid = "grid" in css_content
                has_variables = ":root" in css_content and "--" in css_content
                
                responsive_score = sum([has_media_queries, has_flexbox, has_grid, has_variables])
                
                self.test_result("responsive_design", responsive_score >= 3,
                               f"Responsive features: {responsive_score}/4")
            except Exception as e:
                self.test_result("responsive_design", False, f"CSS check error: {e}")
        else:
            self.test_result("responsive_design", False, "CSS file not found")
    
    def test_accessibility_features(self):
        """Test accessibility features"""
        logger.info("🔍 Testing Accessibility Features")
        
        # Check templates for accessibility features
        template_dir = project_root / "integrated_system" / "web" / "templates"
        accessibility_features = []
        
        for template_file in template_dir.glob("*.html"):
            try:
                content = template_file.read_text()
                
                # Check for accessibility attributes
                if 'alt=' in content:
                    accessibility_features.append("alt attributes")
                if 'aria-' in content:
                    accessibility_features.append("ARIA attributes")
                if 'title=' in content:
                    accessibility_features.append("title attributes")
                if 'tabindex' in content:
                    accessibility_features.append("tab navigation")
                    
            except Exception as e:
                logger.warning(f"Could not check accessibility in {template_file}: {e}")
        
        accessibility_score = len(set(accessibility_features))
        self.test_result("accessibility", accessibility_score >= 2,
                        f"Accessibility features found: {accessibility_score}")
    
    def test_error_handling(self):
        """Test error handling"""
        logger.info("🔍 Testing Error Handling")
        
        # Check for error template
        error_template = project_root / "integrated_system" / "web" / "templates" / "error.html"
        error_template_exists = error_template.exists()
        
        # Check JavaScript for error handling
        js_file = project_root / "integrated_system" / "web" / "static" / "js" / "main.js"
        js_error_handling = False
        
        if js_file.exists():
            try:
                js_content = js_file.read_text()
                js_error_handling = "catch" in js_content and "error" in js_content.lower()
            except Exception as e:
                logger.warning(f"Could not check JavaScript: {e}")
        
        self.test_result("error_handling", error_template_exists and js_error_handling,
                        "Error template and JS error handling present")
    
    async def run_all_tests(self):
        """Run all UI tests"""
        logger.info("🚀 Starting Cognitive-Twin UI Test Suite")
        logger.info("=" * 60)
        
        # Run all tests
        self.test_template_files()
        self.test_static_files()
        self.test_fastapi_integration()
        self.test_main_app()
        self.test_security_fixes()
        self.test_branding_update()
        self.test_responsive_design()
        self.test_accessibility_features()
        self.test_error_handling()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("🧪 COGNITIVE-TWIN UI TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"🎯 Success Rate: {success_rate:.1f}%")
        
        logger.info("")
        logger.info("📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            message = f" - {result['message']}" if result["message"] else ""
            logger.info(f"   {status}: {test_name.replace('_', ' ').title()}{message}")
        
        logger.info("")
        if success_rate >= 90:
            logger.info("🎉 UI STATUS: EXCELLENT - Ready for production!")
        elif success_rate >= 70:
            logger.info("✅ UI STATUS: GOOD - Minor issues to address")
        elif success_rate >= 50:
            logger.info("⚠️  UI STATUS: PARTIAL - Significant improvements needed")
        else:
            logger.info("❌ UI STATUS: POOR - Major issues require attention")
        
        logger.info("")
        logger.info("🔧 Next Steps:")
        failed_tests = [name for name, result in self.test_results.items() if not result["passed"]]
        
        if failed_tests:
            logger.info("   1. Address failed test issues:")
            for test in failed_tests:
                logger.info(f"      - {test.replace('_', ' ').title()}")
            logger.info("   2. Re-run tests: python test_ui.py")
            logger.info("   3. Test in browser: uvicorn integrated_system.main:app --reload")
        else:
            logger.info("   1. Start the server: uvicorn integrated_system.main:app --reload")
            logger.info("   2. Open browser to: http://localhost:8000")
            logger.info("   3. Test all UI functionality manually")
        
        logger.info("=" * 60)
        
        return success_rate

def create_demo_data():
    """Create demo data files for testing"""
    logger.info("📁 Creating demo data files")
    
    # Create logs directory
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create demo data file
    demo_data = {
        "messages": [
            {"sender": "user", "text": "Hello!", "timestamp": "2024-01-01T10:00:00Z"},
            {"sender": "twin", "text": "Hi there! How can I help you today?", "timestamp": "2024-01-01T10:00:05Z"}
        ],
        "metadata": {
            "total_conversations": 42,
            "total_insights": 15,
            "data_sources": 3
        }
    }
    
    import json
    demo_file = project_root / "demo_data.json"
    demo_file.write_text(json.dumps(demo_data, indent=2))
    
    logger.info(f"✅ Demo data created: {demo_file}")

async def main():
    """Main test function"""
    # Create demo data
    create_demo_data()
    
    # Run UI tests
    tester = UITester()
    await tester.run_all_tests()
    success_rate = tester.generate_report()
    
    # Return appropriate exit code
    return 0 if success_rate and success_rate >= 80 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
