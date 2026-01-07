# CogniLink Examples

This directory contains example scripts demonstrating how to use CogniLink for various use cases.

## Basic Usage Example

The `basic_usage.py` script demonstrates the core functionality of CogniLink:

1. Importing email and message data from sample JSON files
2. Building a communication graph
3. Analyzing communication patterns
4. Analyzing relationships
5. Analyzing topics and content
6. Generating reports in HTML and Markdown formats

To run the basic usage example:

```bash
cd cognilink
python -m examples.basic_usage
```

This will:
- Import the sample data from `data/sample/`
- Create a communication graph
- Perform analysis on the data
- Generate reports in the `examples/output/` directory

## Advanced Usage Example

The `advanced_usage.py` script demonstrates more advanced features of CogniLink:

1. Creating and using custom configurations
2. Filtering data during import
3. Customizing analysis parameters
4. Processing text content with NLP features
5. Generating customized reports

To run the advanced usage example:

```bash
cd cognilink
python -m examples.advanced_usage
```

This example shows how to:
- Create custom configuration settings
- Apply filters to imported data
- Extract entities and keywords from text content
- Customize analysis parameters
- Generate detailed reports with custom settings

## Advanced Connectors Example

The `advanced_connectors.py` script demonstrates how to use the advanced connectors in CogniLink:

1. Importing data from iOS backups
2. Importing data from Twitter/X exports
3. Importing data from Spotify exports
4. Importing data from Tinder exports
5. Analyzing combined data from multiple sources

To run the advanced connectors example:

```bash
cd cognilink
python -m examples.advanced_connectors
```

This example shows how to:
- Use specialized connectors for different data sources
- Extract messages, contacts, and other data from iOS backups
- Extract tweets, direct messages, and followers from Twitter
- Extract listening history and playlists from Spotify
- Extract matches and messages from Tinder
- Combine data from multiple sources into a single communication graph

Note: This example requires sample data files to be placed in the `data/sample/` directory. The script will check for available data files and process them accordingly.

## Output

The example scripts will create an `output` directory containing:

- `comm_graph.json`: The communication graph built from the sample data
- `advanced_comm_graph.json`: The communication graph with advanced processing
- `advanced_connectors_graph.json`: The communication graph with data from multiple sources
- `report.html`: An HTML report with visualizations and analysis results
- `report.md`: A Markdown version of the report
- `advanced_report.html`: An HTML report with advanced analysis results
- `advanced_report.md`: A Markdown version of the advanced report
- `advanced_connectors_report.html`: An HTML report with analysis of multi-source data
- `advanced_connectors_report.md`: A Markdown version of the multi-source report
- `config/`: Custom configuration files used in the advanced example

## Creating Your Own Examples

To create your own examples:

1. Create a new Python file in this directory
2. Import the necessary CogniLink modules
3. Use the CogniLink API to import, analyze, and report on your data
4. Run your script with `python -m examples.your_script_name`

See the existing examples for templates to get started.