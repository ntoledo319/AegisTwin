"""
Command Line Interface for CogniLink

This module provides a command-line interface for interacting with CogniLink.
"""

import argparse
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional
import importlib
import inspect
from datetime import datetime
import colorama
from colorama import Fore, Back, Style
from tabulate import tabulate
from tqdm import tqdm

from cognilink.core.config import Config
from cognilink.pipeline.connectors import BaseConnector
from cognilink.interface.reports import ReportGenerator
from cognilink.interface.export import export_data
from cognilink.interface.visualize import create_visualization
from cognilink.interface.query import query_data

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)

logger = logging.getLogger(__name__)

class CLI:
    """
    Command Line Interface for CogniLink.
    
    This class provides a command-line interface for interacting with CogniLink,
    including importing data, analyzing data, and generating reports.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = Config()
        self.connectors = {}
        self._load_connectors()
    
    def _load_connectors(self):
        """Load all available connectors."""
        # Import the connectors module
        from cognilink.pipeline import connectors
        
        # Get all connector classes
        for name in dir(connectors):
            obj = getattr(connectors, name)
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseConnector) and 
                obj != BaseConnector):
                # Add connector to the dictionary
                connector_name = name.replace('Connector', '').lower()
                self.connectors[connector_name] = obj
    
    def run(self, args=None):
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code
        """
        parser = self._create_parser()
        
        # Parse arguments
        if args is None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(args)
        
        # Set up logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=log_level, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Process commands
        try:
            if args.command == 'import':
                self._handle_import(args)
            elif args.command == 'analyze':
                self._handle_analyze(args)
            elif args.command == 'report':
                self._handle_report(args)
            elif args.command == 'list':
                self._handle_list(args)
            elif args.command == 'config':
                self._handle_config(args)
            elif args.command == 'export':
                self._handle_export(args)
            elif args.command == 'visualize':
                self._handle_visualize(args)
            elif args.command == 'query':
                self._handle_query(args)
            elif args.command == 'web':
                self._handle_web(args)
            else:
                print(f"{Fore.RED}Unknown command: {args.command}{Style.RESET_ALL}")
                parser.print_help()
                return 1
            
            return 0
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            return 1
    
    def _create_parser(self):
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description=f"{Fore.CYAN}CogniLink: Personal Digital Communication Analyzer{Style.RESET_ALL}",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument('-v', '--verbose', action='store_true', 
                           help='Enable verbose output')
        
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # Import command
        import_parser = subparsers.add_parser('import', 
                                             help='Import data from various sources')
        import_parser.add_argument('source', choices=list(self.connectors.keys()),
                                  help='Source type to import from')
        import_parser.add_argument('path', help='Path to the data file or directory')
        import_parser.add_argument('--data-types', nargs='+', 
                                  help='Specific data types to import (optional)')
        import_parser.add_argument('--config', help='Path to a custom config file')
        
        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', 
                                              help='Analyze imported data')
        analyze_parser.add_argument('--type', choices=['patterns', 'relationships', 'topics', 'all'],
                                   default='all', help='Type of analysis to perform')
        analyze_parser.add_argument('--config', help='Path to a custom config file')
        
        # Report command
        report_parser = subparsers.add_parser('report', 
                                             help='Generate reports from analyzed data')
        report_parser.add_argument('--format', choices=['html', 'markdown', 'text'],
                                  default='html', help='Report format')
        report_parser.add_argument('--output', help='Output directory for reports')
        report_parser.add_argument('--config', help='Path to a custom config file')
        
        # List command
        list_parser = subparsers.add_parser('list', 
                                           help='List available components or imported data')
        list_parser.add_argument('what', choices=['connectors', 'data', 'analyses', 'reports'],
                                help='What to list')
        
        # Config command
        config_parser = subparsers.add_parser('config', 
                                             help='View or modify configuration')
        config_parser.add_argument('action', choices=['view', 'set', 'reset'],
                                  help='Action to perform on configuration')
        config_parser.add_argument('--section', help='Configuration section')
        config_parser.add_argument('--key', help='Configuration key')
        config_parser.add_argument('--value', help='Configuration value')
        
        # Export command
        export_parser = subparsers.add_parser('export',
                                             help='Export data to various formats')
        export_parser.add_argument('--format', choices=['json', 'csv', 'xml', 'yaml', 'excel'],
                                  default='json', help='Export format')
        export_parser.add_argument('--output', required=True,
                                  help='Output file path')
        export_parser.add_argument('--analysis', help='Analysis file to export (defaults to latest)')
        export_parser.add_argument('--section', help='Section of analysis to export (e.g., patterns, relationships)')
        
        # Visualize command
        visualize_parser = subparsers.add_parser('visualize',
                                               help='Create visualizations from analysis results')
        visualize_parser.add_argument('type', choices=['time_series', 'bar_chart', 'pie_chart', 
                                                     'network_graph', 'heatmap', 'word_cloud',
                                                     'scatter_plot', 'bubble_chart', 'radar_chart'],
                                    help='Type of visualization to create')
        visualize_parser.add_argument('--output', required=True,
                                    help='Output file path')
        visualize_parser.add_argument('--analysis', help='Analysis file to visualize (defaults to latest)')
        visualize_parser.add_argument('--section', help='Section of analysis to visualize (e.g., patterns.time_of_day_activity)')
        visualize_parser.add_argument('--title', help='Title for the visualization')
        
        # Query command
        query_parser = subparsers.add_parser('query',
                                           help='Query data using natural language')
        query_parser.add_argument('query', help='Natural language query')
        query_parser.add_argument('--visualize', action='store_true',
                                help='Create visualization of query results if applicable')
        query_parser.add_argument('--output', help='Output file path for visualization')
        
        # Web command
        web_parser = subparsers.add_parser('web',
                                         help='Start the web interface')
        web_parser.add_argument('--port', type=int, default=8080,
                              help='Port to listen on (default: 8080)')
        web_parser.add_argument('--no-browser', action='store_true',
                              help='Do not open browser automatically')
        
        return parser
    
    def _handle_import(self, args):
        """Handle the import command."""
        print(f"\n{Fore.CYAN}=== CogniLink Data Import ==={Style.RESET_ALL}")
        
        # Load custom config if provided
        if args.config:
            self.config.load_from_file(args.config)
        
        # Get the connector class
        connector_class = self.connectors.get(args.source)
        if not connector_class:
            print(f"{Fore.RED}Error: Unknown source type: {args.source}{Style.RESET_ALL}")
            sys.exit(1)
        
        # Create connector instance
        connector_config = self.config.get_connector_config(args.source)
        connector = connector_class(connector_config)
        
        print(f"{Fore.GREEN}Importing data from {args.source}...{Style.RESET_ALL}")
        print(f"Source path: {args.path}")
        
        if args.data_types:
            print(f"Data types: {', '.join(args.data_types)}")
        
        try:
            # Start import
            start_time = datetime.now()
            
            # Create progress bar
            with tqdm(desc=f"Importing {args.source} data", unit="items") as pbar:
                # Extract data
                data_items = []
                for item in connector.extract_from_file(args.path, args.data_types):
                    data_items.append(item)
                    pbar.update(1)
            
            # Calculate import time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Save imported data
            data_dir = os.path.join(self.config.get('paths', 'data_dir'), args.source)
            os.makedirs(data_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(data_dir, f"import_{timestamp}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_items, f, indent=2)
            
            # Print summary
            print(f"\n{Fore.GREEN}Import completed successfully!{Style.RESET_ALL}")
            print(f"Imported {len(data_items)} items in {duration:.2f} seconds")
            print(f"Data saved to: {output_file}")
            
            # Print item type breakdown
            item_types = {}
            for item in data_items:
                item_type = item.get('type', 'unknown')
                if item_type not in item_types:
                    item_types[item_type] = 0
                item_types[item_type] += 1
            
            print("\nItem type breakdown:")
            for item_type, count in item_types.items():
                print(f"  - {item_type}: {count} items")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error during import: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_analyze(self, args):
        """Handle the analyze command."""
        print(f"\n{Fore.CYAN}=== CogniLink Data Analysis ==={Style.RESET_ALL}")
        
        # Load custom config if provided
        if args.config:
            self.config.load_from_file(args.config)
        
        # Determine which analyses to run
        analyses = []
        if args.type == 'all' or args.type == 'patterns':
            analyses.append('patterns')
        if args.type == 'all' or args.type == 'relationships':
            analyses.append('relationships')
        if args.type == 'all' or args.type == 'topics':
            analyses.append('topics')
        
        # Import analysis modules
        from cognilink.analysis.patterns import CommunicationPatternAnalyzer
        from cognilink.analysis.relationships import RelationshipAnalyzer
        from cognilink.analysis.topics import TopicAnalyzer
        
        # Load data
        data_dir = self.config.get('paths', 'data_dir')
        all_data = []
        
        print(f"{Fore.GREEN}Loading data for analysis...{Style.RESET_ALL}")
        
        # Find all data files
        data_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.startswith('import_') and file.endswith('.json'):
                    data_files.append(os.path.join(root, file))
        
        if not data_files:
            print(f"{Fore.RED}No imported data found. Please import data first.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Load data from files
        for data_file in data_files:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.extend(data)
            except Exception as e:
                print(f"{Fore.YELLOW}Warning: Could not load data from {data_file}: {str(e)}{Style.RESET_ALL}")
        
        print(f"Loaded {len(all_data)} items from {len(data_files)} data files")
        
        # Run analyses
        results = {}
        
        try:
            for analysis_type in analyses:
                print(f"\n{Fore.GREEN}Running {analysis_type} analysis...{Style.RESET_ALL}")
                
                if analysis_type == 'patterns':
                    analyzer = CommunicationPatternAnalyzer(self.config.get_analysis_config('patterns'))
                    results['patterns'] = analyzer.analyze(all_data)
                    
                    # Print some pattern results
                    if results['patterns'].get('time_of_day_activity'):
                        print("\nTime of day activity:")
                        time_data = [(hour, count) for hour, count in results['patterns']['time_of_day_activity'].items()]
                        time_data.sort(key=lambda x: int(x[0]))
                        print(tabulate(time_data, headers=['Hour', 'Activity Count'], tablefmt='pretty'))
                    
                elif analysis_type == 'relationships':
                    analyzer = RelationshipAnalyzer(self.config.get_analysis_config('relationships'))
                    results['relationships'] = analyzer.analyze(all_data)
                    
                    # Print top relationships
                    if results['relationships'].get('top_contacts'):
                        print("\nTop contacts:")
                        contacts_data = [(i+1, contact['name'], contact['interaction_count']) 
                                        for i, contact in enumerate(results['relationships']['top_contacts'][:5])]
                        print(tabulate(contacts_data, headers=['Rank', 'Contact', 'Interactions'], tablefmt='pretty'))
                    
                elif analysis_type == 'topics':
                    analyzer = TopicAnalyzer(self.config.get_analysis_config('topics'))
                    results['topics'] = analyzer.analyze(all_data)
                    
                    # Print top topics
                    if results['topics'].get('top_topics'):
                        print("\nTop topics:")
                        topics_data = [(i+1, topic['name'], topic['frequency']) 
                                      for i, topic in enumerate(results['topics']['top_topics'][:5])]
                        print(tabulate(topics_data, headers=['Rank', 'Topic', 'Frequency'], tablefmt='pretty'))
            
            # Save analysis results
            results_dir = self.config.get('paths', 'results_dir')
            os.makedirs(results_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(results_dir, f"analysis_{timestamp}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n{Fore.GREEN}Analysis completed successfully!{Style.RESET_ALL}")
            print(f"Results saved to: {output_file}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error during analysis: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_report(self, args):
        """Handle the report command."""
        print(f"\n{Fore.CYAN}=== CogniLink Report Generation ==={Style.RESET_ALL}")
        
        # Load custom config if provided
        if args.config:
            self.config.load_from_file(args.config)
        
        # Set output directory
        output_dir = args.output or self.config.get('paths', 'reports_dir')
        os.makedirs(output_dir, exist_ok=True)
        
        # Load analysis results
        results_dir = self.config.get('paths', 'results_dir')
        
        # Find the most recent analysis file
        analysis_files = []
        for file in os.listdir(results_dir):
            if file.startswith('analysis_') and file.endswith('.json'):
                analysis_files.append(os.path.join(results_dir, file))
        
        if not analysis_files:
            print(f"{Fore.RED}No analysis results found. Please run analysis first.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Sort by modification time (newest first)
        analysis_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_analysis = analysis_files[0]
        
        print(f"{Fore.GREEN}Loading analysis results from {os.path.basename(latest_analysis)}...{Style.RESET_ALL}")
        
        try:
            with open(latest_analysis, 'r', encoding='utf-8') as f:
                analysis_results = json.load(f)
            
            # Create report generator
            report_config = self.config.get_interface_config('reports')
            report_generator = ReportGenerator(report_config)
            
            # Generate report
            print(f"{Fore.GREEN}Generating {args.format} report...{Style.RESET_ALL}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(output_dir, f"report_{timestamp}.{args.format}")
            
            report_generator.generate_report(analysis_results, args.format, report_file)
            
            print(f"\n{Fore.GREEN}Report generated successfully!{Style.RESET_ALL}")
            print(f"Report saved to: {report_file}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error generating report: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_list(self, args):
        """Handle the list command."""
        if args.what == 'connectors':
            self._list_connectors()
        elif args.what == 'data':
            self._list_data()
        elif args.what == 'analyses':
            self._list_analyses()
        elif args.what == 'reports':
            self._list_reports()
    
    def _list_connectors(self):
        """List available connectors."""
        print(f"\n{Fore.CYAN}=== Available Connectors ==={Style.RESET_ALL}")
        
        connector_data = []
        for name, connector_class in self.connectors.items():
            # Get description from docstring
            description = connector_class.__doc__.split('\n')[0] if connector_class.__doc__ else ""
            connector_data.append((name, description))
        
        # Sort by name
        connector_data.sort(key=lambda x: x[0])
        
        # Print table
        print(tabulate(connector_data, headers=['Name', 'Description'], tablefmt='pretty'))
    
    def _list_data(self):
        """List imported data files."""
        print(f"\n{Fore.CYAN}=== Imported Data Files ==={Style.RESET_ALL}")
        
        data_dir = self.config.get('paths', 'data_dir')
        
        if not os.path.exists(data_dir):
            print(f"{Fore.YELLOW}No data directory found. Import some data first.{Style.RESET_ALL}")
            return
        
        data_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.startswith('import_') and file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, data_dir)
                    source = rel_path if rel_path != '.' else 'unknown'
                    
                    # Get file stats
                    stats = os.stat(file_path)
                    size = stats.st_size
                    modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Get item count
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            item_count = len(data)
                    except:
                        item_count = 0
                    
                    data_files.append((file, source, item_count, self._format_size(size), modified))
        
        if not data_files:
            print(f"{Fore.YELLOW}No imported data files found.{Style.RESET_ALL}")
            return
        
        # Sort by modification time (newest first)
        data_files.sort(key=lambda x: x[4], reverse=True)
        
        # Print table
        print(tabulate(data_files, headers=['File', 'Source', 'Items', 'Size', 'Modified'], tablefmt='pretty'))
    
    def _list_analyses(self):
        """List analysis results."""
        print(f"\n{Fore.CYAN}=== Analysis Results ==={Style.RESET_ALL}")
        
        results_dir = self.config.get('paths', 'results_dir')
        
        if not os.path.exists(results_dir):
            print(f"{Fore.YELLOW}No results directory found. Run analysis first.{Style.RESET_ALL}")
            return
        
        analysis_files = []
        for file in os.listdir(results_dir):
            if file.startswith('analysis_') and file.endswith('.json'):
                file_path = os.path.join(results_dir, file)
                
                # Get file stats
                stats = os.stat(file_path)
                size = stats.st_size
                modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Get analysis types
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        analysis_types = ', '.join(data.keys())
                except:
                    analysis_types = 'unknown'
                
                analysis_files.append((file, analysis_types, self._format_size(size), modified))
        
        if not analysis_files:
            print(f"{Fore.YELLOW}No analysis results found.{Style.RESET_ALL}")
            return
        
        # Sort by modification time (newest first)
        analysis_files.sort(key=lambda x: x[3], reverse=True)
        
        # Print table
        print(tabulate(analysis_files, headers=['File', 'Analysis Types', 'Size', 'Modified'], tablefmt='pretty'))
    
    def _list_reports(self):
        """List generated reports."""
        print(f"\n{Fore.CYAN}=== Generated Reports ==={Style.RESET_ALL}")
        
        reports_dir = self.config.get('paths', 'reports_dir')
        
        if not os.path.exists(reports_dir):
            print(f"{Fore.YELLOW}No reports directory found. Generate reports first.{Style.RESET_ALL}")
            return
        
        report_files = []
        for file in os.listdir(reports_dir):
            if file.startswith('report_'):
                file_path = os.path.join(reports_dir, file)
                
                # Get file stats
                stats = os.stat(file_path)
                size = stats.st_size
                modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine format
                if file.endswith('.html'):
                    format_type = 'HTML'
                elif file.endswith('.md'):
                    format_type = 'Markdown'
                elif file.endswith('.txt'):
                    format_type = 'Text'
                else:
                    format_type = 'Unknown'
                
                report_files.append((file, format_type, self._format_size(size), modified))
        
        if not report_files:
            print(f"{Fore.YELLOW}No generated reports found.{Style.RESET_ALL}")
            return
        
        # Sort by modification time (newest first)
        report_files.sort(key=lambda x: x[3], reverse=True)
        
        # Print table
        print(tabulate(report_files, headers=['File', 'Format', 'Size', 'Modified'], tablefmt='pretty'))
    
    def _handle_config(self, args):
        """Handle the config command."""
        if args.action == 'view':
            self._view_config(args.section, args.key)
        elif args.action == 'set':
            self._set_config(args.section, args.key, args.value)
        elif args.action == 'reset':
            self._reset_config(args.section)
    
    def _view_config(self, section=None, key=None):
        """View configuration."""
        print(f"\n{Fore.CYAN}=== CogniLink Configuration ==={Style.RESET_ALL}")
        
        if section and key:
            # View specific key
            value = self.config.get(section, key)
            print(f"{section}.{key} = {value}")
        elif section:
            # View section
            section_config = self.config.get_section(section)
            print(f"\n{Fore.GREEN}[{section}]{Style.RESET_ALL}")
            for key, value in section_config.items():
                print(f"{key} = {value}")
        else:
            # View all sections
            for section_name in self.config.get_sections():
                print(f"\n{Fore.GREEN}[{section_name}]{Style.RESET_ALL}")
                section_config = self.config.get_section(section_name)
                for key, value in section_config.items():
                    print(f"{key} = {value}")
    
    def _set_config(self, section, key, value):
        """Set configuration value."""
        if not section or not key or value is None:
            print(f"{Fore.RED}Error: Section, key, and value are required for set command.{Style.RESET_ALL}")
            return
        
        # Set value
        self.config.set(section, key, value)
        self.config.save()
        
        print(f"{Fore.GREEN}Configuration updated:{Style.RESET_ALL}")
        print(f"{section}.{key} = {value}")
    
    def _reset_config(self, section=None):
        """Reset configuration."""
        if section:
            # Reset section
            self.config.reset_section(section)
            print(f"{Fore.GREEN}Reset configuration section: {section}{Style.RESET_ALL}")
        else:
            # Reset all
            self.config.reset()
            print(f"{Fore.GREEN}Reset all configuration to defaults{Style.RESET_ALL}")
        
        self.config.save()
    
    def _handle_export(self, args):
        """Handle the export command."""
        print(f"\n{Fore.CYAN}=== CogniLink Data Export ==={Style.RESET_ALL}")
        
        # Load analysis results
        results_dir = self.config.get('paths', 'results_dir')
        
        # Find the analysis file to export
        if args.analysis:
            analysis_path = os.path.join(results_dir, args.analysis)
            if not os.path.exists(analysis_path):
                print(f"{Fore.RED}Analysis file not found: {args.analysis}{Style.RESET_ALL}")
                sys.exit(1)
        else:
            # Find the most recent analysis file
            analysis_files = []
            for file in os.listdir(results_dir):
                if file.startswith('analysis_') and file.endswith('.json'):
                    analysis_files.append(os.path.join(results_dir, file))
            
            if not analysis_files:
                print(f"{Fore.RED}No analysis results found. Please run analysis first.{Style.RESET_ALL}")
                sys.exit(1)
            
            # Sort by modification time (newest first)
            analysis_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            analysis_path = analysis_files[0]
        
        print(f"{Fore.GREEN}Loading analysis results from {os.path.basename(analysis_path)}...{Style.RESET_ALL}")
        
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_results = json.load(f)
            
            # Extract section if specified
            if args.section:
                if args.section in analysis_results:
                    export_data = analysis_results[args.section]
                else:
                    print(f"{Fore.RED}Section not found in analysis results: {args.section}{Style.RESET_ALL}")
                    sys.exit(1)
            else:
                export_data = analysis_results
            
            # Export data
            print(f"{Fore.GREEN}Exporting data to {args.format} format...{Style.RESET_ALL}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            
            # Export data
            export_data(export_data, args.format, args.output)
            
            print(f"\n{Fore.GREEN}Data exported successfully!{Style.RESET_ALL}")
            print(f"Exported to: {args.output}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error exporting data: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_visualize(self, args):
        """Handle the visualize command."""
        print(f"\n{Fore.CYAN}=== CogniLink Data Visualization ==={Style.RESET_ALL}")
        
        # Load analysis results
        results_dir = self.config.get('paths', 'results_dir')
        
        # Find the analysis file to visualize
        if args.analysis:
            analysis_path = os.path.join(results_dir, args.analysis)
            if not os.path.exists(analysis_path):
                print(f"{Fore.RED}Analysis file not found: {args.analysis}{Style.RESET_ALL}")
                sys.exit(1)
        else:
            # Find the most recent analysis file
            analysis_files = []
            for file in os.listdir(results_dir):
                if file.startswith('analysis_') and file.endswith('.json'):
                    analysis_files.append(os.path.join(results_dir, file))
            
            if not analysis_files:
                print(f"{Fore.RED}No analysis results found. Please run analysis first.{Style.RESET_ALL}")
                sys.exit(1)
            
            # Sort by modification time (newest first)
            analysis_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            analysis_path = analysis_files[0]
        
        print(f"{Fore.GREEN}Loading analysis results from {os.path.basename(analysis_path)}...{Style.RESET_ALL}")
        
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis_results = json.load(f)
            
            # Extract section if specified
            if args.section:
                # Handle nested sections (e.g., patterns.time_of_day_activity)
                sections = args.section.split('.')
                data = analysis_results
                
                for section in sections:
                    if section in data:
                        data = data[section]
                    else:
                        print(f"{Fore.RED}Section not found in analysis results: {section}{Style.RESET_ALL}")
                        sys.exit(1)
                
                visualization_data = data
            else:
                # Try to find appropriate data for the visualization type
                if args.type == 'time_series':
                    if 'patterns' in analysis_results and 'frequency_over_time' in analysis_results['patterns']:
                        visualization_data = analysis_results['patterns']['frequency_over_time']
                    else:
                        print(f"{Fore.RED}No suitable time series data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                elif args.type == 'bar_chart':
                    if 'patterns' in analysis_results and 'time_of_day_activity' in analysis_results['patterns']:
                        visualization_data = analysis_results['patterns']['time_of_day_activity']
                    else:
                        print(f"{Fore.RED}No suitable bar chart data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                elif args.type == 'pie_chart':
                    if 'patterns' in analysis_results and 'platform_distribution' in analysis_results['patterns']:
                        visualization_data = analysis_results['patterns']['platform_distribution']
                    else:
                        print(f"{Fore.RED}No suitable pie chart data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                elif args.type == 'network_graph':
                    if 'relationships' in analysis_results and 'communication_network' in analysis_results['relationships']:
                        visualization_data = analysis_results['relationships']['communication_network']
                    else:
                        print(f"{Fore.RED}No suitable network graph data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                elif args.type == 'heatmap':
                    if 'relationships' in analysis_results and 'contact_similarity' in analysis_results['relationships']:
                        visualization_data = analysis_results['relationships']['contact_similarity']
                    else:
                        print(f"{Fore.RED}No suitable heatmap data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                elif args.type == 'word_cloud':
                    if 'topics' in analysis_results and 'word_frequencies' in analysis_results['topics']:
                        visualization_data = analysis_results['topics']['word_frequencies']
                    else:
                        print(f"{Fore.RED}No suitable word cloud data found in analysis results.{Style.RESET_ALL}")
                        sys.exit(1)
                
                else:
                    print(f"{Fore.RED}Please specify a section for this visualization type.{Style.RESET_ALL}")
                    sys.exit(1)
            
            # Create visualization
            print(f"{Fore.GREEN}Creating {args.type} visualization...{Style.RESET_ALL}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            
            # Create visualization
            title = args.title or f"CogniLink {args.type.replace('_', ' ').title()}"
            create_visualization(visualization_data, args.type, args.output, title=title)
            
            print(f"\n{Fore.GREEN}Visualization created successfully!{Style.RESET_ALL}")
            print(f"Saved to: {args.output}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error creating visualization: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_query(self, args):
        """Handle the query command."""
        print(f"\n{Fore.CYAN}=== CogniLink Natural Language Query ==={Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Query: {args.query}{Style.RESET_ALL}")
        
        try:
            # Execute query
            result = query_data(args.query)
            
            if result['success']:
                # Print query type and parameters
                print(f"\nQuery type: {result['query_type']}")
                if result['params']:
                    print(f"Parameters: {result['params']}")
                
                # Print results based on query type
                if result['query_type'] == 'top_contacts':
                    print(f"\n{Fore.GREEN}Top Contacts:{Style.RESET_ALL}")
                    contacts_data = [(i+1, contact['name'], contact['message_count']) 
                                    for i, contact in enumerate(result['top_contacts'])]
                    print(tabulate(contacts_data, headers=['Rank', 'Contact', 'Messages'], tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {contact['name']: contact['message_count'] for contact in result['top_contacts']}
                        output_path = args.output or 'top_contacts.png'
                        create_visualization(viz_data, 'bar_chart', output_path, 
                                           title='Top Contacts', orientation='horizontal')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'frequency_by_period':
                    print(f"\n{Fore.GREEN}Message Frequency by {result['period'].title()}:{Style.RESET_ALL}")
                    freq_data = [(item['period'], item['count']) for item in result['frequency_data']]
                    print(tabulate(freq_data, headers=['Period', 'Count'], tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {item['period']: item['count'] for item in result['frequency_data']}
                        output_path = args.output or f"frequency_by_{result['period']}.png"
                        create_visualization(viz_data, 'time_series', output_path, 
                                           title=f"Message Frequency by {result['period'].title()}")
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'peak_activity_time':
                    print(f"\n{Fore.GREEN}Peak Activity Times:{Style.RESET_ALL}")
                    print(f"Peak hour: {result['peak_hour_formatted']} ({result['peak_hour_count']} messages)")
                    print(f"Peak day: {result['peak_day']} ({result['peak_day_count']} messages)")
                    
                    # Create visualization if requested
                    if args.visualize:
                        output_path = args.output or 'activity_by_hour.png'
                        create_visualization(result['hour_activity'], 'bar_chart', output_path, 
                                           title='Activity by Hour of Day')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'contact_activity':
                    print(f"\n{Fore.GREEN}Activity with {result['contact']}:{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    print(f"First message: {result['first_message_date']}")
                    print(f"Last message: {result['last_message_date']}")
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {item['date']: item['count'] for item in result['activity_data']}
                        output_path = args.output or f"activity_with_{result['contact']}.png"
                        create_visualization(viz_data, 'time_series', output_path, 
                                           title=f"Communication with {result['contact']}")
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'key_relationships':
                    print(f"\n{Fore.GREEN}Key Relationships:{Style.RESET_ALL}")
                    rel_data = [(i+1, rel['name'], rel['total_messages'], 
                               f"{rel['balance']:.2f}", rel['duration_days']) 
                              for i, rel in enumerate(result['key_relationships'])]
                    print(tabulate(rel_data, 
                                  headers=['Rank', 'Contact', 'Messages', 'Balance', 'Duration (days)'], 
                                  tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {rel['name']: rel['strength'] for rel in result['key_relationships']}
                        output_path = args.output or 'key_relationships.png'
                        create_visualization(viz_data, 'bar_chart', output_path, 
                                           title='Key Relationships', orientation='horizontal')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'specific_relationship':
                    print(f"\n{Fore.GREEN}Relationship with {result['contact']}:{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    print(f"Messages sent: {result['sent_messages']}")
                    print(f"Messages received: {result['received_messages']}")
                    print(f"Balance: {result['balance']:.2f}")
                    print(f"Duration: {result['duration_days']} days")
                    print(f"First contact: {result['first_date']}")
                    print(f"Last contact: {result['last_date']}")
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {item['date']: item['count'] for item in result['activity_data']}
                        output_path = args.output or f"relationship_with_{result['contact']}.png"
                        create_visualization(viz_data, 'time_series', output_path, 
                                           title=f"Relationship with {result['contact']}")
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'communication_network':
                    print(f"\n{Fore.GREEN}Communication Network:{Style.RESET_ALL}")
                    print(f"Total contacts: {result['total_contacts']}")
                    print(f"Total connections: {result['total_connections']}")
                    
                    # Create visualization if requested
                    if args.visualize:
                        output_path = args.output or 'communication_network.png'
                        create_visualization(result['network'], 'network_graph', output_path, 
                                           title='Communication Network')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'top_topics':
                    print(f"\n{Fore.GREEN}Top Topics:{Style.RESET_ALL}")
                    topic_data = [(i+1, topic['topic'], topic['count']) 
                                for i, topic in enumerate(result['top_topics'])]
                    print(tabulate(topic_data, headers=['Rank', 'Topic', 'Count'], tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {topic['topic']: topic['count'] for topic in result['top_topics']}
                        output_path = args.output or 'top_topics.png'
                        create_visualization(viz_data, 'word_cloud', output_path, 
                                           title='Top Topics')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'contact_topics':
                    print(f"\n{Fore.GREEN}Topics with {result['contact']}:{Style.RESET_ALL}")
                    topic_data = [(i+1, topic['topic'], topic['count']) 
                                for i, topic in enumerate(result['top_topics'])]
                    print(tabulate(topic_data, headers=['Rank', 'Topic', 'Count'], tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {topic['topic']: topic['count'] for topic in result['top_topics']}
                        output_path = args.output or f"topics_with_{result['contact']}.png"
                        create_visualization(viz_data, 'word_cloud', output_path, 
                                           title=f"Topics with {result['contact']}")
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'topic_messages':
                    print(f"\n{Fore.GREEN}Messages about '{result['topic']}':{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    
                    if result['messages']:
                        msg_data = [(msg['sender'], msg['recipient'], 
                                   msg['timestamp'], msg['content']) 
                                  for msg in result['messages']]
                        print(tabulate(msg_data, 
                                      headers=['Sender', 'Recipient', 'Timestamp', 'Content'], 
                                      tablefmt='pretty'))
                
                elif result['query_type'] == 'messages_by_month':
                    print(f"\n{Fore.GREEN}Messages in {result['month'].title()}:{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    
                    if result['year_data']:
                        year_data = [(item['year'], item['count']) for item in result['year_data']]
                        print(tabulate(year_data, headers=['Year', 'Count'], tablefmt='pretty'))
                        
                        # Create visualization if requested
                        if args.visualize:
                            viz_data = {str(item['year']): item['count'] for item in result['year_data']}
                            output_path = args.output or f"messages_in_{result['month']}.png"
                            create_visualization(viz_data, 'bar_chart', output_path, 
                                               title=f"Messages in {result['month'].title()}")
                            print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'messages_by_year':
                    print(f"\n{Fore.GREEN}Messages in {result['year']}:{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    
                    if result['month_data']:
                        month_data = [(item['month_name'], item['count']) for item in result['month_data']]
                        print(tabulate(month_data, headers=['Month', 'Count'], tablefmt='pretty'))
                        
                        # Create visualization if requested
                        if args.visualize:
                            viz_data = {item['month_name']: item['count'] for item in result['month_data']}
                            output_path = args.output or f"messages_in_{result['year']}.png"
                            create_visualization(viz_data, 'bar_chart', output_path, 
                                               title=f"Messages in {result['year']}")
                            print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'messages_by_date_range':
                    print(f"\n{Fore.GREEN}Messages from {result['start_date']} to {result['end_date']}:{Style.RESET_ALL}")
                    print(f"Total messages: {result['total_messages']}")
                    
                    # Create visualization if requested
                    if args.visualize:
                        viz_data = {item['date']: item['count'] for item in result['date_data']}
                        output_path = args.output or 'messages_by_date_range.png'
                        create_visualization(viz_data, 'time_series', output_path, 
                                           title=f"Messages from {result['start_date']} to {result['end_date']}")
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'all_data':
                    print(f"\n{Fore.GREEN}Data Statistics:{Style.RESET_ALL}")
                    print(f"Total items: {result['total_items']}")
                    print(f"Date range: {result['first_date']} to {result['last_date']} ({result['duration_days']} days)")
                    
                    print("\nItem types:")
                    for item_type, count in result['type_counts'].items():
                        print(f"  - {item_type}: {count}")
                    
                    print("\nPlatforms:")
                    for platform, count in result['platform_counts'].items():
                        print(f"  - {platform}: {count}")
                    
                    # Create visualization if requested
                    if args.visualize:
                        output_path = args.output or 'platform_distribution.png'
                        create_visualization(result['platform_counts'], 'pie_chart', output_path, 
                                           title='Platform Distribution')
                        print(f"\nVisualization saved to: {output_path}")
                
                elif result['query_type'] == 'summary':
                    print(f"\n{Fore.GREEN}Summary:{Style.RESET_ALL}")
                    print(f"Total items: {result['total_items']}")
                    print(f"Date range: {result['first_date']} to {result['last_date']} ({result['duration_days']} days)")
                    
                    print("\nTop contacts:")
                    contacts_data = [(i+1, contact['name'], contact['message_count']) 
                                    for i, contact in enumerate(result['top_contacts'])]
                    print(tabulate(contacts_data, headers=['Rank', 'Contact', 'Messages'], tablefmt='pretty'))
                    
                    print(f"\nPeak activity: {result['peak_hour_formatted']} on {result['peak_day']}")
                    
                    print("\nTop topics:")
                    topics_data = [(i+1, topic['topic'], topic['count']) 
                                  for i, topic in enumerate(result['top_topics'])]
                    print(tabulate(topics_data, headers=['Rank', 'Topic', 'Count'], tablefmt='pretty'))
                    
                    # Create visualization if requested
                    if args.visualize:
                        output_path = args.output or 'communication_summary.png'
                        viz_data = {contact['name']: contact['message_count'] for contact in result['top_contacts']}
                        create_visualization(viz_data, 'bar_chart', output_path, 
                                           title='Top Contacts', orientation='horizontal')
                        print(f"\nVisualization saved to: {output_path}")
                
                else:
                    print(f"\n{Fore.GREEN}Query Results:{Style.RESET_ALL}")
                    print(json.dumps(result, indent=2))
            else:
                print(f"\n{Fore.RED}Error: {result['error']}{Style.RESET_ALL}")
                
                if 'suggestions' in result:
                    print("\nSuggestions:")
                    for suggestion in result['suggestions']:
                        print(f"  - {suggestion}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error executing query: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _handle_web(self, args):
        """Handle the web command."""
        print(f"\n{Fore.CYAN}=== CogniLink Web Interface ==={Style.RESET_ALL}")
        
        try:
            from cognilink.interface.web import run_web_interface
            
            print(f"{Fore.GREEN}Starting web interface on port {args.port}...{Style.RESET_ALL}")
            server_url = run_web_interface(args.port, not args.no_browser)
            
            print(f"\n{Fore.GREEN}Web interface running at: {server_url}{Style.RESET_ALL}")
            print("Press Ctrl+C to stop the server")
            
            # Keep the server running until interrupted
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Shutting down server...{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Error starting web interface: {str(e)}{Style.RESET_ALL}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _format_size(self, bytes):
        """Format file size for display."""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1048576:
            return f"{bytes / 1024:.1f} KB"
        elif bytes < 1073741824:
            return f"{bytes / 1048576:.1f} MB"
        else:
            return f"{bytes / 1073741824:.1f} GB"


def main():
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code
    """
    cli = CLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())