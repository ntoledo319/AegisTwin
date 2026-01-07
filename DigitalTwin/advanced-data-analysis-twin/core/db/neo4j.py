"""
Neo4j graph database client for the Advanced Data Analysis & Digital Twin System.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Neo4j graph database client.
    """
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Neo4j client.
        
        Parameters:
        - uri: Neo4j connection URI
        - user: Neo4j username
        - password: Neo4j password
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    async def connect(self) -> None:
        """
        Connect to Neo4j.
        
        Raises:
        - ServiceUnavailable: If connection fails
        - AuthError: If authentication fails
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j: {self.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from Neo4j.
        """
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Disconnected from Neo4j")
    
    async def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Run a Cypher query.
        
        Parameters:
        - query: Cypher query
        - parameters: Query parameters
        
        Returns:
        - List of records as dictionaries
        
        Raises:
        - ValueError: If not connected to Neo4j
        - Exception: If query execution fails
        """
        if not self.driver:
            raise ValueError("Not connected to Neo4j")
        
        parameters = parameters or {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to execute Neo4j query: {e}")
            raise
    
    async def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Create a node in the graph.
        
        Parameters:
        - label: Node label
        - properties: Node properties
        
        Returns:
        - ID of the created node
        
        Raises:
        - Exception: If node creation fails
        """
        query = f"CREATE (n:{label} $properties) RETURN id(n) as id"
        result = await self.run_query(query, {"properties": properties})
        return str(result[0]["id"])
    
    async def create_relationship(self, from_node_id: str, to_node_id: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a relationship between nodes.
        
        Parameters:
        - from_node_id: ID of the source node
        - to_node_id: ID of the target node
        - relationship_type: Type of relationship
        - properties: Relationship properties
        
        Returns:
        - ID of the created relationship
        
        Raises:
        - Exception: If relationship creation fails
        """
        properties = properties or {}
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{relationship_type} $properties]->(b)
        RETURN id(r) as id
        """
        result = await self.run_query(query, {
            "from_id": int(from_node_id),
            "to_id": int(to_node_id),
            "properties": properties
        })
        return str(result[0]["id"])
    
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.
        
        Parameters:
        - node_id: ID of the node
        
        Returns:
        - Node properties and labels
        
        Raises:
        - Exception: If query fails
        """
        query = """
        MATCH (n)
        WHERE id(n) = $id
        RETURN n, labels(n) as labels
        """
        result = await self.run_query(query, {"id": int(node_id)})
        if not result:
            return None
        
        node = dict(result[0]["n"])
        node["labels"] = result[0]["labels"]
        return node
    
    async def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by ID.
        
        Parameters:
        - relationship_id: ID of the relationship
        
        Returns:
        - Relationship properties and type
        
        Raises:
        - Exception: If query fails
        """
        query = """
        MATCH ()-[r]->()
        WHERE id(r) = $id
        RETURN r, type(r) as type
        """
        result = await self.run_query(query, {"id": int(relationship_id)})
        if not result:
            return None
        
        relationship = dict(result[0]["r"])
        relationship["type"] = result[0]["type"]
        return relationship
    
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update a node's properties.
        
        Parameters:
        - node_id: ID of the node
        - properties: New properties
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - Exception: If update fails
        """
        query = """
        MATCH (n)
        WHERE id(n) = $id
        SET n += $properties
        RETURN n
        """
        result = await self.run_query(query, {
            "id": int(node_id),
            "properties": properties
        })
        return len(result) > 0
    
    async def update_relationship(self, relationship_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update a relationship's properties.
        
        Parameters:
        - relationship_id: ID of the relationship
        - properties: New properties
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - Exception: If update fails
        """
        query = """
        MATCH ()-[r]->()
        WHERE id(r) = $id
        SET r += $properties
        RETURN r
        """
        result = await self.run_query(query, {
            "id": int(relationship_id),
            "properties": properties
        })
        return len(result) > 0
    
    async def delete_node(self, node_id: str) -> bool:
        """
        Delete a node.
        
        Parameters:
        - node_id: ID of the node
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - Exception: If deletion fails
        """
        query = """
        MATCH (n)
        WHERE id(n) = $id
        DETACH DELETE n
        """
        await self.run_query(query, {"id": int(node_id)})
        return True
    
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.
        
        Parameters:
        - relationship_id: ID of the relationship
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - Exception: If deletion fails
        """
        query = """
        MATCH ()-[r]->()
        WHERE id(r) = $id
        DELETE r
        """
        await self.run_query(query, {"id": int(relationship_id)})
        return True
    
    async def find_nodes(self, labels: Optional[Union[str, List[str]]] = None, properties: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find nodes by labels and properties.
        
        Parameters:
        - labels: Node label(s)
        - properties: Node properties to match
        - limit: Maximum number of nodes to return
        
        Returns:
        - List of nodes
        
        Raises:
        - Exception: If query fails
        """
        properties = properties or {}
        
        if labels:
            if isinstance(labels, list):
                label_str = ":".join(labels)
            else:
                label_str = labels
            
            query = f"""
            MATCH (n:{label_str})
            WHERE ALL(key IN keys($properties) WHERE n[key] = $properties[key])
            RETURN n, id(n) as id, labels(n) as labels
            LIMIT $limit
            """
        else:
            query = """
            MATCH (n)
            WHERE ALL(key IN keys($properties) WHERE n[key] = $properties[key])
            RETURN n, id(n) as id, labels(n) as labels
            LIMIT $limit
            """
        
        result = await self.run_query(query, {
            "properties": properties,
            "limit": limit
        })
        
        nodes = []
        for record in result:
            node = dict(record["n"])
            node["id"] = str(record["id"])
            node["labels"] = record["labels"]
            nodes.append(node)
        
        return nodes
    
    async def find_relationships(self, relationship_type: Optional[str] = None, properties: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find relationships by type and properties.
        
        Parameters:
        - relationship_type: Type of relationship
        - properties: Relationship properties to match
        - limit: Maximum number of relationships to return
        
        Returns:
        - List of relationships
        
        Raises:
        - Exception: If query fails
        """
        properties = properties or {}
        
        if relationship_type:
            query = f"""
            MATCH (a)-[r:{relationship_type}]->(b)
            WHERE ALL(key IN keys($properties) WHERE r[key] = $properties[key])
            RETURN r, id(r) as id, type(r) as type, id(a) as from_id, id(b) as to_id
            LIMIT $limit
            """
        else:
            query = """
            MATCH (a)-[r]->(b)
            WHERE ALL(key IN keys($properties) WHERE r[key] = $properties[key])
            RETURN r, id(r) as id, type(r) as type, id(a) as from_id, id(b) as to_id
            LIMIT $limit
            """
        
        result = await self.run_query(query, {
            "properties": properties,
            "limit": limit
        })
        
        relationships = []
        for record in result:
            relationship = dict(record["r"])
            relationship["id"] = str(record["id"])
            relationship["type"] = record["type"]
            relationship["from_id"] = str(record["from_id"])
            relationship["to_id"] = str(record["to_id"])
            relationships.append(relationship)
        
        return relationships

# Singleton instance
neo4j_client = Neo4jClient()