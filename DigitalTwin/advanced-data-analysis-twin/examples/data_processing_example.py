#!/usr/bin/env python3
"""
Example script demonstrating the data processing pipeline with various connectors and processors.
"""

import asyncio
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

from data_processing import (
    create_pipeline,
    get_available_connectors,
    get_available_processors,
    MessagingConnector,
    SocialMediaConnector,
    ProductivityConnector,
    TextProcessor,
    EntityProcessor,
    NormalizationProcessor
)

async def run_pipeline_example(config_file: str = None):
    """
    Run a data processing pipeline example.
    
    Args:
        config_file: Path to pipeline configuration file
    """
    # Load configuration if provided
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Use default configuration
        config = {
            "pipeline_id": "example_pipeline",
            "connectors": [
                {
                    "connector_id": "messaging_connector",
                    "type": "messaging",
                    "platform": "whatsapp",
                    "source_path": "data/examples/whatsapp_chat.txt"
                },
                {
                    "connector_id": "social_connector",
                    "type": "social",
                    "platform": "twitter",
                    "source_path": "data/examples/twitter_export"
                },
                {
                    "connector_id": "productivity_connector",
                    "type": "productivity",
                    "platform": "google",
                    "source_path": "data/examples/google_export"
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
                },
                {
                    "processor_id": "normalization_processor",
                    "type": "normalization",
                    "lowercase": True,
                    "remove_punctuation": False,
                    "remove_whitespace": True
                }
            ],
            "max_concurrent_tasks": 3,
            "error_handling": "continue"
        }
    
    # Create example data directories if they don't exist
    os.makedirs("data/examples", exist_ok=True)
    
    # Create example WhatsApp chat file if it doesn't exist
    whatsapp_file = Path("data/examples/whatsapp_chat.txt")
    if not whatsapp_file.exists():
        with open(whatsapp_file, 'w') as f:
            f.write("""[09/26/2023, 10:15:30] John Doe: Hello everyone! Welcome to the project team.
[09/26/2023, 10:16:45] Jane Smith: Thanks John! I'm excited to work on this project.
[09/26/2023, 10:18:20] Alex Johnson: Me too! When is our first meeting?
[09/26/2023, 10:20:05] John Doe: Let's schedule it for tomorrow at 2 PM.
[09/26/2023, 10:21:30] Jane Smith: Works for me. Should we invite the client?
[09/26/2023, 10:23:15] John Doe: Yes, I'll send an invite to everyone including the client from Acme Corp.
[09/26/2023, 10:25:00] Alex Johnson: Great! I'll prepare the presentation slides.
""")
    
    # Create example Twitter export directory if it doesn't exist
    twitter_dir = Path("data/examples/twitter_export")
    twitter_dir.mkdir(exist_ok=True)
    
    # Create example tweet.js file if it doesn't exist
    tweet_file = twitter_dir / "tweet.js"
    if not tweet_file.exists():
        with open(tweet_file, 'w') as f:
            f.write("""window.YTD.tweet.part0 = [
  {
    "tweet" : {
      "id" : "1234567890",
      "created_at" : "Wed Sep 26 15:30:45 +0000 2023",
      "full_text" : "Just started working on an exciting new AI project with @JaneSmith and @AlexJohnson! #MachineLearning #AI",
      "user" : {
        "screen_name" : "JohnDoe"
      },
      "entities" : {
        "hashtags" : [
          {"text": "MachineLearning"},
          {"text": "AI"}
        ],
        "user_mentions" : [
          {"screen_name": "JaneSmith"},
          {"screen_name": "AlexJohnson"}
        ]
      },
      "favorite_count" : 25,
      "retweet_count" : 10
    }
  },
  {
    "tweet" : {
      "id" : "1234567891",
      "created_at" : "Wed Sep 26 16:45:30 +0000 2023",
      "full_text" : "Our team meeting with Acme Corp went really well today. Looking forward to the next steps! #ProjectSuccess",
      "user" : {
        "screen_name" : "JohnDoe"
      },
      "entities" : {
        "hashtags" : [
          {"text": "ProjectSuccess"}
        ],
        "user_mentions" : []
      },
      "favorite_count" : 15,
      "retweet_count" : 5
    }
  }
]""")
    
    # Create example Google export directory if it doesn't exist
    google_dir = Path("data/examples/google_export")
    google_dir.mkdir(exist_ok=True)
    
    # Create example Docs directory if it doesn't exist
    docs_dir = google_dir / "Drive" / "Docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create example document file if it doesn't exist
    doc_file = docs_dir / "Project_Plan.html"
    if not doc_file.exists():
        with open(doc_file, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Project Plan</title>
</head>
<body>
    <h1>Project Plan: AI Integration</h1>
    <h2>Team Members</h2>
    <ul>
        <li>John Doe (Project Manager)</li>
        <li>Jane Smith (Data Scientist)</li>
        <li>Alex Johnson (Software Engineer)</li>
    </ul>
    <h2>Client</h2>
    <p>Acme Corporation</p>
    <h2>Timeline</h2>
    <p>Start Date: October 1, 2023</p>
    <p>End Date: December 15, 2023</p>
    <h2>Objectives</h2>
    <ol>
        <li>Integrate machine learning models into existing systems</li>
        <li>Develop predictive analytics dashboard</li>
        <li>Train client team on AI capabilities</li>
    </ol>
    <h2>Budget</h2>
    <p>Total Budget: $150,000</p>
</body>
</html>""")
    
    print("Creating data processing pipeline...")
    pipeline = await create_pipeline(config)
    
    print("Running pipeline...")
    results = await pipeline.run({
        "connector_parameters": {
            "messaging_connector": {
                "max_messages": 10
            },
            "social_connector": {
                "content_types": ["posts"]
            },
            "productivity_connector": {
                "content_types": ["docs"]
            }
        },
        "processor_parameters": {}
    })
    
    print("\nPipeline execution completed!")
    print(f"Extracted {results['summary']['total_items_extracted']} items")
    print(f"Processed {results['summary']['total_items_processed']} items")
    print(f"Processing time: {results['summary']['processing_time']:.2f} seconds")
    
    # Save results to file
    output_dir = Path("data/results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "pipeline_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    # Print some example insights
    print("\nExample insights from processed data:")
    
    # Extract entities from text content
    all_entities = []
    for connector_id, connector_result in results["connector_results"].items():
        if connector_result.get("success", False):
            for item in connector_result.get("data", []):
                content = item.get("content", "")
                if content:
                    # Process content with entity processor
                    entity_processor = EntityProcessor()
                    entity_result = await entity_processor.process_text(content)
                    all_entities.extend(entity_result.get("entities", []))
    
    # Count entity types
    entity_types = {}
    for entity in all_entities:
        entity_type = entity.get("type", "UNKNOWN")
        if entity_type not in entity_types:
            entity_types[entity_type] = 0
        entity_types[entity_type] += 1
    
    print("\nEntity types found:")
    for entity_type, count in entity_types.items():
        print(f"  - {entity_type}: {count}")
    
    # Extract top entities
    entity_texts = {}
    for entity in all_entities:
        entity_text = entity.get("text", "").lower()
        entity_type = entity.get("type", "UNKNOWN")
        if entity_text:
            key = f"{entity_type}:{entity_text}"
            if key not in entity_texts:
                entity_texts[key] = 0
            entity_texts[key] += 1
    
    print("\nTop entities:")
    sorted_entities = sorted(entity_texts.items(), key=lambda x: x[1], reverse=True)[:10]
    for entity_key, count in sorted_entities:
        entity_type, entity_text = entity_key.split(":", 1)
        print(f"  - {entity_text} ({entity_type}): {count}")

def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="Data Processing Pipeline Example")
    parser.add_argument("--config", help="Path to pipeline configuration file")
    args = parser.parse_args()
    
    # Print available connectors and processors
    print("Available connectors:")
    for connector_type, description in get_available_connectors().items():
        print(f"  - {connector_type}: {description}")
    
    print("\nAvailable processors:")
    for processor_type, description in get_available_processors().items():
        print(f"  - {processor_type}: {description}")
    
    # Run the pipeline example
    asyncio.run(run_pipeline_example(args.config))

if __name__ == "__main__":
    main()