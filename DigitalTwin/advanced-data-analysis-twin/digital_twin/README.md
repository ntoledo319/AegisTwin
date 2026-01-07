# Digital Twin Documentation

## Overview

The Digital Twin is a core component of the Advanced Data Analysis & Digital Twin System. It creates a virtual mental model of the user, enabling meaningful conversation and personalized interaction. This document provides an overview of the Digital Twin components and how to use them.

## Components

The Digital Twin consists of three main components:

1. **Personality Engine**: Models and evolves the user's personality based on their data.
2. **Memory System**: Stores and retrieves different types of memories about the user and their interactions.
3. **Conversation Engine**: Enables natural, context-aware conversations with the user.

## Installation

The Digital Twin components are part of the Advanced Data Analysis & Digital Twin System. To install the system, follow these steps:

```bash
# Clone the repository
git clone https://github.com/your-organization/advanced-data-analysis-twin.git

# Navigate to the project directory
cd advanced-data-analysis-twin

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The Digital Twin components can be configured using a YAML configuration file. The default configuration file is located at `config/digital_twin.yaml`. You can specify a different configuration file using the `DIGITAL_TWIN_CONFIG_PATH` environment variable.

Example configuration:

```yaml
personality_engine:
  learning_rate: 0.1
  stability_factors:
    openness: 0.5
    conscientiousness: 0.7
    extraversion: 0.6
    agreeableness: 0.6
    neuroticism: 0.5
  alignment_strength: 0.7

memory_system:
  episodic_memory_dir: "data/memories/episodic"
  semantic_memory_dir: "data/memories/semantic"
  procedural_memory_dir: "data/memories/procedural"
  index_dir: "data/memories/index"
  consolidation_interval: 86400  # 24 hours in seconds
  importance_threshold: 0.5

conversation_engine:
  max_context_history: 10
  max_topics_history: 5
  max_entities_history: 20
  max_intents_history: 5
  llm_provider: "openai"
  llm_model: "gpt-4"
  temperature: 0.7
  max_tokens: 500
```

## Usage

### Basic Usage

Here's a simple example of how to use the Digital Twin components:

```python
import asyncio
from digital_twin import PersonalityEngine, MemorySystem, ConversationEngine
from digital_twin.config import get_config

async def main():
    # Get configuration
    config = get_config()
    
    # Initialize components
    personality_engine = PersonalityEngine(config.get_section("personality_engine"))
    memory_system = MemorySystem(config.get_section("memory_system"))
    conversation_engine = ConversationEngine(
        personality_engine=personality_engine,
        memory_system=memory_system,
        config=config.get_section("conversation_engine")
    )
    
    # Extract personality traits
    user_data = {
        "text": {
            "content": "I enjoy hiking and reading science fiction."
        }
    }
    traits = await personality_engine.extract_traits(user_data)
    
    # Create personality profile
    profile = await personality_engine.create_personality_profile("user123", traits)
    
    # Process a conversation message
    response = await conversation_engine.process_message(
        user_id="user123",
        message="Tell me about hiking trails.",
        context={}
    )
    
    print(f"Response: {response['response']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### API Usage

The Digital Twin components are also accessible through the API:

```
POST /api/digital-twin/conversation/message
{
    "message": "Tell me about hiking trails.",
    "context": {}
}
```

## Component Details

### Personality Engine

The Personality Engine models and evolves the user's personality based on their data. It consists of the following components:

- **PersonalityEngine**: Core class for modeling and evolving user personality
- **PersonalityTraitExtractor**: Base class for extracting personality traits from user data
  - **TextualTraitExtractor**: Extracts traits from written content
  - **CommunicationTraitExtractor**: Extracts traits from messaging patterns
  - **ActivityTraitExtractor**: Extracts traits from app usage and browsing behavior
  - **SocialTraitExtractor**: Extracts traits from social media and contacts
  - **ConsumptionTraitExtractor**: Extracts traits from purchases and media consumption
- **PersonalityEvolutionEngine**: Evolves personality traits over time based on new data
- **PersonalityAlignmentModule**: Aligns responses with the user's personality profile

### Memory System

The Memory System stores and retrieves different types of memories about the user and their interactions. It consists of the following components:

- **MemorySystem**: Core class for managing different types of memories
- **EpisodicMemory**: Stores and retrieves event-based memories
- **SemanticMemory**: Stores and retrieves factual knowledge
- **ProceduralMemory**: Stores and retrieves skills and procedures
- **MemoryIndex**: Indexes memories for efficient retrieval

### Conversation Engine

The Conversation Engine enables natural, context-aware conversations with the user. It consists of the following components:

- **ConversationEngine**: Core class for natural conversations
- **ContextManager**: Manages conversation context and history
- **ResponseGenerator**: Generates responses based on user messages, context, and memories
- **ConversationAnalyzer**: Analyzes user messages for intent, sentiment, and topics

## Cognitive-Twin Omega Integration

The Digital Twin integrates with Cognitive-Twin Omega for advanced pattern recognition and behavioral analysis:

- **BehavioralPatternAnalyzer**: Adapter for Cognitive-Twin Omega's PatternHydra
- Integration with pattern recognition capabilities

## API Reference

### Conversation API

- `POST /api/digital-twin/conversation/message`: Process a user message and generate a response
- `POST /api/digital-twin/conversation/start`: Start a new conversation
- `POST /api/digital-twin/conversation/end`: End a conversation

### Memory API

- `POST /api/digital-twin/memory`: Store a memory
- `GET /api/digital-twin/memory/{memory_id}`: Get a memory by ID
- `PUT /api/digital-twin/memory/{memory_id}`: Update a memory
- `DELETE /api/digital-twin/memory/{memory_id}`: Delete a memory
- `POST /api/digital-twin/memory/query`: Query memories
- `POST /api/digital-twin/memory/consolidate`: Consolidate memories

### Personality API

- `GET /api/digital-twin/personality/profile`: Get a user's personality profile
- `POST /api/digital-twin/personality/extract`: Extract personality traits from user data
- `POST /api/digital-twin/personality/create-profile`: Create a personality profile from traits
- `PUT /api/digital-twin/personality/update-profile`: Update a personality profile with new data

## Examples

For more examples, see the `examples` directory:

- `digital_twin_example.py`: Demonstrates basic usage of the Digital Twin components

## Contributing

Contributions to the Digital Twin components are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.