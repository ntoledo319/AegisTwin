"""
Knowledge graph visualization module.

This module provides functionality for visualizing knowledge graphs,
including graph visualization and interactive exploration.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
import os
from datetime import datetime
import base64
import tempfile

logger = logging.getLogger(__name__)

class KnowledgeGraphVisualization:
    """Visualization for knowledge graphs."""
    
    def __init__(self, query_engine=None):
        """
        Initialize the knowledge graph visualization.
        
        Args:
            query_engine: Knowledge graph query engine instance
        """
        self.query_engine = query_engine
        self.initialized = False
        self.visualization_libraries_available = False
        
        # Try to import visualization libraries
        try:
            import networkx as nx
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            
            self.nx = nx
            self.plt = plt
            self.visualization_libraries_available = True
            logger.info("Visualization libraries available")
        except ImportError:
            logger.warning("Visualization libraries not available")
    
    async def initialize(self):
        """Initialize the knowledge graph visualization."""
        logger.info("Initializing knowledge graph visualization")
        
        # Initialize query engine if provided
        if self.query_engine and not self.query_engine.initialized:
            await self.query_engine.initialize()
        
        self.initialized = True
        logger.info("Knowledge graph visualization initialized")
    
    async def create_graph_visualization(self, entity_ids: List[str] = None, 
                                        include_relationships: bool = True,
                                        layout: str = 'spring',
                                        width: int = 800,
                                        height: int = 600) -> Dict[str, Any]:
        """
        Create a visualization of the knowledge graph.
        
        Args:
            entity_ids: List of entity IDs to include (optional)
            include_relationships: Whether to include relationships
            layout: Graph layout algorithm
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info("Creating graph visualization")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        if not self.query_engine:
            logger.warning("Query engine not available")
            return {'error': "Query engine not available"}
        
        # Get subgraph
        if entity_ids:
            subgraph = await self.query_engine.get_subgraph(entity_ids, include_relationships)
        else:
            # Use all entities (up to a limit)
            all_entity_ids = list(self.query_engine.entities.keys())[:100]  # Limit to 100 entities
            subgraph = await self.query_engine.get_subgraph(all_entity_ids, include_relationships)
        
        # Create NetworkX graph
        G = self.nx.DiGraph()
        
        # Add entities as nodes
        for entity_id, entity in subgraph['entities'].items():
            # Create node attributes
            node_attrs = {
                'label': entity['text'],
                'type': entity['type']
            }
            
            G.add_node(entity_id, **node_attrs)
        
        # Add relationships as edges
        for relationship in subgraph['relationships']:
            source_id = relationship['source']
            target_id = relationship['target']
            
            # Skip if source or target not in graph
            if source_id not in G.nodes or target_id not in G.nodes:
                continue
            
            # Create edge attributes
            edge_attrs = {
                'label': relationship['type'],
                'weight': relationship.get('confidence', 0.5)
            }
            
            G.add_edge(source_id, target_id, **edge_attrs)
        
        # Create visualization
        plt = self.plt
        plt.figure(figsize=(width/100, height/100), dpi=100)
        
        # Choose layout
        if layout == 'spring':
            pos = self.nx.spring_layout(G)
        elif layout == 'circular':
            pos = self.nx.circular_layout(G)
        elif layout == 'kamada_kawai':
            pos = self.nx.kamada_kawai_layout(G)
        elif layout == 'spectral':
            pos = self.nx.spectral_layout(G)
        else:
            pos = self.nx.spring_layout(G)
        
        # Get node colors based on type
        node_types = [G.nodes[node]['type'] for node in G.nodes]
        unique_types = list(set(node_types))
        color_map = {}
        for i, node_type in enumerate(unique_types):
            color_map[node_type] = i / max(1, len(unique_types) - 1)
        
        node_colors = [color_map[G.nodes[node]['type']] for node in G.nodes]
        
        # Draw nodes
        self.nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap=plt.cm.viridis, 
                                   node_size=500, alpha=0.8)
        
        # Draw edges
        edge_weights = [G.edges[edge]['weight'] * 2 for edge in G.edges]
        self.nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, 
                                   arrowsize=20, connectionstyle='arc3,rad=0.1')
        
        # Draw labels
        self.nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
        
        # Draw edge labels
        edge_labels = {(u, v): G.edges[u, v]['label'] for u, v in G.edges}
        self.nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        # Create legend for node types
        legend_elements = []
        for node_type, color_value in color_map.items():
            from matplotlib.lines import Line2D
            legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=plt.cm.viridis(color_value), 
                                         markersize=10, label=node_type))
        
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Remove axis
        plt.axis('off')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.savefig(tmp.name, bbox_inches='tight')
            plt.close()
            
            # Read image data
            with open(tmp.name, 'rb') as f:
                image_data = f.read()
            
            # Clean up
            os.unlink(tmp.name)
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return {
            'image_data': image_base64,
            'image_format': 'png',
            'width': width,
            'height': height,
            'entity_count': len(subgraph['entities']),
            'relationship_count': len(subgraph['relationships'])
        }
    
    async def create_interactive_visualization(self, entity_ids: List[str] = None,
                                              include_relationships: bool = True) -> Dict[str, Any]:
        """
        Create an interactive visualization of the knowledge graph.
        
        Args:
            entity_ids: List of entity IDs to include (optional)
            include_relationships: Whether to include relationships
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info("Creating interactive visualization")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.query_engine:
            logger.warning("Query engine not available")
            return {'error': "Query engine not available"}
        
        # Get subgraph
        if entity_ids:
            subgraph = await self.query_engine.get_subgraph(entity_ids, include_relationships)
        else:
            # Use all entities (up to a limit)
            all_entity_ids = list(self.query_engine.entities.keys())[:100]  # Limit to 100 entities
            subgraph = await self.query_engine.get_subgraph(all_entity_ids, include_relationships)
        
        # Create visualization data for D3.js or other interactive visualization libraries
        nodes = []
        for entity_id, entity in subgraph['entities'].items():
            nodes.append({
                'id': entity_id,
                'label': entity['text'],
                'type': entity['type'],
                'properties': entity.get('properties', {})
            })
        
        links = []
        for relationship in subgraph['relationships']:
            source_id = relationship['source']
            target_id = relationship['target']
            
            # Skip if source or target not in subgraph
            if source_id not in subgraph['entities'] or target_id not in subgraph['entities']:
                continue
            
            links.append({
                'source': source_id,
                'target': target_id,
                'label': relationship['type'],
                'weight': relationship.get('confidence', 0.5)
            })
        
        # Create HTML for interactive visualization
        html = self._create_interactive_html(nodes, links)
        
        return {
            'html': html,
            'nodes': nodes,
            'links': links,
            'entity_count': len(nodes),
            'relationship_count': len(links)
        }
    
    def _create_interactive_html(self, nodes: List[Dict[str, Any]], 
                                links: List[Dict[str, Any]]) -> str:
        """
        Create HTML for interactive visualization.
        
        Args:
            nodes: List of nodes
            links: List of links
            
        Returns:
            HTML string
        """
        # Create HTML with D3.js
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Knowledge Graph Visualization</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; }}
                svg {{ width: 100%; height: 100vh; }}
                .node {{ stroke: #fff; stroke-width: 1.5px; }}
                .link {{ stroke: #999; stroke-opacity: 0.6; }}
                .node-label {{ font-family: sans-serif; font-size: 10px; }};
                .link-label {{ font-family: sans-serif; font-size: 8px; fill: #666; }}
            </style>
        </head>
        <body>
            <svg id="graph"></svg>
            <script>
                // Graph data
                const nodes = {json.dumps(nodes)};
                const links = {json.dumps(links)};
                
                // Create a color scale for node types
                const nodeTypes = [...new Set(nodes.map(d => d.type))];
                const color = d3.scaleOrdinal()
                    .domain(nodeTypes)
                    .range(d3.schemeCategory10);
                
                // Create SVG
                const svg = d3.select("#graph");
                const width = window.innerWidth;
                const height = window.innerHeight;
                const g = svg.append("g");
                
                // Add zoom behavior
                svg.call(d3.zoom()
                    .scaleExtent([0.1, 10])
                    .on("zoom", (event) => {{
                        g.attr("transform", event.transform);
                    }}));
                
                // Create simulation
                const simulation = d3.forceSimulation(nodes)
                    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("x", d3.forceX(width / 2).strength(0.1))
                    .force("y", d3.forceY(height / 2).strength(0.1));
                
                // Create links
                const link = g.selectAll(".link")
                    .data(links)
                    .enter().append("line")
                    .attr("class", "link")
                    .attr("stroke-width", d => Math.sqrt(d.weight) * 2);
                
                // Create nodes
                const node = g.selectAll(".node")
                    .data(nodes)
                    .enter().append("circle")
                    .attr("class", "node")
                    .attr("r", 5)
                    .attr("fill", d => color(d.type))
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));
                
                // Add node labels
                const nodeLabel = g.selectAll(".node-label")
                    .data(nodes)
                    .enter().append("text")
                    .attr("class", "node-label")
                    .attr("dx", 8)
                    .attr("dy", ".35em")
                    .text(d => d.label);
                
                // Add link labels
                const linkLabel = g.selectAll(".link-label")
                    .data(links)
                    .enter().append("text")
                    .attr("class", "link-label")
                    .attr("dy", -5)
                    .append("textPath")
                    .attr("xlink:href", (d, i) => "#link-path-" + i)
                    .text(d => d.label);
                
                // Add tooltips
                node.append("title")
                    .text(d => `${d.label} (${d.type})`);
                
                // Update positions
                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);
                    
                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);
                    
                    nodeLabel
                        .attr("x", d => d.x)
                        .attr("y", d => d.y);
                }});
                
                // Drag functions
                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}
                
                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}
                
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}
                
                // Create legend
                const legend = svg.append("g")
                    .attr("transform", "translate(20, 20)");
                
                nodeTypes.forEach((type, i) => {{
                    const legendRow = legend.append("g")
                        .attr("transform", `translate(0, ${i * 20})`);
                    
                    legendRow.append("circle")
                        .attr("r", 5)
                        .attr("fill", color(type));
                    
                    legendRow.append("text")
                        .attr("x", 10)
                        .attr("y", 5)
                        .text(type)
                        .style("font-family", "sans-serif")
                        .style("font-size", "12px");
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def create_entity_visualization(self, entity_id: str) -> Dict[str, Any]:
        """
        Create a visualization focused on a single entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info(f"Creating entity visualization for {entity_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        if not self.query_engine:
            logger.warning("Query engine not available")
            return {'error': "Query engine not available"}
        
        # Check if entity exists
        if entity_id not in self.query_engine.entities:
            logger.warning(f"Entity {entity_id} not found")
            return {'error': f"Entity {entity_id} not found"}
        
        # Get entity
        entity = self.query_engine.entities[entity_id]
        
        # Get neighbors
        neighbors = await self.query_engine.get_entity_neighbors(entity_id)
        
        # Create NetworkX graph
        G = self.nx.DiGraph()
        
        # Add central entity
        G.add_node(entity_id, label=entity['text'], type=entity['type'], central=True)
        
        # Add neighbor entities
        for neighbor in neighbors:
            neighbor_entity = neighbor['entity']
            neighbor_id = neighbor_entity['id']
            
            G.add_node(neighbor_id, label=neighbor_entity['text'], type=neighbor_entity['type'], central=False)
            
            # Add relationship
            relationship = neighbor['relationship']
            direction = neighbor['direction']
            
            if direction == 'outgoing':
                G.add_edge(entity_id, neighbor_id, label=relationship['type'], 
                          weight=relationship.get('confidence', 0.5))
            else:
                G.add_edge(neighbor_id, entity_id, label=relationship['type'], 
                          weight=relationship.get('confidence', 0.5))
        
        # Create visualization
        plt = self.plt
        plt.figure(figsize=(10, 8), dpi=100)
        
        # Use spring layout with central entity fixed at center
        pos = self.nx.spring_layout(G, fixed=[entity_id], pos={entity_id: [0, 0]})
        
        # Get node colors based on type and central status
        node_colors = []
        for node in G.nodes:
            if G.nodes[node].get('central', False):
                node_colors.append('red')  # Central node is red
            else:
                node_type = G.nodes[node]['type']
                # Use a hash of the node type to generate a color
                import hashlib
                hash_val = int(hashlib.md5(node_type.encode()).hexdigest(), 16)
                node_colors.append(f"#{hash_val % 0xFFFFFF:06x}")
        
        # Draw nodes
        self.nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                   node_size=[800 if G.nodes[node].get('central', False) else 300 for node in G.nodes], 
                                   alpha=0.8)
        
        # Draw edges
        edge_weights = [G.edges[edge]['weight'] * 2 for edge in G.edges]
        self.nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, 
                                   arrowsize=20, connectionstyle='arc3,rad=0.1')
        
        # Draw labels
        self.nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
        
        # Draw edge labels
        edge_labels = {(u, v): G.edges[u, v]['label'] for u, v in G.edges}
        self.nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        # Add title
        plt.title(f"Entity: {entity['text']} ({entity['type']})")
        
        # Remove axis
        plt.axis('off')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.savefig(tmp.name, bbox_inches='tight')
            plt.close()
            
            # Read image data
            with open(tmp.name, 'rb') as f:
                image_data = f.read()
            
            # Clean up
            os.unlink(tmp.name)
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return {
            'image_data': image_base64,
            'image_format': 'png',
            'entity': entity,
            'neighbor_count': len(neighbors)
        }