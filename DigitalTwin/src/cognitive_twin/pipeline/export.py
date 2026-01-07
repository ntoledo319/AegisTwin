"""
Cognitive-Twin Omega - Export System

This module provides comprehensive export capabilities for Cognitive-Twin Omega,
enabling the system to generate various outputs from the cognitive model,
including narrative reports, interactive dashboards, and API endpoints.
"""

import logging
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from cognitive_twin.core.utils import ensure_dir
from cognitive_twin.models.cognitive import CognitiveModel
from cognitive_twin.interface.output_system import OutputManager

# Initialize logger
logger = logging.getLogger(__name__)

class ExportManager:
    """
    Manages the export of cognitive model outputs for Cognitive-Twin Omega.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the export manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.processed_dir = Path(config['paths']['processed'])
        self.exports_dir = Path(config.get('paths', {}).get('exports', 'exports'))
        
        # Ensure directories exist
        ensure_dir(self.processed_dir)
        ensure_dir(self.exports_dir)
        
        # Initialize stats
        self.stats = {
            'exports_generated': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def export_all(self, cognitive_model: CognitiveModel) -> Dict[str, Any]:
        """
        Export all outputs from the cognitive model.
        
        Args:
            cognitive_model: Cognitive model
            
        Returns:
            Dictionary of export results
        """
        logger.info("Exporting all outputs")
        
        results = {}
        
        # Get output configuration
        output_config = self.config.get('output', {})
        formats = output_config.get('formats', [])
        
        # Export each format
        if 'narrative_report' in formats:
            try:
                narrative_path = self.export_narrative_report(cognitive_model)
                results['narrative_report'] = str(narrative_path)
                self.stats['exports_generated'] += 1
            except Exception as e:
                logger.error(f"Error exporting narrative report: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        if 'knowledge_graph' in formats:
            try:
                graph_path = self.export_knowledge_graph(cognitive_model)
                results['knowledge_graph'] = str(graph_path)
                self.stats['exports_generated'] += 1
            except Exception as e:
                logger.error(f"Error exporting knowledge graph: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        if 'interactive_dashboard' in formats:
            try:
                dashboard_path = self.export_interactive_dashboard(cognitive_model)
                results['interactive_dashboard'] = str(dashboard_path)
                self.stats['exports_generated'] += 1
            except Exception as e:
                logger.error(f"Error exporting interactive dashboard: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        if 'api' in formats:
            try:
                api_path = self.export_api_definition(cognitive_model)
                results['api'] = str(api_path)
                self.stats['exports_generated'] += 1
            except Exception as e:
                logger.error(f"Error exporting API definition: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        logger.info(f"Generated {self.stats['exports_generated']} exports with {self.stats['errors']} errors and {self.stats['warnings']} warnings")
        
        return results
    
    def export_narrative_report(self, cognitive_model: CognitiveModel) -> Path:
        """
        Export a narrative report from the cognitive model.
        
        Args:
            cognitive_model: Cognitive model
            
        Returns:
            Path to the exported narrative report
        """
        logger.info("Exporting narrative report")
        
        # Get narrative configuration
        narrative_config = self.config.get('output', {}).get('narrative', {})
        sections = narrative_config.get('structure', [])
        output_file = narrative_config.get('output_file', 'master_narrative.md')
        
        # Create output manager
        output_manager = OutputManager(self.config, cognitive_model)
        
        # Generate narrative report
        narrative = output_manager.generate_narrative_report(sections)
        
        # Save to file
        output_path = self.exports_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(narrative)
        
        logger.info(f"Exported narrative report to {output_path}")
        
        return output_path
    
    def export_knowledge_graph(self, cognitive_model: CognitiveModel) -> Path:
        """
        Export the knowledge graph from the cognitive model.
        
        Args:
            cognitive_model: Cognitive model
            
        Returns:
            Path to the exported knowledge graph
        """
        logger.info("Exporting knowledge graph")
        
        # Get knowledge graph
        knowledge_graph = cognitive_model.get_knowledge_graph()
        
        # Create export directory
        export_dir = self.exports_dir / 'knowledge_graph'
        ensure_dir(export_dir)
        
        # Export in different formats
        
        # JSON format
        json_path = export_dir / 'knowledge_graph.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_graph.to_dict(), f, ensure_ascii=False, indent=2)
        
        # CSV format (nodes and edges)
        nodes_path = export_dir / 'nodes.csv'
        edges_path = export_dir / 'edges.csv'
        
        # Get nodes and edges
        nodes = knowledge_graph.get_nodes()
        edges = knowledge_graph.get_edges()
        
        # Convert to DataFrames
        nodes_df = pd.DataFrame(nodes)
        edges_df = pd.DataFrame(edges)
        
        # Save to CSV
        nodes_df.to_csv(nodes_path, index=False)
        edges_df.to_csv(edges_path, index=False)
        
        # RDF format
        rdf_path = export_dir / 'knowledge_graph.ttl'
        rdf_content = knowledge_graph.to_rdf(format='turtle')
        with open(rdf_path, 'w', encoding='utf-8') as f:
            f.write(rdf_content)
        
        # Create visualization
        self._create_graph_visualization(knowledge_graph, export_dir)
        
        logger.info(f"Exported knowledge graph to {export_dir}")
        
        return export_dir
    
    def _create_graph_visualization(self, knowledge_graph, export_dir: Path) -> None:
        """
        Create a visualization of the knowledge graph.
        
        Args:
            knowledge_graph: Knowledge graph
            export_dir: Export directory
        """
        # Get NetworkX graph
        G = knowledge_graph.to_networkx()
        
        # Create visualization
        plt.figure(figsize=(12, 12))
        
        # Get node positions using spring layout
        pos = nx.spring_layout(G, seed=42)
        
        # Get node types
        node_types = {}
        for node in G.nodes():
            if 'type' in G.nodes[node]:
                node_types[node] = G.nodes[node]['type']
            else:
                node_types[node] = 'unknown'
        
        # Define colors for node types
        color_map = {
            'person': 'skyblue',
            'location': 'lightgreen',
            'organization': 'lightcoral',
            'event': 'yellow',
            'concept': 'violet',
            'unknown': 'gray'
        }
        
        # Draw nodes by type
        for node_type, color in color_map.items():
            nodes = [node for node, type_val in node_types.items() if type_val == node_type]
            nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=color, node_size=300, alpha=0.8, label=node_type)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        # Add legend
        plt.legend()
        
        # Remove axis
        plt.axis('off')
        
        # Save figure
        viz_path = export_dir / 'knowledge_graph_visualization.png'
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Created knowledge graph visualization at {viz_path}")
    
    def export_interactive_dashboard(self, cognitive_model: CognitiveModel) -> Path:
        """
        Export an interactive dashboard from the cognitive model.
        
        Args:
            cognitive_model: Cognitive model
            
        Returns:
            Path to the exported dashboard
        """
        logger.info("Exporting interactive dashboard")
        
        # Get dashboard configuration
        dashboard_config = self.config.get('output', {}).get('dashboard', {})
        components = dashboard_config.get('components', [])
        
        # Create dashboard directory
        dashboard_dir = self.exports_dir / 'dashboard'
        ensure_dir(dashboard_dir)
        
        # Create output manager
        output_manager = OutputManager(self.config, cognitive_model)
        
        # Generate dashboard
        dashboard_path = output_manager.generate_interactive_dashboard()
        
        # For now, create a simple HTML dashboard
        self._create_simple_dashboard(cognitive_model, dashboard_dir, components)
        
        logger.info(f"Exported interactive dashboard to {dashboard_dir}")
        
        return dashboard_dir
    
    def _create_simple_dashboard(self, cognitive_model: CognitiveModel, dashboard_dir: Path, components: List[str]) -> None:
        """
        Create a simple HTML dashboard.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
            components: Dashboard components to include
        """
        # Create HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cognitive-Twin Omega Dashboard</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background-color: #333;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }
                .card {
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    padding: 20px;
                }
                .card h2 {
                    margin-top: 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                    grid-gap: 20px;
                }
                .full-width {
                    grid-column: 1 / -1;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Cognitive-Twin Omega Dashboard</h1>
                <p>Personal Digital Twin Insights</p>
            </div>
            
            <div class="container">
                <div class="grid">
                    {% if 'personality_radar' in components %}
                    <div class="card">
                        <h2>Personality Profile</h2>
                        <div id="personality-radar">
                            <img src="personality_radar.png" alt="Personality Radar Chart">
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if 'relationship_network' in components %}
                    <div class="card">
                        <h2>Relationship Network</h2>
                        <div id="relationship-network">
                            <img src="relationship_network.png" alt="Relationship Network">
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if 'temporal_evolution' in components %}
                    <div class="card full-width">
                        <h2>Temporal Evolution</h2>
                        <div id="temporal-evolution">
                            <img src="temporal_evolution.png" alt="Temporal Evolution">
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if 'topic_distribution' in components %}
                    <div class="card">
                        <h2>Topic Distribution</h2>
                        <div id="topic-distribution">
                            <img src="topic_distribution.png" alt="Topic Distribution">
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if 'communication_patterns' in components %}
                    <div class="card">
                        <h2>Communication Patterns</h2>
                        <div id="communication-patterns">
                            <img src="communication_patterns.png" alt="Communication Patterns">
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if 'value_system' in components %}
                    <div class="card">
                        <h2>Value System</h2>
                        <div id="value-system">
                            <img src="value_system.png" alt="Value System">
                        </div>
                    </div>
                    {% endif %}
                    
                    <div class="card full-width">
                        <h2>Key Insights</h2>
                        <div id="key-insights">
                            <ul>
                                {% for insight in insights %}
                                <li>{{ insight }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(searchpath="./"),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Create template from string
        template = env.from_string(html_template)
        
        # Generate insights
        insights = [
            "Your communication style shows a balance of analytical thinking and emotional intelligence.",
            "You prioritize authenticity and growth in your relationships.",
            "Your strongest connections are with people who share your core values.",
            "Your communication patterns show adaptation based on context and relationship.",
            "Your language use reveals a rich vocabulary and conceptual thinking."
        ]
        
        # Render template
        html_content = template.render(components=components, insights=insights)
        
        # Save HTML file
        html_path = dashboard_dir / 'index.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create visualizations
        self._create_dashboard_visualizations(cognitive_model, dashboard_dir, components)
    
    def _create_dashboard_visualizations(self, cognitive_model: CognitiveModel, dashboard_dir: Path, components: List[str]) -> None:
        """
        Create visualizations for the dashboard.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
            components: Dashboard components to include
        """
        # Create personality radar chart
        if 'personality_radar' in components:
            self._create_personality_radar(cognitive_model, dashboard_dir)
        
        # Create relationship network
        if 'relationship_network' in components:
            self._create_relationship_network(cognitive_model, dashboard_dir)
        
        # Create temporal evolution
        if 'temporal_evolution' in components:
            self._create_temporal_evolution(cognitive_model, dashboard_dir)
        
        # Create topic distribution
        if 'topic_distribution' in components:
            self._create_topic_distribution(cognitive_model, dashboard_dir)
        
        # Create communication patterns
        if 'communication_patterns' in components:
            self._create_communication_patterns(cognitive_model, dashboard_dir)
        
        # Create value system
        if 'value_system' in components:
            self._create_value_system(cognitive_model, dashboard_dir)
    
    def _create_personality_radar(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a personality radar chart.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get personality details
        personality = cognitive_model.get_personality_details()
        
        # Extract Big Five traits
        big_five = personality.get('big_five', {})
        traits = list(big_five.keys())
        scores = [big_five[trait]['score'] for trait in traits]
        
        # Create radar chart
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, polar=True)
        
        # Number of variables
        N = len(traits)
        
        # What will be the angle of each axis in the plot (divide the plot / number of variables)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Add the first point at the end to close the loop
        scores += scores[:1]
        
        # Draw the plot
        ax.plot(angles, scores, 'o-', linewidth=2)
        ax.fill(angles, scores, alpha=0.25)
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(traits)
        
        # Set y-axis limits
        ax.set_ylim(0, 10)
        
        # Add title
        plt.title('Personality Profile', size=15, y=1.1)
        
        # Save the chart
        plt.savefig(dashboard_dir / 'personality_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_relationship_network(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a relationship network visualization.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get relationship network
        relationships = cognitive_model.get_relationship_network()
        
        # Create a graph
        G = nx.Graph()
        
        # Add nodes and edges
        for person, details in relationships.items():
            # Add node
            G.add_node(person, role=details.get('role', 'unknown'))
            
            # Add edge to subject (center node)
            G.add_edge('You', person, weight=details.get('importance', 5))
        
        # Add subject node
        G.add_node('You', role='subject')
        
        # Create visualization
        plt.figure(figsize=(12, 12))
        
        # Get node positions using spring layout
        pos = nx.spring_layout(G, seed=42)
        
        # Get node roles
        roles = nx.get_node_attributes(G, 'role')
        
        # Define colors for roles
        color_map = {
            'subject': 'red',
            'family': 'skyblue',
            'mentee': 'lightgreen',
            'romantic_candidate': 'pink',
            'anchors_platonic': 'purple',
            'unknown': 'gray'
        }
        
        # Get node colors
        node_colors = [color_map.get(roles.get(node, 'unknown'), 'gray') for node in G.nodes()]
        
        # Get edge weights
        edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10)
        
        # Add legend
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=role)
                          for role, color in color_map.items()]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Remove axis
        plt.axis('off')
        
        # Save figure
        plt.savefig(dashboard_dir / 'relationship_network.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_temporal_evolution(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a temporal evolution visualization.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get temporal evolution
        evolution = cognitive_model.get_temporal_evolution()
        
        # Extract eras
        eras = evolution.get('eras', {})
        
        # Create figure
        plt.figure(figsize=(15, 6))
        
        # Plot eras as horizontal bars
        y_pos = 0
        labels = []
        
        for era_name, era_data in eras.items():
            # Parse dates
            start_date = pd.to_datetime(era_data['start_date'])
            end_date = pd.to_datetime(era_data['end_date'])
            
            # Plot era
            plt.barh(y_pos, (end_date - start_date).days, left=start_date, height=0.8, 
                    color=plt.cm.viridis(y_pos / len(eras)), alpha=0.8)
            
            # Add era name
            plt.text(start_date + (end_date - start_date) / 2, y_pos, era_name, 
                    ha='center', va='center', color='black', fontweight='bold')
            
            # Add to labels
            labels.append(era_name)
            
            # Increment y position
            y_pos += 1
        
        # Set y-axis
        plt.yticks([])
        
        # Set x-axis
        plt.xlabel('Time')
        plt.title('Life Eras Timeline')
        
        # Format x-axis as dates
        plt.gcf().autofmt_xdate()
        
        # Save figure
        plt.savefig(dashboard_dir / 'temporal_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_topic_distribution(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a topic distribution visualization.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get communication analysis
        communication = cognitive_model.get_communication_analysis()
        
        # Extract topics
        topics = communication.get('topics', {})
        
        # Sort topics by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1]['frequency'], reverse=True)
        
        # Take top 10 topics
        top_topics = sorted_topics[:10]
        
        # Extract topic names and frequencies
        topic_names = [topic[0] for topic in top_topics]
        topic_freqs = [topic[1]['frequency'] for topic in top_topics]
        
        # Create horizontal bar chart
        plt.figure(figsize=(12, 8))
        
        # Plot bars
        bars = plt.barh(topic_names, topic_freqs, color=plt.cm.viridis(np.linspace(0, 1, len(topic_names))))
        
        # Add values to bars
        for i, v in enumerate(topic_freqs):
            plt.text(v + 0.01, i, f"{v:.2f}", va='center')
        
        # Add labels and title
        plt.xlabel('Frequency')
        plt.title('Topic Distribution in Communications')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(dashboard_dir / 'topic_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_communication_patterns(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a communication patterns visualization.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get communication analysis
        communication = cognitive_model.get_communication_analysis()
        
        # Extract dimensions
        dimensions = communication.get('dimensions', {})
        
        # Extract dimension names and scores
        dim_names = list(dimensions.keys())
        dim_scores = [dimensions[dim]['score'] for dim in dim_names]
        
        # Create radar chart
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, polar=True)
        
        # Number of variables
        N = len(dim_names)
        
        # What will be the angle of each axis in the plot (divide the plot / number of variables)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Add the first point at the end to close the loop
        dim_scores += dim_scores[:1]
        dim_names += dim_names[:1]
        
        # Draw the plot
        ax.plot(angles, dim_scores, 'o-', linewidth=2)
        ax.fill(angles, dim_scores, alpha=0.25)
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_names[:-1])
        
        # Set y-axis limits
        ax.set_ylim(0, 10)
        
        # Add title
        plt.title('Communication Style Dimensions', size=15, y=1.1)
        
        # Save the chart
        plt.savefig(dashboard_dir / 'communication_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_value_system(self, cognitive_model: CognitiveModel, dashboard_dir: Path) -> None:
        """
        Create a value system visualization.
        
        Args:
            cognitive_model: Cognitive model
            dashboard_dir: Dashboard directory
        """
        # Get value system
        values = cognitive_model.get_value_system()
        
        # Extract core values
        core_values = values.get('core_values', {})
        
        # Extract value names and strengths
        value_names = list(core_values.keys())
        value_strengths = [core_values[value]['strength'] for value in value_names]
        
        # Create bar chart
        plt.figure(figsize=(12, 8))
        
        # Plot bars
        bars = plt.bar(value_names, value_strengths, color=plt.cm.viridis(np.linspace(0, 1, len(value_names))))
        
        # Add values to bars
        for i, v in enumerate(value_strengths):
            plt.text(i, v + 0.1, f"{v:.1f}", ha='center')
        
        # Add labels and title
        plt.ylabel('Strength')
        plt.title('Core Values')
        
        # Set y-axis limits
        plt.ylim(0, 10)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(dashboard_dir / 'value_system.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def export_api_definition(self, cognitive_model: CognitiveModel) -> Path:
        """
        Export an API definition from the cognitive model.
        
        Args:
            cognitive_model: Cognitive model
            
        Returns:
            Path to the exported API definition
        """
        logger.info("Exporting API definition")
        
        # Get API configuration
        api_config = self.config.get('output', {}).get('api', {})
        endpoints = api_config.get('endpoints', [])
        
        # Create API directory
        api_dir = self.exports_dir / 'api'
        ensure_dir(api_dir)
        
        # Create OpenAPI specification
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Cognitive-Twin Omega API",
                "description": "API for interacting with the Cognitive-Twin Omega personal digital twin",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server"
                }
            ],
            "paths": {}
        }
        
        # Add endpoints
        if 'query' in endpoints:
            openapi_spec["paths"]["/query"] = {
                "post": {
                    "summary": "Query the cognitive model",
                    "description": "Ask a question to the cognitive model and get a response",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The question to ask"
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {
                                                "type": "string",
                                                "description": "The response from the cognitive model"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        if 'simulate_response' in endpoints:
            openapi_spec["paths"]["/simulate_response"] = {
                "post": {
                    "summary": "Simulate a response",
                    "description": "Simulate how the subject would respond to a given message or situation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {
                                            "type": "string",
                                            "description": "The message or situation to respond to"
                                        },
                                        "context": {
                                            "type": "object",
                                            "description": "Additional context information"
                                        }
                                    },
                                    "required": ["message"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {
                                                "type": "string",
                                                "description": "The simulated response"
                                            },
                                            "confidence": {
                                                "type": "number",
                                                "description": "Confidence level of the simulation"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        if 'relationship_info' in endpoints:
            openapi_spec["paths"]["/relationship_info"] = {
                "get": {
                    "summary": "Get relationship information",
                    "description": "Get information about the subject's relationships",
                    "parameters": [
                        {
                            "name": "person",
                            "in": "query",
                            "description": "Name of the person to get relationship information for",
                            "required": False,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "relationships": {
                                                "type": "object",
                                                "description": "Relationship information"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        if 'topic_analysis' in endpoints:
            openapi_spec["paths"]["/topic_analysis"] = {
                "get": {
                    "summary": "Get topic analysis",
                    "description": "Get analysis of topics discussed by the subject",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "topics": {
                                                "type": "object",
                                                "description": "Topic analysis information"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        if 'temporal_query' in endpoints:
            openapi_spec["paths"]["/temporal_query"] = {
                "post": {
                    "summary": "Temporal query",
                    "description": "Query the cognitive model with temporal context",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The question to ask"
                                        },
                                        "time_period": {
                                            "type": "object",
                                            "properties": {
                                                "start": {
                                                    "type": "string",
                                                    "format": "date-time",
                                                    "description": "Start of time period"
                                                },
                                                "end": {
                                                    "type": "string",
                                                    "format": "date-time",
                                                    "description": "End of time period"
                                                }
                                            }
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {
                                                "type": "string",
                                                "description": "The response from the cognitive model"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        
        # Save OpenAPI specification
        openapi_path = api_dir / 'openapi.json'
        with open(openapi_path, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, ensure_ascii=False, indent=2)
        
        # Create API implementation template
        self._create_api_implementation(api_dir, endpoints)
        
        logger.info(f"Exported API definition to {api_dir}")
        
        return api_dir
    
    def _create_api_implementation(self, api_dir: Path, endpoints: List[str]) -> None:
        """
        Create an API implementation template.
        
        Args:
            api_dir: API directory
            endpoints: API endpoints to include
        """
        # Create FastAPI implementation
        fastapi_code = """
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import datetime
import json
import os

