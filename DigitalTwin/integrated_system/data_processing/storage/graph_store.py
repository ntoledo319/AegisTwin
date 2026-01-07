"""
Graph store for the integrated system.
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime

from core.config import config
from core.db import db_manager

logger = logging.getLogger(__name__)

class GraphStore:
    """Graph store for storing and retrieving graph data."""
    
    def __init__(self):
        """Initialize the graph store."""
        self.neo4j_driver = None
        self.storage_dir = config.get("storage.data_dir", "data")
        
    async def initialize(self):
        """Initialize the graph store."""
        logger.info("Initializing graph store...")
        
        # Create storage directory if it doesn't exist
        graph_dir = os.path.join(self.storage_dir, "graphs")
        os.makedirs(graph_dir, exist_ok=True)
        
        # Get Neo4j driver
        self.neo4j_driver = db_manager.neo4j_driver
        
        logger.info("Graph store initialization complete")
        
    async def create_node(self, 
                         label: str, 
                         properties: Dict[str, Any]) -> str:
        """
        Create a node in the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Node ID
        """
        try:
            # Generate node ID if not provided
            if "id" not in properties:
                properties["id"] = f"{label}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(properties))}"
                
            # Add metadata
            properties["created_at"] = datetime.now().isoformat()
            
            # Create node in Neo4j
            if self.neo4j_driver:
                query = f"""
                CREATE (n:{label} $properties)
                RETURN n.id as id
                """
                
                result = await self.neo4j_driver.run_query(query, {"properties": properties})
                
                if result and len(result) > 0:
                    return result[0]["id"]
                    
            # Store in file system
            node_data = {
                "label": label,
                "properties": properties
            }
            
            graph_dir = os.path.join(self.storage_dir, "graphs", "nodes")
            os.makedirs(graph_dir, exist_ok=True)
            
            node_path = os.path.join(graph_dir, f"{properties['id']}.json")
            
            with open(node_path, 'w', encoding='utf-8') as f:
                json.dump(node_data, f, default=self._json_serializer)
                
            logger.info(f"Created node: {properties['id']}")
            
            return properties["id"]
            
        except Exception as e:
            logger.error(f"Error creating node: {str(e)}")
            raise
            
    async def create_relationship(self, 
                                 source_id: str, 
                                 target_id: str,
                                 type_name: str,
                                 properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a relationship between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            type_name: Relationship type
            properties: Optional relationship properties
            
        Returns:
            Relationship ID
        """
        try:
            # Initialize properties if not provided
            properties = properties or {}
            
            # Generate relationship ID if not provided
            if "id" not in properties:
                properties["id"] = f"{type_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(source_id + target_id)}"
                
            # Add metadata
            properties["created_at"] = datetime.now().isoformat()
            properties["source_id"] = source_id
            properties["target_id"] = target_id
            
            # Create relationship in Neo4j
            if self.neo4j_driver:
                query = f"""
                MATCH (source), (target)
                WHERE source.id = $source_id AND target.id = $target_id
                CREATE (source)-[r:{type_name} $properties]->(target)
                RETURN r.id as id
                """
                
                result = await self.neo4j_driver.run_query(
                    query, 
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "properties": properties
                    }
                )
                
                if result and len(result) > 0:
                    return result[0]["id"]
                    
            # Store in file system
            relationship_data = {
                "source_id": source_id,
                "target_id": target_id,
                "type": type_name,
                "properties": properties
            }
            
            graph_dir = os.path.join(self.storage_dir, "graphs", "relationships")
            os.makedirs(graph_dir, exist_ok=True)
            
            relationship_path = os.path.join(graph_dir, f"{properties['id']}.json")
            
            with open(relationship_path, 'w', encoding='utf-8') as f:
                json.dump(relationship_data, f, default=self._json_serializer)
                
            logger.info(f"Created relationship: {properties['id']}")
            
            return properties["id"]
            
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise
            
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node or None if not found
        """
        try:
            # Try to get from Neo4j
            if self.neo4j_driver:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                RETURN n
                """
                
                result = await self.neo4j_driver.run_query(query, {"node_id": node_id})
                
                if result and len(result) > 0:
                    return result[0]["n"]
                    
            # Try to get from file system
            node_path = os.path.join(self.storage_dir, "graphs", "nodes", f"{node_id}.json")
            
            if os.path.exists(node_path):
                with open(node_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            logger.warning(f"Node not found: {node_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting node: {str(e)}")
            return None
            
    async def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            Relationship or None if not found
        """
        try:
            # Try to get from Neo4j
            if self.neo4j_driver:
                query = """
                MATCH ()-[r]->()
                WHERE r.id = $relationship_id
                RETURN r
                """
                
                result = await self.neo4j_driver.run_query(query, {"relationship_id": relationship_id})
                
                if result and len(result) > 0:
                    return result[0]["r"]
                    
            # Try to get from file system
            relationship_path = os.path.join(self.storage_dir, "graphs", "relationships", f"{relationship_id}.json")
            
            if os.path.exists(relationship_path):
                with open(relationship_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            logger.warning(f"Relationship not found: {relationship_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting relationship: {str(e)}")
            return None
            
    async def query_nodes(self, 
                         labels: Optional[List[str]] = None,
                         properties: Optional[Dict[str, Any]] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query nodes.
        
        Args:
            labels: Optional list of node labels
            properties: Optional node properties
            limit: Maximum number of nodes to return
            
        Returns:
            List of matching nodes
        """
        try:
            # Build query
            if self.neo4j_driver:
                # Build Cypher query
                if labels:
                    label_str = ":".join(labels)
                    query = f"""
                    MATCH (n:{label_str})
                    """
                else:
                    query = """
                    MATCH (n)
                    """
                    
                # Add property conditions
                if properties:
                    conditions = []
                    for key, value in properties.items():
                        conditions.append(f"n.{key} = ${key}")
                        
                    if conditions:
                        query += "WHERE " + " AND ".join(conditions)
                        
                # Add limit
                query += f"""
                RETURN n
                LIMIT {limit}
                """
                
                # Execute query
                result = await self.neo4j_driver.run_query(query, properties or {})
                
                if result:
                    return [record["n"] for record in result]
                    
            # Fall back to file system
            nodes = []
            nodes_dir = os.path.join(self.storage_dir, "graphs", "nodes")
            
            if os.path.exists(nodes_dir):
                for filename in os.listdir(nodes_dir):
                    if filename.endswith(".json"):
                        node_path = os.path.join(nodes_dir, filename)
                        with open(node_path, 'r', encoding='utf-8') as f:
                            node = json.load(f)
                            
                            # Filter by labels
                            if labels and node["label"] not in labels:
                                continue
                                
                            # Filter by properties
                            if properties:
                                match = True
                                for key, value in properties.items():
                                    if key not in node["properties"] or node["properties"][key] != value:
                                        match = False
                                        break
                                        
                                if not match:
                                    continue
                                    
                            nodes.append(node)
                            
                            if len(nodes) >= limit:
                                break
                                
            return nodes
            
        except Exception as e:
            logger.error(f"Error querying nodes: {str(e)}")
            return []
            
    async def query_relationships(self, 
                                 types: Optional[List[str]] = None,
                                 properties: Optional[Dict[str, Any]] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query relationships.
        
        Args:
            types: Optional list of relationship types
            properties: Optional relationship properties
            limit: Maximum number of relationships to return
            
        Returns:
            List of matching relationships
        """
        try:
            # Build query
            if self.neo4j_driver:
                # Build Cypher query
                if types:
                    type_str = "|".join([f":{t}" for t in types])
                    query = f"""
                    MATCH ()-[r{type_str}]->()
                    """
                else:
                    query = """
                    MATCH ()-[r]->()
                    """
                    
                # Add property conditions
                if properties:
                    conditions = []
                    for key, value in properties.items():
                        conditions.append(f"r.{key} = ${key}")
                        
                    if conditions:
                        query += "WHERE " + " AND ".join(conditions)
                        
                # Add limit
                query += f"""
                RETURN r
                LIMIT {limit}
                """
                
                # Execute query
                result = await self.neo4j_driver.run_query(query, properties or {})
                
                if result:
                    return [record["r"] for record in result]
                    
            # Fall back to file system
            relationships = []
            relationships_dir = os.path.join(self.storage_dir, "graphs", "relationships")
            
            if os.path.exists(relationships_dir):
                for filename in os.listdir(relationships_dir):
                    if filename.endswith(".json"):
                        relationship_path = os.path.join(relationships_dir, filename)
                        with open(relationship_path, 'r', encoding='utf-8') as f:
                            relationship = json.load(f)
                            
                            # Filter by types
                            if types and relationship["type"] not in types:
                                continue
                                
                            # Filter by properties
                            if properties:
                                match = True
                                for key, value in properties.items():
                                    if key not in relationship["properties"] or relationship["properties"][key] != value:
                                        match = False
                                        break
                                        
                                if not match:
                                    continue
                                    
                            relationships.append(relationship)
                            
                            if len(relationships) >= limit:
                                break
                                
            return relationships
            
        except Exception as e:
            logger.error(f"Error querying relationships: {str(e)}")
            return []
            
    async def get_neighbors(self, 
                           node_id: str,
                           direction: str = "both",
                           types: Optional[List[str]] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get neighbors of a node.
        
        Args:
            node_id: Node ID
            direction: Direction of relationships ("outgoing", "incoming", or "both")
            types: Optional list of relationship types
            limit: Maximum number of neighbors to return
            
        Returns:
            List of neighboring nodes with their relationships
        """
        try:
            # Build query
            if self.neo4j_driver:
                # Build Cypher query based on direction
                if direction == "outgoing":
                    if types:
                        type_str = "|".join([f":{t}" for t in types])
                        query = f"""
                        MATCH (n)-[r{type_str}]->(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                    else:
                        query = f"""
                        MATCH (n)-[r]->(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                elif direction == "incoming":
                    if types:
                        type_str = "|".join([f":{t}" for t in types])
                        query = f"""
                        MATCH (n)<-[r{type_str}]-(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                    else:
                        query = f"""
                        MATCH (n)<-[r]-(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                else:  # both
                    if types:
                        type_str = "|".join([f":{t}" for t in types])
                        query = f"""
                        MATCH (n)-[r{type_str}]-(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                    else:
                        query = f"""
                        MATCH (n)-[r]-(neighbor)
                        WHERE n.id = $node_id
                        RETURN neighbor, r
                        LIMIT {limit}
                        """
                        
                # Execute query
                result = await self.neo4j_driver.run_query(query, {"node_id": node_id})
                
                if result:
                    return [{"node": record["neighbor"], "relationship": record["r"]} for record in result]
                    
            # Fall back to file system
            neighbors = []
            
            # Get all relationships
            relationships_dir = os.path.join(self.storage_dir, "graphs", "relationships")
            
            if os.path.exists(relationships_dir):
                for filename in os.listdir(relationships_dir):
                    if filename.endswith(".json"):
                        relationship_path = os.path.join(relationships_dir, filename)
                        with open(relationship_path, 'r', encoding='utf-8') as f:
                            relationship = json.load(f)
                            
                            # Filter by direction and node ID
                            if direction == "outgoing" and relationship["source_id"] == node_id:
                                neighbor_id = relationship["target_id"]
                            elif direction == "incoming" and relationship["target_id"] == node_id:
                                neighbor_id = relationship["source_id"]
                            elif direction == "both" and (relationship["source_id"] == node_id or relationship["target_id"] == node_id):
                                neighbor_id = relationship["target_id"] if relationship["source_id"] == node_id else relationship["source_id"]
                            else:
                                continue
                                
                            # Filter by relationship type
                            if types and relationship["type"] not in types:
                                continue
                                
                            # Get neighbor node
                            neighbor_node = await self.get_node(neighbor_id)
                            
                            if neighbor_node:
                                neighbors.append({
                                    "node": neighbor_node,
                                    "relationship": relationship
                                })
                                
                            if len(neighbors) >= limit:
                                break
                                
            return neighbors
            
        except Exception as e:
            logger.error(f"Error getting neighbors: {str(e)}")
            return []
            
    async def update_node(self, 
                         node_id: str, 
                         properties: Dict[str, Any]) -> bool:
        """
        Update a node.
        
        Args:
            node_id: Node ID
            properties: Properties to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in Neo4j
            if self.neo4j_driver:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                SET n += $properties
                RETURN n
                """
                
                result = await self.neo4j_driver.run_query(
                    query, 
                    {
                        "node_id": node_id,
                        "properties": properties
                    }
                )
                
                if result and len(result) > 0:
                    # Update in file system
                    node_path = os.path.join(self.storage_dir, "graphs", "nodes", f"{node_id}.json")
                    
                    if os.path.exists(node_path):
                        with open(node_path, 'r', encoding='utf-8') as f:
                            node_data = json.load(f)
                            
                        # Update properties
                        node_data["properties"].update(properties)
                        
                        with open(node_path, 'w', encoding='utf-8') as f:
                            json.dump(node_data, f, default=self._json_serializer)
                            
                    logger.info(f"Updated node: {node_id}")
                    return True
                    
            # Fall back to file system only
            node_path = os.path.join(self.storage_dir, "graphs", "nodes", f"{node_id}.json")
            
            if os.path.exists(node_path):
                with open(node_path, 'r', encoding='utf-8') as f:
                    node_data = json.load(f)
                    
                # Update properties
                node_data["properties"].update(properties)
                
                with open(node_path, 'w', encoding='utf-8') as f:
                    json.dump(node_data, f, default=self._json_serializer)
                    
                logger.info(f"Updated node: {node_id}")
                return True
                
            logger.warning(f"Node not found for update: {node_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating node: {str(e)}")
            return False
            
    async def update_relationship(self, 
                                 relationship_id: str, 
                                 properties: Dict[str, Any]) -> bool:
        """
        Update a relationship.
        
        Args:
            relationship_id: Relationship ID
            properties: Properties to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in Neo4j
            if self.neo4j_driver:
                query = """
                MATCH ()-[r]->()
                WHERE r.id = $relationship_id
                SET r += $properties
                RETURN r
                """
                
                result = await self.neo4j_driver.run_query(
                    query, 
                    {
                        "relationship_id": relationship_id,
                        "properties": properties
                    }
                )
                
                if result and len(result) > 0:
                    # Update in file system
                    relationship_path = os.path.join(self.storage_dir, "graphs", "relationships", f"{relationship_id}.json")
                    
                    if os.path.exists(relationship_path):
                        with open(relationship_path, 'r', encoding='utf-8') as f:
                            relationship_data = json.load(f)
                            
                        # Update properties
                        relationship_data["properties"].update(properties)
                        
                        with open(relationship_path, 'w', encoding='utf-8') as f:
                            json.dump(relationship_data, f, default=self._json_serializer)
                            
                    logger.info(f"Updated relationship: {relationship_id}")
                    return True
                    
            # Fall back to file system only
            relationship_path = os.path.join(self.storage_dir, "graphs", "relationships", f"{relationship_id}.json")
            
            if os.path.exists(relationship_path):
                with open(relationship_path, 'r', encoding='utf-8') as f:
                    relationship_data = json.load(f)
                    
                # Update properties
                relationship_data["properties"].update(properties)
                
                with open(relationship_path, 'w', encoding='utf-8') as f:
                    json.dump(relationship_data, f, default=self._json_serializer)
                    
                logger.info(f"Updated relationship: {relationship_id}")
                return True
                
            logger.warning(f"Relationship not found for update: {relationship_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating relationship: {str(e)}")
            return False
            
    async def delete_node(self, node_id: str) -> bool:
        """
        Delete a node.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete in Neo4j
            if self.neo4j_driver:
                query = """
                MATCH (n)
                WHERE n.id = $node_id
                DETACH DELETE n
                """
                
                await self.neo4j_driver.run_query(query, {"node_id": node_id})
                
            # Delete from file system
            node_path = os.path.join(self.storage_dir, "graphs", "nodes", f"{node_id}.json")
            
            if os.path.exists(node_path):
                os.remove(node_path)
                
            logger.info(f"Deleted node: {node_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting node: {str(e)}")
            return False
            
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete in Neo4j
            if self.neo4j_driver:
                query = """
                MATCH ()-[r]->()
                WHERE r.id = $relationship_id
                DELETE r
                """
                
                await self.neo4j_driver.run_query(query, {"relationship_id": relationship_id})
                
            # Delete from file system
            relationship_path = os.path.join(self.storage_dir, "graphs", "relationships", f"{relationship_id}.json")
            
            if os.path.exists(relationship_path):
                os.remove(relationship_path)
                
            logger.info(f"Deleted relationship: {relationship_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting relationship: {str(e)}")
            return False
            
    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Run a custom query.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            Query results
        """
        try:
            if self.neo4j_driver:
                return await self.neo4j_driver.run_query(query, parameters or {})
                
            logger.warning("Neo4j driver not available for custom query")
            return []
            
        except Exception as e:
            logger.error(f"Error running query: {str(e)}")
            return []
            
    def _json_serializer(self, obj):
        """
        JSON serializer for objects not serializable by default json code.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")