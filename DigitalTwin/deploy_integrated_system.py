#!/usr/bin/env python3
"""
Deployment script for the Integrated Data Analysis & Digital Twin System.
"""

import os
import sys
import argparse
import logging
import subprocess
import shutil
import time
import json
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/deploy.log")
    ]
)
logger = logging.getLogger(__name__)

# Deployment configurations
DEPLOYMENT_CONFIGS = {
    "development": {
        "docker_compose_file": "docker-compose.dev.yml",
        "env_file": ".env.development",
        "build_args": ["--build-arg", "ENV=development"]
    },
    "staging": {
        "docker_compose_file": "docker-compose.staging.yml",
        "env_file": ".env.staging",
        "build_args": ["--build-arg", "ENV=staging"]
    },
    "production": {
        "docker_compose_file": "docker-compose.yml",
        "env_file": ".env.production",
        "build_args": ["--build-arg", "ENV=production"]
    }
}

def create_directories():
    """Create necessary directories."""
    directories = ["logs", "deploy", "backups"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def run_tests():
    """Run tests before deployment."""
    logger.info("Running tests before deployment...")
    
    # Run tests
    result = subprocess.run(
        ["python", "run_integrated_system.py", "--test"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Tests failed: {result.stderr}")
        return False
    
    logger.info("All tests passed")
    return True

def create_backup():
    """Create a backup of the current deployment."""
    logger.info("Creating backup...")
    
    # Create backup directory with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = f"backups/backup-{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup configuration files
    config_files = [
        "docker-compose.yml",
        "Dockerfile",
        "Dockerfile.integrated_system",
        ".env",
        "integrated_system/.env"
    ]
    
    for file in config_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            logger.info(f"Backed up {file}")
    
    # Backup database dumps if available
    if os.path.exists("data/postgres"):
        subprocess.run(
            ["pg_dump", "-U", "postgres", "-h", "localhost", "-d", "integrated_system", "-f", f"{backup_dir}/postgres_dump.sql"],
            capture_output=True
        )
        logger.info("Backed up PostgreSQL database")
    
    if os.path.exists("data/mongodb"):
        subprocess.run(
            ["mongodump", "--out", f"{backup_dir}/mongodb_dump"],
            capture_output=True
        )
        logger.info("Backed up MongoDB database")
    
    logger.info(f"Backup created at {backup_dir}")
    return backup_dir

def build_docker_images(environment):
    """Build Docker images."""
    logger.info(f"Building Docker images for {environment} environment...")
    
    config = DEPLOYMENT_CONFIGS[environment]
    
    # Build the main image
    result = subprocess.run(
        ["docker", "build", "-t", "integrated-system:latest"] + config["build_args"] + ["."],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to build Docker image: {result.stderr}")
        return False
    
    logger.info("Docker images built successfully")
    return True

def deploy_with_docker_compose(environment):
    """Deploy using Docker Compose."""
    logger.info(f"Deploying with Docker Compose for {environment} environment...")
    
    config = DEPLOYMENT_CONFIGS[environment]
    
    # Copy environment file
    if os.path.exists(config["env_file"]):
        shutil.copy2(config["env_file"], ".env")
        logger.info(f"Copied {config['env_file']} to .env")
    
    # Deploy with Docker Compose
    result = subprocess.run(
        ["docker-compose", "-f", config["docker_compose_file"], "up", "-d"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to deploy with Docker Compose: {result.stderr}")
        return False
    
    logger.info("Deployed successfully with Docker Compose")
    return True

def run_database_migrations():
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    # Run migrations
    result = subprocess.run(
        ["docker-compose", "exec", "api", "python", "manage.py", "migrate"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to run database migrations: {result.stderr}")
        return False
    
    logger.info("Database migrations completed successfully")
    return True

def verify_deployment():
    """Verify the deployment."""
    logger.info("Verifying deployment...")
    
    # Wait for services to start
    time.sleep(10)
    
    # Check if API is responding
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8080/api/health"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get("status") == "ok":
                    logger.info("API is responding correctly")
                    return True
            
            logger.warning(f"API not responding correctly yet, retrying ({retry_count + 1}/{max_retries})...")
            retry_count += 1
            time.sleep(5)
            
        except Exception as e:
            logger.warning(f"Error checking API: {str(e)}, retrying ({retry_count + 1}/{max_retries})...")
            retry_count += 1
            time.sleep(5)
    
    logger.error("Failed to verify deployment")
    return False

def rollback_deployment(backup_dir):
    """Rollback deployment to previous state."""
    logger.info(f"Rolling back deployment using backup: {backup_dir}")
    
    # Stop current deployment
    subprocess.run(
        ["docker-compose", "down"],
        capture_output=True
    )
    
    # Restore configuration files
    for file in os.listdir(backup_dir):
        if os.path.isfile(os.path.join(backup_dir, file)) and not file.endswith("_dump.sql"):
            shutil.copy2(os.path.join(backup_dir, file), ".")
            logger.info(f"Restored {file}")
    
    # Restore databases if needed
    if os.path.exists(f"{backup_dir}/postgres_dump.sql"):
        subprocess.run(
            ["docker-compose", "up", "-d", "postgres"],
            capture_output=True
        )
        time.sleep(5)  # Wait for database to start
        
        subprocess.run(
            ["docker-compose", "exec", "-T", "postgres", "psql", "-U", "postgres", "-d", "integrated_system", "-f", "/tmp/postgres_dump.sql"],
            input=open(f"{backup_dir}/postgres_dump.sql", "rb").read(),
            capture_output=True
        )
        logger.info("Restored PostgreSQL database")
    
    if os.path.exists(f"{backup_dir}/mongodb_dump"):
        subprocess.run(
            ["docker-compose", "up", "-d", "mongodb"],
            capture_output=True
        )
        time.sleep(5)  # Wait for database to start
        
        subprocess.run(
            ["docker-compose", "exec", "-T", "mongodb", "mongorestore", "/tmp/mongodb_dump"],
            input=open(f"{backup_dir}/mongodb_dump", "rb").read(),
            capture_output=True
        )
        logger.info("Restored MongoDB database")
    
    # Start previous deployment
    subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True
    )
    
    logger.info("Rollback completed")

def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Deploy the Integrated Data Analysis & Digital Twin System")
    parser.add_argument("--environment", choices=["development", "staging", "production"], default="development",
                        help="Deployment environment (default: development)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests before deployment")
    parser.add_argument("--skip-backup", action="store_true", help="Skip creating backup before deployment")
    parser.add_argument("--force", action="store_true", help="Force deployment even if tests fail")
    args = parser.parse_args()
    
    try:
        # Create directories
        create_directories()
        
        # Run tests if not skipped
        if not args.skip_tests:
            tests_passed = run_tests()
            if not tests_passed and not args.force:
                logger.error("Tests failed, aborting deployment")
                return 1
        
        # Create backup if not skipped
        backup_dir = None
        if not args.skip_backup:
            backup_dir = create_backup()
        
        # Build Docker images
        if not build_docker_images(args.environment):
            if backup_dir:
                rollback_deployment(backup_dir)
            return 1
        
        # Deploy with Docker Compose
        if not deploy_with_docker_compose(args.environment):
            if backup_dir:
                rollback_deployment(backup_dir)
            return 1
        
        # Run database migrations
        if not run_database_migrations():
            if backup_dir:
                rollback_deployment(backup_dir)
            return 1
        
        # Verify deployment
        if not verify_deployment():
            logger.warning("Deployment verification failed")
            if backup_dir and input("Do you want to rollback? (y/n): ").lower() == 'y':
                rollback_deployment(backup_dir)
                return 1
        
        logger.info(f"Deployment to {args.environment} environment completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())