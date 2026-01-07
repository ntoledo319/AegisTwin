"""
CogniLink: Personal Digital Communication Analyzer

Main entry point for the CogniLink system.
"""

import sys
import os
import logging
import argparse
from cognilink.interface.cli import CLI
from cognilink.interface.web import WebInterface
from cognilink.core.utils import setup_logging
from cognilink.core.cache import Cache
from cognilink.core.config import Config

def main():
    """
    Main entry point for CogniLink.
    
    Returns:
        Exit code
    """
    # Set up logging
    setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="CogniLink: Personal Digital Communication Analyzer"
    )
    parser.add_argument('--web', action='store_true', 
                       help='Start the web interface')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port for the web interface (default: 8080)')
    parser.add_argument('--no-browser', action='store_true',
                       help='Do not open browser automatically')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear cache before starting')
    parser.add_argument('--config', type=str,
                       help='Path to custom configuration file')
    parser.add_argument('--version', action='store_true',
                       help='Show version information')
    
    # Parse initial arguments to check for special flags
    args, remaining = parser.parse_known_args()
    
    # Handle version flag
    if args.version:
        print("CogniLink: Personal Digital Communication Analyzer")
        print("Version: 1.0.0")
        return 0
    
    # Handle clear cache flag
    if args.clear_cache:
        cache = Cache()
        cache.clear()
        print("Cache cleared successfully.")
    
    # Handle custom config
    if args.config:
        config = Config()
        config.load_from_file(args.config)
        print(f"Loaded configuration from {args.config}")
    
    # Run in web mode if specified
    if args.web:
        try:
            from cognilink.interface.web import run_web_interface
            server_url = run_web_interface(args.port, not args.no_browser)
            print(f"CogniLink web interface running at {server_url}")
            print("Press Ctrl+C to stop the server")
            
            # Keep the server running until interrupted
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down server...")
                return 0
        except Exception as e:
            logging.error(f"Error starting web interface: {str(e)}")
            return 1
    # Run in CLI mode
    else:
        cli = CLI()
        return cli.run(remaining)

if __name__ == '__main__':
    sys.exit(main())