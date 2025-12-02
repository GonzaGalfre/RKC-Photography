"""
PyWebView API Bridge

Exposes Python backend functions to JavaScript frontend via PyWebView's JS API.
All methods in the Api class can be called from JavaScript as:
    window.pywebview.api.method_name(args)

Design Decision: Using PyWebView's native JS-Python bridge instead of HTTP server because:
- Simpler architecture (no server to manage)
- No port conflicts or firewall issues
- Direct function calls with proper return values
- Built-in support for callbacks and async operations
"""

import os
import base64
import threading
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from .image_processor import generate_preview, SUPPORTED_FORMATS
from .batch_processor import (
    BatchProcessor,
    ProcessingConfig,
    ProcessingProgress,
    ProcessingState
)
from .config import (
    load_processing_config,
    save_processing_config,
    save_recent_folders
)

# Use tkinter for native file dialogs (built-in, modern Windows dialogs)
def _select_folder(title: str = "Select Folder") -> Optional[str]:
    """Open a native folder selection dialog using tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # Bring dialog to front
        
        folder = filedialog.askdirectory(title=title)
        
        root.destroy()
        return folder if folder else None
    except Exception:
        return None


def _select_file(title: str = "Select File", filetypes: list = None) -> Optional[str]:
    """Open a native file selection dialog using tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        if filetypes is None:
            filetypes = [
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All Files", "*.*")
            ]
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # Bring dialog to front
        
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        
        root.destroy()
        return file_path if file_path else None
    except Exception:
        return None


# Keep HAS_QT for compatibility but we now use tkinter for dialogs
try:
    from PyQt6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


