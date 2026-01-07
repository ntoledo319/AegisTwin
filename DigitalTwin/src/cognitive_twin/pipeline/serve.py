"""
Cognitive-Twin Omega - Service System

This module provides capabilities for serving the Cognitive-Twin Omega system
through APIs and interactive dashboards.
"""

import logging
import json
import os
import sys
import signal
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set

from cognitive_twin.core.utils import ensure_dir
from cognitive_twin.models.cognitive import CognitiveModel

# Initialize logger
logger = logging.getLogger(__name__)

class ServiceManager:
    """
    Manages the serving of Cognitive-Twin Omega through APIs and dashboards.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the service manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.exports_dir = Path(config.get('paths', {}).get('exports', 'exports'))
        
        # Ensure directories exist
        ensure_dir(self.exports_dir)
        
        # Initialize stats
        self.stats = {
            'services_started': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Initialize service processes
        self.processes = {}
    
    def start_services(self, cognitive_model: CognitiveModel, api_port: int = 8000, dashboard_port: int = 8050) -> Dict[str, Any]:
        """
        Start API and dashboard services.
        
        Args:
            cognitive_model: Cognitive model
            api_port: Port for the API server
            dashboard_port: Port for the dashboard server
            
        Returns:
            Dictionary of service information
        """
        logger.info("Starting services")
        
        results = {}
        
        # Get output configuration
        output_config = self.config.get('output', {})
        
        # Start API if enabled
        api_config = output_config.get('api', {})
        if api_config.get('enabled', False):
            try:
                api_info = self.start_api_server(cognitive_model, api_port)
                results['api'] = api_info
                self.stats['services_started'] += 1
            except Exception as e:
                logger.error(f"Error starting API server: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        # Start dashboard if enabled
        dashboard_config = output_config.get('dashboard', {})
        if dashboard_config.get('enabled', False):
            try:
                dashboard_info = self.start_dashboard_server(cognitive_model, dashboard_port)
                results['dashboard'] = dashboard_info
                self.stats['services_started'] += 1
            except Exception as e:
                logger.error(f"Error starting dashboard server: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        logger.info(f"Started {self.stats['services_started']} services with {self.stats['errors']} errors and {self.stats['warnings']} warnings")
        
        return results
    
    def start_api_server(self, cognitive_model: CognitiveModel, port: int = 8000) -> Dict[str, Any]:
        """
        Start the API server.
        
        Args:
            cognitive_model: Cognitive model
            port: Port for the API server
            
        Returns:
            Dictionary of API server information
        """
        logger.info(f"Starting API server on port {port}")
        
        # Check if API implementation exists
        api_dir = self.exports_dir / 'api'
        api_file = api_dir / 'main.py'
        
        if not api_file.exists():
            logger.warning(f"API implementation not found at {api_file}")
            logger.info("Generating API implementation")
            
            # Create API directory
            ensure_dir(api_dir)
            
            # Create API implementation
            self._create_api_implementation(api_dir, cognitive_model)
        
        # Start API server
        try:
            # Build command
            cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)]
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=str(api_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process
            self.processes['api'] = process
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise RuntimeError(f"API server failed to start: {stderr}")
            
            logger.info(f"API server started on port {port}")
            
            # Start log monitoring thread
            threading.Thread(target=self._monitor_logs, args=(process, "API"), daemon=True).start()
            
            return {
                'url': f"http://localhost:{port}",
                'docs_url': f"http://localhost:{port}/docs",
                'port': port,
                'status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Error starting API server: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            
            return {
                'port': port,
                'status': 'error',
                'error': str(e)
            }
    
    def _create_api_implementation(self, api_dir: Path, cognitive_model: CognitiveModel) -> None:
        """
        Create an API implementation.
        
        Args:
            api_dir: API directory
            cognitive_model: Cognitive model
        """
        # Create FastAPI implementation
        fastapi_code = """
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import datetime
import json
import os
import sys
import pickle

