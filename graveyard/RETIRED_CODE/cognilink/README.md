# CogniLink: Personal Digital Communication Analyzer

CogniLink is a tool for analyzing personal digital communications to extract insights about communication patterns, relationships, and knowledge.

## Overview

CogniLink analyzes your digital communications (emails, messages, etc.) to help you understand:

- **Communication Patterns**: How, when, and with whom you communicate
- **Relationships**: The nature and strength of your digital relationships
- **Topics & Knowledge**: What topics you discuss and what knowledge is shared

## Features

- **Data Import**: Import data from various sources:
  - Email (MBOX, EML, JSON)
  - Messages (WhatsApp, Telegram, etc.)
  - iOS Backups (messages, contacts, calls)
  - Social Media (Twitter/X)
  - Music Platforms (Spotify)
  - Dating Apps (Tinder)
- **Communication Analysis**: Analyze communication patterns and habits
- **Relationship Analysis**: Identify and characterize relationships
- **Topic Analysis**: Extract topics and themes from communications
- **Report Generation**: Generate HTML, Markdown, or text reports

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

1. Clone or download this repository
2. Navigate to the project directory
3. Run the installation script:

```bash
bash install.sh
```

Or install manually:

```bash
# Basic installation
pip install -e .

# With NLP features
pip install -e ".[nlp]"

# With visualization features
pip install -e ".[viz]"

# With development tools
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

CogniLink provides a command-line interface for all operations:

```bash
# Import data
cognilink import --source emails.mbox --type email_mbox --output comm_graph.json

# Analyze data
cognilink analyze --input comm_graph.json --type all --output analysis_results.json

# Generate report
cognilink report --input analysis_results.json --type html --output report.html
```

### Basic Workflow

1. **Import Data**: Import your communication data from various sources
2. **Analyze Data**: Analyze the imported data to extract insights
3. **Generate Reports**: Create reports to visualize and understand the insights

### Examples

The `examples` directory contains sample scripts demonstrating how to use CogniLink:

- `basic_usage.py`: Demonstrates the core functionality
- `advanced_usage.py`: Shows more advanced features like custom configuration and filtering
- `advanced_connectors.py`: Demonstrates how to use the advanced connectors for iOS backups, social media, etc.

To run an example:

```bash
python -m examples.basic_usage
```

## Data Sources

CogniLink can import data from:

### Email
- MBOX files
- EML files
- JSON exports

### Messages
- JSON exports from WhatsApp, Telegram, Signal, etc.
- CSV formats with configurable mappings
- Text files with message content

### Phone Backups
- iOS backups (messages, contacts, calls, notes, calendar)

### Social Media
- Twitter/X (tweets, direct messages, followers)

### Music Platforms
- Spotify (listening history, playlists, library)

### Dating Apps
- Tinder (matches, messages, profile)

## Configuration

CogniLink uses YAML configuration files located in the `config` directory:

- `connectors.yaml`: Configuration for data connectors
- `processors.yaml`: Configuration for data processors
- `analysis.yaml`: Configuration for analysis components
- `interface.yaml`: Configuration for user interface components

## Templates

Report templates are located in the `templates` directory:

- `report.html`: Template for HTML reports
- `report.md`: Template for Markdown reports
- `report.txt`: Template for plain text reports

You can customize these templates or create your own to change the appearance and structure of your reports.

## Privacy & Security

CogniLink is designed to run locally on your machine. Your data never leaves your computer, ensuring your communications remain private and secure.

## Project Structure

```
cognilink/
├── core/               # Core components
├── pipeline/           # Data pipeline components
│   ├── connectors/     # Data connectors
│   └── processors/     # Data processors
├── analysis/           # Analysis components
├── interface/          # User interface components
├── config/             # Configuration files
├── templates/          # Report templates
├── examples/           # Example scripts
├── data/               # Sample data
│   └── sample/         # Sample files for testing
└── tests/              # Tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NetworkX for graph analysis
- spaCy for natural language processing
- NLTK for text analysis
- Gensim for topic modeling