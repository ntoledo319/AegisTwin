"""
Cognitive-Twin Omega - Advanced Output System

This module provides sophisticated output methods for the Cognitive-Twin Omega
personal digital twin, focusing on making insights accessible, meaningful,
and human-like while preserving depth and complexity.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import datetime
import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.progress import track

from cognitive_twin.core.knowledge_graph import KnowledgeGraph
from cognitive_twin.models.cognitive import CognitiveModel
from cognitive_twin.models.personality import PersonalityModel

# Initialize logger
logger = logging.getLogger(__name__)
console = Console()

class OutputManager:
    """
    Manages the output generation for Cognitive-Twin Omega.
    
    This class handles the transformation of complex internal representations
    into human-readable, insightful, and engaging outputs across multiple formats.
    """
    
    def __init__(self, config: Dict[str, Any], cognitive_model: Optional['CognitiveModel'] = None):
        """
        Initialize the OutputManager.
        
        Args:
            config: Configuration dictionary
            cognitive_model: Optional cognitive model instance
        """
        self.config = config
        self.cognitive_model = cognitive_model
        self.output_dir = Path(config['paths']['processed'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Output style configuration
        self.style_config = config.get('output', {}).get('style', {})
        self.verbosity = self.style_config.get('verbosity', 'balanced')
        self.tone = self.style_config.get('tone', 'conversational')
        self.structure = self.style_config.get('structure', 'narrative')
        
        # Initialize visualization settings
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_context("talk")
        
    def generate_narrative_report(self, sections: Optional[List[str]] = None) -> str:
        """
        Generate a comprehensive narrative report about the person.
        
        Args:
            sections: Optional list of sections to include
            
        Returns:
            Markdown formatted narrative report
        """
        if not self.cognitive_model:
            return "Error: Cognitive model not available"
            
        # Default sections if none provided
        if not sections:
            sections = [
                "executive_summary",
                "personality_profile",
                "relationship_analysis",
                "communication_patterns",
                "value_system",
                "temporal_evolution",
                "cognitive_framework"
            ]
            
        report_parts = []
        
        # Title
        person_name = self.config['project'].get('subject_name', 'You')
        report_parts.append(f"# {person_name}'s Digital Twin Narrative\n")
        report_parts.append(f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d')}*\n")
        
        # Generate each requested section
        for section in sections:
            method_name = f"_generate_{section}_section"
            if hasattr(self, method_name):
                section_content = getattr(self, method_name)()
                report_parts.append(section_content)
            else:
                logger.warning(f"No method found for generating section: {section}")
        
        # Combine all sections
        full_report = "\n\n".join(report_parts)
        
        # Save to file
        output_path = self.output_dir / "master_narrative.md"
        output_path.write_text(full_report)
        logger.info(f"Narrative report saved to {output_path}")
        
        return full_report
    
    def _generate_executive_summary_section(self) -> str:
        """Generate the executive summary section."""
        personality = self.cognitive_model.get_personality_summary()
        values = self.cognitive_model.get_core_values()
        communication = self.cognitive_model.get_communication_style()
        
        summary = [
            "## Executive Summary\n",
            "This digital twin represents a comprehensive model of your digital persona, " 
            "constructed from analysis of your communications, interactions, and expressed thoughts.\n",
            "### Key Insights\n"
        ]
        
        # Add personality insights
        summary.append("#### Personality Essence\n")
        summary.append(personality['summary'])
        
        # Add core values
        summary.append("\n#### Core Values\n")
        for value, strength in values.items():
            summary.append(f"- **{value}**: {strength['description']}")
        
        # Add communication style
        summary.append("\n#### Communication Style\n")
        summary.append(communication['summary'])
        
        # Add relationship insights
        top_relationships = self.cognitive_model.get_key_relationships(limit=3)
        summary.append("\n#### Key Relationships\n")
        for person, details in top_relationships.items():
            summary.append(f"- **{person}**: {details['summary']}")
        
        return "\n".join(summary)
    
    def _generate_personality_profile_section(self) -> str:
        """Generate the personality profile section."""
        personality = self.cognitive_model.get_personality_details()
        
        section = [
            "## Personality Profile\n",
            "This section explores the multifaceted aspects of your personality as expressed through your digital communications.\n"
        ]
        
        # Big Five traits
        section.append("### Big Five Personality Traits\n")
        section.append("Your communications reveal the following personality dimensions:\n")
        
        for trait, details in personality['big_five'].items():
            section.append(f"#### {trait.title()} ({details['score']:.1f}/10)\n")
            section.append(details['description'])
            section.append("\n**How this manifests in your communications:**\n")
            for example in details['examples'][:3]:
                section.append(f"- {example}")
            section.append("")
        
        # Values system
        section.append("### Core Values System\n")
        section.append("Your communications reveal these core values that guide your decisions and perspectives:\n")
        
        for value, details in personality['values'].items():
            section.append(f"#### {value}\n")
            section.append(f"**Strength**: {details['strength']}/10\n")
            section.append(details['description'])
            section.append("\n**Evidence in communications:**\n")
            for example in details['evidence'][:3]:
                section.append(f"- {example}")
            section.append("")
        
        # Cognitive patterns
        section.append("### Cognitive Patterns\n")
        section.append("Your typical approaches to problems and decisions include:\n")
        
        for pattern, details in personality['cognitive_patterns'].items():
            section.append(f"#### {pattern}\n")
            section.append(details['description'])
            section.append("\n**Examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        # Emotional patterns
        section.append("### Emotional Expression\n")
        section.append("Your emotional landscape as expressed in communications:\n")
        
        # Create a visualization of emotional distribution
        emotions = personality['emotional_patterns']
        emotion_names = list(emotions.keys())
        emotion_values = [e['frequency'] for e in emotions.values()]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(emotion_names, emotion_values, color=sns.color_palette("viridis", len(emotion_names)))
        plt.title("Emotional Expression Distribution")
        plt.ylabel("Frequency")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the figure
        emotion_chart_path = self.output_dir / "emotion_distribution.png"
        plt.savefig(emotion_chart_path)
        plt.close()
        
        section.append(f"![Emotional Expression Distribution](emotion_distribution.png)\n")
        
        # Add descriptions of top emotions
        for emotion, details in sorted(emotions.items(), key=lambda x: x[1]['frequency'], reverse=True)[:5]:
            section.append(f"#### {emotion}\n")
            section.append(details['description'])
            section.append("\n**Context examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        return "\n".join(section)
    
    def _generate_relationship_analysis_section(self) -> str:
        """Generate the relationship analysis section."""
        relationships = self.cognitive_model.get_relationship_network()
        
        section = [
            "## Relationship Analysis\n",
            "This section explores your social connections and how you interact with different people in your life.\n"
        ]
        
        # Relationship network visualization
        section.append("### Relationship Network\n")
        section.append("The following visualization shows your social connections and their relative importance:\n")
        
        # Create network visualization
        network_chart_path = self.output_dir / "relationship_network.png"
        self._create_relationship_network_visualization(relationships, network_chart_path)
        section.append(f"![Relationship Network](relationship_network.png)\n")
        
        # Key relationships
        section.append("### Key Relationships\n")
        section.append("The most significant relationships in your communications:\n")
        
        for person, details in sorted(relationships.items(), 
                                     key=lambda x: x[1]['importance'], 
                                     reverse=True)[:10]:
            section.append(f"#### {person}\n")
            section.append(f"**Role**: {details['role']}\n")
            section.append(f"**Importance**: {details['importance']}/10\n")
            section.append(f"**Communication Frequency**: {details['frequency_description']}\n")
            section.append(f"**Relationship Quality**: {details['quality_description']}\n")
            section.append(details['summary'])
            
            # Add communication patterns specific to this relationship
            section.append("\n**Communication Patterns:**\n")
            for pattern in details['communication_patterns'][:3]:
                section.append(f"- {pattern}")
            
            # Add notable quotes or exchanges
            section.append("\n**Notable Exchanges:**\n")
            for exchange in details['notable_exchanges'][:2]:
                section.append(f"- {exchange}")
            
            section.append("")
        
        # Relationship dynamics
        section.append("### Relationship Dynamics\n")
        section.append("Patterns observed across your relationships:\n")
        
        dynamics = self.cognitive_model.get_relationship_dynamics()
        for dynamic, description in dynamics.items():
            section.append(f"#### {dynamic}\n")
            section.append(description)
            section.append("")
        
        return "\n".join(section)
    
    def _generate_communication_patterns_section(self) -> str:
        """Generate the communication patterns section."""
        communication = self.cognitive_model.get_communication_analysis()
        
        section = [
            "## Communication Patterns\n",
            "This section analyzes how you express yourself and interact with others through digital communication.\n"
        ]
        
        # Overall style
        section.append("### Overall Communication Style\n")
        section.append(communication['overall_style']['description'])
        
        # Create radar chart for communication dimensions
        dimensions = communication['dimensions']
        dim_names = list(dimensions.keys())
        dim_values = [d['score'] for d in dimensions.values()]
        
        # Create radar chart
        plt.figure(figsize=(10, 10))
        angles = np.linspace(0, 2*np.pi, len(dim_names), endpoint=False).tolist()
        angles += angles[:1]  # Close the loop
        
        dim_values += dim_values[:1]  # Close the loop
        
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, dim_values, 'o-', linewidth=2)
        ax.fill(angles, dim_values, alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), dim_names)
        ax.set_ylim(0, 10)
        ax.grid(True)
        
        plt.title("Communication Style Dimensions")
        comm_chart_path = self.output_dir / "communication_dimensions.png"
        plt.savefig(comm_chart_path)
        plt.close()
        
        section.append(f"\n![Communication Style Dimensions](communication_dimensions.png)\n")
        
        # Describe each dimension
        section.append("### Communication Dimensions\n")
        for dim_name, details in dimensions.items():
            section.append(f"#### {dim_name} ({details['score']}/10)\n")
            section.append(details['description'])
            section.append("\n**Examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        # Context adaptation
        section.append("### Context Adaptation\n")
        section.append("How your communication style changes across different contexts:\n")
        
        for context, details in communication['context_adaptation'].items():
            section.append(f"#### {context}\n")
            section.append(details['description'])
            section.append("\n**Key differences:**\n")
            for diff in details['key_differences']:
                section.append(f"- {diff}")
            section.append("")
        
        # Temporal patterns
        section.append("### Temporal Patterns\n")
        section.append("How your communication has evolved over time:\n")
        
        for pattern, description in communication['temporal_patterns'].items():
            section.append(f"#### {pattern}\n")
            section.append(description)
            section.append("")
        
        # Topic preferences
        section.append("### Topic Preferences\n")
        section.append("Subjects you tend to discuss most frequently:\n")
        
        # Create topic distribution visualization
        topics = communication['topics']
        topic_names = list(topics.keys())
        topic_values = [t['frequency'] for t in topics.values()]
        
        plt.figure(figsize=(12, 6))
        bars = plt.barh(topic_names, topic_values, color=sns.color_palette("viridis", len(topic_names)))
        plt.title("Topic Distribution in Communications")
        plt.xlabel("Frequency")
        plt.tight_layout()
        
        topic_chart_path = self.output_dir / "topic_distribution.png"
        plt.savefig(topic_chart_path)
        plt.close()
        
        section.append(f"![Topic Distribution](topic_distribution.png)\n")
        
        # Describe top topics
        for topic, details in sorted(topics.items(), key=lambda x: x[1]['frequency'], reverse=True)[:5]:
            section.append(f"#### {topic}\n")
            section.append(details['description'])
            section.append("")
        
        return "\n".join(section)
    
    def _generate_value_system_section(self) -> str:
        """Generate the value system section."""
        values = self.cognitive_model.get_value_system()
        
        section = [
            "## Value System\n",
            "This section explores your core values, beliefs, and principles as expressed through your communications.\n"
        ]
        
        # Core values
        section.append("### Core Values\n")
        section.append("The fundamental values that appear to guide your decisions and perspectives:\n")
        
        for value, details in values['core_values'].items():
            section.append(f"#### {value}\n")
            section.append(f"**Strength**: {details['strength']}/10\n")
            section.append(details['description'])
            section.append("\n**How this manifests:**\n")
            for example in details['manifestations'][:3]:
                section.append(f"- {example}")
            section.append("")
        
        # Moral foundations
        section.append("### Moral Foundations\n")
        section.append("Your moral reasoning appears to be based on these foundations:\n")
        
        foundations = values['moral_foundations']
        foundation_names = list(foundations.keys())
        foundation_values = [f['strength'] for f in foundations.values()]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(foundation_names, foundation_values, color=sns.color_palette("viridis", len(foundation_names)))
        plt.title("Moral Foundations Profile")
        plt.ylabel("Strength")
        plt.ylim(0, 10)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        moral_chart_path = self.output_dir / "moral_foundations.png"
        plt.savefig(moral_chart_path)
        plt.close()
        
        section.append(f"![Moral Foundations Profile](moral_foundations.png)\n")
        
        for foundation, details in foundations.items():
            section.append(f"#### {foundation} ({details['strength']}/10)\n")
            section.append(details['description'])
            section.append("")
        
        # Belief system
        section.append("### Belief System\n")
        section.append("Key beliefs expressed in your communications:\n")
        
        for belief_area, beliefs in values['beliefs'].items():
            section.append(f"#### {belief_area}\n")
            for belief, details in beliefs.items():
                section.append(f"- **{belief}**: {details['description']}")
            section.append("")
        
        # Value conflicts
        section.append("### Value Tensions\n")
        section.append("Areas where your values appear to create tension or nuance:\n")
        
        for tension, details in values['value_tensions'].items():
            section.append(f"#### {tension}\n")
            section.append(details['description'])
            section.append("\n**Examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        return "\n".join(section)
    
    def _generate_temporal_evolution_section(self) -> str:
        """Generate the temporal evolution section."""
        evolution = self.cognitive_model.get_temporal_evolution()
        
        section = [
            "## Temporal Evolution\n",
            "This section explores how your communication patterns, relationships, and expressed values have evolved over time.\n"
        ]
        
        # Life eras
        section.append("### Life Eras\n")
        section.append("Distinct periods identified in your communications:\n")
        
        # Create timeline visualization
        eras = evolution['eras']
        era_names = list(eras.keys())
        era_starts = [e['start_date'] for e in eras.values()]
        era_ends = [e['end_date'] for e in eras.values()]
        
        # Convert dates to numeric for plotting
        start_dates = pd.to_datetime(era_starts)
        end_dates = pd.to_datetime(era_ends)
        
        plt.figure(figsize=(12, 6))
        for i, era in enumerate(era_names):
            plt.barh(i, (end_dates[i] - start_dates[i]).days, left=start_dates[i], 
                    height=0.8, color=sns.color_palette("viridis", len(era_names))[i])
            plt.text(start_dates[i] + (end_dates[i] - start_dates[i])/2, i, 
                    era, ha='center', va='center')
        
        plt.yticks([])
        plt.title("Life Eras Timeline")
        plt.tight_layout()
        
        timeline_path = self.output_dir / "life_eras_timeline.png"
        plt.savefig(timeline_path)
        plt.close()
        
        section.append(f"![Life Eras Timeline](life_eras_timeline.png)\n")
        
        # Describe each era
        for era, details in eras.items():
            section.append(f"#### {era}\n")
            section.append(f"**Period**: {details['start_date']} to {details['end_date']}\n")
            section.append(details['description'])
            section.append("\n**Key characteristics:**\n")
            for char in details['characteristics']:
                section.append(f"- {char}")
            section.append("")
        
        # Evolution of communication style
        section.append("### Evolution of Communication Style\n")
        section.append("How your communication style has changed over time:\n")
        
        comm_evolution = evolution['communication_evolution']
        for aspect, details in comm_evolution.items():
            section.append(f"#### {aspect}\n")
            section.append(details['description'])
            section.append("")
        
        # Relationship evolution
        section.append("### Relationship Evolution\n")
        section.append("How your key relationships have evolved:\n")
        
        rel_evolution = evolution['relationship_evolution']
        for person, details in rel_evolution.items():
            section.append(f"#### {person}\n")
            section.append(details['description'])
            section.append("\n**Key transitions:**\n")
            for transition in details['transitions']:
                section.append(f"- {transition}")
            section.append("")
        
        # Value evolution
        section.append("### Value Evolution\n")
        section.append("How your expressed values have evolved over time:\n")
        
        value_evolution = evolution['value_evolution']
        for value, details in value_evolution.items():
            section.append(f"#### {value}\n")
            section.append(details['description'])
            section.append("")
        
        return "\n".join(section)
    
    def _generate_cognitive_framework_section(self) -> str:
        """Generate the cognitive framework section."""
        framework = self.cognitive_model.get_cognitive_framework()
        
        section = [
            "## Cognitive Framework\n",
            "This section explores your thought patterns, decision-making approaches, and knowledge structures.\n"
        ]
        
        # Decision making
        section.append("### Decision-Making Patterns\n")
        section.append("Your typical approaches to making decisions:\n")
        
        for pattern, details in framework['decision_making'].items():
            section.append(f"#### {pattern}\n")
            section.append(details['description'])
            section.append("\n**Examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        # Knowledge domains
        section.append("### Knowledge Domains\n")
        section.append("Areas where you demonstrate knowledge and expertise:\n")
        
        domains = framework['knowledge_domains']
        domain_names = list(domains.keys())
        domain_values = [d['strength'] for d in domains.values()]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(domain_names, domain_values, color=sns.color_palette("viridis", len(domain_names)))
        plt.title("Knowledge Domain Strengths")
        plt.ylabel("Strength")
        plt.ylim(0, 10)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        domains_chart_path = self.output_dir / "knowledge_domains.png"
        plt.savefig(domains_chart_path)
        plt.close()
        
        section.append(f"![Knowledge Domain Strengths](knowledge_domains.png)\n")
        
        # Describe top domains
        for domain, details in sorted(domains.items(), key=lambda x: x[1]['strength'], reverse=True)[:5]:
            section.append(f"#### {domain}\n")
            section.append(details['description'])
            section.append("")
        
        # Reasoning patterns
        section.append("### Reasoning Patterns\n")
        section.append("Your typical approaches to reasoning and problem-solving:\n")
        
        for pattern, details in framework['reasoning_patterns'].items():
            section.append(f"#### {pattern}\n")
            section.append(details['description'])
            section.append("\n**Examples:**\n")
            for example in details['examples'][:2]:
                section.append(f"- {example}")
            section.append("")
        
        # Mental models
        section.append("### Mental Models\n")
        section.append("Frameworks you use to understand the world:\n")
        
        for model, details in framework['mental_models'].items():
            section.append(f"#### {model}\n")
            section.append(details['description'])
            section.append("")
        
        return "\n".join(section)
    
    def _create_relationship_network_visualization(self, relationships: Dict[str, Any], output_path: Path) -> None:
        """
        Create a visualization of the relationship network.
        
        Args:
            relationships: Dictionary of relationship data
            output_path: Path to save the visualization
        """
        # This is a placeholder for actual network visualization code
        # In a real implementation, you would use networkx and matplotlib to create a graph
        
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, "Relationship Network Visualization\n(Placeholder)", 
                ha='center', va='center', fontsize=20)
        plt.axis('off')
        plt.savefig(output_path)
        plt.close()
    
    def generate_interactive_dashboard(self) -> str:
        """
        Generate an interactive dashboard for exploring the digital twin.
        
        Returns:
            URL or path to the dashboard
        """
        # This would typically generate a Dash or Streamlit dashboard
        # For now, we'll just return a placeholder
        dashboard_path = self.output_dir / "dashboard.html"
        
        # Create a simple HTML file as a placeholder
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cognitive-Twin Omega Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                h1 { color: #2c3e50; }
                .placeholder { 
                    padding: 50px; 
                    background-color: #ecf0f1; 
                    border-radius: 5px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1>Cognitive-Twin Omega Interactive Dashboard</h1>
            <div class="placeholder">
                <h2>Dashboard Placeholder</h2>
                <p>In a full implementation, this would be an interactive dashboard with visualizations and filters.</p>
            </div>
        </body>
        </html>
        """
        
        dashboard_path.write_text(html_content)
        return str(dashboard_path)
    
    def generate_knowledge_graph_export(self, format: str = "json") -> str:
        """
        Export the knowledge graph in the specified format.
        
        Args:
            format: Export format (json, csv, neo4j)
            
        Returns:
            Path to the exported file
        """
        if not self.cognitive_model:
            return "Error: Cognitive model not available"
            
        knowledge_graph = self.cognitive_model.get_knowledge_graph()
        
        if format == "json":
            output_path = self.output_dir / "knowledge_graph.json"
            with open(output_path, 'w') as f:
                json.dump(knowledge_graph.to_dict(), f, indent=2)
            return str(output_path)
        
        elif format == "csv":
            nodes_path = self.output_dir / "knowledge_graph_nodes.csv"
            edges_path = self.output_dir / "knowledge_graph_edges.csv"
            
            # Export nodes
            nodes_df = pd.DataFrame(knowledge_graph.get_nodes())
            nodes_df.to_csv(nodes_path, index=False)
            
            # Export edges
            edges_df = pd.DataFrame(knowledge_graph.get_edges())
            edges_df.to_csv(edges_path, index=False)
            
            return f"Nodes: {nodes_path}, Edges: {edges_path}"
        
        else:
            return f"Unsupported export format: {format}"
    
    def generate_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response to a user query based on the cognitive model.
        
        Args:
            query: User query
            context: Optional context information
            
        Returns:
            Response text
        """
        if not self.cognitive_model:
            return "Error: Cognitive model not available"
            
        # Process the query
        response = self.cognitive_model.generate_response(query, context)
        
        # Format the response based on style configuration
        if self.tone == "conversational":
            # Add conversational elements
            response = self._add_conversational_elements(response)
        
        return response
    
    def _add_conversational_elements(self, text: str) -> str:
        """Add conversational elements to make text more human-like."""
        # Add fillers and conversational markers
        fillers = ["Well, ", "So, ", "Hmm, ", "You know, ", "I'd say ", "I think "]
        
        # Only add a filler at the beginning sometimes
        if np.random.random() < 0.3:
            text = np.random.choice(fillers) + text[0].lower() + text[1:]
        
        # Add thinking pauses
        thinking_pauses = [", um, ", ", uh, ", ", like, ", ", I mean, ", ", you know, "]
        if len(text) > 50 and np.random.random() < 0.4:
            # Find a good spot to insert a pause
            sentences = re.split(r'([.!?] )', text)
            if len(sentences) > 2:
                insert_idx = np.random.randint(1, len(sentences)//2)
                sentences.insert(insert_idx*2, np.random.choice(thinking_pauses))
                text = ''.join(sentences)
        
        # Add personal reflections sometimes
        reflections = [
            " I've noticed this pattern before.",
            " This reminds me of something similar.",
            " I've been thinking about this recently.",
            " This seems to be a recurring theme."
        ]
        if np.random.random() < 0.2:
            text += np.random.choice(reflections)
        
        return text
    
    def display_in_console(self, content: str, format: str = "markdown") -> None:
        """
        Display content in the console with rich formatting.
        
        Args:
            content: Content to display
            format: Format of the content (markdown, table, etc.)
        """
        if format == "markdown":
            console.print(Markdown(content))
        else:
            console.print(content)
    
    def create_visualization(self, data: Dict[str, Any], viz_type: str, title: str) -> Path:
        """
        Create a visualization based on the provided data.
        
        Args:
            data: Data for visualization
            viz_type: Type of visualization
            title: Title for the visualization
            
        Returns:
            Path to the saved visualization
        """
        plt.figure(figsize=(10, 6))
        
        if viz_type == "bar":
            plt.bar(list(data.keys()), list(data.values()))
        elif viz_type == "pie":
            plt.pie(list(data.values()), labels=list(data.keys()), autopct='%1.1f%%')
        elif viz_type == "line":
            plt.plot(list(data.keys()), list(data.values()))
        else:
            plt.text(0.5, 0.5, f"Unsupported visualization type: {viz_type}", 
                    ha='center', va='center')
        
        plt.title(title)
        plt.tight_layout()
        
        # Save the visualization
        output_path = self.output_dir / f"{title.lower().replace(' ', '_')}.png"
        plt.savefig(output_path)
        plt.close()
        
        return output_path