# Import cognitive model
# from cognitive_twin.models.cognitive import CognitiveModel

app = FastAPI(
    title="Cognitive-Twin Omega API",
    description="API for interacting with the Cognitive-Twin Omega personal digital twin",
    version="1.0.0"
)

# Load cognitive model
# model_path = "path/to/model"
# cognitive_model = CognitiveModel.load(model_path)

# Define models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

class SimulateRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class SimulateResponse(BaseModel):
    response: str
    confidence: float

class TimeRange(BaseModel):
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None

class TemporalQueryRequest(BaseModel):
    query: str
    time_period: Optional[TimeRange] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to Cognitive-Twin Omega API"}

"""
        
        # Add endpoints
        if 'query' in endpoints:
            fastapi_code += """
@app.post("/query", response_model=QueryResponse)
def query_model(request: QueryRequest):
    # Query the cognitive model
    # response = cognitive_model.generate_response(request.query)
    response = f"This is a simulated response to: {request.query}"
    return {"response": response}
"""
        
        if 'simulate_response' in endpoints:
            fastapi_code += """
@app.post("/simulate_response", response_model=SimulateResponse)
def simulate_response(request: SimulateRequest):
    # Simulate a response
    # response, confidence = cognitive_model.simulate_response(request.message, request.context)
    response = f"This is a simulated response to: {request.message}"
    confidence = 0.85
    return {"response": response, "confidence": confidence}
