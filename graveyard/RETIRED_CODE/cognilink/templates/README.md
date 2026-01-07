# CogniLink Report Templates

This directory contains templates for generating reports in various formats.

## Available Templates

- `report.html`: Template for HTML reports
- `report.md`: Template for Markdown reports
- `report.txt`: Template for plain text reports

## Template Variables

These templates use the following variables:

- `{{title}}`: The title of the report
- `{{date}}`: The date when the report was generated
- `{{content}}`: The main content of the report

## Customizing Templates

You can customize these templates to change the appearance and structure of your reports. The report generator will use these templates when generating reports.

### HTML Template

The HTML template includes CSS styling for the report. You can modify the CSS to change the appearance of the report, including colors, fonts, and layout.

### Markdown Template

The Markdown template includes sections for the report title, date, content, and footer. You can modify the structure to add additional sections or change the formatting.

### Text Template

The text template is a simple plain text template with minimal formatting. You can modify it to change the structure of the report.

## Using Custom Templates

To use a custom template, specify the template path when generating a report:

```python
from cognilink.interface.reports import ReportGenerator

report_generator = ReportGenerator()
report_generator.generate_html_report(results, 'output.html', template_path='path/to/custom_template.html')
```

Or from the command line:

```bash
cognilink report --input results.json --type html --output report.html --template path/to/custom_template.html
```