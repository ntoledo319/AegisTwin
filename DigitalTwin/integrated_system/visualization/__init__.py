"""
Visualization module for the integrated system.

This module provides visualization capabilities for the integrated system,
including charts, graphs, and interactive dashboards.
"""

import logging
from typing import Dict, List, Any, Optional
from .charts import ChartGenerator
from .graphs import GraphVisualizer
from .dashboards import DashboardGenerator

logger = logging.getLogger(__name__)

class VisualizationManager:
    """Manager for visualization components."""
    
    def __init__(self):
        """Initialize the visualization manager."""
        # Create components
        self.chart_generator = ChartGenerator()
        self.graph_visualizer = GraphVisualizer()
        self.dashboard_generator = DashboardGenerator(
            chart_generator=self.chart_generator,
            graph_visualizer=self.graph_visualizer
        )
        self.initialized = False
    
    async def initialize(self):
        """Initialize the visualization manager."""
        logger.info("Initializing visualization manager")
        
        # Initialize components
        await self.chart_generator.initialize()
        await self.graph_visualizer.initialize()
        await self.dashboard_generator.initialize()
        
        self.initialized = True
        logger.info("Visualization manager initialized")
    
    async def create_chart(self, chart_type: str, data: Dict[str, Any], 
                          title: str = None, **kwargs) -> Dict[str, Any]:
        """
        Create a chart visualization.
        
        Args:
            chart_type: Type of chart (bar, line, pie, scatter, heatmap)
            data: Chart data
            title: Chart title
            **kwargs: Additional chart parameters
            
        Returns:
            Dictionary containing chart data
        """
        logger.info(f"Creating {chart_type} chart")
        
        if not self.initialized:
            await self.initialize()
        
        # Set default title if not provided
        if title is None:
            title = f"{chart_type.capitalize()} Chart"
        
        # Create chart based on type
        if chart_type == 'bar':
            return await self.chart_generator.create_bar_chart(
                data=data,
                title=title,
                x_label=kwargs.get('x_label', 'X'),
                y_label=kwargs.get('y_label', 'Y'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
        elif chart_type == 'line':
            return await self.chart_generator.create_line_chart(
                data=data,
                title=title,
                x_label=kwargs.get('x_label', 'X'),
                y_label=kwargs.get('y_label', 'Y'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
        elif chart_type == 'pie':
            return await self.chart_generator.create_pie_chart(
                data=data,
                title=title,
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
        elif chart_type == 'scatter':
            return await self.chart_generator.create_scatter_plot(
                data=data,
                title=title,
                x_label=kwargs.get('x_label', 'X'),
                y_label=kwargs.get('y_label', 'Y'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
        elif chart_type == 'heatmap':
            return await self.chart_generator.create_heatmap(
                data=data,
                title=title,
                x_label=kwargs.get('x_label', 'X'),
                y_label=kwargs.get('y_label', 'Y'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
        else:
            logger.warning(f"Unknown chart type: {chart_type}")
            return {'error': f"Unknown chart type: {chart_type}"}
    
    async def create_graph(self, nodes: List[Dict[str, Any]], 
                          edges: List[Dict[str, Any]],
                          title: str = "Network Graph",
                          layout: str = "spring",
                          **kwargs) -> Dict[str, Any]:
        """
        Create a graph visualization.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            title: Graph title
            layout: Graph layout algorithm
            **kwargs: Additional graph parameters
            
        Returns:
            Dictionary containing graph visualization data
        """
        logger.info("Creating graph visualization")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.graph_visualizer.create_network_graph(
            nodes=nodes,
            edges=edges,
            title=title,
            layout=layout,
            width=kwargs.get('width', 800),
            height=kwargs.get('height', 600)
        )
    
    async def create_dashboard(self, components: List[Dict[str, Any]], 
                              title: str = "Dashboard",
                              layout: List[List[int]] = None) -> Dict[str, Any]:
        """
        Create a dashboard with multiple components.
        
        Args:
            components: List of component dictionaries
            title: Dashboard title
            layout: Grid layout for components
            
        Returns:
            Dictionary containing dashboard data
        """
        logger.info("Creating dashboard")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.dashboard_generator.create_dashboard(
            components=components,
            title=title,
            layout=layout
        )
    
    async def create_visualization_from_data(self, data: Any, 
                                           visualization_type: str = 'auto',
                                           title: str = None,
                                           **kwargs) -> Dict[str, Any]:
        """
        Create a visualization from data, automatically determining the best visualization type.
        
        Args:
            data: Data to visualize
            visualization_type: Type of visualization (auto, chart, graph, dashboard)
            title: Visualization title
            **kwargs: Additional visualization parameters
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info(f"Creating visualization from data (type: {visualization_type})")
        
        if not self.initialized:
            await self.initialize()
        
        # Determine visualization type if auto
        if visualization_type == 'auto':
            visualization_type = await self._determine_visualization_type(data)
        
        # Create visualization based on type
        if visualization_type == 'chart':
            chart_type = await self._determine_chart_type(data)
            return await self.create_chart(chart_type, data, title, **kwargs)
        elif visualization_type == 'graph':
            # Extract nodes and edges from data
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            return await self.create_graph(nodes, edges, title, **kwargs)
        elif visualization_type == 'dashboard':
            # Extract components from data
            components = data.get('components', [])
            layout = data.get('layout', None)
            return await self.create_dashboard(components, title, layout)
        else:
            logger.warning(f"Unknown visualization type: {visualization_type}")
            return {'error': f"Unknown visualization type: {visualization_type}"}
    
    async def _determine_visualization_type(self, data: Any) -> str:
        """
        Determine the best visualization type for the data.
        
        Args:
            data: Data to visualize
            
        Returns:
            Visualization type (chart, graph, dashboard)
        """
        # Check if data has nodes and edges (graph)
        if isinstance(data, dict) and 'nodes' in data and 'edges' in data:
            return 'graph'
        
        # Check if data has components (dashboard)
        if isinstance(data, dict) and 'components' in data:
            return 'dashboard'
        
        # Default to chart
        return 'chart'
    
    async def _determine_chart_type(self, data: Any) -> str:
        """
        Determine the best chart type for the data.
        
        Args:
            data: Data to visualize
            
        Returns:
            Chart type (bar, line, pie, scatter, heatmap)
        """
        # Check if data has categories (pie chart)
        if isinstance(data, dict) and 'categories' in data and 'values' in data:
            return 'pie'
        
        # Check if data has matrix (heatmap)
        if isinstance(data, dict) and 'matrix' in data:
            return 'heatmap'
        
        # Check if data has series (line chart)
        if isinstance(data, dict) and 'series' in data:
            return 'line'
        
        # Check if data has points (scatter plot)
        if isinstance(data, dict) and 'points' in data:
            return 'scatter'
        
        # Default to bar chart
        return 'bar'