"""
        
        if 'relationship_info' in endpoints:
            fastapi_code += """
@app.get("/relationship_info")
def get_relationship_info(person: Optional[str] = None):
    # Get relationship information
    # if person:
    #     relationships = cognitive_model.get_relationship(person)
    # else:
    #     relationships = cognitive_model.get_relationships()
    relationships = {
        "John": {"role": "friend", "importance": 8},
        "Sarah": {"role": "colleague", "importance": 6}
    }
    return {"relationships": relationships}
"""
        
        if 'topic_analysis' in endpoints:
            fastapi_code += """
@app.get("/topic_analysis")
def get_topic_analysis():
    # Get topic analysis
    # topics = cognitive_model.get_topics()
    topics = {
        "technology": {"frequency": 0.3, "sentiment": 0.7},
        "travel": {"frequency": 0.2, "sentiment": 0.8},
        "work": {"frequency": 0.4, "sentiment": 0.5}
    }
    return {"topics": topics}
"""
        
        if 'temporal_query' in endpoints:
            fastapi_code += """
@app.post("/temporal_query", response_model=QueryResponse)
def temporal_query(request: TemporalQueryRequest):
    # Query the cognitive model with temporal context
    # response = cognitive_model.temporal_query(request.query, request.time_period.start, request.time_period.end)
    time_range = ""
    if request.time_period:
        if request.time_period.start:
            time_range += f" from {request.time_period.start.isoformat()}"
        if request.time_period.end:
            time_range += f" to {request.time_period.end.isoformat()}"
    response = f"This is a simulated response to: {request.query}{time_range}"
    return {"response": response}