# Add parent directory to path to import cognitive model
sys.path.append('..')

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

# Create FastAPI app
app = FastAPI(
    title="Cognitive-Twin Omega API",
    description="API for interacting with the Cognitive-Twin Omega personal digital twin",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load cognitive model
cognitive_model = None

try:
    # Try to load the model from the models directory
    model_path = "../models/cognitive"
    
    # Check if directory exists
    if os.path.exists(model_path):
        # Import the cognitive model class
        try:
            from cognitive_twin.models.cognitive import CognitiveModel
            cognitive_model = CognitiveModel.load(model_path)
            print(f"Loaded cognitive model from {model_path}")
        except Exception as e:
            print(f"Error loading cognitive model: {str(e)}")
    else:
        print(f"Model directory {model_path} not found")
except Exception as e:
    print(f"Error loading cognitive model: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to Cognitive-Twin Omega API", "model_loaded": cognitive_model is not None}

@app.post("/query", response_model=QueryResponse)
def query_model(request: QueryRequest):
    if cognitive_model is None:
        return {"response": f"Cognitive model not loaded. This is a simulated response to: {request.query}"}
    
    try:
        response = cognitive_model.generate_response(request.query)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error generating response: {str(e)}"}

@app.post("/simulate_response", response_model=SimulateResponse)
def simulate_response(request: SimulateRequest):
    if cognitive_model is None:
        return {"response": f"Cognitive model not loaded. This is a simulated response to: {request.message}", "confidence": 0.5}
    
    try:
        response = cognitive_model.generate_response(request.message, request.context)
        return {"response": response, "confidence": 0.85}
    except Exception as e:
        return {"response": f"Error simulating response: {str(e)}", "confidence": 0.0}

@app.get("/relationship_info")
def get_relationship_info(person: Optional[str] = None):
    if cognitive_model is None:
        return {"relationships": {"example_person": {"role": "friend", "importance": 8}}}
    
    try:
        if person:
            relationships = {person: cognitive_model.get_relationship_network().get(person, {})}
        else:
            relationships = cognitive_model.get_relationship_network()
        return {"relationships": relationships}
    except Exception as e:
        return {"error": f"Error getting relationship info: {str(e)}"}

@app.get("/topic_analysis")
def get_topic_analysis():
    if cognitive_model is None:
        return {"topics": {"example_topic": {"frequency": 0.5, "description": "Example topic"}}}
    
    try:
        communication = cognitive_model.get_communication_analysis()
        topics = communication.get('topics', {})
        return {"topics": topics}
    except Exception as e:
        return {"error": f"Error getting topic analysis: {str(e)}"}

@app.post("/temporal_query", response_model=QueryResponse)
def temporal_query(request: TemporalQueryRequest):
    if cognitive_model is None:
        time_range = ""
        if request.time_period:
            if request.time_period.start:
                time_range += f" from {request.time_period.start.isoformat()}"
            if request.time_period.end:
                time_range += f" to {request.time_period.end.isoformat()}"
        return {"response": f"Cognitive model not loaded. This is a simulated response to: {request.query}{time_range}"}
    
    try:
        # In a real implementation, you would use the time period to filter the data
        response = cognitive_model.generate_response(request.query)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error generating response: {str(e)}"}

@app.get("/personality")
def get_personality():
    if cognitive_model is None:
        return {"personality": {"example_trait": {"score": 0.5, "description": "Example trait"}}}
    
    try:
        personality = cognitive_model.get_personality_details()
        return {"personality": personality}
    except Exception as e:
        return {"error": f"Error getting personality: {str(e)}"}

@app.get("/communication_style")
def get_communication_style():
    if cognitive_model is None:
        return {"communication_style": {"example_dimension": {"score": 0.5, "description": "Example dimension"}}}
    
    try:
        communication_style = cognitive_model.get_communication_style()
        return {"communication_style": communication_style}
    except Exception as e:
        return {"error": f"Error getting communication style: {str(e)}"}

@app.get("/values")
def get_values():
    if cognitive_model is None:
        return {"values": {"example_value": {"strength": 0.5, "description": "Example value"}}}
    
    try:
        values = cognitive_model.get_core_values()
        return {"values": values}
    except Exception as e:
        return {"error": f"Error getting values: {str(e)}"}

@app.get("/temporal_evolution")
def get_temporal_evolution():
    if cognitive_model is None:
        return {"temporal_evolution": {"example_era": {"start_date": "2020-01-01", "end_date": "2020-12-31", "description": "Example era"}}}
    
    try:
        temporal_evolution = cognitive_model.get_temporal_evolution()
        return {"temporal_evolution": temporal_evolution}
    except Exception as e:
        return {"error": f"Error getting temporal evolution: {str(e)}"}

@app.get("/cognitive_framework")
def get_cognitive_framework():
    if cognitive_model is None:
        return {"cognitive_framework": {"example_pattern": {"description": "Example pattern"}}}
    
    try:
        cognitive_framework = cognitive_model.get_cognitive_framework()
        return {"cognitive_framework": cognitive_framework}
    except Exception as e:
        return {"error": f"Error getting cognitive framework: {str(e)}"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": cognitive_model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        
        # Save FastAPI implementation
        api_file = api_dir / 'main.py'
        with open(api_file, 'w', encoding='utf-8') as f:
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
    
    def start_dashboard_server(self, cognitive_model: CognitiveModel, port: int = 8050) -> Dict[str, Any]:
        """
        Start the dashboard server.
        
        Args:
            cognitive_model: Cognitive model
            port: Port for the dashboard server
            
        Returns:
            Dictionary of dashboard server information
        """
        logger.info(f"Starting dashboard server on port {port}")
        
        # Check if dashboard implementation exists
        dashboard_dir = self.exports_dir / 'dashboard'
        dashboard_file = dashboard_dir / 'app.py'
        
        if not dashboard_file.exists():
            logger.warning(f"Dashboard implementation not found at {dashboard_file}")
            logger.info("Generating dashboard implementation")
            
            # Create dashboard directory
            ensure_dir(dashboard_dir)
            
            # Create dashboard implementation
            self._create_dashboard_implementation(dashboard_dir, cognitive_model)
        
        # Start dashboard server
        try:
            # Build command
            cmd = [sys.executable, "app.py", str(port)]
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=str(dashboard_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process
            self.processes['dashboard'] = process
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise RuntimeError(f"Dashboard server failed to start: {stderr}")
            
            logger.info(f"Dashboard server started on port {port}")
            
            # Start log monitoring thread
            threading.Thread(target=self._monitor_logs, args=(process, "Dashboard"), daemon=True).start()
            
            return {
                'url': f"http://localhost:{port}",
                'port': port,
                'status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Error starting dashboard server: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            
            return {
                'port': port,
                'status': 'error',
                'error': str(e)
            }
    
    def _create_dashboard_implementation(self, dashboard_dir: Path, cognitive_model: CognitiveModel) -> None:
        """
        Create a dashboard implementation.
        
        Args:
            dashboard_dir: Dashboard directory
            cognitive_model: Cognitive model
        """
        # Create Dash implementation
        dash_code = """
import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path to import cognitive model
sys.path.append('..')

# Check if API is running
API_URL = "http://localhost:8000"

def check_api():
    try:
        response = requests.get(f"{API_URL}/health")
        return response.status_code == 200
    except:
        return False

# Initialize Dash app
app = dash.Dash(__name__, title="Cognitive-Twin Omega Dashboard")

# Define app layout
app.layout = html.Div([
    html.Div([
        html.H1("Cognitive-Twin Omega Dashboard"),
        html.P("Personal Digital Twin Insights"),
        html.Div(id="api-status")
    ], className="header"),
    
    html.Div([
        html.Div([
            html.Div([
                html.H2("Personality Profile"),
                dcc.Graph(id="personality-radar")
            ], className="card"),
            
            html.Div([
                html.H2("Communication Style"),
                dcc.Graph(id="communication-radar")
            ], className="card"),
            
            html.Div([
                html.H2("Value System"),
                dcc.Graph(id="value-system")
            ], className="card"),
            
            html.Div([
                html.H2("Topic Distribution"),
                dcc.Graph(id="topic-distribution")
            ], className="card"),
            
            html.Div([
                html.H2("Relationship Network"),
                dcc.Graph(id="relationship-network")
            ], className="card full-width"),
            
            html.Div([
                html.H2("Temporal Evolution"),
                dcc.Graph(id="temporal-evolution")
            ], className="card full-width"),
            
            html.Div([
                html.H2("Digital Twin Query"),
                dcc.Textarea(
                    id="query-input",
                    placeholder="Ask your digital twin a question...",
                    style={"width": "100%", "height": 100}
                ),
                html.Button("Submit", id="query-button", n_clicks=0),
                html.Div(id="query-output", className="query-output")
            ], className="card full-width")
        ], className="grid")
    ], className="container"),
    
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

# Define callbacks
@callback(
    Output("api-status", "children"),
    Input("interval-component", "n_intervals")
)
def update_api_status(n):
    if check_api():
        return html.Span("API Connected", style={"color": "green"})
    else:
        return html.Span("API Disconnected", style={"color": "red"})

@callback(
    Output("personality-radar", "figure"),
    Input("interval-component", "n_intervals")
)
def update_personality_radar(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/personality")
            data = response.json()
            
            if 'personality' in data and 'big_five' in data['personality']:
                big_five = data['personality']['big_five']
                traits = list(big_five.keys())
                scores = [big_five[trait]['score'] for trait in traits]
                
                # Create radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=traits,
                    fill='toself',
                    name='Personality'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )
                    ),
                    title="Big Five Personality Traits"
                )
                
                return fig
        
        # Fallback to placeholder
        return create_placeholder_personality_radar()
    except:
        return create_placeholder_personality_radar()

def create_placeholder_personality_radar():
    traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    scores = [7.5, 6.8, 5.2, 7.9, 4.3]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=traits,
        fill='toself',
        name='Personality'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        title="Big Five Personality Traits (Placeholder)"
    )
    
    return fig

@callback(
    Output("communication-radar", "figure"),
    Input("interval-component", "n_intervals")
)
def update_communication_radar(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/communication_style")
            data = response.json()
            
            if 'communication_style' in data:
                style = data['communication_style']
                dimensions = []
                scores = []
                
                for dim, details in style.items():
                    if isinstance(details, dict) and 'score' in details:
                        dimensions.append(dim)
                        scores.append(details['score'])
                
                if dimensions and scores:
                    # Create radar chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatterpolar(
                        r=scores,
                        theta=dimensions,
                        fill='toself',
                        name='Communication Style'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )
                        ),
                        title="Communication Style Dimensions"
                    )
                    
                    return fig
        
        # Fallback to placeholder
        return create_placeholder_communication_radar()
    except:
        return create_placeholder_communication_radar()

def create_placeholder_communication_radar():
    dimensions = ["Formality", "Directness", "Emotionality", "Verbosity", "Humor Usage"]
    scores = [5.5, 7.2, 6.8, 6.5, 7.8]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=dimensions,
        fill='toself',
        name='Communication Style'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        title="Communication Style Dimensions (Placeholder)"
    )
    
    return fig

@callback(
    Output("value-system", "figure"),
    Input("interval-component", "n_intervals")
)
def update_value_system(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/values")
            data = response.json()
            
            if 'values' in data:
                values = data['values']
                value_names = []
                value_strengths = []
                
                for value, details in values.items():
                    if isinstance(details, dict) and 'strength' in details:
                        value_names.append(value)
                        value_strengths.append(details['strength'])
                
                if value_names and value_strengths:
                    # Create bar chart
                    fig = px.bar(
                        x=value_names,
                        y=value_strengths,
                        title="Core Values",
                        labels={"x": "Value", "y": "Strength"},
                        range_y=[0, 10]
                    )
                    
                    return fig
        
        # Fallback to placeholder
        return create_placeholder_value_system()
    except:
        return create_placeholder_value_system()

def create_placeholder_value_system():
    value_names = ["Authenticity", "Growth", "Connection", "Autonomy", "Impact"]
    value_strengths = [8.7, 8.2, 7.9, 7.5, 7.2]
    
    fig = px.bar(
        x=value_names,
        y=value_strengths,
        title="Core Values (Placeholder)",
        labels={"x": "Value", "y": "Strength"},
        range_y=[0, 10]
    )
    
    return fig

@callback(
    Output("topic-distribution", "figure"),
    Input("interval-component", "n_intervals")
)
def update_topic_distribution(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/topic_analysis")
            data = response.json()
            
            if 'topics' in data:
                topics = data['topics']
                topic_names = []
                topic_freqs = []
                
                for topic, details in topics.items():
                    if isinstance(details, dict) and 'frequency' in details:
                        topic_names.append(topic)
                        topic_freqs.append(details['frequency'])
                
                if topic_names and topic_freqs:
                    # Sort by frequency
                    sorted_indices = np.argsort(topic_freqs)[::-1]
                    topic_names = [topic_names[i] for i in sorted_indices[:10]]
                    topic_freqs = [topic_freqs[i] for i in sorted_indices[:10]]
                    
                    # Create horizontal bar chart
                    fig = px.bar(
                        y=topic_names,
                        x=topic_freqs,
                        title="Topic Distribution",
                        labels={"y": "Topic", "x": "Frequency"},
                        orientation='h'
                    )
                    
                    return fig
        
        # Fallback to placeholder
        return create_placeholder_topic_distribution()
    except:
        return create_placeholder_topic_distribution()

def create_placeholder_topic_distribution():
    topic_names = ["Personal Growth", "Relationships", "Ideas & Concepts", "Creative Pursuits", "Practical Planning",
                  "Current Events", "Humor & Entertainment", "Emotional Support"]
    topic_freqs = [0.18, 0.16, 0.15, 0.12, 0.10, 0.08, 0.12, 0.09]
    
    fig = px.bar(
        y=topic_names,
        x=topic_freqs,
        title="Topic Distribution (Placeholder)",
        labels={"y": "Topic", "x": "Frequency"},
        orientation='h'
    )
    
    return fig

@callback(
    Output("relationship-network", "figure"),
    Input("interval-component", "n_intervals")
)
def update_relationship_network(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/relationship_info")
            data = response.json()
            
            if 'relationships' in data:
                relationships = data['relationships']
                
                # Create network visualization
                nodes = []
                edges = []
                
                # Add subject node
                nodes.append({
                    'id': 'You',
                    'label': 'You',
                    'group': 'subject',
                    'size': 20
                })
                
                # Add relationship nodes and edges
                for person, details in relationships.items():
                    # Add node
                    role = details.get('role', 'unknown')
                    importance = details.get('importance', 5)
                    
                    nodes.append({
                        'id': person,
                        'label': person,
                        'group': role,
                        'size': 10 + importance
                    })
                    
                    # Add edge
                    edges.append({
                        'from': 'You',
                        'to': person,
                        'value': importance
                    })
                
                # Create figure
                fig = go.Figure()
                
                # Create a network layout
                G = nx.Graph()
                for node in nodes:
                    G.add_node(node['id'])
                for edge in edges:
                    G.add_edge(edge['from'], edge['to'])
                
                pos = nx.spring_layout(G)
                
                # Add edges
                edge_x = []
                edge_y = []
                for edge in edges:
                    x0, y0 = pos[edge['from']]
                    x1, y1 = pos[edge['to']]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))
                
                # Add nodes
                node_x = []
                node_y = []
                node_text = []
                node_size = []
                node_color = []
                
                color_map = {
                    'subject': 'red',
                    'family': 'blue',
                    'mentee': 'green',
                    'romantic_candidate': 'pink',
                    'anchors_platonic': 'purple',
                    'unknown': 'gray'
                }
                
                for node in nodes:
                    x, y = pos[node['id']]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node['label'])
                    node_size.append(node['size'])
                    node_color.append(color_map.get(node['group'], 'gray'))
                
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers',
                    hoverinfo='text',
                    text=node_text,
                    marker=dict(
                        showscale=False,
                        color=node_color,
                        size=node_size,
                        line=dict(width=2, color='white')
                    )
                ))
                
                fig.update_layout(
                    title="Relationship Network",
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                return fig
        
        # Fallback to placeholder
        return create_placeholder_relationship_network()
    except Exception as e:
        print(f"Error in relationship network: {str(e)}")
        return create_placeholder_relationship_network()

def create_placeholder_relationship_network():
    # Create a simple placeholder network
    fig = go.Figure()
    
    # Create a simple star network
    center_x, center_y = 0, 0
    points = 8
    radius = 1
    
    # Add edges
    edge_x = []
    edge_y = []
    for i in range(points):
        angle = 2 * np.pi * i / points
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        edge_x.extend([center_x, x, None])
        edge_y.extend([center_y, y, None])
    
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    ))
    
    # Add nodes
    node_x = [center_x]
    node_y = [center_y]
    node_text = ["You"]
    node_size = [20]
    node_color = ["red"]
    
    # Add peripheral nodes
    for i in range(points):
        angle = 2 * np.pi * i / points
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"Person {i+1}")
        node_size.append(10)
        node_color.append("blue")
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=2, color='white')
        )
    ))
    
    fig.update_layout(
        title="Relationship Network (Placeholder)",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    return fig

@callback(
    Output("temporal-evolution", "figure"),
    Input("interval-component", "n_intervals")
)
def update_temporal_evolution(n):
    try:
        if check_api():
            response = requests.get(f"{API_URL}/temporal_evolution")
            data = response.json()
            
            if 'temporal_evolution' in data and 'eras' in data['temporal_evolution']:
                eras = data['temporal_evolution']['eras']
                
                # Create figure
                fig = go.Figure()
                
                # Add eras as horizontal bars
                y_pos = 0
                for era_name, era_data in eras.items():
                    # Parse dates
                    start_date = pd.to_datetime(era_data['start_date'])
                    end_date = pd.to_datetime(era_data['end_date'])
                    
                    # Add era
                    fig.add_trace(go.Bar(
                        x=[(end_date - start_date).days],
                        y=[era_name],
                        orientation='h',
                        base=[start_date],
                        width=0.8,
                        text=[era_name],
                        hoverinfo='text',
                        hovertext=[era_data['description']]
                    ))
                
                fig.update_layout(
                    title="Life Eras Timeline",
                    xaxis_title="Time",
                    yaxis_title="Era",
                    barmode='stack'
                )
                
                return fig
        
        # Fallback to placeholder
        return create_placeholder_temporal_evolution()
    except:
        return create_placeholder_temporal_evolution()

def create_placeholder_temporal_evolution():
    # Create a simple placeholder timeline
    eras = [
        {"name": "College Years", "start": "2019-09-01", "end": "2023-05-15", "description": "Period of academic focus and social exploration"},
        {"name": "Post-College Transition", "start": "2023-05-16", "end": "2023-08-31", "description": "Period of adjustment and career exploration"},
        {"name": "Graduate School", "start": "2023-09-01", "end": "2025-09-26", "description": "Period of specialized focus and professional development"}
    ]
    
    fig = go.Figure()
    
    for era in eras:
        start_date = pd.to_datetime(era['start'])
        end_date = pd.to_datetime(era['end'])
        
        fig.add_trace(go.Bar(
            x=[(end_date - start_date).days],
            y=[era['name']],
            orientation='h',
            base=[start_date],
            width=0.8,
            text=[era['name']],
            hoverinfo='text',
            hovertext=[era['description']]
        ))
    
    fig.update_layout(
        title="Life Eras Timeline (Placeholder)",
        xaxis_title="Time",
        yaxis_title="Era",
        barmode='stack'
    )
    
    return fig

@callback(
    Output("query-output", "children"),
    Input("query-button", "n_clicks"),
    Input("query-input", "value")
)
def update_query_output(n_clicks, query):
    if n_clicks > 0 and query:
        try:
            if check_api():
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": query}
                )
                data = response.json()
                
                if 'response' in data:
                    return html.Div([
                        html.P(f"Q: {query}", style={"font-weight": "bold"}),
                        html.P(f"A: {data['response']}")
                    ])
            
            # Fallback to placeholder
            return html.Div([
                html.P(f"Q: {query}", style={"font-weight": "bold"}),
                html.P(f"A: This is a placeholder response to your query. The API is not available.")
            ])
        except:
            return html.Div([
                html.P(f"Q: {query}", style={"font-weight": "bold"}),
                html.P("Error processing query. Please try again.")
            ])
    
    return html.Div()

# Add CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
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
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
                grid-gap: 20px;
            }
            .full-width {
                grid-column: 1 / -1;
            }
            .query-output {
                margin-top: 20px;
                padding: 10px;
                border-left: 4px solid #333;
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == "__main__":
    port = 8050
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    app.run_server(debug=True, host="0.0.0.0", port=port)
"""
        
        # Save Dash implementation
        dashboard_file = dashboard_dir / 'app.py'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(dash_code.strip())
        
        # Create requirements.txt
        requirements = """
dash>=2.14.2
plotly>=5.18.0
pandas>=2.2.0
numpy>=1.26.0
requests>=2.31.0
networkx>=3.2.1
"""
        
        requirements_path = dashboard_dir / 'requirements.txt'
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements.strip())
    
    def _monitor_logs(self, process: subprocess.Popen, name: str) -> None:
        """
        Monitor logs from a process.
        
        Args:
            process: Process to monitor
            name: Name of the process
        """
        while process.poll() is None:
            stdout_line = process.stdout.readline()
            if stdout_line:
                logger.info(f"{name} stdout: {stdout_line.strip()}")
            
            stderr_line = process.stderr.readline()
            if stderr_line:
                logger.error(f"{name} stderr: {stderr_line.strip()}")
        
        # Process has terminated
        returncode = process.poll()
        logger.info(f"{name} process terminated with return code {returncode}")
    
    def stop_services(self) -> None:
        """Stop all running services."""
        logger.info("Stopping services")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"Stopping {name} service")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} service did not terminate gracefully, killing")
                    process.kill()
        
        self.processes = {}


def start_services(config: Dict[str, Any], cognitive_model: CognitiveModel, api_port: int = 8000, dashboard_port: int = 8050) -> Dict[str, Any]:
    """
    Start API and dashboard services.
    
    Args:
        config: Configuration dictionary
        cognitive_model: Cognitive model
        api_port: Port for the API server
        dashboard_port: Port for the dashboard server
        
    Returns:
        Dictionary of service information
    """
    service_manager = ServiceManager(config)
    return service_manager.start_services(cognitive_model, api_port, dashboard_port)

def stop_services(config: Dict[str, Any]) -> None:
    """
    Stop all running services.
    
    Args:
        config: Configuration dictionary
    """
    service_manager = ServiceManager(config)
    service_manager.stop_services()