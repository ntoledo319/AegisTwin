"""
Web Interface for CogniLink

This module provides a simple web interface for interacting with CogniLink.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import urllib.parse
import tempfile
import shutil

from cognilink.core.config import Config
from cognilink.pipeline.connectors import BaseConnector
from cognilink.interface.reports import ReportGenerator

logger = logging.getLogger(__name__)

class CogniLinkWebHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for CogniLink web interface.
    """
    
    def __init__(self, *args, web_interface=None, **kwargs):
        self.web_interface = web_interface
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        # Parse URL and query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Serve static files
        if path.startswith('/static/'):
            return super().do_GET()
        
        # Handle API requests
        if path.startswith('/api/'):
            return self.handle_api_request(path)
        
        # Serve main page or other routes
        if path == '/' or path == '/index.html':
            self.serve_main_page()
        elif path == '/import':
            self.serve_import_page()
        elif path == '/analyze':
            self.serve_analyze_page()
        elif path == '/reports':
            self.serve_reports_page()
        elif path == '/settings':
            self.serve_settings_page()
        else:
            # Default to main page
            self.serve_main_page()
    
    def do_POST(self):
        """Handle POST requests."""
        # Parse URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Get content length
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse JSON data
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON data")
            return
        
        # Handle different POST endpoints
        if path == '/api/import':
            self.handle_import_request(data)
        elif path == '/api/analyze':
            self.handle_analyze_request(data)
        elif path == '/api/report':
            self.handle_report_request(data)
        elif path == '/api/settings':
            self.handle_settings_request(data)
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_api_request(self, path):
        """Handle API GET requests."""
        if path == '/api/connectors':
            self.send_connectors_list()
        elif path == '/api/data':
            self.send_data_list()
        elif path == '/api/analyses':
            self.send_analyses_list()
        elif path == '/api/reports':
            self.send_reports_list()
        elif path == '/api/settings':
            self.send_settings()
        else:
            self.send_error(404, "API endpoint not found")
    
    def send_connectors_list(self):
        """Send list of available connectors."""
        connectors = self.web_interface.get_connectors()
        self.send_json_response(connectors)
    
    def send_data_list(self):
        """Send list of imported data files."""
        data_files = self.web_interface.get_data_files()
        self.send_json_response(data_files)
    
    def send_analyses_list(self):
        """Send list of analysis results."""
        analyses = self.web_interface.get_analyses()
        self.send_json_response(analyses)
    
    def send_reports_list(self):
        """Send list of generated reports."""
        reports = self.web_interface.get_reports()
        self.send_json_response(reports)
    
    def send_settings(self):
        """Send current settings."""
        settings = self.web_interface.get_settings()
        self.send_json_response(settings)
    
    def handle_import_request(self, data):
        """Handle import data request."""
        try:
            result = self.web_interface.import_data(
                source=data.get('source'),
                path=data.get('path'),
                data_types=data.get('data_types')
            )
            self.send_json_response({"success": True, "result": result})
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            self.send_json_response({"success": False, "error": str(e)})
    
    def handle_analyze_request(self, data):
        """Handle analyze data request."""
        try:
            result = self.web_interface.analyze_data(
                analysis_type=data.get('type', 'all')
            )
            self.send_json_response({"success": True, "result": result})
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            self.send_json_response({"success": False, "error": str(e)})
    
    def handle_report_request(self, data):
        """Handle generate report request."""
        try:
            result = self.web_interface.generate_report(
                format_type=data.get('format', 'html'),
                analysis_id=data.get('analysis_id')
            )
            self.send_json_response({"success": True, "result": result})
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            self.send_json_response({"success": False, "error": str(e)})
    
    def handle_settings_request(self, data):
        """Handle settings update request."""
        try:
            result = self.web_interface.update_settings(data)
            self.send_json_response({"success": True, "result": result})
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            self.send_json_response({"success": False, "error": str(e)})
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def serve_main_page(self):
        """Serve the main page."""
        content = self.web_interface.get_html_template('index.html')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_import_page(self):
        """Serve the import page."""
        content = self.web_interface.get_html_template('import.html')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_analyze_page(self):
        """Serve the analyze page."""
        content = self.web_interface.get_html_template('analyze.html')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_reports_page(self):
        """Serve the reports page."""
        content = self.web_interface.get_html_template('reports.html')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_settings_page(self):
        """Serve the settings page."""
        content = self.web_interface.get_html_template('settings.html')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override log message to use our logger."""
        logger.debug(f"{self.client_address[0]} - {format % args}")


class WebInterface:
    """
    Web interface for CogniLink.
    
    This class provides a web interface for interacting with CogniLink,
    including importing data, analyzing data, and generating reports.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the web interface.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.connectors = {}
        self.server = None
        self.server_thread = None
        self.web_dir = os.path.join(os.path.dirname(__file__), 'web')
        
        # Create temporary directory for web files if needed
        if not os.path.exists(self.web_dir):
            os.makedirs(self.web_dir, exist_ok=True)
        
        # Load connectors
        self._load_connectors()
        
        # Create HTML templates if they don't exist
        self._ensure_templates_exist()
    
    def _load_connectors(self):
        """Load all available connectors."""
        # Import the connectors module
        from cognilink.pipeline import connectors
        import inspect
        
        # Get all connector classes
        for name in dir(connectors):
            obj = getattr(connectors, name)
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseConnector) and 
                obj != BaseConnector):
                # Add connector to the dictionary
                connector_name = name.replace('Connector', '').lower()
                self.connectors[connector_name] = obj
    
    def _ensure_templates_exist(self):
        """Ensure HTML templates exist."""
        templates = [
            'index.html',
            'import.html',
            'analyze.html',
            'reports.html',
            'settings.html',
            'styles.css',
            'scripts.js'
        ]
        
        for template in templates:
            template_path = os.path.join(self.web_dir, template)
            if not os.path.exists(template_path):
                self._create_default_template(template)
    
    def _create_default_template(self, template_name):
        """Create a default HTML template."""
        template_path = os.path.join(self.web_dir, template_name)
        
        if template_name == 'index.html':
            content = self._get_index_html()
        elif template_name == 'import.html':
            content = self._get_import_html()
        elif template_name == 'analyze.html':
            content = self._get_analyze_html()
        elif template_name == 'reports.html':
            content = self._get_reports_html()
        elif template_name == 'settings.html':
            content = self._get_settings_html()
        elif template_name == 'styles.css':
            content = self._get_styles_css()
        elif template_name == 'scripts.js':
            content = self._get_scripts_js()
        else:
            content = "<html><body><h1>CogniLink</h1></body></html>"
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_html_template(self, template_name):
        """
        Get HTML template content.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template content
        """
        template_path = os.path.join(self.web_dir, template_name)
        
        if not os.path.exists(template_path):
            self._create_default_template(template_name)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def start_server(self, port=8080, open_browser=True):
        """
        Start the web server.
        
        Args:
            port: Port to listen on
            open_browser: Whether to open a browser window
            
        Returns:
            Server URL
        """
        if self.server:
            logger.warning("Server already running")
            return f"http://localhost:{self.server.server_port}"
        
        # Create handler with reference to this instance
        handler = lambda *args, **kwargs: CogniLinkWebHandler(*args, web_interface=self, **kwargs)
        
        # Try to start server on the specified port
        try:
            self.server = socketserver.TCPServer(("", port), handler)
            server_port = port
        except OSError:
            # If port is in use, try a random port
            self.server = socketserver.TCPServer(("", 0), handler)
            server_port = self.server.server_port
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        server_url = f"http://localhost:{server_port}"
        logger.info(f"Server started at {server_url}")
        
        # Open browser if requested
        if open_browser:
            webbrowser.open(server_url)
        
        return server_url
    
    def stop_server(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.server_thread = None
            logger.info("Server stopped")
    
    def get_connectors(self):
        """
        Get list of available connectors.
        
        Returns:
            List of connector information
        """
        return [
            {
                "id": name,
                "name": name.capitalize(),
                "description": connector.__doc__.split('\n')[0] if connector.__doc__ else ""
            }
            for name, connector in self.connectors.items()
        ]
    
    def get_data_files(self):
        """
        Get list of imported data files.
        
        Returns:
            List of data file information
        """
        data_dir = self.config.get('paths', 'data_dir')
        data_files = []
        
        if os.path.exists(data_dir):
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if file.startswith('import_') and file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, data_dir)
                        source = rel_path if rel_path != '.' else 'unknown'
                        
                        # Get file stats
                        stats = os.stat(file_path)
                        size = stats.st_size
                        modified = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                        
                        # Get item count
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                item_count = len(data)
                        except:
                            item_count = 0
                        
                        data_files.append({
                            "id": file,
                            "name": file,
                            "source": source,
                            "path": file_path,
                            "size": size,
                            "modified": modified,
                            "item_count": item_count
                        })
        
        return data_files
    
    def get_analyses(self):
        """
        Get list of analysis results.
        
        Returns:
            List of analysis information
        """
        results_dir = self.config.get('paths', 'results_dir')
        analyses = []
        
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.startswith('analysis_') and file.endswith('.json'):
                    file_path = os.path.join(results_dir, file)
                    
                    # Get file stats
                    stats = os.stat(file_path)
                    size = stats.st_size
                    modified = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                    
                    # Get analysis types
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            analysis_types = list(data.keys())
                    except:
                        analysis_types = []
                    
                    analyses.append({
                        "id": file,
                        "name": file,
                        "path": file_path,
                        "size": size,
                        "modified": modified,
                        "types": analysis_types
                    })
        
        return analyses
    
    def get_reports(self):
        """
        Get list of generated reports.
        
        Returns:
            List of report information
        """
        reports_dir = self.config.get('paths', 'reports_dir')
        reports = []
        
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.startswith('report_'):
                    file_path = os.path.join(reports_dir, file)
                    
                    # Get file stats
                    stats = os.stat(file_path)
                    size = stats.st_size
                    modified = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                    
                    # Determine format
                    if file.endswith('.html'):
                        format_type = 'html'
                    elif file.endswith('.md'):
                        format_type = 'markdown'
                    elif file.endswith('.txt'):
                        format_type = 'text'
                    else:
                        format_type = 'unknown'
                    
                    reports.append({
                        "id": file,
                        "name": file,
                        "path": file_path,
                        "size": size,
                        "modified": modified,
                        "format": format_type
                    })
        
        return reports
    
    def get_settings(self):
        """
        Get current settings.
        
        Returns:
            Dictionary of settings
        """
        return {
            "paths": {
                "data_dir": self.config.get('paths', 'data_dir'),
                "results_dir": self.config.get('paths', 'results_dir'),
                "reports_dir": self.config.get('paths', 'reports_dir')
            },
            "connectors": self.config.get_section('connectors'),
            "processors": self.config.get_section('processors'),
            "analysis": self.config.get_section('analysis'),
            "interface": self.config.get_section('interface')
        }
    
    def import_data(self, source, path, data_types=None):
        """
        Import data from a source.
        
        Args:
            source: Source type
            path: Path to the data file or directory
            data_types: Specific data types to import
            
        Returns:
            Import result information
        """
        # Get the connector class
        connector_class = self.connectors.get(source)
        if not connector_class:
            raise ValueError(f"Unknown source type: {source}")
        
        # Create connector instance
        connector_config = self.config.get_connector_config(source)
        connector = connector_class(connector_config)
        
        # Extract data
        start_time = datetime.datetime.now()
        data_items = list(connector.extract_from_file(path, data_types))
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save imported data
        data_dir = os.path.join(self.config.get('paths', 'data_dir'), source)
        os.makedirs(data_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(data_dir, f"import_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_items, f, indent=2)
        
        # Calculate item type breakdown
        item_types = {}
        for item in data_items:
            item_type = item.get('type', 'unknown')
            if item_type not in item_types:
                item_types[item_type] = 0
            item_types[item_type] += 1
        
        return {
            "file": output_file,
            "item_count": len(data_items),
            "duration": duration,
            "item_types": item_types
        }
    
    def analyze_data(self, analysis_type='all'):
        """
        Analyze imported data.
        
        Args:
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result information
        """
        # Determine which analyses to run
        analyses = []
        if analysis_type == 'all' or analysis_type == 'patterns':
            analyses.append('patterns')
        if analysis_type == 'all' or analysis_type == 'relationships':
            analyses.append('relationships')
        if analysis_type == 'all' or analysis_type == 'topics':
            analyses.append('topics')
        
        # Import analysis modules
        from cognilink.analysis.patterns import CommunicationPatternAnalyzer
        from cognilink.analysis.relationships import RelationshipAnalyzer
        from cognilink.analysis.topics import TopicAnalyzer
        
        # Load data
        data_dir = self.config.get('paths', 'data_dir')
        all_data = []
        
        # Find all data files
        data_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.startswith('import_') and file.endswith('.json'):
                    data_files.append(os.path.join(root, file))
        
        if not data_files:
            raise ValueError("No imported data found. Please import data first.")
        
        # Load data from files
        for data_file in data_files:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.extend(data)
            except Exception as e:
                logger.warning(f"Could not load data from {data_file}: {str(e)}")
        
        # Run analyses
        results = {}
        start_time = datetime.datetime.now()
        
        for analysis_type in analyses:
            if analysis_type == 'patterns':
                analyzer = CommunicationPatternAnalyzer(self.config.get_analysis_config('patterns'))
                results['patterns'] = analyzer.analyze(all_data)
            elif analysis_type == 'relationships':
                analyzer = RelationshipAnalyzer(self.config.get_analysis_config('relationships'))
                results['relationships'] = analyzer.analyze(all_data)
            elif analysis_type == 'topics':
                analyzer = TopicAnalyzer(self.config.get_analysis_config('topics'))
                results['topics'] = analyzer.analyze(all_data)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save analysis results
        results_dir = self.config.get('paths', 'results_dir')
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(results_dir, f"analysis_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        return {
            "file": output_file,
            "analyses": list(results.keys()),
            "duration": duration,
            "data_items": len(all_data),
            "data_files": len(data_files)
        }
    
    def generate_report(self, format_type='html', analysis_id=None):
        """
        Generate a report from analysis results.
        
        Args:
            format_type: Format of the report
            analysis_id: ID of the analysis to use
            
        Returns:
            Report information
        """
        # Load analysis results
        results_dir = self.config.get('paths', 'results_dir')
        
        if analysis_id:
            # Use specified analysis
            analysis_path = os.path.join(results_dir, analysis_id)
            if not os.path.exists(analysis_path):
                raise ValueError(f"Analysis file not found: {analysis_id}")
        else:
            # Find the most recent analysis file
            analysis_files = []
            for file in os.listdir(results_dir):
                if file.startswith('analysis_') and file.endswith('.json'):
                    analysis_files.append(os.path.join(results_dir, file))
            
            if not analysis_files:
                raise ValueError("No analysis results found. Please run analysis first.")
            
            # Sort by modification time (newest first)
            analysis_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            analysis_path = analysis_files[0]
        
        # Load analysis results
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        # Create report generator
        report_config = self.config.get_interface_config('reports')
        report_generator = ReportGenerator(report_config)
        
        # Set output directory
        output_dir = self.config.get('paths', 'reports_dir')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate report
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f"report_{timestamp}.{format_type}")
        
        start_time = datetime.datetime.now()
        report_generator.generate_report(analysis_results, format_type, report_file)
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "file": report_file,
            "format": format_type,
            "duration": duration,
            "analysis": os.path.basename(analysis_path)
        }
    
    def update_settings(self, settings):
        """
        Update settings.
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Updated settings
        """
        # Update paths
        if 'paths' in settings:
            for key, value in settings['paths'].items():
                self.config.set('paths', key, value)
        
        # Update connector settings
        if 'connectors' in settings:
            for connector, config in settings['connectors'].items():
                for key, value in config.items():
                    self.config.set('connectors', f"{connector}.{key}", value)
        
        # Update processor settings
        if 'processors' in settings:
            for processor, config in settings['processors'].items():
                for key, value in config.items():
                    self.config.set('processors', f"{processor}.{key}", value)
        
        # Update analysis settings
        if 'analysis' in settings:
            for analysis, config in settings['analysis'].items():
                for key, value in config.items():
                    self.config.set('analysis', f"{analysis}.{key}", value)
        
        # Update interface settings
        if 'interface' in settings:
            for interface, config in settings['interface'].items():
                for key, value in config.items():
                    self.config.set('interface', f"{interface}.{key}", value)
        
        # Save settings
        self.config.save()
        
        return self.get_settings()
    
    def _get_index_html(self):
        """Get default index.html content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CogniLink - Personal Digital Communication Analyzer</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CogniLink</h1>
            <p class="subtitle">Personal Digital Communication Analyzer</p>
        </header>
        
        <nav>
            <ul>
                <li><a href="/" class="active">Home</a></li>
                <li><a href="/import">Import Data</a></li>
                <li><a href="/analyze">Analyze Data</a></li>
                <li><a href="/reports">Reports</a></li>
                <li><a href="/settings">Settings</a></li>
            </ul>
        </nav>
        
        <main>
            <section class="welcome">
                <h2>Welcome to CogniLink</h2>
                <p>CogniLink helps you analyze your digital communications to extract insights about your communication patterns, relationships, and knowledge.</p>
            </section>
            
            <section class="quick-actions">
                <h3>Quick Actions</h3>
                <div class="card-grid">
                    <div class="card">
                        <h4>Import Data</h4>
                        <p>Import data from various sources including emails, messages, and social media.</p>
                        <a href="/import" class="button">Import Data</a>
                    </div>
                    <div class="card">
                        <h4>Analyze Data</h4>
                        <p>Analyze your communication patterns, relationships, and topics.</p>
                        <a href="/analyze" class="button">Analyze Data</a>
                    </div>
                    <div class="card">
                        <h4>Generate Reports</h4>
                        <p>Generate reports from your analysis results.</p>
                        <a href="/reports" class="button">Generate Reports</a>
                    </div>
                </div>
            </section>
            
            <section class="status">
                <h3>System Status</h3>
                <div id="status-container">
                    <p>Loading status...</p>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2025 CogniLink - Personal Digital Communication Analyzer</p>
        </footer>
    </div>
    
    <script src="scripts.js"></script>
    <script>
        // Load status information
        document.addEventListener('DOMContentLoaded', function() {
            loadStatus();
        });
        
        function loadStatus() {
            Promise.all([
                fetch('/api/data').then(response => response.json()),
                fetch('/api/analyses').then(response => response.json()),
                fetch('/api/reports').then(response => response.json())
            ])
            .then(([data, analyses, reports]) => {
                const statusContainer = document.getElementById('status-container');
                
                let html = '<div class="status-grid">';
                
                html += `<div class="status-item">
                    <h4>Imported Data</h4>
                    <p class="status-value">${data.length}</p>
                    <p>data files</p>
                </div>`;
                
                html += `<div class="status-item">
                    <h4>Analysis Results</h4>
                    <p class="status-value">${analyses.length}</p>
                    <p>analysis files</p>
                </div>`;
                
                html += `<div class="status-item">
                    <h4>Generated Reports</h4>
                    <p class="status-value">${reports.length}</p>
                    <p>report files</p>
                </div>`;
                
                html += '</div>';
                
                statusContainer.innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading status:', error);
                document.getElementById('status-container').innerHTML = 
                    '<p class="error">Error loading status information. Please try again later.</p>';
            });
        }
    </script>
</body>
</html>
"""
    
    def _get_import_html(self):
        """Get default import.html content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Import Data - CogniLink</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CogniLink</h1>
            <p class="subtitle">Personal Digital Communication Analyzer</p>
        </header>
        
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/import" class="active">Import Data</a></li>
                <li><a href="/analyze">Analyze Data</a></li>
                <li><a href="/reports">Reports</a></li>
                <li><a href="/settings">Settings</a></li>
            </ul>
        </nav>
        
        <main>
            <section>
                <h2>Import Data</h2>
                <p>Import your digital communication data from various sources.</p>
                
                <div class="form-container">
                    <form id="import-form">
                        <div class="form-group">
                            <label for="source">Data Source:</label>
                            <select id="source" name="source" required>
                                <option value="">Select a data source</option>
                                <!-- Connectors will be loaded dynamically -->
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="path">File or Directory Path:</label>
                            <input type="text" id="path" name="path" required placeholder="Enter path to data file or directory">
                        </div>
                        
                        <div class="form-group">
                            <label for="data-types">Data Types (optional):</label>
                            <input type="text" id="data-types" name="data-types" placeholder="e.g., messages,contacts,profile">
                            <small>Comma-separated list of data types to import. Leave empty to import all available types.</small>
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="button primary">Import Data</button>
                            <button type="reset" class="button">Reset</button>
                        </div>
                    </form>
                </div>
            </section>
            
            <section>
                <h3>Import Status</h3>
                <div id="import-status" class="status-box">
                    <p>No import in progress</p>
                </div>
            </section>
            
            <section>
                <h3>Imported Data</h3>
                <div id="data-list">
                    <p>Loading data files...</p>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2025 CogniLink - Personal Digital Communication Analyzer</p>
        </footer>
    </div>
    
    <script src="scripts.js"></script>
    <script>
        // Load connectors and data files when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadConnectors();
            loadDataFiles();
            
            // Set up form submission
            document.getElementById('import-form').addEventListener('submit', function(e) {
                e.preventDefault();
                importData();
            });
        });
        
        function loadConnectors() {
            fetch('/api/connectors')
                .then(response => response.json())
                .then(connectors => {
                    const select = document.getElementById('source');
                    
                    // Clear existing options (except the first one)
                    while (select.options.length > 1) {
                        select.remove(1);
                    }
                    
                    // Add connector options
                    connectors.forEach(connector => {
                        const option = document.createElement('option');
                        option.value = connector.id;
                        option.textContent = connector.name;
                        select.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading connectors:', error);
                });
        }
        
        function loadDataFiles() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    const dataList = document.getElementById('data-list');
                    
                    if (data.length === 0) {
                        dataList.innerHTML = '<p>No data files found. Import some data to get started.</p>';
                        return;
                    }
                    
                    let html = '<table class="data-table">';
                    html += '<thead><tr><th>Name</th><th>Source</th><th>Items</th><th>Size</th><th>Modified</th></tr></thead>';
                    html += '<tbody>';
                    
                    data.forEach(file => {
                        html += `<tr>
                            <td>${file.name}</td>
                            <td>${file.source}</td>
                            <td>${file.item_count}</td>
                            <td>${formatSize(file.size)}</td>
                            <td>${formatDate(file.modified)}</td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    dataList.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading data files:', error);
                    document.getElementById('data-list').innerHTML = 
                        '<p class="error">Error loading data files. Please try again later.</p>';
                });
        }
        
        function importData() {
            const form = document.getElementById('import-form');
            const source = form.elements['source'].value;
            const path = form.elements['path'].value;
            const dataTypes = form.elements['data-types'].value;
            
            // Update status
            const statusBox = document.getElementById('import-status');
            statusBox.innerHTML = '<p>Importing data... Please wait.</p>';
            statusBox.classList.add('loading');
            
            // Prepare request data
            const requestData = {
                source: source,
                path: path
            };
            
            // Add data types if specified
            if (dataTypes) {
                requestData.data_types = dataTypes.split(',').map(type => type.trim());
            }
            
            // Send import request
            fetch('/api/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Show success message
                    let html = '<div class="success-message">';
                    html += '<h4>Import Completed Successfully</h4>';
                    html += `<p>Imported ${result.result.item_count} items in ${result.result.duration.toFixed(2)} seconds.</p>`;
                    
                    // Show item type breakdown
                    if (result.result.item_types) {
                        html += '<h5>Item Type Breakdown:</h5>';
                        html += '<ul>';
                        for (const [type, count] of Object.entries(result.result.item_types)) {
                            html += `<li>${type}: ${count} items</li>`;
                        }
                        html += '</ul>';
                    }
                    
                    html += `<p>Data saved to: ${result.result.file}</p>`;
                    html += '</div>';
                    
                    statusBox.innerHTML = html;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('success');
                    
                    // Reload data files list
                    loadDataFiles();
                } else {
                    // Show error message
                    statusBox.innerHTML = `<p class="error">Error: ${result.error}</p>`;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('error');
                }
            })
            .catch(error => {
                console.error('Error importing data:', error);
                statusBox.innerHTML = '<p class="error">Error importing data. Please try again later.</p>';
                statusBox.classList.remove('loading');
                statusBox.classList.add('error');
            });
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
            else return (bytes / 1073741824).toFixed(1) + ' GB';
        }
        
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }
    </script>
</body>
</html>
"""
    
    def _get_analyze_html(self):
        """Get default analyze.html content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyze Data - CogniLink</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CogniLink</h1>
            <p class="subtitle">Personal Digital Communication Analyzer</p>
        </header>
        
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/import">Import Data</a></li>
                <li><a href="/analyze" class="active">Analyze Data</a></li>
                <li><a href="/reports">Reports</a></li>
                <li><a href="/settings">Settings</a></li>
            </ul>
        </nav>
        
        <main>
            <section>
                <h2>Analyze Data</h2>
                <p>Analyze your imported data to extract insights about your communication patterns, relationships, and topics.</p>
                
                <div class="form-container">
                    <form id="analyze-form">
                        <div class="form-group">
                            <label for="analysis-type">Analysis Type:</label>
                            <select id="analysis-type" name="analysis-type">
                                <option value="all" selected>All Analyses</option>
                                <option value="patterns">Communication Patterns</option>
                                <option value="relationships">Relationships</option>
                                <option value="topics">Topics</option>
                            </select>
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="button primary">Run Analysis</button>
                        </div>
                    </form>
                </div>
            </section>
            
            <section>
                <h3>Analysis Status</h3>
                <div id="analysis-status" class="status-box">
                    <p>No analysis in progress</p>
                </div>
            </section>
            
            <section>
                <h3>Analysis Results</h3>
                <div id="analysis-list">
                    <p>Loading analysis results...</p>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2025 CogniLink - Personal Digital Communication Analyzer</p>
        </footer>
    </div>
    
    <script src="scripts.js"></script>
    <script>
        // Load analysis results when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadAnalysisResults();
            
            // Set up form submission
            document.getElementById('analyze-form').addEventListener('submit', function(e) {
                e.preventDefault();
                runAnalysis();
            });
        });
        
        function loadAnalysisResults() {
            fetch('/api/analyses')
                .then(response => response.json())
                .then(analyses => {
                    const analysisList = document.getElementById('analysis-list');
                    
                    if (analyses.length === 0) {
                        analysisList.innerHTML = '<p>No analysis results found. Run an analysis to get started.</p>';
                        return;
                    }
                    
                    let html = '<table class="data-table">';
                    html += '<thead><tr><th>Name</th><th>Analysis Types</th><th>Size</th><th>Modified</th><th>Actions</th></tr></thead>';
                    html += '<tbody>';
                    
                    analyses.forEach(analysis => {
                        html += `<tr>
                            <td>${analysis.name}</td>
                            <td>${analysis.types.join(', ')}</td>
                            <td>${formatSize(analysis.size)}</td>
                            <td>${formatDate(analysis.modified)}</td>
                            <td>
                                <button class="button small" onclick="generateReport('${analysis.id}', 'html')">HTML Report</button>
                                <button class="button small" onclick="generateReport('${analysis.id}', 'markdown')">MD Report</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    analysisList.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading analysis results:', error);
                    document.getElementById('analysis-list').innerHTML = 
                        '<p class="error">Error loading analysis results. Please try again later.</p>';
                });
        }
        
        function runAnalysis() {
            const form = document.getElementById('analyze-form');
            const analysisType = form.elements['analysis-type'].value;
            
            // Update status
            const statusBox = document.getElementById('analysis-status');
            statusBox.innerHTML = '<p>Running analysis... Please wait. This may take a while for large datasets.</p>';
            statusBox.classList.add('loading');
            
            // Send analysis request
            fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: analysisType
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Show success message
                    let html = '<div class="success-message">';
                    html += '<h4>Analysis Completed Successfully</h4>';
                    html += `<p>Analyzed ${result.result.data_items} items from ${result.result.data_files} files in ${result.result.duration.toFixed(2)} seconds.</p>`;
                    html += `<p>Analysis types: ${result.result.analyses.join(', ')}</p>`;
                    html += `<p>Results saved to: ${result.result.file}</p>`;
                    
                    // Add report generation buttons
                    html += '<div class="button-group">';
                    html += `<button class="button" onclick="generateReport(null, 'html')">Generate HTML Report</button>`;
                    html += `<button class="button" onclick="generateReport(null, 'markdown')">Generate Markdown Report</button>`;
                    html += `<button class="button" onclick="generateReport(null, 'text')">Generate Text Report</button>`;
                    html += '</div>';
                    
                    html += '</div>';
                    
                    statusBox.innerHTML = html;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('success');
                    
                    // Reload analysis results list
                    loadAnalysisResults();
                } else {
                    // Show error message
                    statusBox.innerHTML = `<p class="error">Error: ${result.error}</p>`;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('error');
                }
            })
            .catch(error => {
                console.error('Error running analysis:', error);
                statusBox.innerHTML = '<p class="error">Error running analysis. Please try again later.</p>';
                statusBox.classList.remove('loading');
                statusBox.classList.add('error');
            });
        }
        
        function generateReport(analysisId, format) {
            // Update status
            const statusBox = document.getElementById('analysis-status');
            statusBox.innerHTML = '<p>Generating report... Please wait.</p>';
            statusBox.classList.add('loading');
            statusBox.classList.remove('success', 'error');
            
            // Send report generation request
            fetch('/api/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: format,
                    analysis_id: analysisId
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Show success message
                    let html = '<div class="success-message">';
                    html += '<h4>Report Generated Successfully</h4>';
                    html += `<p>Generated ${format} report in ${result.result.duration.toFixed(2)} seconds.</p>`;
                    html += `<p>Report saved to: ${result.result.file}</p>`;
                    html += '</div>';
                    
                    statusBox.innerHTML = html;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('success');
                    
                    // Redirect to reports page
                    setTimeout(() => {
                        window.location.href = '/reports';
                    }, 2000);
                } else {
                    // Show error message
                    statusBox.innerHTML = `<p class="error">Error: ${result.error}</p>`;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('error');
                }
            })
            .catch(error => {
                console.error('Error generating report:', error);
                statusBox.innerHTML = '<p class="error">Error generating report. Please try again later.</p>';
                statusBox.classList.remove('loading');
                statusBox.classList.add('error');
            });
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
            else return (bytes / 1073741824).toFixed(1) + ' GB';
        }
        
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }
    </script>
</body>
</html>
"""
    
    def _get_reports_html(self):
        """Get default reports.html content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reports - CogniLink</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CogniLink</h1>
            <p class="subtitle">Personal Digital Communication Analyzer</p>
        </header>
        
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/import">Import Data</a></li>
                <li><a href="/analyze">Analyze Data</a></li>
                <li><a href="/reports" class="active">Reports</a></li>
                <li><a href="/settings">Settings</a></li>
            </ul>
        </nav>
        
        <main>
            <section>
                <h2>Reports</h2>
                <p>View and manage your generated reports.</p>
                
                <div class="button-group">
                    <button class="button" onclick="window.location.href='/analyze'">Generate New Report</button>
                </div>
            </section>
            
            <section>
                <h3>Generated Reports</h3>
                <div id="reports-list">
                    <p>Loading reports...</p>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2025 CogniLink - Personal Digital Communication Analyzer</p>
        </footer>
    </div>
    
    <script src="scripts.js"></script>
    <script>
        // Load reports when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadReports();
        });
        
        function loadReports() {
            fetch('/api/reports')
                .then(response => response.json())
                .then(reports => {
                    const reportsList = document.getElementById('reports-list');
                    
                    if (reports.length === 0) {
                        reportsList.innerHTML = '<p>No reports found. Generate a report to get started.</p>';
                        return;
                    }
                    
                    let html = '<table class="data-table">';
                    html += '<thead><tr><th>Name</th><th>Format</th><th>Size</th><th>Modified</th><th>Actions</th></tr></thead>';
                    html += '<tbody>';
                    
                    reports.forEach(report => {
                        html += `<tr>
                            <td>${report.name}</td>
                            <td>${report.format.toUpperCase()}</td>
                            <td>${formatSize(report.size)}</td>
                            <td>${formatDate(report.modified)}</td>
                            <td>
                                <a href="${report.path}" class="button small" target="_blank">View</a>
                                <button class="button small" onclick="downloadReport('${report.path}')">Download</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    reportsList.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading reports:', error);
                    document.getElementById('reports-list').innerHTML = 
                        '<p class="error">Error loading reports. Please try again later.</p>';
                });
        }
        
        function downloadReport(path) {
            // Create a link element
            const link = document.createElement('a');
            link.href = path;
            link.download = path.split('/').pop();
            
            // Append to body, click, and remove
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
            else return (bytes / 1073741824).toFixed(1) + ' GB';
        }
        
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }
    </script>
</body>
</html>
"""
    
    def _get_settings_html(self):
        """Get default settings.html content."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - CogniLink</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>CogniLink</h1>
            <p class="subtitle">Personal Digital Communication Analyzer</p>
        </header>
        
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/import">Import Data</a></li>
                <li><a href="/analyze">Analyze Data</a></li>
                <li><a href="/reports">Reports</a></li>
                <li><a href="/settings" class="active">Settings</a></li>
            </ul>
        </nav>
        
        <main>
            <section>
                <h2>Settings</h2>
                <p>Configure CogniLink settings.</p>
                
                <div id="settings-container">
                    <p>Loading settings...</p>
                </div>
                
                <div class="form-actions">
                    <button id="save-settings" class="button primary">Save Settings</button>
                    <button id="reset-settings" class="button">Reset to Defaults</button>
                </div>
            </section>
            
            <section>
                <h3>Settings Status</h3>
                <div id="settings-status" class="status-box">
                    <p>No changes made</p>
                </div>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2025 CogniLink - Personal Digital Communication Analyzer</p>
        </footer>
    </div>
    
    <script src="scripts.js"></script>
    <script>
        // Load settings when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadSettings();
            
            // Set up button handlers
            document.getElementById('save-settings').addEventListener('click', saveSettings);
            document.getElementById('reset-settings').addEventListener('click', resetSettings);
        });
        
        let currentSettings = {};
        
        function loadSettings() {
            fetch('/api/settings')
                .then(response => response.json())
                .then(settings => {
                    currentSettings = settings;
                    renderSettings(settings);
                })
                .catch(error => {
                    console.error('Error loading settings:', error);
                    document.getElementById('settings-container').innerHTML = 
                        '<p class="error">Error loading settings. Please try again later.</p>';
                });
        }
        
        function renderSettings(settings) {
            const container = document.getElementById('settings-container');
            
            let html = '<div class="settings-form">';
            
            // Paths section
            html += '<div class="settings-section">';
            html += '<h4>Paths</h4>';
            
            for (const [key, value] of Object.entries(settings.paths)) {
                html += `<div class="form-group">
                    <label for="path-${key}">${formatLabel(key)}:</label>
                    <input type="text" id="path-${key}" name="path-${key}" value="${value}">
                </div>`;
            }
            
            html += '</div>';
            
            // Connectors section
            html += '<div class="settings-section">';
            html += '<h4>Connectors</h4>';
            
            for (const [connector, config] of Object.entries(settings.connectors)) {
                html += `<div class="settings-subsection">
                    <h5>${formatLabel(connector)}</h5>`;
                
                for (const [key, value] of Object.entries(config)) {
                    const inputId = `connector-${connector}-${key}`;
                    html += `<div class="form-group">
                        <label for="${inputId}">${formatLabel(key)}:</label>
                        <input type="text" id="${inputId}" name="${inputId}" value="${value}">
                    </div>`;
                }
                
                html += '</div>';
            }
            
            html += '</div>';
            
            // Analysis section
            html += '<div class="settings-section">';
            html += '<h4>Analysis</h4>';
            
            for (const [analysis, config] of Object.entries(settings.analysis)) {
                html += `<div class="settings-subsection">
                    <h5>${formatLabel(analysis)}</h5>`;
                
                for (const [key, value] of Object.entries(config)) {
                    const inputId = `analysis-${analysis}-${key}`;
                    html += `<div class="form-group">
                        <label for="${inputId}">${formatLabel(key)}:</label>
                        <input type="text" id="${inputId}" name="${inputId}" value="${value}">
                    </div>`;
                }
                
                html += '</div>';
            }
            
            html += '</div>';
            
            // Interface section
            html += '<div class="settings-section">';
            html += '<h4>Interface</h4>';
            
            for (const [interface, config] of Object.entries(settings.interface)) {
                html += `<div class="settings-subsection">
                    <h5>${formatLabel(interface)}</h5>`;
                
                for (const [key, value] of Object.entries(config)) {
                    const inputId = `interface-${interface}-${key}`;
                    html += `<div class="form-group">
                        <label for="${inputId}">${formatLabel(key)}:</label>
                        <input type="text" id="${inputId}" name="${inputId}" value="${value}">
                    </div>`;
                }
                
                html += '</div>';
            }
            
            html += '</div>';
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        function saveSettings() {
            // Update status
            const statusBox = document.getElementById('settings-status');
            statusBox.innerHTML = '<p>Saving settings... Please wait.</p>';
            statusBox.classList.add('loading');
            statusBox.classList.remove('success', 'error');
            
            // Collect settings from form
            const newSettings = {
                paths: {},
                connectors: {},
                analysis: {},
                interface: {}
            };
            
            // Collect path settings
            for (const [key, value] of Object.entries(currentSettings.paths)) {
                const inputId = `path-${key}`;
                const input = document.getElementById(inputId);
                if (input) {
                    newSettings.paths[key] = input.value;
                }
            }
            
            // Collect connector settings
            for (const [connector, config] of Object.entries(currentSettings.connectors)) {
                newSettings.connectors[connector] = {};
                
                for (const key of Object.keys(config)) {
                    const inputId = `connector-${connector}-${key}`;
                    const input = document.getElementById(inputId);
                    if (input) {
                        newSettings.connectors[connector][key] = input.value;
                    }
                }
            }
            
            // Collect analysis settings
            for (const [analysis, config] of Object.entries(currentSettings.analysis)) {
                newSettings.analysis[analysis] = {};
                
                for (const key of Object.keys(config)) {
                    const inputId = `analysis-${analysis}-${key}`;
                    const input = document.getElementById(inputId);
                    if (input) {
                        newSettings.analysis[analysis][key] = input.value;
                    }
                }
            }
            
            // Collect interface settings
            for (const [interface, config] of Object.entries(currentSettings.interface)) {
                newSettings.interface[interface] = {};
                
                for (const key of Object.keys(config)) {
                    const inputId = `interface-${interface}-${key}`;
                    const input = document.getElementById(inputId);
                    if (input) {
                        newSettings.interface[interface][key] = input.value;
                    }
                }
            }
            
            // Send settings update request
            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newSettings)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Show success message
                    statusBox.innerHTML = '<p class="success-message">Settings saved successfully.</p>';
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('success');
                    
                    // Update current settings
                    currentSettings = result.result;
                } else {
                    // Show error message
                    statusBox.innerHTML = `<p class="error">Error: ${result.error}</p>`;
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('error');
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                statusBox.innerHTML = '<p class="error">Error saving settings. Please try again later.</p>';
                statusBox.classList.remove('loading');
                statusBox.classList.add('error');
            });
        }
        
        function resetSettings() {
            if (confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
                // Update status
                const statusBox = document.getElementById('settings-status');
                statusBox.innerHTML = '<p>Resetting settings... Please wait.</p>';
                statusBox.classList.add('loading');
                statusBox.classList.remove('success', 'error');
                
                // Send reset request
                fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ reset: true })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        // Show success message
                        statusBox.innerHTML = '<p class="success-message">Settings reset to defaults.</p>';
                        statusBox.classList.remove('loading');
                        statusBox.classList.add('success');
                        
                        // Update current settings and re-render
                        currentSettings = result.result;
                        renderSettings(currentSettings);
                    } else {
                        // Show error message
                        statusBox.innerHTML = `<p class="error">Error: ${result.error}</p>`;
                        statusBox.classList.remove('loading');
                        statusBox.classList.add('error');
                    }
                })
                .catch(error => {
                    console.error('Error resetting settings:', error);
                    statusBox.innerHTML = '<p class="error">Error resetting settings. Please try again later.</p>';
                    statusBox.classList.remove('loading');
                    statusBox.classList.add('error');
                });
            }
        }
        
        function formatLabel(key) {
            // Convert snake_case or camelCase to Title Case with spaces
            return key
                .replace(/_/g, ' ')
                .replace(/([A-Z])/g, ' $1')
                .replace(/^./, str => str.toUpperCase());
        }
    </script>
</body>
</html>
"""
    
    def _get_styles_css(self):
        """Get default styles.css content."""
        return """/* CogniLink Web Interface Styles */

:root {
    --primary-color: #3498db;
    --primary-dark: #2980b9;
    --secondary-color: #2ecc71;
    --secondary-dark: #27ae60;
    --accent-color: #e74c3c;
    --accent-dark: #c0392b;
    --text-color: #333;
    --text-light: #666;
    --background-color: #f9f9f9;
    --card-background: #fff;
    --border-color: #ddd;
    --shadow-color: rgba(0, 0, 0, 0.1);
    --success-color: #2ecc71;
    --error-color: #e74c3c;
    --warning-color: #f39c12;
    --info-color: #3498db;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --primary-color: #3498db;
        --primary-dark: #2980b9;
        --secondary-color: #2ecc71;
        --secondary-dark: #27ae60;
        --accent-color: #e74c3c;
        --accent-dark: #c0392b;
        --text-color: #f5f5f5;
        --text-light: #aaa;
        --background-color: #222;
        --card-background: #333;
        --border-color: #444;
        --shadow-color: rgba(0, 0, 0, 0.3);
    }
}

/* Base styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
    margin: 0;
    padding: 0;
    transition: background-color 0.3s ease;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Header styles */
header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 30px 0;
    text-align: center;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px var(--shadow-color);
}

h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
}

.subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-top: 10px;
}

/* Navigation styles */
nav {
    background-color: var(--card-background);
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px var(--shadow-color);
    overflow: hidden;
}

nav ul {
    display: flex;
    list-style: none;
    padding: 0;
}

nav li {
    flex: 1;
    text-align: center;
}

nav a {
    display: block;
    padding: 15px 0;
    color: var(--text-color);
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s ease;
}

nav a:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

nav a.active {
    background-color: var(--primary-color);
    color: white;
}

/* Main content styles */
main {
    margin-bottom: 40px;
}

section {
    background-color: var(--card-background);
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px var(--shadow-color);
}

h2 {
    color: var(--primary-color);
    margin-bottom: 15px;
    font-size: 1.8rem;
}

h3 {
    color: var(--secondary-color);
    margin-top: 20px;
    margin-bottom: 15px;
    font-size: 1.4rem;
}

h4 {
    color: var(--primary-color);
    margin-top: 15px;
    margin-bottom: 10px;
    font-size: 1.2rem;
}

p {
    margin-bottom: 15px;
}

/* Form styles */
.form-container {
    margin: 20px 0;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

input[type="text"],
input[type="number"],
input[type="email"],
input[type="password"],
select,
textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 1rem;
    background-color: var(--card-background);
    color: var(--text-color);
}

input:focus,
select:focus,
textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

small {
    display: block;
    margin-top: 5px;
    color: var(--text-light);
    font-size: 0.9rem;
}

.form-actions {
    margin-top: 20px;
    display: flex;
    gap: 10px;
}

/* Button styles */
.button {
    display: inline-block;
    padding: 10px 20px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: background-color 0.3s ease;
}

.button:hover {
    background-color: var(--primary-dark);
}

.button.primary {
    background-color: var(--primary-color);
}

.button.primary:hover {
    background-color: var(--primary-dark);
}

.button.secondary {
    background-color: var(--secondary-color);
}

.button.secondary:hover {
    background-color: var(--secondary-dark);
}

.button.danger {
    background-color: var(--accent-color);
}

.button.danger:hover {
    background-color: var(--accent-dark);
}

.button.small {
    padding: 5px 10px;
    font-size: 0.9rem;
}

.button-group {
    display: flex;
    gap: 10px;
    margin: 15px 0;
}

/* Table styles */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    box-shadow: 0 2px 3px var(--shadow-color);
    border-radius: 8px;
    overflow: hidden;
}

.data-table th,
.data-table td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.data-table th {
    background-color: var(--primary-color);
    color: white;
}

.data-table tr:nth-child(even) {
    background-color: rgba(0, 0, 0, 0.02);
}

.data-table tr:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

/* Card styles */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.card {
    background-color: var(--card-background);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px var(--shadow-color);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px var(--shadow-color);
}

.card h4 {
    color: var(--primary-color);
    margin-bottom: 10px;
}

/* Status styles */
.status-box {
    background-color: var(--card-background);
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    border-left: 4px solid var(--info-color);
}

.status-box.loading {
    border-left-color: var(--warning-color);
    animation: pulse 1.5s infinite;
}

.status-box.success {
    border-left-color: var(--success-color);
}

.status-box.error {
    border-left-color: var(--error-color);
}

.success-message {
    color: var(--success-color);
    font-weight: 500;
}

.error {
    color: var(--error-color);
    font-weight: 500;
}

.warning {
    color: var(--warning-color);
    font-weight: 500;
}

/* Status grid */
.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.status-item {
    background-color: var(--card-background);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 2px 4px var(--shadow-color);
    border-top: 3px solid var(--primary-color);
}

.status-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--primary-color);
    margin: 10px 0;
}

/* Settings styles */
.settings-form {
    margin: 20px 0;
}

.settings-section {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
}

.settings-section:last-child {
    border-bottom: none;
}

.settings-subsection {
    margin: 15px 0;
    padding: 15px;
    background-color: rgba(0, 0, 0, 0.02);
    border-radius: 4px;
}

/* Footer styles */
footer {
    text-align: center;
    margin-top: 40px;
    padding: 20px;
    color: var(--text-light);
    font-size: 0.9rem;
    border-top: 1px solid var(--border-color);
}

/* Animation */
@keyframes pulse {
    0% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
    100% {
        opacity: 1;
    }
}

/* Responsive styles */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    h1 {
        font-size: 2rem;
    }
    
    nav ul {
        flex-direction: column;
    }
    
    .card-grid,
    .status-grid {
        grid-template-columns: 1fr;
    }
    
    .button-group {
        flex-direction: column;
    }
    
    .form-actions {
        flex-direction: column;
    }
    
    .data-table {
        display: block;
        overflow-x: auto;
    }
}
"""
    
    def _get_scripts_js(self):
        """Get default scripts.js content."""
        return """/**
 * CogniLink Web Interface Scripts
 * 
 * This file contains JavaScript functionality for the CogniLink web interface.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any global functionality
    initTooltips();
    initCollapsibleSections();
    initDarkModeToggle();
});

/**
 * Initialize tooltips for elements with data-tooltip attribute
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        tooltip.style.position = 'absolute';
        tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = 'white';
        tooltip.style.padding = '5px 10px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '14px';
        tooltip.style.zIndex = '100';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.opacity = '0';
        tooltip.style.transition = 'opacity 0.3s';
        
        // Add tooltip to document
        document.body.appendChild(tooltip);
        
        // Show tooltip on hover
        element.addEventListener('mouseenter', (e) => {
            const rect = element.getBoundingClientRect();
            tooltip.style.left = `${rect.left + window.scrollX}px`;
            tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
            tooltip.style.opacity = '1';
        });
        
        // Hide tooltip on mouse leave
        element.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
        });
    });
}

/**
 * Initialize collapsible sections
 */
function initCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    
    collapsibleHeaders.forEach(header => {
        const content = header.nextElementSibling;
        
        if (content && content.classList.contains('collapsible-content')) {
            // Initially hide content if not marked as expanded
            if (!header.classList.contains('expanded')) {
                content.style.display = 'none';
            }
            
            // Add expand/collapse functionality
            header.addEventListener('click', () => {
                const isExpanded = header.classList.contains('expanded');
                
                // Toggle content visibility
                content.style.display = isExpanded ? 'none' : 'block';
                
                // Update header indicator
                header.classList.toggle('expanded', !isExpanded);
            });
            
            // Add indicator
            const indicator = document.createElement('span');
            indicator.className = 'collapse-indicator';
            indicator.textContent = header.classList.contains('expanded') ? '▼' : '▶';
            header.appendChild(indicator);
        }
    });
}

/**
 * Initialize dark mode toggle
 */
function initDarkModeToggle() {
    // Create toggle button if it doesn't exist
    if (!document.getElementById('dark-mode-toggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'dark-mode-toggle';
        toggleBtn.innerHTML = '🌙';
        toggleBtn.title = 'Toggle Dark Mode';
        toggleBtn.style.position = 'fixed';
        toggleBtn.style.bottom = '20px';
        toggleBtn.style.right = '20px';
        toggleBtn.style.width = '50px';
        toggleBtn.style.height = '50px';
        toggleBtn.style.borderRadius = '50%';
        toggleBtn.style.backgroundColor = 'var(--card-background)';
        toggleBtn.style.border = '2px solid var(--border-color)';
        toggleBtn.style.fontSize = '20px';
        toggleBtn.style.cursor = 'pointer';
        toggleBtn.style.zIndex = '100';
        toggleBtn.style.boxShadow = '0 2px 5px var(--shadow-color)';
        
        // Add toggle functionality
        toggleBtn.addEventListener('click', () => {
            const isDarkMode = document.body.classList.toggle('dark-mode');
            toggleBtn.innerHTML = isDarkMode ? '☀️' : '🌙';
            
            // Store preference
            localStorage.setItem('darkMode', isDarkMode);
        });
        
        // Add to document
        document.body.appendChild(toggleBtn);
        
        // Check for saved preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
            toggleBtn.innerHTML = '☀️';
        }
    }
}

/**
 * Format file size for display
 */
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
    else return (bytes / 1073741824).toFixed(1) + ' GB';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Show a notification message
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.padding = '15px 20px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '1000';
    notification.style.maxWidth = '300px';
    notification.style.boxShadow = '0 3px 6px rgba(0, 0, 0, 0.2)';
    
    // Set color based on type
    if (type === 'success') {
        notification.style.backgroundColor = 'var(--success-color)';
    } else if (type === 'error') {
        notification.style.backgroundColor = 'var(--error-color)';
    } else if (type === 'warning') {
        notification.style.backgroundColor = 'var(--warning-color)';
    } else {
        notification.style.backgroundColor = 'var(--info-color)';
    }
    
    notification.style.color = 'white';
    
    // Add close button
    const closeBtn = document.createElement('span');
    closeBtn.textContent = '×';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '5px';
    closeBtn.style.right = '10px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontSize = '18px';
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(notification);
    });
    
    notification.appendChild(closeBtn);
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}

/**
 * Sort a table by the specified column index
 */
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelectorAll('th')[columnIndex];
    
    // Determine sort direction
    const currentDirection = header.getAttribute('data-sort-direction') || 'none';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Update header attribute
    header.setAttribute('data-sort-direction', newDirection);
    
    // Sort the rows
    rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
        const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();
        
        // Try to sort as numbers if possible
        const numA = parseFloat(cellA.replace(/[^0-9.-]+/g, ''));
        const numB = parseFloat(cellB.replace(/[^0-9.-]+/g, ''));
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return newDirection === 'asc' ? numA - numB : numB - numA;
        }
        
        // Otherwise sort as strings
        return newDirection === 'asc' 
            ? cellA.localeCompare(cellB) 
            : cellB.localeCompare(cellA);
    });
    
    // Remove existing rows
    rows.forEach(row => tbody.removeChild(row));
    
    // Add sorted rows
    rows.forEach(row => tbody.appendChild(row));
}
"""


def run_web_interface(port=8080, open_browser=True):
    """
    Run the web interface.
    
    Args:
        port: Port to listen on
        open_browser: Whether to open a browser window
        
    Returns:
        Server URL
    """
    web_interface = WebInterface()
    return web_interface.start_server(port, open_browser)