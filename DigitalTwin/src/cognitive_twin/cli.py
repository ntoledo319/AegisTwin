#!/usr/bin/env python3
"""
Cognitive-Twin CLI - Command Line Interface for the Cognitive-Twin system.

This module provides the command-line interface for running the Cognitive-Twin
personal digital twin system, with various commands for data ingestion, processing,
analysis, and interaction with the resulting cognitive model.
"""

import argparse
import logging
import os
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from cognitive_twin import __version__
from cognitive_twin.core import config, utils
from cognitive_twin.pipeline import (
    ingest,
    preprocess,
    analyze,
    model,
    export,
    serve
)

# Set up rich console
console = Console()

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Set up logging with rich formatting."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure rich handler
    rich_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False
    )
    
    handlers = [rich_handler]
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers
    )
    
    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)
        return cfg
    except Exception as e:
        console.print(f"[bold red]Error loading configuration from {config_path}:[/bold red] {str(e)}")
        sys.exit(1)

def ensure_directories(cfg: Dict[str, Any]) -> None:
    """Ensure all required directories exist."""
    paths = cfg.get('paths', {})
    for key, path in paths.items():
        Path(path).mkdir(parents=True, exist_ok=True)

def run_pipeline(cfg: Dict[str, Any], steps: List[str], skip_steps: List[str] = None) -> None:
    """Run the Cognitive-Twin pipeline with the specified steps."""
    skip_steps = skip_steps or []
    
    # Initialize progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        # Step 1: Data Ingestion
        if "ingest" in steps and "ingest" not in skip_steps:
            task = progress.add_task("[bold blue]Ingesting data sources...", total=100)
            data_sources = ingest.load_all_sources(cfg)
            progress.update(task, completed=100)
        else:
            data_sources = None
        
        # Step 2: Preprocessing
        if "preprocess" in steps and "preprocess" not in skip_steps:
            task = progress.add_task("[bold blue]Preprocessing data...", total=100)
            processed_data = preprocess.process_all(cfg, data_sources)
            progress.update(task, completed=100)
        else:
            processed_data = None
        
        # Step 3: Analysis
        if "analyze" in steps and "analyze" not in skip_steps:
            task = progress.add_task("[bold blue]Analyzing content...", total=100)
            analysis_results = analyze.analyze_all(cfg, processed_data)
            progress.update(task, completed=100)
        else:
            analysis_results = None
        
        # Step 4: Cognitive Modeling
        if "model" in steps and "model" not in skip_steps:
            task = progress.add_task("[bold blue]Building cognitive model...", total=100)
            cognitive_model = model.build_model(cfg, analysis_results)
            progress.update(task, completed=100)
        else:
            cognitive_model = None
        
        # Step 5: Export Results
        if "export" in steps and "export" not in skip_steps:
            task = progress.add_task("[bold blue]Exporting results...", total=100)
            export_results = export.export_all(cfg, cognitive_model)
            progress.update(task, completed=100)
        
        # Step 6: Serve API/Dashboard
        if "serve" in steps and "serve" not in skip_steps:
            task = progress.add_task("[bold blue]Starting API and dashboard...", total=100)
            progress.update(task, completed=50)
            serve.start_services(cfg, cognitive_model)
            progress.update(task, completed=100)

def main() -> None:
    """Main entry point for the Cognitive-Twin CLI."""
    parser = argparse.ArgumentParser(
        description=f"Cognitive-Twin v{__version__} - Advanced Data Analysis & Digital Twin System"
    )
    
    # Global options
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set logging level")
    parser.add_argument("--log-file", help="Path to log file (optional)")
    parser.add_argument("--version", action="version", version=f"Cognitive-Twin v{__version__}")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the Cognitive-Twin pipeline")
    run_parser.add_argument("--all", action="store_true", help="Run all pipeline steps")
    run_parser.add_argument("--steps", nargs="+", choices=["ingest", "preprocess", "analyze", "model", "export", "serve"],
                           help="Specific pipeline steps to run")
    run_parser.add_argument("--skip", nargs="+", choices=["ingest", "preprocess", "analyze", "model", "export", "serve"],
                           help="Pipeline steps to skip")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data from sources")
    ingest_parser.add_argument("--source", choices=["text_messages", "emails", "documents", "social_media", "calendar", "location", "photos", "all"],
                              default="all", help="Specific data source to ingest")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze previously ingested data")
    analyze_parser.add_argument("--type", choices=["nlp", "relationships", "temporal", "cognitive", "all"],
                              default="all", help="Type of analysis to perform")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export analysis results")
    export_parser.add_argument("--format", choices=["narrative", "knowledge_graph", "dashboard", "api", "all"],
                             default="all", help="Export format")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API and dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    serve_parser.add_argument("--dashboard-port", type=int, default=8050, help="Port for the dashboard")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the cognitive model")
    query_parser.add_argument("question", nargs="+", help="Question to ask the model")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize a new Cognitive-Twin project")
    init_parser.add_argument("--directory", default=".", help="Directory to initialize")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    
    # Welcome message
    console.print(f"[bold green]Cognitive-Twin v{__version__}[/bold green]")
    console.print("[bold]Advanced Data Analysis & Digital Twin System[/bold]")
    console.print("=" * 50)
    
    # Handle commands
    if args.command == "run":
        cfg = load_config(args.config)
        ensure_directories(cfg)
        
        if args.all:
            steps = ["ingest", "preprocess", "analyze", "model", "export", "serve"]
        elif args.steps:
            steps = args.steps
        else:
            steps = ["ingest", "preprocess", "analyze", "model", "export"]
        
        run_pipeline(cfg, steps, args.skip)
        
    elif args.command == "ingest":
        cfg = load_config(args.config)
        ensure_directories(cfg)
        
        if args.source == "all":
            ingest.load_all_sources(cfg)
        else:
            ingest.load_source(cfg, args.source)
            
    elif args.command == "analyze":
        cfg = load_config(args.config)
        
        if args.type == "all":
            analyze.analyze_all(cfg)
        else:
            analyze.analyze_specific(cfg, args.type)
            
    elif args.command == "export":
        cfg = load_config(args.config)
        
        if args.format == "all":
            export.export_all(cfg)
        else:
            export.export_specific(cfg, args.format)
            
    elif args.command == "serve":
        cfg = load_config(args.config)
        serve.start_services(cfg, api_port=args.port, dashboard_port=args.dashboard_port)
            
    elif args.command == "query":
        cfg = load_config(args.config)
        question = " ".join(args.question)
        from cognitive_twin.interface import query
        response = query.ask_model(cfg, question)
        console.print(f"[bold cyan]Q:[/bold cyan] {question}")
        console.print(f"[bold green]A:[/bold green] {response}")
            
    elif args.command == "init":
        from cognitive_twin.core import project
        project.initialize(args.directory)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()