class Api:
    """
    API class exposed to JavaScript via PyWebView.
    
    All public methods can be called from JS using:
        window.pywebview.api.methodName(args).then(result => ...)
    
    Methods should return JSON-serializable values (dict, list, str, int, float, bool, None).
    """
    
    def __init__(self, window=None):
        """
        Initialize the API.
        
        Args:
            window: PyWebView window object (set after window creation)
        """
        self._window = window
        self._processor = BatchProcessor()
        self._processor.set_progress_callback(self._on_progress)
        self._processor.set_completion_callback(self._on_complete)
        self._current_config: Optional[ProcessingConfig] = None
    
    def set_window(self, window) -> None:
        """Set the PyWebView window object for callbacks."""
        self._window = window
    
    def _on_progress(self, progress: ProcessingProgress) -> None:
        """
        Callback for processing progress updates.
        Sends progress to JavaScript via window.evaluate_js().
        """
        if self._window:
            try:
                progress_dict = progress.to_dict()
                # Call JavaScript function to update UI
                self._window.evaluate_js(
                    f'window.onProcessingProgress && window.onProcessingProgress({progress_dict})'
                )
            except Exception:
                pass  # Window might be closed
    
    def _on_complete(self, progress: ProcessingProgress) -> None:
        """Callback when processing completes."""
        if self._window:
            try:
                progress_dict = progress.to_dict()
                self._window.evaluate_js(
                    f'window.onProcessingComplete && window.onProcessingComplete({progress_dict})'
                )
            except Exception:
                pass
    
    # ==================== File/Folder Selection ====================
    
    def select_input_folder(self) -> Optional[str]:
        """
        Open native folder selection dialog for input folder.
        
        Returns:
            Selected folder path, or None if cancelled
        """
        folder = _select_folder("Select Input Folder")
        if folder:
            save_recent_folders(input_folder=folder)
            return folder
        return None
    
    def select_output_folder(self) -> Optional[str]:
        """
        Open native folder selection dialog for output folder.
        
        Returns:
            Selected folder path, or None if cancelled
        """
        folder = _select_folder("Select Output Folder")
        if folder:
            save_recent_folders(output_folder=folder)
            return folder
        return None
    
    def select_watermark_file(self) -> Optional[str]:
        """
        Open native file selection dialog for watermark image.
        
        Returns:
            Selected file path, or None if cancelled
        """
        return _select_file("Select Watermark Image")
    
    def select_preview_image(self) -> Optional[str]:
        """
        Open native file selection dialog for selecting a preview image.
        
        Returns:
            Selected file path, or None if cancelled
        """
        return _select_file("Select Preview Image")
    
    # ==================== Configuration ====================
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load saved configuration.
        
        Returns:
            Dictionary with configuration values
        """
        config = load_processing_config()
        return asdict(config)
    
    def save_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        Save configuration.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            True if saved successfully
        """
        try:
            config = ProcessingConfig(
                input_folder=config_dict.get('input_folder', ''),
                output_folder=config_dict.get('output_folder', ''),
                border_thickness=int(config_dict.get('border_thickness', 0)),
                border_color=config_dict.get('border_color', '#FFFFFF'),
                watermark_path=config_dict.get('watermark_path', ''),
                watermark_position=config_dict.get('watermark_position', 'center'),
                watermark_opacity=float(config_dict.get('watermark_opacity', 0.5)),
                watermark_scale=float(config_dict.get('watermark_scale', 25.0)),
                watermark_margin=int(config_dict.get('watermark_margin', 20)),
                filename_prefix=config_dict.get('filename_prefix', ''),
                filename_suffix=config_dict.get('filename_suffix', ''),
                overwrite_existing=bool(config_dict.get('overwrite_existing', False))
            )
            return save_processing_config(config)
        except Exception:
            return False
    
    def validate_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration and return any errors.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            Dictionary with 'valid' (bool) and 'errors' (list of strings)
        """
        try:
            config = ProcessingConfig(
                input_folder=config_dict.get('input_folder', ''),
                output_folder=config_dict.get('output_folder', ''),
                border_thickness=int(config_dict.get('border_thickness', 0)),
                border_color=config_dict.get('border_color', '#FFFFFF'),
                watermark_path=config_dict.get('watermark_path', ''),
                watermark_position=config_dict.get('watermark_position', 'center'),
                watermark_opacity=float(config_dict.get('watermark_opacity', 0.5)),
                watermark_scale=float(config_dict.get('watermark_scale', 25.0)),
                watermark_margin=int(config_dict.get('watermark_margin', 20)),
                filename_prefix=config_dict.get('filename_prefix', ''),
                filename_suffix=config_dict.get('filename_suffix', ''),
                overwrite_existing=bool(config_dict.get('overwrite_existing', False))
            )
            errors = config.validate()
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [str(e)]
            }
    
    # ==================== Preview ====================
    
    def generate_preview(self, config_dict: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """
        Generate a preview of processed image.
        
        Args:
            config_dict: Processing configuration
            image_path: Path to the image to preview
            
        Returns:
            Dictionary with:
                - success: bool
                - image_data: base64-encoded PNG data (if success)
                - error: error message (if not success)
        """
        try:
            image_bytes, error = generate_preview(
                input_path=image_path,
                border_thickness=int(config_dict.get('border_thickness', 0)) or None,
                border_color=config_dict.get('border_color', '#FFFFFF'),
                watermark_path=config_dict.get('watermark_path', '') or None,
                watermark_position=config_dict.get('watermark_position', 'center'),
                watermark_opacity=float(config_dict.get('watermark_opacity', 0.5)),
                watermark_scale=float(config_dict.get('watermark_scale', 25.0)),
                watermark_margin=int(config_dict.get('watermark_margin', 20))
            )
            
            if error:
                return {'success': False, 'error': error}
            
            # Encode as base64 for embedding in HTML
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            return {
                'success': True,
                'image_data': f'data:image/png;base64,{image_base64}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== Processing ====================
    
    def count_images(self, folder_path: str) -> Dict[str, Any]:
        """
        Count supported images in a folder.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Dictionary with 'count' and 'files' (list of filenames)
        """
        if not folder_path or not os.path.isdir(folder_path):
            return {'count': 0, 'files': [], 'error': 'Invalid folder path'}
        
        try:
            files = []
            for filename in os.listdir(folder_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in SUPPORTED_FORMATS:
                    files.append(filename)
            
            return {
                'count': len(files),
                'files': sorted(files)[:100],  # Limit to first 100 for UI
                'total_files': len(files)
            }
        except Exception as e:
            return {'count': 0, 'files': [], 'error': str(e)}
    
    def start_processing(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start batch processing with the given configuration.
        
        Progress updates will be sent via window.onProcessingProgress callback.
        Completion will trigger window.onProcessingComplete callback.
        
        Args:
            config_dict: Processing configuration
            
        Returns:
            Dictionary with 'success' and optional 'error'
        """
        try:
            config = ProcessingConfig(
                input_folder=config_dict.get('input_folder', ''),
                output_folder=config_dict.get('output_folder', ''),
                border_thickness=int(config_dict.get('border_thickness', 0)),
                border_color=config_dict.get('border_color', '#FFFFFF'),
                watermark_path=config_dict.get('watermark_path', ''),
                watermark_position=config_dict.get('watermark_position', 'center'),
                watermark_opacity=float(config_dict.get('watermark_opacity', 0.5)),
                watermark_scale=float(config_dict.get('watermark_scale', 25.0)),
                watermark_margin=int(config_dict.get('watermark_margin', 20)),
                filename_prefix=config_dict.get('filename_prefix', ''),
                filename_suffix=config_dict.get('filename_suffix', ''),
                overwrite_existing=bool(config_dict.get('overwrite_existing', False))
            )
            
            self._current_config = config
            
            # Save config for next session
            save_processing_config(config)
            
            error = self._processor.start(config)
            if error:
                return {'success': False, 'error': error}
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_processing(self) -> Dict[str, Any]:
        """
        Cancel current processing.
        
        Returns:
            Dictionary with 'success'
        """
        self._processor.cancel()
        return {'success': True}
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing status.
        
        Returns:
            Dictionary with current progress information
        """
        progress = self._processor.progress
        return progress.to_dict()
    
    def is_processing(self) -> bool:
        """Check if processing is currently running."""
        return self._processor.is_running
    
    # ==================== Utility ====================
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image file extensions."""
        return sorted(list(SUPPORTED_FORMATS))
    
    def open_folder(self, folder_path: str) -> bool:
        """
        Open a folder in the system file explorer.
        
        Args:
            folder_path: Path to folder to open
            
        Returns:
            True if successful
        """
        if not folder_path or not os.path.isdir(folder_path):
            return False
        
        try:
            import subprocess
            import sys
            
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder_path])
            else:  # Linux
                subprocess.run(['xdg-open', folder_path])
            return True
        except Exception:
            return False
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get application information."""
        from . import __version__
        return {
            'name': 'RKC Photography',
            'version': __version__,
            'supported_formats': sorted(list(SUPPORTED_FORMATS))
        }

