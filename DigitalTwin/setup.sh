#!/bin/bash

# Setup script for the Integrated Data Analysis & Cognitive Twin System
# This script sets up the development environment and installs dependencies

# Exit on error
set -e

# Print colored messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Integrated Data Analysis & Cognitive Twin System ${NC}"
echo -e "${BLUE}  Setup Script                                     ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Check Python version
echo -e "\n${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version)
if [[ $python_version == *"Python 3."* ]]; then
    echo -e "${GREEN}Found $python_version${NC}"
else
    echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
    echo -e "${RED}Found: $python_version${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "\n${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "\n${GREEN}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}Virtual environment activated${NC}"

# Install dependencies
echo -e "\n${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Python dependencies installed${NC}"

# Check if Node.js is installed (for web interface)
echo -e "\n${BLUE}Checking Node.js installation...${NC}"
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo -e "${GREEN}Found Node.js $node_version${NC}"
    
    # Install web dependencies
    if [ -d "web" ]; then
        echo -e "\n${BLUE}Installing web dependencies...${NC}"
        cd web
        npm install
        cd ..
        echo -e "${GREEN}Web dependencies installed${NC}"
    fi
else
    echo -e "${RED}Warning: Node.js not found. Web interface will not be available.${NC}"
    echo -e "${RED}Please install Node.js 16 or higher to use the web interface.${NC}"
fi

# Create necessary directories
echo -e "\n${BLUE}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p cache
mkdir -p outputs
echo -e "${GREEN}Directories created${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created${NC}"
    echo -e "${RED}Please update the .env file with your configuration${NC}"
else
    echo -e "\n${GREEN}.env file already exists${NC}"
fi

# Initialize database
echo -e "\n${BLUE}Initializing database...${NC}"
python -c "from core.db import db_manager; import asyncio; asyncio.run(db_manager.initialize(create_tables=True))"
echo -e "${GREEN}Database initialized${NC}"

# Create example data directories
echo -e "\n${BLUE}Setting up example data...${NC}"
mkdir -p examples/data
echo -e "${GREEN}Example data directories created${NC}"

# Download sample data files if they don't exist
if [ ! -f "examples/data/sample_emails.mbox" ]; then
    echo -e "\n${BLUE}Downloading sample email data...${NC}"
    curl -o examples/data/sample_emails.mbox https://raw.githubusercontent.com/sample-data/email-samples/main/sample_emails.mbox
    echo -e "${GREEN}Sample email data downloaded${NC}"
fi

if [ ! -f "examples/data/sample_messages.json" ]; then
    echo -e "\n${BLUE}Creating sample message data...${NC}"
    cat > examples/data/sample_messages.json << 'EOL'
{
  "messages": [
    {
      "id": "msg1",
      "from": "friend1@example.com",
      "text": "Hey, how are you doing today?",
      "timestamp": "2023-01-01T10:00:00Z",
      "platform": "whatsapp"
    },
    {
      "id": "msg2",
      "from": "user@example.com",
      "text": "I'm good! Just working on that project we discussed.",
      "timestamp": "2023-01-01T10:05:00Z",
      "platform": "whatsapp"
    },
    {
      "id": "msg3",
      "from": "friend1@example.com",
      "text": "Great! How's it coming along?",
      "timestamp": "2023-01-01T10:10:00Z",
      "platform": "whatsapp"
    }
  ]
}
EOL
    echo -e "${GREEN}Sample message data created${NC}"
fi

if [ ! -f "examples/data/sample_calendar.ics" ]; then
    echo -e "\n${BLUE}Creating sample calendar data...${NC}"
    cat > examples/data/sample_calendar.ics << 'EOL'
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sample Calendar//EN
BEGIN:VEVENT
SUMMARY:Team Meeting
DTSTART:20230105T100000Z
DTEND:20230105T110000Z
DESCRIPTION:Weekly team sync meeting
LOCATION:Conference Room A
END:VEVENT
BEGIN:VEVENT
SUMMARY:Project Deadline
DTSTART:20230115T170000Z
DTEND:20230115T180000Z
DESCRIPTION:Final submission for Q1 project
LOCATION:Office
END:VEVENT
BEGIN:VEVENT
SUMMARY:Lunch with Client
DTSTART:20230120T120000Z
DTEND:20230120T133000Z
DESCRIPTION:Discuss new project opportunities
LOCATION:Downtown Cafe
END:VEVENT
END:VCALENDAR
EOL
    echo -e "${GREEN}Sample calendar data created${NC}"
fi

# Run tests to verify installation
echo -e "\n${BLUE}Running tests to verify installation...${NC}"
pytest -xvs tests/unit/test_core.py
echo -e "${GREEN}Tests completed${NC}"

echo -e "\n${BLUE}==================================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "\nTo start the system:"
echo -e "1. Activate the virtual environment: ${BLUE}source venv/bin/activate${NC}"
echo -e "2. Start the API server: ${BLUE}python main.py${NC}"
echo -e "3. In a new terminal, start the web interface: ${BLUE}cd web && npm run dev${NC}"
echo -e "\nAccess the API at: ${BLUE}http://localhost:8000${NC}"
echo -e "Access the web interface at: ${BLUE}http://localhost:3000${NC}"
echo -e "\nRun the demo: ${BLUE}python examples/demo_integrated_system.py${NC}"
echo -e "${BLUE}==================================================${NC}"