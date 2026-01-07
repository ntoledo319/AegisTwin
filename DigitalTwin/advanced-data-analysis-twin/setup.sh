#!/bin/bash

# Setup script for Advanced Data Analysis & Digital Twin System

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Advanced Data Analysis & Digital Twin System...${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs data cache temp

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please update it with your configuration.${NC}"
else
    echo -e "${YELLOW}.env file already exists.${NC}"
fi

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}Python is installed.${NC}"
else
    echo -e "${RED}Python is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    echo -e "${GREEN}pip is installed.${NC}"
else
    echo -e "${RED}pip is not installed. Please install pip.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Check if Docker is installed
if command -v docker &>/dev/null; then
    echo -e "${GREEN}Docker is installed.${NC}"
else
    echo -e "${RED}Docker is not installed. Please install Docker to use the containerized environment.${NC}"
fi

# Check if Docker Compose is installed
if command -v docker-compose &>/dev/null; then
    echo -e "${GREEN}Docker Compose is installed.${NC}"
else
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose to use the containerized environment.${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To start the system:${NC}"
echo -e "  - Update the .env file with your configuration"
echo -e "  - Run 'docker-compose up' to start the containerized environment"
echo -e "  - Or run 'python main.py' to start the API server directly"