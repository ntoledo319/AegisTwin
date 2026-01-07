"""
Report Generator for CogniLink

This module provides functionality to generate reports from analysis results.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import markdown
import jinja2
import datetime
import shutil
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
import numpy as np
import pandas as pd
from wordcloud import WordCloud

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generator for creating reports from analysis results.
    
    This class provides functionality to generate reports in various formats,
    including HTML, Markdown, and plain text.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the report generator.
        
        Args:
            config: Configuration dictionary for the report generator
        """
        self.config = config or {}
        self.template_dir = self.config.get('template_dir', 'templates')
        
        # Create Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Register custom filters
        self.jinja_env.filters['format_date'] = self._format_date
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['percentage'] = self._format_percentage
    
    def generate_report(self, analysis_results: Dict[str, Any], format_type: str, output_path: str) -> str:
        """
        Generate a report from analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis results
            format_type: Format of the report ('html', 'markdown', or 'text')
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        if format_type == 'html':
            return self._generate_html_report(analysis_results, output_path)
        elif format_type == 'markdown':
            return self._generate_markdown_report(analysis_results, output_path)
        elif format_type == 'text':
            return self._generate_text_report(analysis_results, output_path)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")
    
    def _generate_html_report(self, analysis_results: Dict[str, Any], output_path: str) -> str:
        """
        Generate an HTML report.
        
        Args:
            analysis_results: Dictionary containing analysis results
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        # Create output directory for assets
        output_dir = os.path.dirname(output_path)
        assets_dir = os.path.join(output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Generate visualizations
        visualization_paths = self._generate_visualizations(analysis_results, assets_dir)
        
        # Load template
        template = self.jinja_env.get_template('report_html.jinja2')
        
        # Prepare template context
        context = {
            'title': 'CogniLink Communication Analysis Report',
            'generated_at': datetime.datetime.now(),
            'analysis_results': analysis_results,
            'visualizations': visualization_paths
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy CSS and JS files if they exist
        css_source = os.path.join(self.template_dir, 'styles.css')
        js_source = os.path.join(self.template_dir, 'scripts.js')
        
        if os.path.exists(css_source):
            shutil.copy(css_source, os.path.join(output_dir, 'styles.css'))
        
        if os.path.exists(js_source):
            shutil.copy(js_source, os.path.join(output_dir, 'scripts.js'))
        
        return output_path
    
    def _generate_markdown_report(self, analysis_results: Dict[str, Any], output_path: str) -> str:
        """
        Generate a Markdown report.
        
        Args:
            analysis_results: Dictionary containing analysis results
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        # Create output directory for assets
        output_dir = os.path.dirname(output_path)
        assets_dir = os.path.join(output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Generate visualizations
        visualization_paths = self._generate_visualizations(analysis_results, assets_dir)
        
        # Load template
        template = self.jinja_env.get_template('report_markdown.jinja2')
        
        # Prepare template context
        context = {
            'title': 'CogniLink Communication Analysis Report',
            'generated_at': datetime.datetime.now(),
            'analysis_results': analysis_results,
            'visualizations': visualization_paths
        }
        
        # Render template
        md_content = template.render(**context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return output_path
    
    def _generate_text_report(self, analysis_results: Dict[str, Any], output_path: str) -> str:
        """
        Generate a plain text report.
        
        Args:
            analysis_results: Dictionary containing analysis results
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        # Load template
        template = self.jinja_env.get_template('report_text.jinja2')
        
        # Prepare template context
        context = {
            'title': 'CogniLink Communication Analysis Report',
            'generated_at': datetime.datetime.now(),
            'analysis_results': analysis_results
        }
        
        # Render template
        text_content = template.render(**context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return output_path
    
    def _generate_visualizations(self, analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Generate visualizations from analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis results
            output_dir: Directory to save visualizations
            
        Returns:
            Dictionary mapping visualization names to file paths
        """
        visualization_paths = {}
        
        # Set Seaborn style
        sns.set_theme(style="whitegrid")
        
        # Generate visualizations based on available data
        
        # Communication patterns visualizations
        if 'patterns' in analysis_results:
            patterns = analysis_results['patterns']
            
            # Time of day activity
            if 'time_of_day_activity' in patterns:
                viz_path = os.path.join(output_dir, 'time_of_day_activity.png')
                self._create_time_of_day_chart(patterns['time_of_day_activity'], viz_path)
                visualization_paths['time_of_day_activity'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
            
            # Day of week activity
            if 'day_of_week_activity' in patterns:
                viz_path = os.path.join(output_dir, 'day_of_week_activity.png')
                self._create_day_of_week_chart(patterns['day_of_week_activity'], viz_path)
                visualization_paths['day_of_week_activity'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
            
            # Communication frequency over time
            if 'frequency_over_time' in patterns:
                viz_path = os.path.join(output_dir, 'frequency_over_time.png')
                self._create_frequency_chart(patterns['frequency_over_time'], viz_path)
                visualization_paths['frequency_over_time'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
        
        # Relationship visualizations
        if 'relationships' in analysis_results:
            relationships = analysis_results['relationships']
            
            # Top contacts
            if 'top_contacts' in relationships:
                viz_path = os.path.join(output_dir, 'top_contacts.png')
                self._create_top_contacts_chart(relationships['top_contacts'], viz_path)
                visualization_paths['top_contacts'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
            
            # Communication network
            if 'communication_network' in relationships:
                viz_path = os.path.join(output_dir, 'communication_network.png')
                self._create_network_chart(relationships['communication_network'], viz_path)
                visualization_paths['communication_network'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
        
        # Topic visualizations
        if 'topics' in analysis_results:
            topics = analysis_results['topics']
            
            # Top topics
            if 'top_topics' in topics:
                viz_path = os.path.join(output_dir, 'top_topics.png')
                self._create_top_topics_chart(topics['top_topics'], viz_path)
                visualization_paths['top_topics'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
            
            # Word cloud
            if 'word_frequencies' in topics:
                viz_path = os.path.join(output_dir, 'word_cloud.png')
                self._create_word_cloud(topics['word_frequencies'], viz_path)
                visualization_paths['word_cloud'] = os.path.relpath(viz_path, os.path.dirname(output_dir))
        
        return visualization_paths
    
    def _create_time_of_day_chart(self, time_data: Dict[str, int], output_path: str):
        """Create a chart showing activity by hour of day."""
        plt.figure(figsize=(12, 6))
        
        # Convert to list of tuples and sort by hour
        data = [(int(hour), count) for hour, count in time_data.items()]
        data.sort(key=lambda x: x[0])
        
        hours = [item[0] for item in data]
        counts = [item[1] for item in data]
        
        # Create bar chart
        ax = sns.barplot(x=hours, y=counts, palette="viridis")
        
        # Customize chart
        plt.title('Communication Activity by Hour of Day', fontsize=16)
        plt.xlabel('Hour of Day', fontsize=12)
        plt.ylabel('Number of Communications', fontsize=12)
        plt.xticks(range(0, 24))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for i, count in enumerate(counts):
            ax.text(i, count + max(counts)*0.01, str(count), ha='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_day_of_week_chart(self, day_data: Dict[str, int], output_path: str):
        """Create a chart showing activity by day of week."""
        plt.figure(figsize=(10, 6))
        
        # Define day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Prepare data in correct order
        days = []
        counts = []
        for day in day_order:
            if day in day_data:
                days.append(day)
                counts.append(day_data[day])
        
        # Create bar chart
        ax = sns.barplot(x=days, y=counts, palette="viridis")
        
        # Customize chart
        plt.title('Communication Activity by Day of Week', fontsize=16)
        plt.xlabel('Day of Week', fontsize=12)
        plt.ylabel('Number of Communications', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for i, count in enumerate(counts):
            ax.text(i, count + max(counts)*0.01, str(count), ha='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_frequency_chart(self, frequency_data: Dict[str, int], output_path: str):
        """Create a chart showing communication frequency over time."""
        plt.figure(figsize=(14, 6))
        
        # Convert to list of tuples and sort by date
        data = [(date, count) for date, count in frequency_data.items()]
        data.sort(key=lambda x: x[0])
        
        dates = [item[0] for item in data]
        counts = [item[1] for item in data]
        
        # Create line chart
        plt.plot(dates, counts, marker='o', linestyle='-', color='#1f77b4', markersize=4)
        
        # Customize chart
        plt.title('Communication Frequency Over Time', fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Communications', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Format x-axis to show fewer date labels to avoid overcrowding
        if len(dates) > 10:
            plt.xticks(dates[::len(dates)//10], rotation=45)
        else:
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_top_contacts_chart(self, contacts_data: List[Dict[str, Any]], output_path: str):
        """Create a chart showing top contacts by interaction count."""
        plt.figure(figsize=(12, 8))
        
        # Limit to top 15 contacts for readability
        top_contacts = contacts_data[:15]
        
        # Extract names and counts
        names = [contact['name'] for contact in top_contacts]
        counts = [contact['interaction_count'] for contact in top_contacts]
        
        # Create horizontal bar chart
        ax = sns.barplot(y=names, x=counts, palette="viridis", orient='h')
        
        # Customize chart
        plt.title('Top Contacts by Interaction Count', fontsize=16)
        plt.xlabel('Number of Interactions', fontsize=12)
        plt.ylabel('Contact', fontsize=12)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Add value labels on bars
        for i, count in enumerate(counts):
            ax.text(count + max(counts)*0.01, i, str(count), va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_network_chart(self, network_data: Dict[str, Any], output_path: str):
        """Create a network visualization of communication patterns."""
        try:
            import networkx as nx
            
            plt.figure(figsize=(12, 12))
            
            # Create graph
            G = nx.Graph()
            
            # Add nodes
            for node in network_data.get('nodes', []):
                G.add_node(node['id'], name=node['name'], weight=node.get('weight', 1))
            
            # Add edges
            for edge in network_data.get('edges', []):
                G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
            
            # Get node positions using spring layout
            pos = nx.spring_layout(G, k=0.15, iterations=50)
            
            # Get node sizes based on weight
            node_sizes = [G.nodes[node].get('weight', 1) * 100 for node in G.nodes()]
            
            # Get edge weights
            edge_weights = [G.edges[edge].get('weight', 1) for edge in G.edges()]
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='skyblue', alpha=0.8)
            nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, edge_color='gray')
            nx.draw_networkx_labels(G, pos, labels={node: G.nodes[node].get('name', node) for node in G.nodes()}, 
                                   font_size=8, font_family='sans-serif')
            
            plt.title('Communication Network', fontsize=16)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        except ImportError:
            logger.warning("NetworkX library not found. Skipping network visualization.")
            # Create a placeholder image
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "Network visualization requires NetworkX library", 
                    ha='center', va='center', fontsize=14)
            plt.axis('off')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
    
    def _create_top_topics_chart(self, topics_data: List[Dict[str, Any]], output_path: str):
        """Create a chart showing top topics by frequency."""
        plt.figure(figsize=(12, 8))
        
        # Limit to top 15 topics for readability
        top_topics = topics_data[:15]
        
        # Extract names and frequencies
        names = [topic['name'] for topic in top_topics]
        frequencies = [topic['frequency'] for topic in top_topics]
        
        # Create horizontal bar chart
        ax = sns.barplot(y=names, x=frequencies, palette="viridis", orient='h')
        
        # Customize chart
        plt.title('Top Topics by Frequency', fontsize=16)
        plt.xlabel('Frequency', fontsize=12)
        plt.ylabel('Topic', fontsize=12)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Add value labels on bars
        for i, freq in enumerate(frequencies):
            ax.text(freq + max(frequencies)*0.01, i, f"{freq:.2f}", va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_word_cloud(self, word_frequencies: Dict[str, int], output_path: str):
        """Create a word cloud visualization."""
        try:
            plt.figure(figsize=(12, 8))
            
            # Generate word cloud
            wordcloud = WordCloud(width=800, height=400, background_color='white', 
                                 max_words=200, contour_width=3, contour_color='steelblue')
            
            # Generate from frequencies
            wordcloud.generate_from_frequencies(word_frequencies)
            
            # Display the word cloud
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Most Common Words in Communications', fontsize=16)
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        except ImportError:
            logger.warning("WordCloud library not found. Skipping word cloud visualization.")
            # Create a placeholder image
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "Word cloud visualization requires WordCloud library", 
                    ha='center', va='center', fontsize=14)
            plt.axis('off')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
    
    def _format_date(self, value):
        """Format a date value for display in templates."""
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, str):
            try:
                dt = datetime.datetime.fromisoformat(value)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
        return value
    
    def _format_number(self, value):
        """Format a number value for display in templates."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return value
    
    def _format_percentage(self, value, total=None):
        """Format a value as a percentage for display in templates."""
        if isinstance(value, (int, float)) and isinstance(total, (int, float)) and total > 0:
            percentage = (value / total) * 100
            return f"{percentage:.1f}%"
        elif isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return value