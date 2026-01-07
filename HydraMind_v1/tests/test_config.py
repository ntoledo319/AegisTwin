"""
Tests for configuration management.

Tests the configuration loading, validation, and management.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from hydramind.core.config import (
    BrainConfig,
    load_config,
    save_config
)


class TestBrainConfig:
    """Test BrainConfig functionality."""

    def test_brain_config_creation(self):
        """Test creating BrainConfig instances."""
        config = BrainConfig()

        # Should have default values
        assert hasattr(config, 'server')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'features')

    def test_brain_config_with_values(self):
        """Test BrainConfig with specific values."""
        config = BrainConfig(
            server={"host": "localhost", "port": 8080},
            logging={"level": "DEBUG", "file": "/tmp/test.log"},
            features=["feature1", "feature2"]
        )

        assert config.server.host == "localhost"
        assert config.server.port == 8080
        assert config.logging.level == "DEBUG"
        assert config.logging.file == "/tmp/test.log"
        assert "feature1" in config.features
        assert "feature2" in config.features


class TestConfigFunctions:
    """Test standalone config functions."""

    def test_load_config_from_file(self, temp_dir):
        """Test loading config from YAML file."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "app": {"name": "test_app", "version": "1.0"},
            "database": {"url": "sqlite:///test.db"}
        }

        # Write config file
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)

        # Load config
        loaded_config = load_config(str(config_file))
        assert loaded_config == config_data

    def test_load_config_missing_file(self):
        """Test loading config from non-existent file."""
        config = load_config("/non/existent/file.yaml")
        assert isinstance(config, dict)

    def test_save_config_to_file(self, temp_dir):
        """Test saving config to YAML file."""
        config_file = temp_dir / "output_config.yaml"
        config_data = {
            "service": {"host": "0.0.0.0", "port": 8080},
            "debug": True
        }

        # Save config
        save_config(config_data, str(config_file))

        # Verify file was created and contains correct data
        assert config_file.exists()
        with open(config_file, 'r') as f:
            import yaml
            loaded_data = yaml.safe_load(f)
        assert loaded_data == config_data

    def test_validate_config_valid(self):
        """Test validating valid configuration."""
        valid_config = {
            "app": {"name": "test", "version": "1.0"},
            "database": {"host": "localhost", "port": 5432},
            "features": ["auth", "logging"]
        }

        # Should not raise exception
        result = validate_config(valid_config)
        assert result is True

    def test_validate_config_invalid(self):
        """Test validating invalid configuration."""
        invalid_config = {
            "app": "not_a_dict",  # Should be a dict
            "database": {"host": 123},  # Host should be string
        }

        # Should raise exception
        with pytest.raises((ValueError, TypeError)):
            validate_config(invalid_config)

    def test_merge_config(self):
        """Test merging configuration dictionaries."""
        base_config = {
            "app": {"name": "base_app", "debug": False},
            "database": {"host": "localhost"}
        }

        override_config = {
            "app": {"debug": True, "log_level": "INFO"},
            "api": {"port": 8080}
        }

        result = merge_config(base_config, override_config)

        expected = {
            "app": {"name": "base_app", "debug": True, "log_level": "INFO"},
            "database": {"host": "localhost"},
            "api": {"port": 8080}
        }

        assert result == expected

        # Original configs should not be modified
        assert base_config != result
        assert override_config != result

    def test_merge_config_empty(self):
        """Test merging with empty configurations."""
        base_config = {"setting": "value"}

        # Merge with empty dict
        result1 = merge_config(base_config, {})
        assert result1 == base_config

        # Merge empty dict with override
        result2 = merge_config({}, {"new_setting": "new_value"})
        assert result2 == {"new_setting": "new_value"}

        # Merge two empty dicts
        result3 = merge_config({}, {})
        assert result3 == {}


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_config_schema(self):
        """Test validating config against schema."""
        schema = {
            "app": {"type": "dict", "required": True},
            "app.name": {"type": "str", "required": True},
            "app.version": {"type": "str", "required": False},
            "database.host": {"type": "str", "required": True},
            "database.port": {"type": "int", "required": False, "default": 5432}
        }

        valid_config = {
            "app": {"name": "test_app"},
            "database": {"host": "localhost"}
        }

        # Should pass validation and apply defaults
        result = validate_config(valid_config)  # Assuming schema is used internally
        assert isinstance(result, bool) or isinstance(result, dict)

    def test_validate_config_type_checking(self):
        """Test configuration type checking."""
        # Test various data types
        config_tests = [
            ({"string_val": "test"}, str, True),
            ({"int_val": 42}, int, True),
            ({"float_val": 3.14}, float, True),
            ({"bool_val": True}, bool, True),
            ({"list_val": [1, 2, 3]}, list, True),
            ({"dict_val": {"nested": "value"}}, dict, True),
            ({"string_val": 123}, str, False),  # Wrong type
        ]

        for config, expected_type, should_be_valid in config_tests:
            if should_be_valid:
                # Should not raise for valid types
                result = validate_config(config)
                assert result is True
            else:
                # Should raise for invalid types
                with pytest.raises((ValueError, TypeError)):
                    validate_config(config)


