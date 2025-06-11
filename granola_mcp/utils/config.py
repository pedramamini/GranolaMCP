"""
Configuration utilities for GranolaMCP.

Provides simple .env file parsing and configuration management using
Python's standard library only (no external dependencies).
"""

import os
from typing import Dict, Optional


def parse_env_file(env_path: str) -> Dict[str, str]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Args:
        env_path: Path to the .env file

    Returns:
        Dict[str, str]: Dictionary of environment variables

    Raises:
        FileNotFoundError: If the .env file doesn't exist
        ValueError: If the .env file has invalid format
    """
    env_vars = {}

    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env file not found: {env_path}")

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key=value pairs
                if '=' not in line:
                    raise ValueError(f"Invalid format at line {line_num}: {line}")

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env_vars[key] = value

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Error parsing .env file: {e}") from e

    return env_vars


def load_config(env_path: str = ".env") -> Dict[str, str]:
    """
    Load configuration from .env file with fallback to environment variables.

    Args:
        env_path: Path to the .env file (default: ".env")

    Returns:
        Dict[str, str]: Configuration dictionary
    """
    config = {}

    # First, try to load from .env file
    if os.path.exists(env_path):
        try:
            config.update(parse_env_file(env_path))
        except Exception:
            # If .env file parsing fails, continue with environment variables
            pass

    # Override with actual environment variables
    for key, value in os.environ.items():
        if key.startswith('GRANOLA_'):
            config[key] = value

    return config


def get_cache_path(config: Optional[Dict[str, str]] = None) -> str:
    """
    Get the Granola cache file path from configuration.

    Args:
        config: Configuration dictionary (if None, loads from .env)

    Returns:
        str: Path to the Granola cache file
    """
    if config is None:
        config = load_config()

    # Check for cache path in configuration
    cache_path = config.get('GRANOLA_CACHE_PATH')

    if cache_path:
        # Expand user home directory if needed
        return os.path.expanduser(cache_path)

    # Default cache path
    default_path = "/Users/pedram/Library/Application Support/Granola/cache-v3.json"
    return os.path.expanduser(default_path)


def get_config_value(key: str, default: Optional[str] = None, config: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get a configuration value by key.

    Args:
        key: Configuration key
        default: Default value if key not found
        config: Configuration dictionary (if None, loads from .env)

    Returns:
        Optional[str]: Configuration value or default
    """
    if config is None:
        config = load_config()

    return config.get(key, default)


def validate_cache_path(cache_path: str) -> bool:
    """
    Validate that the cache file exists and is readable.

    Args:
        cache_path: Path to the cache file

    Returns:
        bool: True if cache file is valid, False otherwise
    """
    try:
        return os.path.exists(cache_path) and os.path.isfile(cache_path) and os.access(cache_path, os.R_OK)
    except Exception:
        return False


def create_example_env(path: str = ".env.example") -> None:
    """
    Create an example .env file with default configuration.

    Args:
        path: Path where to create the example file
    """
    example_content = '''# GranolaMCP Configuration
# Path to the Granola cache file
GRANOLA_CACHE_PATH=/Users/pedram/Library/Application Support/Granola/cache-v3.json

# Optional: Set timezone (default is America/Chicago)
# GRANOLA_TIMEZONE=America/Chicago

# Optional: Enable debug logging
# GRANOLA_DEBUG=true
'''

    with open(path, 'w', encoding='utf-8') as f:
        f.write(example_content)