"""
Chart visualization module.

This module provides functionality for creating data visualizations and charts,
including static charts and interactive dashboards.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
import os
from datetime import datetime
import base64
import tempfile
import io

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generator for data visualizations and charts."""
    
    def __init__(self):
        """Initialize the chart generator."""
        self.initialized = False
        self.visualization_libraries_available = False
        
        # Try to import visualization libraries
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            
            self.plt = plt
            self.np = np
            self.pd = pd
            self.visualization_libraries_available = True
            logger.info("Visualization libraries available for charts")
        except ImportError:
            logger.warning("Visualization libraries not available for charts")
    
    async def initialize(self):
        """Initialize the chart generator."""
        logger.info("Initializing chart generator")
        
        self.initialized = True
        logger.info("Chart generator initialized")
    
    async def create_bar_chart(self, data: Dict[str, Any], 
                              title: str = "Bar Chart",
                              x_label: str = "X",
                              y_label: str = "Y",
                              width: int = 800,
                              height: int = 600) -> Dict[str, Any]:
        """
        Create a bar chart.
        
        Args:
            data: Dictionary containing 'x' and 'y' lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing chart data
        """
        logger.info("Creating bar chart")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Extract data
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            
            if not x_data or not y_data or len(x_data) != len(y_data):
                return {'error': "Invalid data format"}
            
            # Create figure
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Create bar chart
            plt.bar(x_data, y_data)
            
            # Add labels and title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.title(title)
            
            # Rotate x-axis labels if needed
            if max(len(str(x)) for x in x_data) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name)
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
                'chart_type': 'bar',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {str(e)}")
            return {'error': str(e)}
    
    async def create_line_chart(self, data: Dict[str, Any], 
                               title: str = "Line Chart",
                               x_label: str = "X",
                               y_label: str = "Y",
                               width: int = 800,
                               height: int = 600) -> Dict[str, Any]:
        """
        Create a line chart.
        
        Args:
            data: Dictionary containing 'x' and 'y' lists, or 'series' list of dictionaries
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing chart data
        """
        logger.info("Creating line chart")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Check if data contains series or single x/y
            if 'series' in data:
                # Multiple series
                series_data = data['series']
                for series in series_data:
                    x_data = series.get('x', [])
                    y_data = series.get('y', [])
                    label = series.get('label', 'Series')
                    
                    if x_data and y_data and len(x_data) == len(y_data):
                        plt.plot(x_data, y_data, label=label)
                
                # Add legend
                plt.legend()
            else:
                # Single series
                x_data = data.get('x', [])
                y_data = data.get('y', [])
                
                if not x_data or not y_data or len(x_data) != len(y_data):
                    return {'error': "Invalid data format"}
                
                plt.plot(x_data, y_data)
            
            # Add labels and title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.title(title)
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name)
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
                'chart_type': 'line',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating line chart: {str(e)}")
            return {'error': str(e)}
    
    async def create_pie_chart(self, data: Dict[str, Any], 
                              title: str = "Pie Chart",
                              width: int = 800,
                              height: int = 600) -> Dict[str, Any]:
        """
        Create a pie chart.
        
        Args:
            data: Dictionary containing 'labels' and 'values' lists
            title: Chart title
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing chart data
        """
        logger.info("Creating pie chart")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Extract data
            labels = data.get('labels', [])
            values = data.get('values', [])
            
            if not labels or not values or len(labels) != len(values):
                return {'error': "Invalid data format"}
            
            # Create figure
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Create pie chart
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            plt.axis('equal')
            
            # Add title
            plt.title(title)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name)
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
                'chart_type': 'pie',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating pie chart: {str(e)}")
            return {'error': str(e)}
    
    async def create_scatter_plot(self, data: Dict[str, Any], 
                                 title: str = "Scatter Plot",
                                 x_label: str = "X",
                                 y_label: str = "Y",
                                 width: int = 800,
                                 height: int = 600) -> Dict[str, Any]:
        """
        Create a scatter plot.
        
        Args:
            data: Dictionary containing 'x' and 'y' lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing chart data
        """
        logger.info("Creating scatter plot")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Extract data
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            colors = data.get('colors', None)
            sizes = data.get('sizes', None)
            
            if not x_data or not y_data or len(x_data) != len(y_data):
                return {'error': "Invalid data format"}
            
            # Create figure
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Create scatter plot
            if colors and sizes:
                plt.scatter(x_data, y_data, c=colors, s=sizes, alpha=0.7)
                plt.colorbar(label='Color Value')
            elif colors:
                plt.scatter(x_data, y_data, c=colors, alpha=0.7)
                plt.colorbar(label='Color Value')
            elif sizes:
                plt.scatter(x_data, y_data, s=sizes, alpha=0.7)
            else:
                plt.scatter(x_data, y_data, alpha=0.7)
            
            # Add labels and title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.title(title)
            
            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name)
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
                'chart_type': 'scatter',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating scatter plot: {str(e)}")
            return {'error': str(e)}
    
    async def create_heatmap(self, data: Dict[str, Any], 
                            title: str = "Heatmap",
                            x_label: str = "X",
                            y_label: str = "Y",
                            width: int = 800,
                            height: int = 600) -> Dict[str, Any]:
        """
        Create a heatmap.
        
        Args:
            data: Dictionary containing 'matrix' 2D list, and optional 'x_labels' and 'y_labels'
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing chart data
        """
        logger.info("Creating heatmap")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.visualization_libraries_available:
            logger.warning("Visualization libraries not available")
            return {'error': "Visualization libraries not available"}
        
        try:
            # Extract data
            matrix = data.get('matrix', [])
            x_labels = data.get('x_labels', None)
            y_labels = data.get('y_labels', None)
            
            if not matrix or not all(isinstance(row, list) for row in matrix):
                return {'error': "Invalid data format"}
            
            # Convert to numpy array
            np = self.np
            matrix_array = np.array(matrix)
            
            # Create figure
            plt = self.plt
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Create heatmap
            im = plt.imshow(matrix_array, cmap='viridis')
            
            # Add colorbar
            plt.colorbar(im, label='Value')
            
            # Add labels and title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.title(title)
            
            # Add x and y labels if provided
            if x_labels:
                plt.xticks(range(len(x_labels)), x_labels, rotation=45, ha='right')
            
            if y_labels:
                plt.yticks(range(len(y_labels)), y_labels)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name)
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
                'chart_type': 'heatmap',
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
            return {'error': str(e)}
    
    async def create_interactive_chart(self, data: Dict[str, Any], 
                                      chart_type: str = "line",
                                      title: str = "Interactive Chart",
                                      x_label: str = "X",
                                      y_label: str = "Y") -> Dict[str, Any]:
        """
        Create an interactive chart using Plotly.
        
        Args:
            data: Dictionary containing chart data
            chart_type: Type of chart ('line', 'bar', 'scatter', 'pie')
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            
        Returns:
            Dictionary containing HTML for interactive chart
        """
        logger.info(f"Creating interactive {chart_type} chart")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create HTML for interactive chart using Plotly
            html = self._create_plotly_html(data, chart_type, title, x_label, y_label)
            
            return {
                'html': html,
                'chart_type': chart_type,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive chart: {str(e)}")
            return {'error': str(e)}
    
    def _create_plotly_html(self, data: Dict[str, Any], chart_type: str,
                           title: str, x_label: str, y_label: str) -> str:
        """
        Create HTML for interactive chart using Plotly.
        
        Args:
            data: Dictionary containing chart data
            chart_type: Type of chart
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            
        Returns:
            HTML string
        """
        # Create JSON data for Plotly
        plotly_data = []
        
        if chart_type == 'line':
            if 'series' in data:
                # Multiple series
                for series in data['series']:
                    plotly_data.append({
                        'x': series.get('x', []),
                        'y': series.get('y', []),
                        'type': 'scatter',
                        'mode': 'lines',
                        'name': series.get('label', 'Series')
                    })
            else:
                # Single series
                plotly_data.append({
                    'x': data.get('x', []),
                    'y': data.get('y', []),
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'Series'
                })
        
        elif chart_type == 'bar':
            plotly_data.append({
                'x': data.get('x', []),
                'y': data.get('y', []),
                'type': 'bar',
                'name': 'Series'
            })
        
        elif chart_type == 'scatter':
            plotly_data.append({
                'x': data.get('x', []),
                'y': data.get('y', []),
                'mode': 'markers',
                'type': 'scatter',
                'marker': {
                    'size': data.get('sizes', [10] * len(data.get('x', []))),
                    'color': data.get('colors', [])
                },
                'name': 'Series'
            })
        
        elif chart_type == 'pie':
            plotly_data.append({
                'labels': data.get('labels', []),
                'values': data.get('values', []),
                'type': 'pie',
                'name': 'Series'
            })
        
        # Create layout
        layout = {
            'title': title,
            'xaxis': {'title': x_label},
            'yaxis': {'title': y_label}
        }
        
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div id="chart" style="width: 100%; height: 100vh;"></div>
            <script>
                const data = {json.dumps(plotly_data)};
                const layout = {json.dumps(layout)};
                
                Plotly.newPlot('chart', data, layout, {{responsive: true}});
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def create_dashboard(self, charts: List[Dict[str, Any]], 
                              title: str = "Dashboard",
                              layout: List[List[int]] = None) -> Dict[str, Any]:
        """
        Create a dashboard with multiple charts.
        
        Args:
            charts: List of chart dictionaries
            title: Dashboard title
            layout: Grid layout for charts (e.g., [[0, 1], [2, 3]] for 2x2 grid)
            
        Returns:
            Dictionary containing HTML for dashboard
        """
        logger.info("Creating dashboard")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create HTML for dashboard
            html = self._create_dashboard_html(charts, title, layout)
            
            return {
                'html': html,
                'title': title,
                'chart_count': len(charts)
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _create_dashboard_html(self, charts: List[Dict[str, Any]], 
                              title: str, layout: List[List[int]]) -> str:
        """
        Create HTML for dashboard.
        
        Args:
            charts: List of chart dictionaries
            title: Dashboard title
            layout: Grid layout for charts
            
        Returns:
            HTML string
        """
        # Create grid layout if not provided
        if not layout:
            # Create a simple grid layout
            cols = min(2, len(charts))  # Max 2 columns
            rows = (len(charts) + cols - 1) // cols  # Ceiling division
            
            layout = []
            chart_idx = 0
            for r in range(rows):
                row = []
                for c in range(cols):
                    if chart_idx < len(charts):
                        row.append(chart_idx)
                        chart_idx += 1
                    else:
                        row.append(-1)  # Empty cell
                layout.append(row)
        
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
                .dashboard {{ display: grid; width: 100%; height: 100vh; }}
                .chart-container {{ border: 1px solid #ddd; padding: 10px; }}
                h1 {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="dashboard" style="grid-template-rows: repeat({len(layout)}, 1fr); grid-template-columns: repeat({len(layout[0])}, 1fr);">
        """
        
        # Add chart containers
        for r, row in enumerate(layout):
            for c, chart_idx in enumerate(row):
                if chart_idx >= 0 and chart_idx < len(charts):
                    chart = charts[chart_idx]
                    chart_title = chart.get('title', f'Chart {chart_idx + 1}')
                    
                    html += f"""
                    <div class="chart-container" style="grid-row: {r + 1}; grid-column: {c + 1};">
                        <h3>{chart_title}</h3>
                        <div id="chart-{chart_idx}" style="width: 100%; height: calc(100% - 40px);"></div>
                    </div>
                    """
        
        # Add JavaScript for charts
        html += """
            </div>
            <script>
        """
        
        for i, chart in enumerate(charts):
            chart_type = chart.get('chart_type', 'line')
            chart_data = chart.get('data', {})
            
            # Create Plotly data based on chart type
            plotly_data = []
            
            if chart_type == 'line':
                if 'series' in chart_data:
                    # Multiple series
                    for series in chart_data['series']:
                        plotly_data.append({
                            'x': series.get('x', []),
                            'y': series.get('y', []),
                            'type': 'scatter',
                            'mode': 'lines',
                            'name': series.get('label', f'Series {i}')
                        })
                else:
                    # Single series
                    plotly_data.append({
                        'x': chart_data.get('x', []),
                        'y': chart_data.get('y', []),
                        'type': 'scatter',
                        'mode': 'lines',
                        'name': 'Series'
                    })
            
            elif chart_type == 'bar':
                plotly_data.append({
                    'x': chart_data.get('x', []),
                    'y': chart_data.get('y', []),
                    'type': 'bar',
                    'name': 'Series'
                })
            
            elif chart_type == 'scatter':
                plotly_data.append({
                    'x': chart_data.get('x', []),
                    'y': chart_data.get('y', []),
                    'mode': 'markers',
                    'type': 'scatter',
                    'marker': {
                        'size': chart_data.get('sizes', [10] * len(chart_data.get('x', []))),
                        'color': chart_data.get('colors', [])
                    },
                    'name': 'Series'
                })
            
            elif chart_type == 'pie':
                plotly_data.append({
                    'labels': chart_data.get('labels', []),
                    'values': chart_data.get('values', []),
                    'type': 'pie',
                    'name': 'Series'
                })
            
            # Create layout
            layout = {
                'margin': {'t': 10, 'b': 30, 'l': 30, 'r': 10},
                'xaxis': {'title': chart.get('x_label', 'X')},
                'yaxis': {'title': chart.get('y_label', 'Y')}
            }
            
            html += f"""
                // Chart {i}
                (function() {{
                    const data = {json.dumps(plotly_data)};
                    const layout = {json.dumps(layout)};
                    
                    Plotly.newPlot('chart-{i}', data, layout, {{responsive: true}});
                }})();
            """
        
        html += """
            </script>
        </body>
        </html>
        """
        
        return html