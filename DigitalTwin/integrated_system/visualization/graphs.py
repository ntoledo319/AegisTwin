"""
Graph visualization module.

This module provides functionality for visualizing network and relationship graphs,
including static graph visualizations and interactive network diagrams.
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

class GraphVisualizer:
    """Visualizer for network and relationship graphs."""
    
    def __init__(self):
        """Initialize the graph visualizer."""
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
            logger.info("Visualization libraries available for graphs")
        except ImportError:
            logger.warning("Visualization libraries not available for graphs")
    
    async def initialize(self):
        """Initialize the graph visualizer."""
        logger.info("Initializing graph visualizer")
        
        self.initialized = True
        logger.info("Graph visualizer initialized")
    
    async def create_network_graph(self, nodes: List[Dict[str, Any]], 
                                  edges: List[Dict[str, Any]],
                                  title: str = "Network Graph",
                                  layout: str = "spring",
                                  width: int = 800,
                                  height: int = 600) -> Dict[str, Any]:
        """
        Create a network graph visualization.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            title: Graph title
            layout: Graph layout algorithm
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing graph visualization data
        """
        logger.info("Creating network graph")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Create NetworkX graph
            G = self.nx.DiGraph()
            
            # Add nodes
            for node in nodes:
                # Ensure node has an id
                if 'id' not in node:
                    logger.warning("Node missing id, skipping")
                    continue
                
                # Create node attributes
                node_attrs = {
                    'label': node.get('label', str(node['id'])),
                    'type': node.get('type', 'default')
                }
                
                # Add additional attributes
                for key, value in node.items():
                    if key not in ['id', 'label', 'type']:
                        node_attrs[key] = value
                
                G.add_node(node['id'], **node_attrs)
            
            # Add edges
            for edge in edges:
                # Ensure edge has source and target
                if 'source' not in edge or 'target' not in edge:
                    logger.warning("Edge missing source or target, skipping")
                    continue
                
                # Create edge attributes
                edge_attrs = {
                    'label': edge.get('label', ''),
                    'weight': edge.get('weight', 1.0)
                }
                
                # Add additional attributes
                for key, value in edge.items():
                    if key not in ['source', 'target', 'label', 'weight']:
                        edge_attrs[key] = value
                
                G.add_edge(edge['source'], edge['target'], **edge_attrs)
            
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
            node_types = [G.nodes[node].get('type', 'default') for node in G.nodes]
            unique_types = list(set(node_types))
            color_map = {}
            for i, node_type in enumerate(unique_types):
                color_map[node_type] = i / max(1, len(unique_types) - 1)
            
            node_colors = [color_map[G.nodes[node].get('type', 'default')] for node in G.nodes]
            
            # Get node sizes based on importance or degree
            node_sizes = []
            for node in G.nodes:
                if 'size' in G.nodes[node]:
                    node_sizes.append(G.nodes[node]['size'] * 100)
                elif 'importance' in G.nodes[node]:
                    node_sizes.append(G.nodes[node]['importance'] * 1000)
                else:
                    # Use degree as size
                    node_sizes.append((G.in_degree(node) + G.out_degree(node) + 1) * 100)
            
            # Draw nodes
            self.nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap=plt.cm.viridis, 
                                       node_size=node_sizes, alpha=0.8)
            
            # Draw edges
            edge_weights = [G.edges[edge].get('weight', 1.0) * 2 for edge in G.edges]
            self.nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, 
                                       arrowsize=20, connectionstyle='arc3,rad=0.1')
            
            # Draw labels
            self.nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
            
            # Draw edge labels
            edge_labels = {(u, v): G.edges[u, v].get('label', '') for u, v in G.edges}
            self.nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
            
            # Create legend for node types
            legend_elements = []
            for node_type, color_value in color_map.items():
                from matplotlib.lines import Line2D
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                             markerfacecolor=plt.cm.viridis(color_value), 
                                             markersize=10, label=node_type))
            
            plt.legend(handles=legend_elements, loc='upper right')
            
            # Add title
            plt.title(title)
            
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
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error creating network graph: {str(e)}")
            return {'error': str(e)}
    
    async def create_relationship_graph(self, central_node: Dict[str, Any],
                                       related_nodes: List[Dict[str, Any]],
                                       relationships: List[Dict[str, Any]],
                                       title: str = "Relationship Graph",
                                       width: int = 800,
                                       height: int = 600) -> Dict[str, Any]:
        """
        Create a relationship graph visualization centered on a specific node.
        
        Args:
            central_node: Central node dictionary
            related_nodes: List of related node dictionaries
            relationships: List of relationship dictionaries
            title: Graph title
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing graph visualization data
        """
        logger.info("Creating relationship graph")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Create NetworkX graph
            G = self.nx.DiGraph()
            
            # Add central node
            central_id = central_node['id']
            G.add_node(central_id, label=central_node.get('label', str(central_id)), 
                      type=central_node.get('type', 'central'), central=True)
            
            # Add related nodes
            for node in related_nodes:
                node_id = node['id']
                G.add_node(node_id, label=node.get('label', str(node_id)), 
                          type=node.get('type', 'related'), central=False)
            
            # Add relationships
            for rel in relationships:
                source = rel['source']
                target = rel['target']
                
                # Skip if source or target not in graph
                if source not in G.nodes or target not in G.nodes:
                    continue
                
                G.add_edge(source, target, label=rel.get('label', ''), 
                          weight=rel.get('weight', 1.0))
            
            # Create visualization
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Use spring layout with central node fixed at center
            pos = self.nx.spring_layout(G, fixed=[central_id], pos={central_id: [0, 0]})
            
            # Get node colors based on type and central status
            node_colors = []
            for node in G.nodes:
                if G.nodes[node].get('central', False):
                    node_colors.append('red')  # Central node is red
                else:
                    node_type = G.nodes[node].get('type', 'default')
                    # Use a hash of the node type to generate a color
                    import hashlib
                    hash_val = int(hashlib.md5(node_type.encode()).hexdigest(), 16)
                    node_colors.append(f"#{hash_val % 0xFFFFFF:06x}")
            
            # Get node sizes
            node_sizes = []
            for node in G.nodes:
                if G.nodes[node].get('central', False):
                    node_sizes.append(800)  # Central node is larger
                else:
                    node_sizes.append(300)  # Related nodes are smaller
            
            # Draw nodes
            self.nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                       node_size=node_sizes, alpha=0.8)
            
            # Draw edges
            edge_weights = [G.edges[edge].get('weight', 1.0) * 2 for edge in G.edges]
            self.nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, 
                                       arrowsize=20, connectionstyle='arc3,rad=0.1')
            
            # Draw labels
            self.nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
            
            # Draw edge labels
            edge_labels = {(u, v): G.edges[u, v].get('label', '') for u, v in G.edges}
            self.nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
            
            # Add title
            plt.title(title)
            
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
                'central_node': central_node['id'],
                'related_node_count': len(related_nodes),
                'relationship_count': len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Error creating relationship graph: {str(e)}")
            return {'error': str(e)}
    
    async def create_interactive_graph(self, nodes: List[Dict[str, Any]], 
                                      edges: List[Dict[str, Any]],
                                      title: str = "Interactive Graph") -> Dict[str, Any]:
        """
        Create an interactive graph visualization.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            title: Graph title
            
        Returns:
            Dictionary containing HTML for interactive graph
        """
        logger.info("Creating interactive graph")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create HTML for interactive graph
            html = self._create_interactive_graph_html(nodes, edges, title)
            
            return {
                'html': html,
                'title': title,
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive graph: {str(e)}")
            return {'error': str(e)}
    
    def _create_interactive_graph_html(self, nodes: List[Dict[str, Any]], 
                                      edges: List[Dict[str, Any]],
                                      title: str) -> str:
        """
        Create HTML for interactive graph using D3.js.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            title: Graph title
            
        Returns:
            HTML string
        """
        # Prepare nodes and links for D3
        d3_nodes = []
        for node in nodes:
            d3_node = {
                'id': node['id'],
                'label': node.get('label', str(node['id'])),
                'group': node.get('type', 'default')
            }
            
            # Add additional attributes
            for key, value in node.items():
                if key not in ['id', 'label', 'type']:
                    d3_node[key] = value
            
            d3_nodes.append(d3_node)
        
        d3_links = []
        for edge in edges:
            d3_link = {
                'source': edge['source'],
                'target': edge['target'],
                'label': edge.get('label', ''),
                'value': edge.get('weight', 1.0)
            }
            
            # Add additional attributes
            for key, value in edge.items():
                if key not in ['source', 'target', 'label', 'weight']:
                    d3_link[key] = value
            
            d3_links.append(d3_link)
        
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; }}
                svg {{ width: 100%; height: 100vh; }}
                .node {{ stroke: #fff; stroke-width: 1.5px; }}
                .link {{ stroke: #999; stroke-opacity: 0.6; }}
                .node-label {{ font-family: sans-serif; font-size: 10px; }};
                .link-label {{ font-family: sans-serif; font-size: 8px; fill: #666; }}
                .tooltip {{ position: absolute; padding: 10px; background-color: white; border: 1px solid #ddd; border-radius: 5px; pointer-events: none; }}
            </style>
        </head>
        <body>
            <svg id="graph"></svg>
            <div class="tooltip" style="opacity: 0;"></div>
            <script>
                // Graph data
                const nodes = {json.dumps(d3_nodes)};
                const links = {json.dumps(d3_links)};
                
                // Create a color scale for node groups
                const nodeGroups = [...new Set(nodes.map(d => d.group))];
                const color = d3.scaleOrdinal()
                    .domain(nodeGroups)
                    .range(d3.schemeCategory10);
                
                // Create SVG
                const svg = d3.select("#svg");
                const width = window.innerWidth;
                const height = window.innerHeight;
                const g = svg.append("g");
                
                // Add zoom behavior
                svg.call(d3.zoom()
                    .scaleExtent([0.1, 10])
                    .on("zoom", (event) => {{
                        g.attr("transform", event.transform);
                    }}));
                
                // Create tooltip
                const tooltip = d3.select(".tooltip");
                
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
                    .attr("stroke-width", d => Math.sqrt(d.value) * 2);
                
                // Create nodes
                const node = g.selectAll(".node")
                    .data(nodes)
                    .enter().append("circle")
                    .attr("class", "node")
                    .attr("r", d => d.size || 5)
                    .attr("fill", d => color(d.group))
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended))
                    .on("mouseover", showTooltip)
                    .on("mouseout", hideTooltip);
                
                // Add node labels
                const nodeLabel = g.selectAll(".node-label")
                    .data(nodes)
                    .enter().append("text")
                    .attr("class", "node-label")
                    .attr("dx", 8)
                    .attr("dy", ".35em")
                    .text(d => d.label);
                
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
                
                // Tooltip functions
                function showTooltip(event, d) {{
                    // Create tooltip content
                    let content = `<strong>${d.label}</strong><br>`;
                    content += `Group: ${d.group}<br>`;
                    
                    // Add additional attributes
                    for (const [key, value] of Object.entries(d)) {{
                        if (!['id', 'label', 'group', 'index', 'x', 'y', 'vx', 'vy', 'fx', 'fy'].includes(key)) {{
                            content += `${key}: ${value}<br>`;
                        }}
                    }}
                    
                    tooltip.html(content)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px")
                        .style("opacity", 1);
                }}
                
                function hideTooltip() {{
                    tooltip.style("opacity", 0);
                }}
                
                // Create legend
                const legend = svg.append("g")
                    .attr("transform", "translate(20, 20)");
                
                nodeGroups.forEach((group, i) => {{
                    const legendRow = legend.append("g")
                        .attr("transform", `translate(0, ${i * 20})`);
                    
                    legendRow.append("circle")
                        .attr("r", 5)
                        .attr("fill", color(group));
                    
                    legendRow.append("text")
                        .attr("x", 10)
                        .attr("y", 5)
                        .text(group)
                        .style("font-family", "sans-serif")
                        .style("font-size", "12px");
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def create_hierarchical_graph(self, nodes: List[Dict[str, Any]], 
                                       edges: List[Dict[str, Any]],
                                       root_id: str,
                                       title: str = "Hierarchical Graph",
                                       width: int = 800,
                                       height: int = 600) -> Dict[str, Any]:
        """
        Create a hierarchical graph visualization.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            root_id: ID of the root node
            title: Graph title
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing graph visualization data
        """
        logger.info("Creating hierarchical graph")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Create NetworkX graph
            G = self.nx.DiGraph()
            
            # Add nodes
            for node in nodes:
                # Ensure node has an id
                if 'id' not in node:
                    logger.warning("Node missing id, skipping")
                    continue
                
                # Create node attributes
                node_attrs = {
                    'label': node.get('label', str(node['id'])),
                    'type': node.get('type', 'default')
                }
                
                # Add additional attributes
                for key, value in node.items():
                    if key not in ['id', 'label', 'type']:
                        node_attrs[key] = value
                
                G.add_node(node['id'], **node_attrs)
            
            # Add edges
            for edge in edges:
                # Ensure edge has source and target
                if 'source' not in edge or 'target' not in edge:
                    logger.warning("Edge missing source or target, skipping")
                    continue
                
                # Create edge attributes
                edge_attrs = {
                    'label': edge.get('label', ''),
                    'weight': edge.get('weight', 1.0)
                }
                
                # Add additional attributes
                for key, value in edge.items():
                    if key not in ['source', 'target', 'label', 'weight']:
                        edge_attrs[key] = value
                
                G.add_edge(edge['source'], edge['target'], **edge_attrs)
            
            # Check if root node exists
            if root_id not in G.nodes:
                logger.warning(f"Root node {root_id} not found")
                return {'error': f"Root node {root_id} not found"}
            
            # Create visualization
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Use hierarchical layout
            pos = self.nx.nx_agraph.graphviz_layout(G, prog='dot', root=root_id)
            
            # Get node colors based on type
            node_types = [G.nodes[node].get('type', 'default') for node in G.nodes]
            unique_types = list(set(node_types))
            color_map = {}
            for i, node_type in enumerate(unique_types):
                color_map[node_type] = i / max(1, len(unique_types) - 1)
            
            node_colors = [color_map[G.nodes[node].get('type', 'default')] for node in G.nodes]
            
            # Get node sizes based on level in hierarchy
            node_sizes = []
            for node in G.nodes:
                try:
                    # Calculate level as shortest path length from root
                    level = self.nx.shortest_path_length(G, root_id, node)
                    # Size decreases with level
                    node_sizes.append(1000 / (level + 1))
                except (self.nx.NetworkXNoPath, self.nx.NodeNotFound):
                    # Node not reachable from root
                    node_sizes.append(100)
            
            # Draw nodes
            self.nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap=plt.cm.viridis, 
                                       node_size=node_sizes, alpha=0.8)
            
            # Draw edges
            self.nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, 
                                       arrowsize=20, connectionstyle='arc3,rad=0.0')
            
            # Draw labels
            self.nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
            
            # Add title
            plt.title(title)
            
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
                'root_id': root_id,
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
            
        except Exception as e:
            logger.error(f"Error creating hierarchical graph: {str(e)}")
            return {'error': str(e)}