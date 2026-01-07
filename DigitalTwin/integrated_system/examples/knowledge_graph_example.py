#!/usr/bin/env python3
"""
Knowledge Graph Example

This script demonstrates the functionality of the integrated knowledge graph system.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/knowledge_graph_example.log")
    ]
)
logger = logging.getLogger(__name__)

# Import knowledge graph
from integrated_system.knowledge_graph import KnowledgeGraph

async def main():
    """Main function to demonstrate knowledge graph functionality."""
    logger.info("Starting Knowledge Graph Example")
    
    # Create and initialize knowledge graph
    logger.info("Creating knowledge graph")
    kg = KnowledgeGraph()
    await kg.initialize()
    
    # Process some text to extract entities and relationships
    logger.info("Processing text to extract entities and relationships")
    
    # Example text about technology companies
    tech_text = """
    Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
    Tim Cook is the CEO of Apple. Apple was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne.
    Apple develops and sells consumer electronics, computer software, and online services.
    
    Microsoft Corporation is an American multinational technology company with headquarters in Redmond, Washington.
    Satya Nadella is the CEO of Microsoft. Microsoft was founded by Bill Gates and Paul Allen.
    Microsoft develops and sells computer software, consumer electronics, and personal computers.
    
    Google is a technology company that specializes in Internet-related services and products.
    Sundar Pichai is the CEO of Google. Google was founded by Larry Page and Sergey Brin.
    Google is known for its search engine, but also offers services such as cloud computing and software.
    """
    
    tech_results = await kg.process_text(tech_text, context={"domain": "technology", "source": "example"})
    logger.info(f"Extracted {len(tech_results['entities'])} entities and {len(tech_results['relationships'])} relationships from technology text")
    
    # Example text about universities
    university_text = """
    Harvard University is a private Ivy League research university in Cambridge, Massachusetts.
    Harvard was established in 1636 and is the oldest institution of higher education in the United States.
    
    Stanford University is a private research university in Stanford, California.
    Stanford was founded in 1885 by Leland and Jane Stanford in memory of their only child.
    
    MIT (Massachusetts Institute of Technology) is a private research university in Cambridge, Massachusetts.
    MIT was founded in 1861 and is known for its research and education in physical sciences and engineering.
    """
    
    university_results = await kg.process_text(university_text, context={"domain": "education", "source": "example"})
    logger.info(f"Extracted {len(university_results['entities'])} entities and {len(university_results['relationships'])} relationships from university text")
    
    # Add some entities and relationships manually
    logger.info("Adding entities and relationships manually")
    
    # Add AI as a concept
    ai_entity = await kg.add_entity(
        entity_text="Artificial Intelligence",
        entity_type="CONCEPT",
        properties={
            "abbreviation": "AI",
            "definition": "The simulation of human intelligence processes by machines"
        }
    )
    logger.info(f"Added AI entity: {ai_entity['id']}")
    
    # Add machine learning as a concept
    ml_entity = await kg.add_entity(
        entity_text="Machine Learning",
        entity_type="CONCEPT",
        properties={
            "abbreviation": "ML",
            "definition": "A subset of AI that enables systems to learn and improve from experience"
        }
    )
    logger.info(f"Added ML entity: {ml_entity['id']}")
    
    # Add relationship between AI and ML
    ai_ml_rel = await kg.add_relationship(
        source_id=ai_entity['id'],
        target_id=ml_entity['id'],
        relationship_type="INCLUDES",
        properties={
            "description": "AI includes machine learning as a subset"
        },
        confidence=0.9
    )
    logger.info(f"Added relationship: {ai_ml_rel.get('id', 'Unknown')}")
    
    # Add relationships between companies and AI
    for company_name in ["Google", "Microsoft", "Apple"]:
        # Search for company entity
        company_entities = await kg.query_entities({"text": company_name})
        
        if company_entities:
            company_entity = company_entities[0]
            
            # Add relationship to AI
            company_ai_rel = await kg.add_relationship(
                source_id=company_entity['id'],
                target_id=ai_entity['id'],
                relationship_type="DEVELOPS",
                properties={
                    "description": f"{company_name} develops AI technologies"
                },
                confidence=0.8
            )
            logger.info(f"Added relationship: {company_ai_rel.get('id', 'Unknown')}")
    
    # Query entities
    logger.info("Querying entities")
    
    # Query companies
    companies = await kg.query_entities({"type": "ORG"}, limit=10)
    logger.info(f"Found {len(companies)} companies/organizations")
    
    # Query people
    people = await kg.query_entities({"type": "PERSON"}, limit=10)
    logger.info(f"Found {len(people)} people")
    
    # Query concepts
    concepts = await kg.query_entities({"type": "CONCEPT"}, limit=10)
    logger.info(f"Found {len(concepts)} concepts")
    
    # Find relationships between entities
    logger.info("Finding relationships between entities")
    
    # Find relationships for Apple
    apple_entities = await kg.query_entities({"text": "Apple"})
    if apple_entities:
        apple_entity = apple_entities[0]
        apple_neighbors = await kg.get_entity_neighbors(apple_entity['id'])
        logger.info(f"Apple has {len(apple_neighbors)} neighboring entities")
        
        # Print some neighbor information
        for i, neighbor in enumerate(apple_neighbors[:3]):  # Show first 3 neighbors
            logger.info(f"Neighbor {i+1}: {neighbor['entity']['text']} ({neighbor['relationship']['type']})")
    
    # Find path between entities
    logger.info("Finding paths between entities")
    
    # Find path between Google and Harvard
    google_entities = await kg.query_entities({"text": "Google"})
    harvard_entities = await kg.query_entities({"text": "Harvard"})
    
    if google_entities and harvard_entities:
        google_entity = google_entities[0]
        harvard_entity = harvard_entities[0]
        
        path = await kg.find_path(google_entity['id'], harvard_entity['id'], max_depth=4)
        
        if path:
            logger.info(f"Found path from Google to Harvard with {len(path)} elements")
            
            # Print path
            path_str = ""
            for i, item in enumerate(path):
                if item['type'] == 'entity':
                    path_str += item['data']['text']
                else:
                    path_str += f" --[{item['data']['type']}]--> "
            
            logger.info(f"Path: {path_str}")
        else:
            logger.info("No path found between Google and Harvard")
    
    # Perform semantic search
    logger.info("Performing semantic search")
    
    # Search for technology companies
    tech_search = await kg.semantic_search("technology company software", limit=5)
    logger.info(f"Found {len(tech_search)} entities related to 'technology company software'")
    
    # Print search results
    for i, result in enumerate(tech_search):
        logger.info(f"Result {i+1}: {result['entity']['text']} (Score: {result['score']:.2f})")
    
    # Create visualizations
    logger.info("Creating visualizations")
    
    # Create graph visualization
    try:
        # Get some entity IDs for visualization
        entity_ids = []
        for entity_type in ["ORG", "PERSON", "CONCEPT"]:
            entities = await kg.query_entities({"type": entity_type}, limit=5)
            entity_ids.extend([entity['id'] for entity in entities])
        
        # Create visualization
        visualization = await kg.create_graph_visualization(
            entity_ids=entity_ids,
            include_relationships=True,
            layout='spring',
            width=1200,
            height=800
        )
        
        # Save visualization to file
        if 'image_data' in visualization:
            import base64
            
            # Create directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Save image
            with open("output/knowledge_graph.png", "wb") as f:
                f.write(base64.b64decode(visualization['image_data']))
            
            logger.info("Saved graph visualization to output/knowledge_graph.png")
        else:
            logger.warning("Visualization libraries not available")
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
    
    # Create interactive visualization
    try:
        interactive_viz = await kg.create_interactive_visualization(
            entity_ids=entity_ids,
            include_relationships=True
        )
        
        # Save HTML to file
        if 'html' in interactive_viz:
            # Create directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Save HTML
            with open("output/knowledge_graph_interactive.html", "w") as f:
                f.write(interactive_viz['html'])
            
            logger.info("Saved interactive visualization to output/knowledge_graph_interactive.html")
        else:
            logger.warning("Interactive visualization not available")
    except Exception as e:
        logger.error(f"Error creating interactive visualization: {str(e)}")
    
    # Get graph statistics
    logger.info("Getting graph statistics")
    stats = await kg.get_graph_stats()
    logger.info(f"Knowledge graph has {stats['entity_count']} entities and {stats['relationship_count']} relationships")
    logger.info(f"Entity types: {', '.join(stats['entity_type_counts'].keys())}")
    logger.info(f"Relationship types: {', '.join(stats['relationship_type_counts'].keys())}")
    
    logger.info("Knowledge Graph Example completed")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    
    # Run the example
    asyncio.run(main())