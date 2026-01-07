#!/usr/bin/env python3
"""
Cognitive-Twin Setup Script

Comprehensive setup script for installing dependencies, configuring the system,
and preparing the Cognitive-Twin environment for production use.
"""

import os
import sys
import subprocess
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CognitiveTwinSetup:
    """Setup and configuration manager for Cognitive-Twin"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a shell command and return success status"""
        try:
            logger.info(f"🔧 {description}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.successes.append(description)
                logger.info(f"✅ {description} - SUCCESS")
                return True
            else:
                error_msg = f"{description} - FAILED: {result.stderr}"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"{description} - EXCEPTION: {str(e)}"
            self.errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            logger.info(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
            return True
        else:
            logger.error(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Requires Python 3.10+")
            return False
    
    def install_dependencies(self) -> bool:
        """Install all required dependencies"""
        logger.info("📦 Installing Dependencies")
        
        success = True
        
        # Install from requirements.txt
        if self.run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Installing dependencies from requirements.txt"
        ):
            # Additional specific installations
            additional_deps = [
                (["pip", "install", "pydantic-settings>=2.0.0"], "Installing pydantic-settings"),
                (["pip", "install", "redis>=5.0.1"], "Installing Redis client"),
                (["pip", "install", "motor>=3.3.0"], "Installing Motor (async MongoDB)"),
                (["pip", "install", "chromadb>=0.4.22"], "Installing ChromaDB"),
                (["pip", "install", "asyncpg>=0.29.0"], "Installing AsyncPG"),
                (["pip", "install", "websockets>=12.0"], "Installing WebSockets"),
                (["pip", "install", "psutil>=5.9.6"], "Installing psutil")
            ]
            
            for cmd, desc in additional_deps:
                self.run_command([sys.executable, "-m"] + cmd, desc)
        else:
            success = False
        
        return success
    
    def setup_directories(self) -> bool:
        """Create necessary directories"""
        logger.info("📁 Setting up directories")
        
        directories = [
            "logs",
            "data",
            "uploads",
            "backups",
            "chroma_db",
            "tmp"
        ]
        
        success = True
        for directory in directories:
            try:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            except Exception as e:
                logger.error(f"❌ Failed to create directory {directory}: {e}")
                success = False
        
        return success
    
    def create_environment_file(self) -> bool:
        """Create example environment file"""
        logger.info("⚙️  Creating environment configuration")
        
        env_content = """# Cognitive-Twin Environment Configuration

# Application Settings
COGNITIVE_TWIN_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=change-me-in-production-please
JWT_SECRET_KEY=change-me-in-production-jwt

# AI/ML Configuration
OPENROUTER_API_KEY=your-openrouter-api-key-here
AI_MODEL_TIMEOUT=30
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7

# Database Configuration
POSTGRES_URL=postgresql://user:password@localhost:5432/cognitive_twin
MONGODB_URL=mongodb://localhost:27017/cognitive_twin
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Vector Memory Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=text-embedding-3-large

# File Upload Configuration
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIRECTORY=./uploads

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_DIRECTORY=./backups
BACKUP_RETENTION_DAYS=30

# SSL/TLS (for production)
SSL_ENABLED=false
SSL_CERT_PATH=
SSL_KEY_PATH=
"""
        
        try:
            env_file = self.project_root / ".env.example"
            env_file.write_text(env_content)
            logger.info("✅ Created .env.example file")
            
            # Create actual .env if it doesn't exist
            actual_env = self.project_root / ".env"
            if not actual_env.exists():
                actual_env.write_text(env_content)
                logger.info("✅ Created .env file")
            else:
                logger.info("ℹ️  .env file already exists, not overwriting")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create environment file: {e}")
            return False
    
    def setup_git_hooks(self) -> bool:
        """Set up git hooks if in a git repository"""
        if not (self.project_root / ".git").exists():
            logger.info("ℹ️  Not a git repository, skipping git hooks")
            return True
        
        logger.info("🔧 Setting up git hooks")
        
        try:
            # Install pre-commit hooks
            if self.run_command(
                [sys.executable, "-m", "pre_commit", "install"],
                "Installing pre-commit hooks"
            ):
                return True
        except Exception as e:
            logger.warning(f"⚠️  Pre-commit setup failed: {e}")
        
        return False
    
    def verify_installation(self) -> Dict[str, bool]:
        """Verify the installation"""
        logger.info("🔍 Verifying installation")
        
        verification_results = {}
        
        # Test imports
        test_imports = [
            ("fastapi", "FastAPI"),
            ("pydantic_settings", "Pydantic Settings"),
            ("redis", "Redis"),
            ("motor", "Motor"),
            ("chromadb", "ChromaDB"),
            ("asyncpg", "AsyncPG"),
            ("websockets", "WebSockets"),
            ("psutil", "psutil")
        ]
        
        for module, name in test_imports:
            try:
                __import__(module)
                verification_results[name] = True
                logger.info(f"✅ {name} import successful")
            except ImportError:
                verification_results[name] = False
                logger.warning(f"⚠️  {name} import failed")
        
        # Test core modules
        sys.path.insert(0, str(self.project_root / "src"))
        
        core_modules = [
            ("cognitive_twin.ai.openrouter_client", "AI Client"),
            ("cognitive_twin.memory.memory_manager", "Memory Manager"),
            ("cognitive_twin.health.health_checker", "Health Checker")
        ]
        
        for module, name in core_modules:
            try:
                __import__(module)
                verification_results[name] = True
                logger.info(f"✅ {name} module working")
            except Exception as e:
                verification_results[name] = False
                logger.warning(f"⚠️  {name} module failed: {e}")
        
        return verification_results
    
    def generate_report(self) -> None:
        """Generate setup report"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎯 COGNITIVE-TWIN SETUP REPORT")
        logger.info("=" * 60)
        
        logger.info(f"✅ Successes: {len(self.successes)}")
        logger.info(f"⚠️  Warnings: {len(self.warnings)}")
        logger.info(f"❌ Errors: {len(self.errors)}")
        
        if self.successes:
            logger.info("")
            logger.info("✅ Successful Operations:")
            for success in self.successes:
                logger.info(f"   • {success}")
        
        if self.warnings:
            logger.info("")
            logger.info("⚠️  Warnings:")
            for warning in self.warnings:
                logger.info(f"   • {warning}")
        
        if self.errors:
            logger.info("")
            logger.info("❌ Errors:")
            for error in self.errors:
                logger.info(f"   • {error}")
        
        logger.info("")
        logger.info("🔧 Next Steps:")
        
        if self.errors:
            logger.info("   1. Review and fix the errors listed above")
            logger.info("   2. Install missing dependencies manually if needed")
            logger.info("   3. Configure your .env file with proper API keys and database URLs")
            logger.info("   4. Re-run the validation: python final_system_validation.py")
        else:
            logger.info("   1. Configure your .env file with proper API keys and database URLs")
            logger.info("   2. Set up external services (Redis, databases) if needed")
            logger.info("   3. Run the validation: python final_system_validation.py")
            logger.info("   4. Start the system: uvicorn integrated_system.main:app --reload")
        
        logger.info("")
        logger.info("📚 Documentation:")
        logger.info("   • README.md - General overview and setup")
        logger.info("   • requirements.txt - All Python dependencies") 
        logger.info("   • .env.example - Environment configuration template")
        logger.info("   • final_system_validation.py - System health check")
        
        logger.info("=" * 60)
    
    def run_setup(self) -> bool:
        """Run complete setup process"""
        logger.info("🚀 Starting Cognitive-Twin Setup")
        logger.info("=" * 60)
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Run setup steps
        steps = [
            (self.setup_directories, "Setting up directories"),
            (self.create_environment_file, "Creating environment configuration"),
            (self.install_dependencies, "Installing dependencies"),
            (self.setup_git_hooks, "Setting up git hooks")
        ]
        
        for step_func, step_name in steps:
            try:
                logger.info(f"🔧 {step_name}")
                if not step_func():
                    self.warnings.append(f"{step_name} completed with issues")
                else:
                    self.successes.append(step_name)
            except Exception as e:
                error_msg = f"{step_name} failed: {str(e)}"
                self.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Verify installation
        verification_results = self.verify_installation()
        
        # Generate report
        self.generate_report()
        
        # Return success status
        return len(self.errors) == 0

def main():
    """Main setup function"""
    setup = CognitiveTwinSetup()
    success = setup.run_setup()
    
    if success:
        logger.info("🎉 Setup completed successfully!")
        return 0
    else:
        logger.error("💥 Setup completed with errors. Please review the report above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
