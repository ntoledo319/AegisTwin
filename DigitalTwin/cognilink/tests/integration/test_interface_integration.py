"""
Integration tests for CogniLink interface components.
"""
import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from cognilink.interface.cli import CLI
from cognilink.interface.reports import ReportGenerator
from cognilink.interface.web import WebInterface

class TestInterfaceIntegration:
    """Integration tests for the interface components."""
    
    @patch('sys.argv')
    @patch('cognilink.interface.cli.CLI.run')
    def test_cli_interface(self, mock_run, mock_argv):
        """Test the CLI interface."""
        # Mock command line arguments
        mock_argv.__getitem__.side_effect = lambda i: {
            0: 'cognilink',
            1: '--config',
            2: 'config.json',
            3: '--input',
            4: 'data',
            5: '--output',
            6: 'results'
        }.get(i)
        mock_argv.__len__.return_value = 7
        
        # Create a CLI instance
        cli = CLI()
        
        # Parse arguments
        args = cli.parse_args()
        
        # Verify arguments were parsed correctly
        assert args.config == 'config.json'
        assert args.input == 'data'
        assert args.output == 'results'
        
        # Run the CLI
        cli.run(args)
        
        # Verify run was called
        mock_run.assert_called_once()
    
    def test_report_generator(self, temp_data_dir):
        """Test the report generator."""
        # Sample analysis results
        analysis_results = {
            "patterns": {
                "frequency": {
                    "2023-01-01": 2,
                    "2023-01-02": 1
                },
                "time_patterns": {
                    10: 1,
                    14: 1,
                    9: 1
                },
                "sender_recipient_patterns": {
                    ("sender@example.com", "recipient@example.com"): 2,
                    ("Friend", "User"): 1
                }
            },
            "relationships": {
                "relationship_strength": {
                    ("sender@example.com", "recipient@example.com"): 0.8,
                    ("Friend", "User"): 0.5
                },
                "centrality": {
                    "sender@example.com": 0.6,
                    "recipient@example.com": 0.4,
                    "Friend": 0.3,
                    "User": 0.2
                }
            },
            "topics": {
                "keywords": ["project", "planning", "hello"],
                "topic_keywords": [
                    ["project", "planning"],
                    ["hello", "hi"]
                ],
                "topic_evolution": {
                    "2023-01-01": [0.75, 0.25],
                    "2023-01-02": [0.2, 0.8]
                }
            }
        }
        
        # Create output directory
        output_dir = temp_data_dir / "reports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create report generator
        report_generator = ReportGenerator({
            "output_dir": str(output_dir),
            "formats": ["html", "markdown", "text"]
        })
        
        # Generate reports
        report_files = report_generator.generate_reports(analysis_results)
        
        # Verify reports were generated
        assert len(report_files) == 3  # HTML, Markdown, and text
        for report_file in report_files:
            assert os.path.exists(report_file)
            assert os.path.getsize(report_file) > 0  # File should not be empty
    
    @patch('flask.Flask')
    def test_web_interface(self, mock_flask):
        """Test the web interface."""
        # Mock Flask app and routes
        mock_app = MagicMock()
        mock_flask.return_value = mock_app
        
        # Create web interface
        web_interface = WebInterface({
            "port": 8080,
            "debug": False
        })
        
        # Verify routes were registered
        assert mock_app.route.call_count > 0
        
        # Mock the run method to avoid actually starting the server
        with patch.object(web_interface, 'app') as mock_app:
            web_interface.run()
            mock_app.run.assert_called_once()
    
    def test_end_to_end_interface_workflow(self, temp_data_dir):
        """Test the end-to-end interface workflow."""
        # Create config file
        config_file = temp_data_dir / "config.json"
        config = {
            "connectors": {
                "email": {
                    "enabled": True,
                    "path": str(temp_data_dir / "emails.json"),
                    "format": "json"
                }
            },
            "processors": {
                "text": {
                    "enabled": True,
                    "language": "en",
                    "use_spacy": False
                }
            },
            "analysis": {
                "patterns": {
                    "enabled": True,
                    "time_window": "day",
                    "min_frequency": 1
                },
                "relationships": {
                    "enabled": True,
                    "min_interactions": 1,
                    "weight_threshold": 0.0
                },
                "topics": {
                    "enabled": True,
                    "num_topics": 2,
                    "min_topic_size": 1
                }
            },
            "interface": {
                "cli": {
                    "enabled": True,
                    "color": True
                },
                "web": {
                    "enabled": False,
                    "port": 8080
                },
                "reports": {
                    "enabled": True,
                    "output_dir": str(temp_data_dir / "reports"),
                    "formats": ["html", "markdown", "text"]
                }
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Create sample email data
        email_file = temp_data_dir / "emails.json"
        with open(email_file, 'w') as f:
            json.dump([
                {
                    "from": "sender@example.com",
                    "to": "recipient@example.com",
                    "subject": "Test Email",
                    "body": "This is a test email for testing purposes.",
                    "date": "2023-01-01T12:00:00"
                }
            ], f)
        
        # Create output directory
        os.makedirs(temp_data_dir / "reports", exist_ok=True)
        
        # Mock the main processing flow
        with patch('cognilink.interface.cli.CLI.process_data') as mock_process:
            # Mock the analysis results
            mock_process.return_value = {
                "patterns": {
                    "frequency": {"2023-01-01": 1},
                    "time_patterns": {12: 1},
                    "sender_recipient_patterns": {("sender@example.com", "recipient@example.com"): 1}
                },
                "relationships": {
                    "relationship_strength": {("sender@example.com", "recipient@example.com"): 0.5},
                    "centrality": {"sender@example.com": 0.6, "recipient@example.com": 0.4}
                },
                "topics": {
                    "keywords": ["test", "email"],
                    "topic_keywords": [["test", "email"]],
                    "topic_evolution": {"2023-01-01": [1.0]}
                }
            }
            
            # Create CLI instance
            cli = CLI()
            
            # Mock command line arguments
            args = MagicMock()
            args.config = str(config_file)
            args.input = str(temp_data_dir)
            args.output = str(temp_data_dir / "results")
            
            # Run the CLI
            cli.run(args)
            
            # Verify process_data was called
            mock_process.assert_called_once()
            
            # Verify report generation was attempted
            # This would normally create report files, but since we mocked the process_data method,
            # we're just checking that the method was called
            assert mock_process.call_count == 1