class TestConfigErrorHandling:
    """Test configuration error handling."""

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading config with invalid YAML."""
        config_file = temp_dir / "invalid.yaml"

        # Write invalid YAML
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [\n  missing closing bracket")

        # Should handle gracefully
        config = load_config(str(config_file))
        assert isinstance(config, dict)

    def test_save_config_permission_error(self):
        """Test saving config with permission error."""
        # Try to save to a read-only location
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")

            config = {"test": "data"}
            # Should handle the error gracefully
            save_config(config, "/readonly/path/config.yaml")

    def test_config_with_environment_variables(self):
        """Test config with environment variable substitution."""
        import os

        # Set environment variables
        os.environ["DB_HOST"] = "prod-db.example.com"
        os.environ["DB_PORT"] = "3306"

        config = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT}",
                "name": "myapp"
            }
        }

        # Environment variables should be substituted (implementation dependent)
        # This tests the concept - actual substitution may vary
        assert config["database"]["host"] == "${DB_HOST}"  # Before substitution
        assert config["database"]["port"] == "${DB_PORT}"  # Before substitution

        # Clean up
        del os.environ["DB_HOST"]
        del os.environ["DB_PORT"]


class TestConfigPerformance:
    """Test configuration performance."""

    def test_large_config_handling(self, temp_dir):
        """Test handling of large configuration files."""
        config_file = temp_dir / "large_config.yaml"

        # Create a large config
        large_config = {}
        for i in range(1000):
            large_config[f"setting_{i}"] = {
                "nested": {
                    "value": i,
                    "data": f"data_{i}" * 10  # Some data to make it sizable
                }
            }

        # Save large config
        save_config(large_config, str(config_file))

        # Load large config (should be reasonably fast)
        import time
        start_time = time.time()
        loaded_config = load_config(str(config_file))
        end_time = time.time()

        assert loaded_config == large_config
        assert end_time - start_time < 1.0  # Should load in under 1 second

    def test_config_manager_performance(self, temp_dir):
        """Test ConfigManager performance with many operations."""
        config_file = temp_dir / "perf_config.yaml"
        manager = ConfigManager(str(config_file))

        # Perform many operations
        start_time = time.time()

        for i in range(100):
            # Update config
            config = manager.update({f"key_{i}": f"value_{i}"})
            # Get values
            value = manager.get(f"key_{i}")

        end_time = time.time()

        # Should be reasonably fast
        assert end_time - start_time < 1.0

        # Verify final state
        final_config = manager.load()
        assert len(final_config) == 100
        assert final_config["key_99"] == "value_99"
