#!/usr/bin/env python3
"""
Visualization Example

This script demonstrates the functionality of the integrated visualization system.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
import random

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/visualization_example.log")
    ]
)
logger = logging.getLogger(__name__)

# Import visualization manager
from integrated_system.visualization import VisualizationManager

async def main():
    """Main function to demonstrate visualization functionality."""
    logger.info("Starting Visualization Example")
    
    # Create and initialize visualization manager
    logger.info("Creating visualization manager")
    viz_manager = VisualizationManager()
    await viz_manager.initialize()
    
    # Create a bar chart
    logger.info("Creating bar chart")
    bar_data = {
        'x': ['Category A', 'Category B', 'Category C', 'Category D', 'Category E'],
        'y': [23, 45, 56, 78, 42]
    }
    bar_chart = await viz_manager.create_chart(
        chart_type='bar',
        data=bar_data,
        title='Sample Bar Chart',
        x_label='Categories',
        y_label='Values'
    )
    logger.info(f"Bar chart created: {bar_chart.get('format', 'unknown')} format")
    
    # Save bar chart to file
    if 'image_base64' in bar_chart:
        import base64
        with open('results/bar_chart.png', 'wb') as f:
            f.write(base64.b64decode(bar_chart['image_base64']))
        logger.info("Bar chart saved to results/bar_chart.png")
    
    # Create a line chart with multiple series
    logger.info("Creating line chart")
    line_data = {
        'series': [
            {
                'label': 'Series A',
                'x': list(range(10)),
                'y': [random.randint(10, 100) for _ in range(10)]
            },
            {
                'label': 'Series B',
                'x': list(range(10)),
                'y': [random.randint(10, 100) for _ in range(10)]
            },
            {
                'label': 'Series C',
                'x': list(range(10)),
                'y': [random.randint(10, 100) for _ in range(10)]
            }
        ]
    }
    line_chart = await viz_manager.create_chart(
        chart_type='line',
        data=line_data,
        title='Sample Line Chart',
        x_label='Time',
        y_label='Values'
    )
    logger.info(f"Line chart created: {line_chart.get('format', 'unknown')} format")
    
    # Save line chart to file
    if 'image_base64' in line_chart:
        import base64
        with open('results/line_chart.png', 'wb') as f:
            f.write(base64.b64decode(line_chart['image_base64']))
        logger.info("Line chart saved to results/line_chart.png")
    
    # Create a pie chart
    logger.info("Creating pie chart")
    pie_data = {
        'categories': ['Category A', 'Category B', 'Category C', 'Category D', 'Category E'],
        'values': [23, 45, 56, 78, 42]
    }
    pie_chart = await viz_manager.create_chart(
        chart_type='pie',
        data=pie_data,
        title='Sample Pie Chart'
    )
    logger.info(f"Pie chart created: {pie_chart.get('format', 'unknown')} format")
    
    # Save pie chart to file
    if 'image_base64' in pie_chart:
        import base64
        with open('results/pie_chart.png', 'wb') as f:
            f.write(base64.b64decode(pie_chart['image_base64']))
        logger.info("Pie chart saved to results/pie_chart.png")
    
    # Create a network graph
    logger.info("Creating network graph")
    nodes = [
        {'id': 1, 'label': 'Node 1', 'type': 'person', 'group': 1, 'size': 10},
        {'id': 2, 'label': 'Node 2', 'type': 'person', 'group': 1, 'size': 10},
        {'id': 3, 'label': 'Node 3', 'type': 'organization', 'group': 2, 'size': 15},
        {'id': 4, 'label': 'Node 4', 'type': 'organization', 'group': 2, 'size': 15},
        {'id': 5, 'label': 'Node 5', 'type': 'event', 'group': 3, 'size': 8},
        {'id': 6, 'label': 'Node 6', 'type': 'event', 'group': 3, 'size': 8},
        {'id': 7, 'label': 'Node 7', 'type': 'location', 'group': 4, 'size': 12}
    ]
    
    edges = [
        {'source': 1, 'target': 2, 'type': 'friend', 'weight': 1},
        {'source': 1, 'target': 3, 'type': 'member', 'weight': 2},
        {'source': 2, 'target': 3, 'type': 'member', 'weight': 2},
        {'source': 3, 'target': 4, 'type': 'partner', 'weight': 3},
        {'source': 2, 'target': 4, 'type': 'member', 'weight': 2},
        {'source': 4, 'target': 5, 'type': 'organizer', 'weight': 2},
        {'source': 5, 'target': 6, 'type': 'related', 'weight': 1},
        {'source': 6, 'target': 7, 'type': 'location', 'weight': 2},
        {'source': 1, 'target': 7, 'type': 'visited', 'weight': 1}
    ]
    
    network_graph = await viz_manager.create_graph(
        nodes=nodes,
        edges=edges,
        title='Sample Network Graph',
        layout='spring'
    )
    logger.info(f"Network graph created: {network_graph.get('format', 'unknown')} format")
    
    # Save network graph to file
    if 'image_base64' in network_graph:
        import base64
        with open('results/network_graph.png', 'wb') as f:
            f.write(base64.b64decode(network_graph['image_base64']))
        logger.info("Network graph saved to results/network_graph.png")
    
    # Create a dashboard with multiple components
    logger.info("Creating dashboard")
    dashboard_components = [
        {
            'type': 'chart',
            'title': 'Sales by Category',
            'chart_type': 'bar',
            'data': bar_data
        },
        {
            'type': 'chart',
            'title': 'Performance Over Time',
            'chart_type': 'line',
            'data': line_data
        },
        {
            'type': 'chart',
            'title': 'Market Share',
            'chart_type': 'pie',
            'data': pie_data
        },
        {
            'type': 'graph',
            'title': 'Relationship Network',
            'data': {
                'nodes': nodes,
                'links': edges
            }
        },
        {
            'type': 'text',
            'title': 'Summary',
            'content': """
            <p>This dashboard provides an overview of key metrics and relationships.</p>
            <ul>
                <li>The bar chart shows sales by category</li>
                <li>The line chart shows performance over time</li>
                <li>The pie chart shows market share</li>
                <li>The network graph shows relationships between entities</li>
            </ul>
            """
        }
    ]
    
    dashboard = await viz_manager.create_dashboard(
        components=dashboard_components,
        title='Sample Dashboard'
    )
    logger.info("Dashboard created")
    
    # Save dashboard HTML to file
    if 'html' in dashboard:
        os.makedirs('results', exist_ok=True)
        with open('results/dashboard.html', 'w') as f:
            f.write(dashboard['html'])
        logger.info("Dashboard saved to results/dashboard.html")
    
    logger.info("Visualization example completed")

if __name__ == "__main__":
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the main function
    asyncio.run(main())