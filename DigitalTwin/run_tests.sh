#!/bin/bash

# Run tests and generate coverage report for CogniLink

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== CogniLink Test Runner ===${NC}"
echo -e "${YELLOW}Running tests with coverage reporting...${NC}"

# Make sure we have the required packages
echo -e "${YELLOW}Checking for required packages...${NC}"
pip install pytest pytest-cov pytest-html > /dev/null

# Create directories for reports if they don't exist
mkdir -p reports/coverage
mkdir -p reports/test_results

# Run the tests with coverage
echo -e "${YELLOW}Running tests...${NC}"
pytest --cov=cognilink --cov-report=html:reports/coverage --html=reports/test_results/report.html -v

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed. Check the report for details.${NC}"
fi

# Display coverage summary
echo -e "${YELLOW}Coverage Summary:${NC}"
coverage report

echo -e "${YELLOW}Test reports generated:${NC}"
echo -e "  - HTML Coverage Report: ${GREEN}reports/coverage/index.html${NC}"
echo -e "  - HTML Test Report: ${GREEN}reports/test_results/report.html${NC}"

echo -e "${YELLOW}=== Test Run Complete ===${NC}"