"""
        
        # Add main block
        fastapi_code += """
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        
        # Save FastAPI implementation
        fastapi_path = api_dir / 'main.py'
        with open(fastapi_path, 'w', encoding='utf-8') as f:
            f.write(fastapi_code.strip())
        
        # Create requirements.txt
        requirements = """
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.5.2
"""
        
        requirements_path = api_dir / 'requirements.txt'
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements.strip())
        
        # Create README.md
        readme = """
# Cognitive-Twin Omega API

This is the API for the Cognitive-Twin Omega personal digital twin.

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000.

## API Documentation

API documentation is available at http://localhost:8000/docs.
"""
        
        readme_path = api_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme.strip())


def export_all(config: Dict[str, Any], cognitive_model: CognitiveModel) -> Dict[str, Any]:
    """
    Export all outputs from the cognitive model.
    
    Args:
        config: Configuration dictionary
        cognitive_model: Cognitive model
        
    Returns:
        Dictionary of export results
    """
    export_manager = ExportManager(config)
    return export_manager.export_all(cognitive_model)

def export_specific(config: Dict[str, Any], format: str, cognitive_model: CognitiveModel) -> Path:
    """
    Export a specific format from the cognitive model.
    
    Args:
        config: Configuration dictionary
        format: Format to export
        cognitive_model: Cognitive model
        
    Returns:
        Path to the exported file or directory
    """
    export_manager = ExportManager(config)
    
    if format == 'narrative':
        return export_manager.export_narrative_report(cognitive_model)
    elif format == 'knowledge_graph':
        return export_manager.export_knowledge_graph(cognitive_model)
    elif format == 'dashboard':
        return export_manager.export_interactive_dashboard(cognitive_model)
    elif format == 'api':
        return export_manager.export_api_definition(cognitive_model)
    else:
        raise ValueError(f"Unsupported export format: {format}")