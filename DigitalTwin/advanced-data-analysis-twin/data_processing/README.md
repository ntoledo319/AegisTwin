# Data Processing Module

The Data Processing module is a core component of the Advanced Data Analysis & Digital Twin System. It provides a flexible and extensible framework for extracting, processing, and analyzing data from various sources.

## Overview

The Data Processing module consists of the following main components:

1. **Data Pipeline**: Orchestrates the data processing workflow, managing connectors and processors.
2. **Connectors**: Extract data from various sources such as email, messaging platforms, social media, and productivity tools.
3. **Processors**: Process and analyze the extracted data, performing tasks such as text analysis, entity extraction, and data normalization.

## Connectors

Connectors are responsible for extracting data from specific sources. The following connectors are currently implemented:

### Email Connector

Extracts data from email accounts using IMAP.

- Supports Gmail, Outlook, Yahoo, and other IMAP-enabled email providers
- Extracts email content, attachments, and metadata
- Supports filtering by date range, sender, subject, and other criteria

### Messaging Connector

Extracts data from messaging platforms.

- Supports WhatsApp, Telegram, Signal, and SMS
- Extracts messages, attachments, and metadata
- Handles various export formats (text files, backups, databases)

### Social Media Connector

Extracts data from social media platforms.

- Supports Twitter/X, Facebook, LinkedIn, Instagram, and Reddit
- Extracts posts, comments, messages, and other content
- Processes user data exports from these platforms

### Productivity Connector

Extracts data from productivity tools.

- Supports Google Workspace (Gmail, Calendar, Drive, Docs)
- Supports Microsoft 365 (Outlook, Calendar, OneDrive, Office)
- Handles calendar exports (ICS files) and document collections

## Processors

Processors analyze and transform the extracted data. The following processors are currently implemented:

### Text Processor

Analyzes and processes textual content.

- Text normalization and cleaning
- Tokenization and lemmatization
- Keyword extraction
- Named entity recognition
- Sentiment analysis
- Topic extraction
- Text summarization

### Entity Processor

Extracts and links entities from text.

- Named entity recognition (people, organizations, locations, etc.)
- Entity linking and disambiguation
- Entity relationship extraction
- Entity metadata enrichment
- Entity frequency and importance analysis

### Normalization Processor

Standardizes and cleans data.

- Text normalization (case, whitespace, punctuation)
- Date and time normalization
- Name and address normalization
- Email and phone number normalization
- JSON and structured data normalization

## Usage

### Creating a Pipeline

```python
from data_processing import create_pipeline

# Define pipeline configuration
config = {
    "pipeline_id": "my_pipeline",
    "connectors": [
        {
            "connector_id": "email_connector",
            "type": "email",
            "host": "imap.gmail.com",
            "port": 993,
            "username": "user@gmail.com",
            "password": "password",
            "use_ssl": True
        },
        {
            "connector_id": "messaging_connector",
            "type": "messaging",
            "platform": "whatsapp",
            "source_path": "data/whatsapp_chat.txt"
        }
    ],
    "processors": [
        {
            "processor_id": "text_processor",
            "type": "text",
            "language": "en",
            "use_spacy": False
        },
        {
            "processor_id": "entity_processor",
            "type": "entity",
            "language": "en",
            "use_spacy": False
        }
    ],
    "max_concurrent_tasks": 3,
    "error_handling": "continue"
}

# Create and initialize the pipeline
pipeline = await create_pipeline(config)
```

### Running the Pipeline

```python
# Run the pipeline with parameters
results = await pipeline.run({
    "connector_parameters": {
        "email_connector": {
            "folder": "INBOX",
            "max_emails": 100,
            "start_date": "2023-01-01"
        },
        "messaging_connector": {
            "max_messages": 500
        }
    },
    "processor_parameters": {
        "text_processor": {
            "max_keywords": 20
        }
    }
})

# Process the results
for connector_id, connector_result in results["connector_results"].items():
    if connector_result.get("success", False):
        for item in connector_result.get("data", []):
            # Process each item
            print(f"Item: {item.get('id')}, Type: {item.get('type')}")
```

### Using Individual Connectors

```python
from data_processing import EmailConnector

# Create a connector
email_connector = EmailConnector({
    "host": "imap.gmail.com",
    "port": 993,
    "username": "user@gmail.com",
    "password": "password",
    "use_ssl": True
})

# Connect to the data source
await email_connector.connect()

# Extract data
data = await email_connector.get_data({
    "folder": "INBOX",
    "max_emails": 100,
    "start_date": "2023-01-01"
})

# Process the data
for item in data.get("data", []):
    print(f"Email: {item.get('subject')}")
```

### Using Individual Processors

```python
from data_processing import TextProcessor

# Create a processor
text_processor = TextProcessor({
    "language": "en",
    "use_spacy": False
})

# Process text
result = await text_processor.process_text("This is a sample text about John Smith who works at Acme Corporation in New York.")

# Extract keywords
keywords = result.get("keywords", [])
for keyword in keywords:
    print(f"Keyword: {keyword.get('text')}, Score: {keyword.get('score')}")

# Extract entities
entities = result.get("entities", [])
for entity in entities:
    print(f"Entity: {entity.get('text')}, Type: {entity.get('type')}")
```

## Examples

See the `examples` directory for complete examples of using the Data Processing module.

- `data_processing_example.py`: Demonstrates how to use the data processing pipeline with various connectors and processors.

## Extending the Module

### Creating a New Connector

To create a new connector, subclass `DataConnectorBase` and implement the required methods:

```python
from data_processing import DataConnectorBase

class MyConnector(DataConnectorBase):
    async def connect(self) -> bool:
        # Implement connection logic
        pass
    
    async def disconnect(self) -> bool:
        # Implement disconnection logic
        pass
    
    async def extract_data(self, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Implement data extraction logic
        pass
    
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Implement data transformation logic
        pass
```

Then register your connector in `connectors/__init__.py`:

```python
from .my_connector import MyConnector

CONNECTOR_REGISTRY = {
    # Existing connectors...
    "my_connector": MyConnector,
}
```

### Creating a New Processor

To create a new processor, implement the required methods:

```python
from core.utils import generate_id, timestamp_now

class MyProcessor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.processor_id = generate_id("my_processor")
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        # Implement text processing logic
        pass
    
    async def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        # Implement batch processing logic
        pass
```

Then register your processor in `processors/__init__.py`:

```python
from .my_processor import MyProcessor

PROCESSOR_REGISTRY = {
    # Existing processors...
    "my_processor": MyProcessor,
}
```

## Error Handling

The Data Processing module provides robust error handling:

- Connector errors are caught and reported in the pipeline results
- Processor errors are caught and handled according to the pipeline's error handling configuration
- The pipeline can be configured to continue processing despite errors or to fail on the first error

## Logging

The module uses the logging system from the core module:

```python
from core.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing data...")
logger.error("An error occurred")
```

## Configuration

The module can be configured through the pipeline configuration:

- Connector-specific configuration
- Processor-specific configuration
- Pipeline-level configuration (concurrency, error handling, etc.)

See the example configuration in the Usage section for details.