"""
Export Module for CogniLink

This module provides functionality for exporting data in various formats.
"""

import os
import json
import csv
import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import yaml

logger = logging.getLogger(__name__)

class Exporter:
    """
    Exporter for CogniLink data.
    
    This class provides methods for exporting data in various formats.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the exporter.
        
        Args:
            config: Optional configuration dictionary
        """
        from cognilink.core.config import Config
        self.config = config or {}
        self.system_config = Config()
    
    def export(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
               format_type: str, output_path: str) -> str:
        """
        Export data to the specified format.
        
        Args:
            data: Data to export
            format_type: Format type (json, csv, xml, yaml, excel)
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Export based on format type
        if format_type.lower() == 'json':
            return self._export_json(data, output_path)
        elif format_type.lower() == 'csv':
            return self._export_csv(data, output_path)
        elif format_type.lower() == 'xml':
            return self._export_xml(data, output_path)
        elif format_type.lower() == 'yaml':
            return self._export_yaml(data, output_path)
        elif format_type.lower() == 'excel':
            return self._export_excel(data, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_json(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                    output_path: str) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported data to JSON: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise
    
    def _export_csv(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                   output_path: str) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        try:
            # Convert to list if it's a dictionary
            if isinstance(data, dict):
                # If it's a nested dictionary, flatten it
                if any(isinstance(v, dict) for v in data.values()):
                    flattened_data = []
                    for key, value in data.items():
                        if isinstance(value, dict):
                            row = {'key': key}
                            row.update(value)
                            flattened_data.append(row)
                        else:
                            flattened_data.append({'key': key, 'value': value})
                    data = flattened_data
                else:
                    data = [{'key': k, 'value': v} for k, v in data.items()]
            
            # Ensure all items have the same keys
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                for item in data:
                    # Fill in missing keys with None
                    row = {k: item.get(k, None) for k in all_keys}
                    writer.writerow(row)
            
            logger.info(f"Exported data to CSV: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def _export_xml(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                   output_path: str) -> str:
        """
        Export data to XML format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        try:
            # Create root element
            root = ET.Element('data')
            
            # Add data to XML
            if isinstance(data, dict):
                for key, value in data.items():
                    self._add_to_xml(root, key, value)
            else:
                for i, item in enumerate(data):
                    item_elem = ET.SubElement(root, 'item')
                    item_elem.set('index', str(i))
                    for key, value in item.items():
                        self._add_to_xml(item_elem, key, value)
            
            # Pretty print XML
            xml_str = ET.tostring(root, encoding='utf-8')
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='  ')
            
            # Write XML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            logger.info(f"Exported data to XML: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting to XML: {str(e)}")
            raise
    
    def _add_to_xml(self, parent: ET.Element, key: str, value: Any) -> None:
        """
        Add a key-value pair to an XML element.
        
        Args:
            parent: Parent XML element
            key: Key
            value: Value
        """
        # Convert key to valid XML tag name
        key = key.replace(' ', '_').replace('-', '_')
        
        if isinstance(value, dict):
            elem = ET.SubElement(parent, key)
            for k, v in value.items():
                self._add_to_xml(elem, k, v)
        elif isinstance(value, list):
            elem = ET.SubElement(parent, key)
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    item_elem = ET.SubElement(elem, 'item')
                    item_elem.set('index', str(i))
                    for k, v in item.items():
                        self._add_to_xml(item_elem, k, v)
                else:
                    item_elem = ET.SubElement(elem, 'item')
                    item_elem.set('index', str(i))
                    item_elem.text = str(item)
        else:
            elem = ET.SubElement(parent, key)
            elem.text = str(value) if value is not None else ''
    
    def _export_yaml(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                    output_path: str) -> str:
        """
        Export data to YAML format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Exported data to YAML: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting to YAML: {str(e)}")
            raise
    
    def _export_excel(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                     output_path: str) -> str:
        """
        Export data to Excel format.
        
        Args:
            data: Data to export
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file
        """
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if isinstance(data, dict):
                    # Handle different types of nested data
                    for key, value in data.items():
                        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                            # List of dictionaries - create a sheet for each key
                            df = pd.DataFrame(value)
                            sheet_name = str(key)[:31]  # Excel sheet names limited to 31 chars
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                        elif isinstance(value, dict):
                            # Nested dictionary - create a sheet with columns for keys and values
                            df = pd.DataFrame(value.items(), columns=['Key', 'Value'])
                            sheet_name = str(key)[:31]
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                        else:
                            # Simple key-value - add to a "General" sheet
                            if 'General' not in writer.sheets:
                                general_data = []
                            else:
                                general_data = writer.sheets['General']
                            general_data.append({'Key': key, 'Value': value})
                            pd.DataFrame(general_data).to_excel(writer, sheet_name='General', index=False)
                else:
                    # List of dictionaries - create a single sheet
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"Exported data to Excel: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise


def export_data(data: Union[Dict[str, Any], List[Dict[str, Any]]], 
               format_type: str, output_path: str) -> str:
    """
    Export data to the specified format.
    
    Args:
        data: Data to export
        format_type: Format type (json, csv, xml, yaml, excel)
        output_path: Path to save the exported data
        
    Returns:
        Path to the exported file
    """
    exporter = Exporter()
    return exporter.export(data, format_type, output_path)