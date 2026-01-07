"""
Visualization Module for CogniLink

This module provides functionality for creating visualizations from analysis results.
"""

import os
import logging
import json
import tempfile
from typing import Dict, List, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import networkx as nx
import numpy as np
import pandas as pd
from wordcloud import WordCloud
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

class Visualizer:
    """
    Visualizer for CogniLink data.
    
    This class provides methods for creating visualizations from analysis results.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the visualizer.
        
        Args:
            config: Optional configuration dictionary
        """
        from cognilink.core.config import Config
        self.config = config or {}
        self.system_config = Config()
        
        # Set up matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        
        # Set up seaborn
        sns.set_theme(style="whitegrid")
        
        # Get color scheme from config
        interface_config = self.system_config.get_section('interface')
        colors = interface_config.get('reports', {}).get('styling', {}).get('colors', {})
        
        self.colors = {
            'primary': colors.get('primary', '#3498db'),
            'secondary': colors.get('secondary', '#2c3e50'),
            'accent': colors.get('accent', '#e74c3c'),
            'text': colors.get('text', '#333333'),
            'background': colors.get('background', '#ffffff')
        }
        
        # Create color palette
        self.palette = [
            self.colors['primary'],
            self.colors['secondary'],
            self.colors['accent'],
            '#2ecc71',  # green
            '#9b59b6',  # purple
            '#f39c12',  # orange
            '#1abc9c',  # turquoise
            '#34495e',  # dark blue
            '#e67e22',  # dark orange
            '#16a085'   # dark turquoise
        ]
    
    def create_visualization(self, data: Dict[str, Any], viz_type: str, 
                            output_path: Optional[str] = None, **kwargs) -> str:
        """
        Create a visualization from data.
        
        Args:
            data: Data to visualize
            viz_type: Type of visualization
            output_path: Path to save the visualization (if None, a temporary file is created)
            **kwargs: Additional arguments for the visualization
            
        Returns:
            Path to the visualization file
        """
        # Create output directory if it doesn't exist
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        else:
            # Create a temporary file
            fd, output_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
        
        # Create visualization based on type
        if viz_type == 'time_series':
            return self.create_time_series(data, output_path, **kwargs)
        elif viz_type == 'bar_chart':
            return self.create_bar_chart(data, output_path, **kwargs)
        elif viz_type == 'pie_chart':
            return self.create_pie_chart(data, output_path, **kwargs)
        elif viz_type == 'network_graph':
            return self.create_network_graph(data, output_path, **kwargs)
        elif viz_type == 'heatmap':
            return self.create_heatmap(data, output_path, **kwargs)
        elif viz_type == 'word_cloud':
            return self.create_word_cloud(data, output_path, **kwargs)
        elif viz_type == 'scatter_plot':
            return self.create_scatter_plot(data, output_path, **kwargs)
        elif viz_type == 'bubble_chart':
            return self.create_bubble_chart(data, output_path, **kwargs)
        elif viz_type == 'radar_chart':
            return self.create_radar_chart(data, output_path, **kwargs)
        elif viz_type == 'sankey_diagram':
            return self.create_sankey_diagram(data, output_path, **kwargs)
        else:
            raise ValueError(f"Unsupported visualization type: {viz_type}")
    
    def create_time_series(self, data: Dict[str, Any], output_path: str, 
                          title: str = 'Time Series', **kwargs) -> str:
        """
        Create a time series visualization.
        
        Args:
            data: Data to visualize (dict with dates as keys and values as values)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Convert data to pandas Series
            if isinstance(data, dict):
                # Sort by date
                sorted_items = sorted(data.items())
                dates = [item[0] for item in sorted_items]
                values = [item[1] for item in sorted_items]
            elif isinstance(data, list):
                # Assume list of dicts with 'date' and 'value' keys
                if all('date' in item and 'value' in item for item in data):
                    sorted_items = sorted(data, key=lambda x: x['date'])
                    dates = [item['date'] for item in sorted_items]
                    values = [item['value'] for item in sorted_items]
                else:
                    # Assume list of values with implicit dates
                    dates = list(range(len(data)))
                    values = data
            else:
                raise ValueError("Data must be a dict or list")
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Plot data
            plt.plot(dates, values, marker='o', linestyle='-', color=self.colors['primary'])
            
            # Add labels and title
            plt.xlabel(kwargs.get('xlabel', 'Date'))
            plt.ylabel(kwargs.get('ylabel', 'Value'))
            plt.title(title)
            
            # Format x-axis for dates if needed
            if isinstance(dates[0], str) and len(dates) > 10:
                plt.xticks(rotation=45)
                plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created time series visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating time series visualization: {str(e)}")
            raise
    
    def create_bar_chart(self, data: Dict[str, Any], output_path: str, 
                        title: str = 'Bar Chart', **kwargs) -> str:
        """
        Create a bar chart visualization.
        
        Args:
            data: Data to visualize (dict with categories as keys and values as values)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Convert data to lists
            if isinstance(data, dict):
                categories = list(data.keys())
                values = list(data.values())
            elif isinstance(data, list):
                # Assume list of dicts with 'category' and 'value' keys
                if all('category' in item and 'value' in item for item in data):
                    categories = [item['category'] for item in data]
                    values = [item['value'] for item in data]
                else:
                    # Assume list of values with implicit categories
                    categories = list(range(len(data)))
                    values = data
            else:
                raise ValueError("Data must be a dict or list")
            
            # Sort data if requested
            if kwargs.get('sort', False):
                sorted_indices = np.argsort(values)
                if kwargs.get('sort_ascending', True):
                    sorted_indices = sorted_indices[::-1]
                categories = [categories[i] for i in sorted_indices]
                values = [values[i] for i in sorted_indices]
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Plot data
            orientation = kwargs.get('orientation', 'vertical')
            if orientation == 'horizontal':
                bars = plt.barh(categories, values, color=self.colors['primary'])
                plt.xlabel(kwargs.get('xlabel', 'Value'))
                plt.ylabel(kwargs.get('ylabel', 'Category'))
            else:
                bars = plt.bar(categories, values, color=self.colors['primary'])
                plt.xlabel(kwargs.get('xlabel', 'Category'))
                plt.ylabel(kwargs.get('ylabel', 'Value'))
            
            # Add value labels on bars
            if kwargs.get('show_values', True):
                for bar in bars:
                    if orientation == 'horizontal':
                        plt.text(bar.get_width() + max(values) * 0.01, 
                                bar.get_y() + bar.get_height() / 2, 
                                str(int(bar.get_width()) if bar.get_width().is_integer() else f"{bar.get_width():.2f}"), 
                                va='center')
                    else:
                        plt.text(bar.get_x() + bar.get_width() / 2, 
                                bar.get_height() + max(values) * 0.01, 
                                str(int(bar.get_height()) if bar.get_height().is_integer() else f"{bar.get_height():.2f}"), 
                                ha='center')
            
            # Add title
            plt.title(title)
            
            # Format x-axis for categories if needed
            if orientation == 'vertical' and len(categories) > 10:
                plt.xticks(rotation=45, ha='right')
            
            # Add grid
            plt.grid(True, axis='y' if orientation == 'vertical' else 'x', linestyle='--', alpha=0.7)
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created bar chart visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating bar chart visualization: {str(e)}")
            raise
    
    def create_pie_chart(self, data: Dict[str, Any], output_path: str, 
                        title: str = 'Pie Chart', **kwargs) -> str:
        """
        Create a pie chart visualization.
        
        Args:
            data: Data to visualize (dict with categories as keys and values as values)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Convert data to lists
            if isinstance(data, dict):
                labels = list(data.keys())
                values = list(data.values())
            elif isinstance(data, list):
                # Assume list of dicts with 'label' and 'value' keys
                if all('label' in item and 'value' in item for item in data):
                    labels = [item['label'] for item in data]
                    values = [item['value'] for item in data]
                else:
                    # Assume list of values with implicit labels
                    labels = [f"Category {i+1}" for i in range(len(data))]
                    values = data
            else:
                raise ValueError("Data must be a dict or list")
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Plot data
            explode = kwargs.get('explode', None)
            if explode is True:
                # Explode the largest slice
                max_index = values.index(max(values))
                explode = [0.1 if i == max_index else 0 for i in range(len(values))]
            
            wedges, texts, autotexts = plt.pie(
                values, 
                labels=None if kwargs.get('legend', True) else labels,
                autopct=kwargs.get('autopct', '%1.1f%%'),
                startangle=kwargs.get('startangle', 90),
                shadow=kwargs.get('shadow', False),
                explode=explode,
                colors=self.palette[:len(values)]
            )
            
            # Customize text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
            
            # Add legend if requested
            if kwargs.get('legend', True):
                plt.legend(
                    wedges, 
                    labels,
                    title=kwargs.get('legend_title', 'Categories'),
                    loc=kwargs.get('legend_loc', 'center left'),
                    bbox_to_anchor=kwargs.get('legend_bbox_to_anchor', (1, 0, 0.5, 1))
                )
            
            # Add title
            plt.title(title)
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            plt.axis('equal')
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created pie chart visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating pie chart visualization: {str(e)}")
            raise
    
    def create_network_graph(self, data: Dict[str, Any], output_path: str, 
                            title: str = 'Network Graph', **kwargs) -> str:
        """
        Create a network graph visualization.
        
        Args:
            data: Data to visualize (dict with 'nodes' and 'edges' keys)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Extract nodes and edges
            if 'nodes' in data and 'edges' in data:
                nodes = data['nodes']
                edges = data['edges']
            else:
                raise ValueError("Data must contain 'nodes' and 'edges' keys")
            
            # Create graph
            G = nx.Graph()
            
            # Add nodes
            for node in nodes:
                if isinstance(node, dict) and 'id' in node:
                    node_id = node['id']
                    G.add_node(node_id, **{k: v for k, v in node.items() if k != 'id'})
                else:
                    G.add_node(node)
            
            # Add edges
            for edge in edges:
                if isinstance(edge, dict) and 'source' in edge and 'target' in edge:
                    source = edge['source']
                    target = edge['target']
                    weight = edge.get('weight', 1.0)
                    G.add_edge(source, target, weight=weight, **{k: v for k, v in edge.items() 
                                                              if k not in ['source', 'target', 'weight']})
                elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                    source, target = edge[:2]
                    weight = edge[2] if len(edge) > 2 else 1.0
                    G.add_edge(source, target, weight=weight)
                else:
                    raise ValueError("Edge must be a dict with 'source' and 'target' keys or a list/tuple")
            
            # Create figure
            plt.figure(figsize=(12, 10))
            
            # Set layout
            layout_type = kwargs.get('layout', 'spring')
            if layout_type == 'spring':
                pos = nx.spring_layout(G, k=kwargs.get('k', 0.3), iterations=kwargs.get('iterations', 50))
            elif layout_type == 'circular':
                pos = nx.circular_layout(G)
            elif layout_type == 'kamada_kawai':
                pos = nx.kamada_kawai_layout(G)
            elif layout_type == 'spectral':
                pos = nx.spectral_layout(G)
            else:
                pos = nx.spring_layout(G)
            
            # Get node sizes and colors
            node_size = kwargs.get('node_size', 300)
            if callable(node_size):
                node_sizes = [node_size(G.nodes[n]) for n in G.nodes()]
            elif isinstance(node_size, dict):
                node_sizes = [node_size.get(n, 300) for n in G.nodes()]
            elif 'size' in G.nodes[list(G.nodes())[0]]:
                node_sizes = [G.nodes[n].get('size', 300) for n in G.nodes()]
            else:
                node_sizes = [node_size] * len(G.nodes())
            
            node_color = kwargs.get('node_color', self.colors['primary'])
            if callable(node_color):
                node_colors = [node_color(G.nodes[n]) for n in G.nodes()]
            elif isinstance(node_color, dict):
                node_colors = [node_color.get(n, self.colors['primary']) for n in G.nodes()]
            elif 'color' in G.nodes[list(G.nodes())[0]]:
                node_colors = [G.nodes[n].get('color', self.colors['primary']) for n in G.nodes()]
            else:
                node_colors = [node_color] * len(G.nodes())
            
            # Get edge weights
            edge_width = kwargs.get('edge_width', 1.0)
            if callable(edge_width):
                edge_widths = [edge_width(G.edges[e]) for e in G.edges()]
            elif isinstance(edge_width, dict):
                edge_widths = [edge_width.get(e, 1.0) for e in G.edges()]
            else:
                edge_widths = [G.edges[e].get('weight', 1.0) for e in G.edges()]
                # Scale edge widths
                if edge_widths:
                    max_width = max(edge_widths)
                    min_width = min(edge_widths)
                    if max_width > min_width:
                        edge_widths = [1 + 5 * (w - min_width) / (max_width - min_width) for w in edge_widths]
                    else:
                        edge_widths = [1.0] * len(edge_widths)
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
            nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5, edge_color='gray')
            
            # Add labels if requested
            if kwargs.get('show_labels', True):
                labels = {}
                for node in G.nodes():
                    if isinstance(node, dict) and 'label' in node:
                        labels[node['id']] = node['label']
                    elif 'label' in G.nodes[node]:
                        labels[node] = G.nodes[node]['label']
                    elif 'name' in G.nodes[node]:
                        labels[node] = G.nodes[node]['name']
                    else:
                        labels[node] = str(node)
                
                nx.draw_networkx_labels(G, pos, labels=labels, font_size=kwargs.get('font_size', 10))
            
            # Add title
            plt.title(title)
            
            # Remove axes
            plt.axis('off')
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created network graph visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating network graph visualization: {str(e)}")
            raise
    
    def create_heatmap(self, data: Union[Dict[str, Dict[str, float]], List[List[float]]], 
                      output_path: str, title: str = 'Heatmap', **kwargs) -> str:
        """
        Create a heatmap visualization.
        
        Args:
            data: Data to visualize (2D array or nested dict)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Convert data to numpy array
            if isinstance(data, dict):
                # Convert nested dict to DataFrame
                df = pd.DataFrame(data).fillna(0)
                row_labels = df.index
                col_labels = df.columns
                data_array = df.values
            elif isinstance(data, list) and all(isinstance(row, list) for row in data):
                # 2D list
                data_array = np.array(data)
                row_labels = kwargs.get('row_labels', [f"Row {i+1}" for i in range(len(data))])
                col_labels = kwargs.get('col_labels', [f"Col {i+1}" for i in range(len(data[0]))])
            else:
                raise ValueError("Data must be a nested dict or 2D list")
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Create heatmap
            ax = sns.heatmap(
                data_array,
                annot=kwargs.get('annot', True),
                fmt=kwargs.get('fmt', '.2f'),
                cmap=kwargs.get('cmap', 'viridis'),
                linewidths=kwargs.get('linewidths', 0.5),
                xticklabels=col_labels,
                yticklabels=row_labels,
                cbar=kwargs.get('cbar', True)
            )
            
            # Add labels and title
            plt.xlabel(kwargs.get('xlabel', ''))
            plt.ylabel(kwargs.get('ylabel', ''))
            plt.title(title)
            
            # Rotate x-axis labels if needed
            if kwargs.get('rotate_xlabels', False):
                plt.xticks(rotation=45, ha='right')
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created heatmap visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating heatmap visualization: {str(e)}")
            raise
    
    def create_word_cloud(self, data: Dict[str, float], output_path: str, 
                         title: str = 'Word Cloud', **kwargs) -> str:
        """
        Create a word cloud visualization.
        
        Args:
            data: Data to visualize (dict with words as keys and frequencies as values)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create word cloud
            wordcloud = WordCloud(
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 400),
                background_color=kwargs.get('background_color', 'white'),
                max_words=kwargs.get('max_words', 200),
                contour_width=kwargs.get('contour_width', 3),
                contour_color=kwargs.get('contour_color', 'steelblue'),
                colormap=kwargs.get('colormap', 'viridis'),
                collocations=kwargs.get('collocations', False)
            )
            
            # Generate word cloud
            wordcloud.generate_from_frequencies(data)
            
            # Display the word cloud
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            # Add title
            if kwargs.get('show_title', True):
                plt.title(title, fontsize=kwargs.get('title_fontsize', 16))
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created word cloud visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating word cloud visualization: {str(e)}")
            raise
    
    def create_scatter_plot(self, data: List[Dict[str, Any]], output_path: str, 
                           title: str = 'Scatter Plot', **kwargs) -> str:
        """
        Create a scatter plot visualization.
        
        Args:
            data: Data to visualize (list of dicts with 'x' and 'y' keys)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Extract x and y values
            if all('x' in item and 'y' in item for item in data):
                x_values = [item['x'] for item in data]
                y_values = [item['y'] for item in data]
                
                # Extract optional values
                colors = [item.get('color', self.colors['primary']) for item in data]
                sizes = [item.get('size', 50) for item in data]
                labels = [item.get('label', '') for item in data]
            elif isinstance(data, list) and len(data) == 2 and all(isinstance(item, list) for item in data):
                # Assume [x_values, y_values]
                x_values, y_values = data
                colors = [self.colors['primary']] * len(x_values)
                sizes = [50] * len(x_values)
                labels = [''] * len(x_values)
            else:
                raise ValueError("Data must be a list of dicts with 'x' and 'y' keys or a list of [x_values, y_values]")
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Create scatter plot
            scatter = plt.scatter(
                x_values,
                y_values,
                c=colors,
                s=sizes,
                alpha=kwargs.get('alpha', 0.7),
                edgecolors=kwargs.get('edgecolors', 'white'),
                linewidths=kwargs.get('linewidths', 0.5)
            )
            
            # Add labels and title
            plt.xlabel(kwargs.get('xlabel', 'X'))
            plt.ylabel(kwargs.get('ylabel', 'Y'))
            plt.title(title)
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Add labels if requested
            if kwargs.get('show_labels', False) and any(labels):
                for i, label in enumerate(labels):
                    if label:
                        plt.annotate(
                            label,
                            (x_values[i], y_values[i]),
                            textcoords="offset points",
                            xytext=(0, 5),
                            ha='center'
                        )
            
            # Add legend if requested
            if kwargs.get('show_legend', False) and 'groups' in kwargs:
                groups = kwargs['groups']
                handles = [plt.Line2D([0], [0], marker='o', color='w', 
                                     markerfacecolor=color, markersize=10) 
                          for color in groups.values()]
                plt.legend(handles, groups.keys(), title=kwargs.get('legend_title', 'Groups'))
            
            # Add trend line if requested
            if kwargs.get('trend_line', False):
                z = np.polyfit(x_values, y_values, 1)
                p = np.poly1d(z)
                plt.plot(x_values, p(x_values), linestyle='--', color=kwargs.get('trend_line_color', 'red'))
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created scatter plot visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating scatter plot visualization: {str(e)}")
            raise
    
    def create_bubble_chart(self, data: List[Dict[str, Any]], output_path: str, 
                           title: str = 'Bubble Chart', **kwargs) -> str:
        """
        Create a bubble chart visualization.
        
        Args:
            data: Data to visualize (list of dicts with 'x', 'y', and 'size' keys)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Extract values
            if all('x' in item and 'y' in item and 'size' in item for item in data):
                x_values = [item['x'] for item in data]
                y_values = [item['y'] for item in data]
                sizes = [item['size'] for item in data]
                
                # Extract optional values
                colors = [item.get('color', self.colors['primary']) for item in data]
                labels = [item.get('label', '') for item in data]
            else:
                raise ValueError("Data must be a list of dicts with 'x', 'y', and 'size' keys")
            
            # Scale sizes
            min_size = kwargs.get('min_size', 20)
            max_size = kwargs.get('max_size', 1000)
            if len(sizes) > 1:
                min_val = min(sizes)
                max_val = max(sizes)
                if max_val > min_val:
                    sizes = [min_size + (max_size - min_size) * (s - min_val) / (max_val - min_val) for s in sizes]
                else:
                    sizes = [min_size] * len(sizes)
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Create bubble chart
            scatter = plt.scatter(
                x_values,
                y_values,
                s=sizes,
                c=colors,
                alpha=kwargs.get('alpha', 0.7),
                edgecolors=kwargs.get('edgecolors', 'white'),
                linewidths=kwargs.get('linewidths', 0.5)
            )
            
            # Add labels and title
            plt.xlabel(kwargs.get('xlabel', 'X'))
            plt.ylabel(kwargs.get('ylabel', 'Y'))
            plt.title(title)
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Add labels if requested
            if kwargs.get('show_labels', True):
                for i, label in enumerate(labels):
                    if label:
                        plt.annotate(
                            label,
                            (x_values[i], y_values[i]),
                            textcoords="offset points",
                            xytext=(0, 5),
                            ha='center'
                        )
            
            # Add legend for sizes if requested
            if kwargs.get('size_legend', True):
                size_legend_values = kwargs.get('size_legend_values', [min(sizes), (min(sizes) + max(sizes)) / 2, max(sizes)])
                size_legend_labels = kwargs.get('size_legend_labels', [f"{v:.1f}" for v in size_legend_values])
                
                # Create legend handles
                handles = [plt.Line2D([0], [0], marker='o', color='w', 
                                     markerfacecolor=self.colors['primary'], 
                                     markersize=np.sqrt(s) / 2) 
                          for s in size_legend_values]
                
                plt.legend(handles, size_legend_labels, 
                          title=kwargs.get('size_legend_title', 'Size'),
                          loc=kwargs.get('size_legend_loc', 'upper right'))
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created bubble chart visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating bubble chart visualization: {str(e)}")
            raise
    
    def create_radar_chart(self, data: Dict[str, List[float]], output_path: str, 
                          title: str = 'Radar Chart', **kwargs) -> str:
        """
        Create a radar chart visualization.
        
        Args:
            data: Data to visualize (dict with categories as keys and values as values)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Extract categories and values
            categories = kwargs.get('categories', list(data.keys()))
            
            # Handle multiple series
            if isinstance(list(data.values())[0], list):
                # Multiple series
                series_names = kwargs.get('series_names', [f"Series {i+1}" for i in range(len(list(data.values())[0]))])
                values = []
                for category in categories:
                    values.append(data[category])
                values = list(zip(*values))  # Transpose
            else:
                # Single series
                series_names = [kwargs.get('series_name', 'Series 1')]
                values = [list(data[category] for category in categories)]
            
            # Number of variables
            N = len(categories)
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Create radar chart
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Close the loop
            
            # Create subplot with polar projection
            ax = plt.subplot(111, polar=True)
            
            # Draw one axis per variable and add labels
            plt.xticks(angles[:-1], categories)
            
            # Draw y-axis labels
            ax.set_rlabel_position(0)
            
            # Plot data
            for i, (name, vals) in enumerate(zip(series_names, values)):
                # Close the loop
                vals_with_closure = list(vals)
                vals_with_closure += vals_with_closure[:1]
                
                # Plot values
                ax.plot(angles, vals_with_closure, linewidth=2, linestyle='solid', label=name, 
                       color=self.palette[i % len(self.palette)])
                ax.fill(angles, vals_with_closure, alpha=0.1, color=self.palette[i % len(self.palette)])
            
            # Add legend
            plt.legend(loc=kwargs.get('legend_loc', 'upper right'))
            
            # Add title
            plt.title(title)
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created radar chart visualization: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating radar chart visualization: {str(e)}")
            raise
    
    def create_sankey_diagram(self, data: Dict[str, Any], output_path: str, 
                             title: str = 'Sankey Diagram', **kwargs) -> str:
        """
        Create a Sankey diagram visualization.
        
        Args:
            data: Data to visualize (dict with 'nodes' and 'links' keys)
            output_path: Path to save the visualization
            title: Title for the visualization
            **kwargs: Additional arguments
            
        Returns:
            Path to the visualization file
        """
        try:
            # Check if matplotlib has Sankey
            if not hasattr(matplotlib.pyplot, 'sankey'):
                raise ImportError("Matplotlib Sankey not available. Try installing matplotlib-sankey.")
            
            # Extract nodes and links
            if 'nodes' in data and 'links' in data:
                nodes = data['nodes']
                links = data['links']
            else:
                raise ValueError("Data must contain 'nodes' and 'links' keys")
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create Sankey diagram
            from matplotlib.sankey import Sankey
            
            # Initialize Sankey diagram
            sankey = Sankey(ax=plt.gca(), scale=0.01, head_angle=150, unit='')
            
            # Add flows
            for link in links:
                source = link['source']
                target = link['target']
                value = link['value']
                
                # Find source and target indices
                source_idx = next((i for i, node in enumerate(nodes) if node['id'] == source), None)
                target_idx = next((i for i, node in enumerate(nodes) if node['id'] == target), None)
                
                if source_idx is not None and target_idx is not None:
                    sankey.add(
                        flows=[value],
                        orientations=[0],
                        labels=[nodes[source_idx].get('name', str(source))],
                        trunklength=1.0,
                        pathlengths=[0.25]
                    )
            
            # Finish diagram
            diagrams = sankey.finish()
            
            # Add title
            plt.title(title)
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            plt.savefig(output_path, dpi=kwargs.get('dpi', 300), bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created Sankey diagram visualization: {output_path}")
            return output_path
        except ImportError:
            logger.warning("Matplotlib Sankey not available. Using network graph instead.")
            return self.create_network_graph(data, output_path, title, **kwargs)
        except Exception as e:
            logger.error(f"Error creating Sankey diagram visualization: {str(e)}")
            raise


def create_visualization(data: Dict[str, Any], viz_type: str, 
                        output_path: Optional[str] = None, **kwargs) -> str:
    """
    Create a visualization from data.
    
    Args:
        data: Data to visualize
        viz_type: Type of visualization
        output_path: Path to save the visualization (if None, a temporary file is created)
        **kwargs: Additional arguments for the visualization
        
    Returns:
        Path to the visualization file
    """
    visualizer = Visualizer()
    return visualizer.create_visualization(data, viz_type, output_path, **kwargs)