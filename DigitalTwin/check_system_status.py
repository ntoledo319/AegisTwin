#!/usr/bin/env python3
"""
Check the status of the Integrated Data Analysis & Cognitive Twin System.

This script checks if the system is running and provides information about its status.
"""

import os
import sys
import requests
import subprocess
import psutil
import time
from datetime import datetime

def check_api_server():
    """Check if the API server is running."""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API server is running")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Docs URL: {data.get('docs_url', '/docs')}")
            print(f"   API URL: {data.get('api_url', '/api/v1')}")
            return True
        else:
            print("❌ API server returned status code:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error checking API server: {str(e)}")
        return False

def check_process(name):
    """Check if a process with the given name is running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if name in proc.info['name'] or any(name in cmd for cmd in proc.info['cmdline'] if cmd):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def check_database_connections():
    """Check database connections."""
    # Check PostgreSQL
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ PostgreSQL is running")
        else:
            print("❌ PostgreSQL is not running or not accessible")
    except Exception as e:
        print(f"❌ Error checking PostgreSQL: {str(e)}")
    
    # Check MongoDB
    try:
        result = subprocess.run(
            ["mongosh", "--eval", "db.version()", "--quiet"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ MongoDB is running (version: {result.stdout.strip()})")
        else:
            print("❌ MongoDB is not running or not accessible")
    except Exception as e:
        print(f"❌ Error checking MongoDB: {str(e)}")
    
    # Check Redis
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip() == "PONG":
            print("✅ Redis is running")
        else:
            print("❌ Redis is not running or not accessible")
    except Exception as e:
        print(f"❌ Error checking Redis: {str(e)}")
    
    # Check Neo4j
    try:
        result = subprocess.run(
            ["cypher-shell", "-u", "neo4j", "-p", "password", "--non-interactive", "RETURN 1;"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Neo4j is running")
        else:
            print("❌ Neo4j is not running or not accessible")
    except Exception as e:
        print(f"❌ Error checking Neo4j: {str(e)}")

def check_directories():
    """Check if required directories exist."""
    directories = ["data", "cache", "logs", "results", "temp"]
    for directory in directories:
        if os.path.isdir(directory):
            print(f"✅ Directory '{directory}' exists")
        else:
            print(f"❌ Directory '{directory}' does not exist")

def check_config_files():
    """Check if configuration files exist."""
    config_files = ["config/base.yaml", "config/development.yaml", "integrated_system/.env.example"]
    for config_file in config_files:
        if os.path.isfile(config_file):
            print(f"✅ Configuration file '{config_file}' exists")
        else:
            print(f"❌ Configuration file '{config_file}' does not exist")
    
    # Check if .env file exists
    if os.path.isfile("integrated_system/.env"):
        print("✅ Environment file 'integrated_system/.env' exists")
    else:
        print("❌ Environment file 'integrated_system/.env' does not exist")

def main():
    """Main function."""
    print("="*80)
    print("INTEGRATED SYSTEM STATUS CHECK")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("CHECKING API SERVER...")
    api_running = check_api_server()
    print()
    
    print("CHECKING PROCESSES...")
    python_pid = check_process("python")
    if python_pid:
        print(f"✅ Python process is running (PID: {python_pid})")
    else:
        print("❌ No Python process found")
    print()
    
    print("CHECKING DATABASE CONNECTIONS...")
    check_database_connections()
    print()
    
    print("CHECKING DIRECTORIES...")
    check_directories()
    print()
    
    print("CHECKING CONFIGURATION FILES...")
    check_config_files()
    print()
    
    print("="*80)
    if api_running:
        print("✅ SYSTEM IS RUNNING")
    else:
        print("❌ SYSTEM IS NOT RUNNING")
    print("="*80)
    
    return 0 if api_running else 1

if __name__ == "__main__":
    sys.exit(main())