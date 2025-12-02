"""
Configuration Module

Handles loading and saving application settings.
Settings are stored as JSON in the user's app data directory.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import asdict

from .batch_processor import ProcessingConfig


def get_config_dir() -> str:
    """
    Get the application configuration directory.
    
    Uses platform-appropriate location:
    - Windows: %APPDATA%/RKC-Photography
    - macOS: ~/Library/Application Support/RKC-Photography
    - Linux: ~/.config/RKC-Photography
    """
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif os.name == 'posix':
        if os.path.exists(os.path.expanduser('~/Library')):  # macOS
            base = os.path.expanduser('~/Library/Application Support')
        else:  # Linux
            base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    else:
        base = os.path.expanduser('~')
    
    config_dir = os.path.join(base, 'RKC-Photography')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_config_file() -> str:
    """Get the path to the main configuration file."""
    return os.path.join(get_config_dir(), 'settings.json')


def load_settings() -> Dict[str, Any]:
    """
    Load settings from the configuration file.
    
    Returns empty dict if file doesn't exist or is invalid.
    """
    config_file = get_config_file()
    
    if not os.path.exists(config_file):
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to the configuration file.
    
    Returns True if successful, False otherwise.
    """
    config_file = get_config_file()
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError:
        return False


def load_processing_config() -> ProcessingConfig:
    """
    Load processing configuration from settings.
    
    Returns default config if no saved settings.
    """
    settings = load_settings()
    processing = settings.get('processing', {})
    
    return ProcessingConfig(
        input_folder=processing.get('input_folder', ''),
        output_folder=processing.get('output_folder', ''),
        border_thickness=processing.get('border_thickness', 0),
        border_color=processing.get('border_color', '#FFFFFF'),
        watermark_path=processing.get('watermark_path', ''),
        watermark_position=processing.get('watermark_position', 'center'),
        watermark_opacity=processing.get('watermark_opacity', 0.5),
        watermark_scale=processing.get('watermark_scale', 25.0),
        watermark_margin=processing.get('watermark_margin', 20),
        filename_prefix=processing.get('filename_prefix', ''),
        filename_suffix=processing.get('filename_suffix', ''),
        overwrite_existing=processing.get('overwrite_existing', False)
    )


def save_processing_config(config: ProcessingConfig) -> bool:
    """
    Save processing configuration to settings.
    
    Preserves other settings in the file.
    """
    settings = load_settings()
    settings['processing'] = asdict(config)
    return save_settings(settings)


def get_recent_folders() -> Dict[str, str]:
    """
    Get recently used input/output folders.
    
    Returns dict with 'input' and 'output' keys (may be empty strings).
    """
    settings = load_settings()
    return {
        'input': settings.get('recent_input_folder', ''),
        'output': settings.get('recent_output_folder', '')
    }


def save_recent_folders(input_folder: str = '', output_folder: str = '') -> bool:
    """Save recently used folders."""
    settings = load_settings()
    if input_folder:
        settings['recent_input_folder'] = input_folder
    if output_folder:
        settings['recent_output_folder'] = output_folder
    return save_settings(settings)

