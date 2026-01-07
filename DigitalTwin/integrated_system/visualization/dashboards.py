"""
Dashboard visualization module.

This module provides functionality for creating interactive dashboards,
combining multiple visualizations into a cohesive interface.
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

class DashboardGenerator:
    """Generator for interactive dashboards."""
    
    def __init__(self, chart_generator=None, graph_visualizer=None):
        """
        Initialize the dashboard generator.
        
        Args:
            chart_generator: Chart generator instance
            graph_visualizer: Graph visualizer instance
        """
        self.chart_generator = chart_generator
        self.graph_visualizer = graph_visualizer
        self.initialized = False
    
    async def initialize(self):
        """Initialize the dashboard generator."""
        logger.info("Initializing dashboard generator")
        
        # Initialize components if provided
        if self.chart_generator and not self.chart_generator.initialized:
            await self.chart_generator.initialize()
        
        if self.graph_visualizer and not self.graph_visualizer.initialized:
            await self.graph_visualizer.initialize()
        
        self.initialized = True
        logger.info("Dashboard generator initialized")
    
    async def create_dashboard(self, components: List[Dict[str, Any]], 
                              title: str = "Dashboard",
                              layout: List[List[int]] = None) -> Dict[str, Any]:
        """
        Create a dashboard with multiple components.
        
        Args:
            components: List of component dictionaries
            title: Dashboard title
            layout: Grid layout for components (e.g., [[0, 1], [2, 3]] for 2x2 grid)
            
        Returns:
            Dictionary containing HTML for dashboard
        """
        logger.info("Creating dashboard")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create HTML for dashboard
            html = await self._create_dashboard_html(components, title, layout)
            
            return {
                'html': html,
                'title': title,
                'component_count': len(components)
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {'error': str(e)}
    
    async def _create_dashboard_html(self, components: List[Dict[str, Any]], 
                                    title: str, layout: List[List[int]]) -> str:
        """
        Create HTML for dashboard.
        
        Args:
            components: List of component dictionaries
            title: Dashboard title
            layout: Grid layout for components
            
        Returns:
            HTML string
        """
        # Create grid layout if not provided
        if not layout:
            # Create a simple grid layout
            cols = min(2, len(components))  # Max 2 columns
            rows = (len(components) + cols - 1) // cols  # Ceiling division
            
            layout = []
            component_idx = 0
            for r in range(rows):
                row = []
                for c in range(cols):
                    if component_idx < len(components):
                        row.append(component_idx)
                        component_idx += 1
                    else:
                        row.append(-1)  # Empty cell
                layout.append(row)
        
        # Process components
        processed_components = []
        for component in components:
            component_type = component.get('type', 'chart')
            component_data = component.get('data', {})
            
            if component_type == 'chart':
                # Process chart component
                processed_component = await self._process_chart_component(component)
            elif component_type == 'graph':
                # Process graph component
                processed_component = await self._process_graph_component(component)
            elif component_type == 'table':
                # Process table component
                processed_component = await self._process_table_component(component)
            elif component_type == 'text':
                # Process text component
                processed_component = await self._process_text_component(component)
            else:
                # Unknown component type
                processed_component = {
                    'type': 'text',
                    'content': f"Unknown component type: {component_type}"
                }
            
            processed_components.append(processed_component)
        
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                }}
                .dashboard {{
                    display: grid;
                    grid-gap: 20px;
                    width: 100%;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .component {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    padding: 15px;
                }}
                .component-header {{
                    margin-top: 0;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #eee;
                }}
                .chart-container {{
                    width: 100%;
                    height: 300px;
                }}
                .graph-container {{
                    width: 100%;
                    height: 400px;
                }}
                .table-container {{
                    width: 100%;
                    overflow-x: auto;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="dashboard" style="grid-template-rows: repeat({len(layout)}, auto); grid-template-columns: repeat({len(layout[0])}, 1fr);">
        """
        
        # Add components
        for r, row in enumerate(layout):
            for c, component_idx in enumerate(row):
                if component_idx >= 0 and component_idx < len(processed_components):
                    component = processed_components[component_idx]
                    component_title = component.get('title', f'Component {component_idx + 1}')
                    component_type = component.get('type', 'text')
                    
                    html += f"""
                    <div class="component" style="grid-row: {r + 1}; grid-column: {c + 1};">
                        <h3 class="component-header">{component_title}</h3>
                    """
                    
                    if component_type == 'chart':
                        html += f"""
                        <div class="chart-container" id="chart-{component_idx}"></div>
                        """
                    elif component_type == 'graph':
                        html += f"""
                        <div class="graph-container" id="graph-{component_idx}"></div>
                        """
                    elif component_type == 'table':
                        html += f"""
                        <div class="table-container">
                            {component.get('content', '')}
                        </div>
                        """
                    elif component_type == 'text':
                        html += f"""
                        <div class="text-container">
                            {component.get('content', '')}
                        </div>
                        """
                    elif component_type == 'image':
                        html += f"""
                        <div class="image-container">
                            <img src="data:image/{component.get('format', 'png')};base64,{component.get('content', '')}" 
                                 style="max-width: 100%; height: auto;" />
                        </div>
                        """
                    
                    html += """
                    </div>
                    """
        
        # Add JavaScript for charts and graphs
        html += """
            </div>
            <script>
        """
        
        # Add chart scripts
        for i, component in enumerate(processed_components):
            if component.get('type') == 'chart' and 'plotly_data' in component:
                html += f"""
                // Chart {i}
                (function() {{
                    const data = {json.dumps(component['plotly_data'])};
                    const layout = {json.dumps(component.get('plotly_layout', {}))};
                    
                    Plotly.newPlot('chart-{i}', data, layout, {{responsive: true}});
                }})();
                """
            elif component.get('type') == 'graph' and 'graph_data' in component:
                html += f"""
                // Graph {i}
                (function() {{
                    const nodes = {json.dumps(component['graph_data']['nodes'])};
                    const links = {json.dumps(component['graph_data']['links'])};
                    
                    // Create a color scale for node groups
                    const nodeGroups = [...new Set(nodes.map(d => d.group))];
                    const color = d3.scaleOrdinal()
                        .domain(nodeGroups)
                        .range(d3.schemeCategory10);
                    
                    // Create SVG
                    const svg = d3.select("#graph-{i}")
                        .append("svg")
                        .attr("width", "100%")
                        .attr("height", "100%");
                    
                    const width = document.getElementById("graph-{i}").clientWidth;
                    const height = document.getElementById("graph-{i}").clientHeight;
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
                        .attr("stroke", "#999")
                        .attr("stroke-opacity", 0.6)
                        .attr("stroke-width", d => Math.sqrt(d.value || 1) * 2);
                    
                    // Create nodes
                    const node = g.selectAll(".node")
                        .data(nodes)
                        .enter().append("circle")
                        .attr("class", "node")
                        .attr("r", d => d.size || 5)
                        .attr("fill", d => color(d.group))
                        .attr("stroke", "#fff")
                        .attr("stroke-width", 1.5)
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
                        .attr("font-family", "sans-serif")
                        .attr("font-size", "10px")
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
                }})();
                """
        
        html += """
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def _process_chart_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a chart component.
        
        Args:
            component: Chart component dictionary
            
        Returns:
            Processed component dictionary
        """
        chart_type = component.get('chart_type', 'line')
        chart_data = component.get('data', {})
        chart_title = component.get('title', 'Chart')
        x_label = component.get('x_label', 'X')
        y_label = component.get('y_label', 'Y')
        
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
                        'name': series.get('label', 'Series')
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
        plotly_layout = {
            'margin': {'t': 10, 'b': 30, 'l': 30, 'r': 10},
            'xaxis': {'title': x_label},
            'yaxis': {'title': y_label}
        }
        
        return {
            'type': 'chart',
            'title': chart_title,
            'plotly_data': plotly_data,
            'plotly_layout': plotly_layout
        }
    
    async def _process_graph_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a graph component.
        
        Args:
            component: Graph component dictionary
            
        Returns:
            Processed component dictionary
        """
        graph_title = component.get('title', 'Graph')
        nodes = component.get('nodes', [])
        edges = component.get('edges', [])
        
        # Prepare nodes and links for D3
        d3_nodes = []
        for node in nodes:
            d3_node = {
                'id': node['id'],
                'label': node.get('label', str(node['id'])),
                'group': node.get('type', 'default'),
                'size': node.get('size', 5)
            }
            
            d3_nodes.append(d3_node)
        
        d3_links = []
        for edge in edges:
            d3_link = {
                'source': edge['source'],
                'target': edge['target'],
                'value': edge.get('weight', 1.0)
            }
            
            d3_links.append(d3_link)
        
        return {
            'type': 'graph',
            'title': graph_title,
            'graph_data': {
                'nodes': d3_nodes,
                'links': d3_links
            }
        }
    
    async def _process_table_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a table component.
        
        Args:
            component: Table component dictionary
            
        Returns:
            Processed component dictionary
        """
        table_title = component.get('title', 'Table')
        headers = component.get('headers', [])
        rows = component.get('rows', [])
        
        # Create HTML table
        table_html = "<table>"
        
        # Add headers
        if headers:
            table_html += "<tr>"
            for header in headers:
                table_html += f"<th>{header}</th>"
            table_html += "</tr>"
        
        # Add rows
        for row in rows:
            table_html += "<tr>"
            for cell in row:
                table_html += f"<td>{cell}</td>"
            table_html += "</tr>"
        
        table_html += "</table>"
        
        return {
            'type': 'table',
            'title': table_title,
            'content': table_html
        }
    
    async def _process_text_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a text component.
        
        Args:
            component: Text component dictionary
            
        Returns:
            Processed component dictionary
        """
        text_title = component.get('title', 'Text')
        text_content = component.get('content', '')
        
        # Format text content as HTML
        if isinstance(text_content, str):
            # Replace newlines with <br>
            text_content = text_content.replace('\n', '<br>')
        else:
            # Convert to string
            text_content = str(text_content)
        
        return {
            'type': 'text',
            'title': text_title,
            'content': text_content
        }
    
    async def create_user_dashboard(self, user_data: Dict[str, Any], 
                                   title: str = "User Dashboard") -> Dict[str, Any]:
        """
        Create a dashboard for a user.
        
        Args:
            user_data: User data dictionary
            title: Dashboard title
            
        Returns:
            Dictionary containing HTML for dashboard
        """
        logger.info("Creating user dashboard")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create components for user dashboard
            components = []
            
            # User profile component
            if 'profile' in user_data:
                profile = user_data['profile']
                profile_html = f"""
                <div style="display: flex; align-items: center;">
                    <div style="flex: 0 0 100px; margin-right: 20px;">
                        <img src="{profile.get('avatar_url', 'https://via.placeholder.com/100')}" 
                             style="width: 100px; height: 100px; border-radius: 50%;" />
                    </div>
                    <div>
                        <h2 style="margin-top: 0;">{profile.get('name', 'User')}</h2>
                        <p>{profile.get('bio', '')}</p>
                        <p><strong>Email:</strong> {profile.get('email', '')}</p>
                        <p><strong>Joined:</strong> {profile.get('joined_date', '')}</p>
                    </div>
                </div>
                """
                
                components.append({
                    'type': 'text',
                    'title': 'Profile',
                    'content': profile_html
                })
            
            # Activity chart component
            if 'activity' in user_data:
                activity = user_data['activity']
                
                if 'daily' in activity:
                    daily_activity = activity['daily']
                    
                    components.append({
                        'type': 'chart',
                        'chart_type': 'line',
                        'title': 'Daily Activity',
                        'x_label': 'Date',
                        'y_label': 'Activity',
                        'data': {
                            'x': daily_activity.get('dates', []),
                            'y': daily_activity.get('counts', [])
                        }
                    })
            
            # Recent items component
            if 'recent_items' in user_data:
                recent_items = user_data['recent_items']
                
                items_html = "<ul style='padding-left: 20px;'>"
                for item in recent_items:
                    items_html += f"<li><strong>{item.get('title', 'Item')}</strong> - {item.get('date', '')}</li>"
                items_html += "</ul>"
                
                components.append({
                    'type': 'text',
                    'title': 'Recent Items',
                    'content': items_html
                })
            
            # Statistics component
            if 'statistics' in user_data:
                stats = user_data['statistics']
                
                if isinstance(stats, dict):
                    components.append({
                        'type': 'chart',
                        'chart_type': 'pie',
                        'title': 'Activity Distribution',
                        'data': {
                            'labels': list(stats.keys()),
                            'values': list(stats.values())
                        }
                    })
            
            # Connections graph component
            if 'connections' in user_data:
                connections = user_data['connections']
                
                if 'nodes' in connections and 'edges' in connections:
                    components.append({
                        'type': 'graph',
                        'title': 'Connections',
                        'nodes': connections['nodes'],
                        'edges': connections['edges']
                    })
            
            # Create dashboard
            return await self.create_dashboard(components, title)
            
        except Exception as e:
            logger.error(f"Error creating user dashboard: {str(e)}")
            return {'error': str(e)}
    
    async def create_analysis_dashboard(self, analysis_data: Dict[str, Any], 
                                       title: str = "Analysis Dashboard") -> Dict[str, Any]:
        """
        Create a dashboard for analysis results.
        
        Args:
            analysis_data: Analysis data dictionary
            title: Dashboard title
            
        Returns:
            Dictionary containing HTML for dashboard
        """
        logger.info("Creating analysis dashboard")
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create components for analysis dashboard
            components = []
            
            # Summary component
            if 'summary' in analysis_data:
                summary = analysis_data['summary']
                
                if isinstance(summary, str):
                    components.append({
                        'type': 'text',
                        'title': 'Summary',
                        'content': summary
                    })
                elif isinstance(summary, dict):
                    summary_html = "<ul style='padding-left: 20px;'>"
                    for key, value in summary.items():
                        summary_html += f"<li><strong>{key}:</strong> {value}</li>"
                    summary_html += "</ul>"
                    
                    components.append({
                        'type': 'text',
                        'title': 'Summary',
                        'content': summary_html
                    })
            
            # Charts component
            if 'charts' in analysis_data:
                charts = analysis_data['charts']
                
                for i, chart in enumerate(charts):
                    components.append({
                        'type': 'chart',
                        'chart_type': chart.get('type', 'line'),
                        'title': chart.get('title', f'Chart {i+1}'),
                        'x_label': chart.get('x_label', 'X'),
                        'y_label': chart.get('y_label', 'Y'),
                        'data': chart.get('data', {})
                    })
            
            # Tables component
            if 'tables' in analysis_data:
                tables = analysis_data['tables']
                
                for i, table in enumerate(tables):
                    components.append({
                        'type': 'table',
                        'title': table.get('title', f'Table {i+1}'),
                        'headers': table.get('headers', []),
                        'rows': table.get('rows', [])
                    })
            
            # Graphs component
            if 'graphs' in analysis_data:
                graphs = analysis_data['graphs']
                
                for i, graph in enumerate(graphs):
                    components.append({
                        'type': 'graph',
                        'title': graph.get('title', f'Graph {i+1}'),
                        'nodes': graph.get('nodes', []),
                        'edges': graph.get('edges', [])
                    })
            
            # Create dashboard
            return await self.create_dashboard(components, title)
            
        except Exception as e:
            logger.error(f"Error creating analysis dashboard: {str(e)}")
            return {'error': str(e)}