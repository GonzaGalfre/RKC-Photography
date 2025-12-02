"""
Batch Processing Module

Handles batch processing of multiple images from a folder.
Provides progress reporting, error collection, and cancellation support.

Design Decision: Process images one-by-one (not in parallel) to:
- Keep memory usage low for large batches
- Simplify error handling and progress reporting
- Avoid overwhelming disk I/O
"""

import os
import threading
from typing import Optional, Callable, List, Dict, Any, Literal
from dataclasses import dataclass, field
from enum import Enum

from .image_processor import (
    is_supported_format,
    process_single_image,
    SUPPORTED_FORMATS,
    WATERMARK_POSITIONS
)


@dataclass
class WatermarkConfig:
    """Configuration for a single watermark."""
    path: str = ""
    position: str = "center"
    opacity: float = 0.5
    scale: float = 25.0
    margin: int = 20
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "position": self.position,
            "opacity": self.opacity,
            "scale": self.scale,
            "margin": self.margin
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WatermarkConfig':
        return WatermarkConfig(
            path=data.get("path", ""),
            position=data.get("position", "center"),
            opacity=float(data.get("opacity", 0.5)),
            scale=float(data.get("scale", 25.0)),
            margin=int(data.get("margin", 20))
        )
    
    def validate(self) -> List[str]:
        """Validate this watermark config."""
        errors = []
        if self.path and not os.path.isfile(self.path):
            errors.append(f"Watermark file not found: {self.path}")
        if self.position not in WATERMARK_POSITIONS:
            errors.append(f"Invalid watermark position: {self.position}")
        if not (0.0 <= self.opacity <= 1.0):
            errors.append("Watermark opacity must be between 0.0 and 1.0")
        if not (1.0 <= self.scale <= 100.0):
            errors.append("Watermark scale must be between 1.0 and 100.0")
        return errors


class ProcessingState(Enum):
    """Current state of the batch processor."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessingConfig:
    """
    Configuration for batch image processing.
    
    Attributes:
        input_folder: Source folder containing images
        output_folder: Destination folder for processed images
        border_thickness: Border thickness in pixels (0 = no border)
        border_color: Border color as hex string
        watermarks: List of watermark configurations
        filename_prefix: Prefix to add to output filenames
        filename_suffix: Suffix to add to output filenames (before extension)
        overwrite_existing: If True, overwrite files in output folder
    """
    input_folder: str = ""
    output_folder: str = ""
    border_thickness: int = 0
    border_color: str = "#FFFFFF"
    watermarks: List[WatermarkConfig] = field(default_factory=list)
    filename_prefix: str = ""
    filename_suffix: str = ""
    overwrite_existing: bool = False
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of error messages.
        Empty list means configuration is valid.
        """
        errors = []
        
        if not self.input_folder:
            errors.append("Input folder is required")
        elif not os.path.isdir(self.input_folder):
            errors.append(f"Input folder does not exist: {self.input_folder}")
            
        if not self.output_folder:
            errors.append("Output folder is required")
            
        if self.border_thickness < 0:
            errors.append("Border thickness cannot be negative")
        
        # Validate each watermark
        for i, wm in enumerate(self.watermarks):
            wm_errors = wm.validate()
            for err in wm_errors:
                errors.append(f"Watermark {i+1}: {err}")
            
        return errors


@dataclass
class ProcessingProgress:
    """
    Tracks progress of batch processing.
    
    Attributes:
        total_files: Total number of files to process
        processed_count: Number of files processed so far
        success_count: Number of files processed successfully
        error_count: Number of files that had errors
        skipped_count: Number of files skipped (unsupported format, etc.)
        current_file: Name of the file currently being processed
        errors: List of error details (file path + error message)
        state: Current processing state
    """
    total_files: int = 0
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    current_file: str = ""
    errors: List[Dict[str, str]] = field(default_factory=list)
    state: ProcessingState = ProcessingState.IDLE
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress as percentage (0-100)."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_count / self.total_files) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (for frontend)."""
        return {
            "total_files": self.total_files,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count,
            "current_file": self.current_file,
            "progress_percent": round(self.progress_percent, 1),
            "errors": self.errors,
            "state": self.state.value
        }


class BatchProcessor:
    """
    Handles batch processing of images from a folder.
    
    Supports:
    - Progress callbacks for UI updates
    - Cancellation
    - Error collection and reporting
    - One-by-one processing to minimize memory usage
    """
    
    def __init__(self):
        self._config: Optional[ProcessingConfig] = None
        self._progress = ProcessingProgress()
        self._cancel_requested = threading.Event()
        self._processing_thread: Optional[threading.Thread] = None
        self._progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
        self._completion_callback: Optional[Callable[[ProcessingProgress], None]] = None
        self._lock = threading.Lock()
    
    @property
    def progress(self) -> ProcessingProgress:
        """Get current progress (thread-safe copy)."""
        with self._lock:
            return ProcessingProgress(
                total_files=self._progress.total_files,
                processed_count=self._progress.processed_count,
                success_count=self._progress.success_count,
                error_count=self._progress.error_count,
                skipped_count=self._progress.skipped_count,
                current_file=self._progress.current_file,
                errors=list(self._progress.errors),
                state=self._progress.state
            )
    
    @property
    def is_running(self) -> bool:
        """Check if processing is currently running."""
        with self._lock:
            return self._progress.state == ProcessingState.RUNNING
    
    def set_progress_callback(self, callback: Callable[[ProcessingProgress], None]) -> None:
        """Set callback function to receive progress updates."""
        self._progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[ProcessingProgress], None]) -> None:
        """Set callback function called when processing completes."""
        self._completion_callback = callback
    
    def _notify_progress(self) -> None:
        """Notify progress callback with current progress."""
        if self._progress_callback:
            try:
                self._progress_callback(self.progress)
            except Exception:
                pass  # Don't let callback errors stop processing
    
    def _find_image_files(self, folder: str) -> List[str]:
        """
        Find all supported image files in a folder (non-recursive).
        
        Returns list of full paths to image files, sorted alphabetically.
        """
        files = []
        try:
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath) and is_supported_format(filepath):
                    files.append(filepath)
        except PermissionError:
            pass
        
        return sorted(files)
    
    def _generate_output_path(self, input_path: str, config: ProcessingConfig) -> str:
        """
        Generate the output path for a processed image.
        
        Applies prefix/suffix to filename and uses output folder.
        """
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        # Apply prefix and suffix
        new_name = f"{config.filename_prefix}{name}{config.filename_suffix}{ext}"
        
        return os.path.join(config.output_folder, new_name)
    
    def _process_batch(self) -> None:
        """
        Main processing loop (runs in separate thread).
        
        Processes images one-by-one, updating progress and checking for cancellation.
        """
        config = self._config
        if not config:
            return
        
        try:
            # Create output folder if it doesn't exist
            os.makedirs(config.output_folder, exist_ok=True)
            
            # Find all image files
            image_files = self._find_image_files(config.input_folder)
            
            with self._lock:
                self._progress.total_files = len(image_files)
                self._progress.state = ProcessingState.RUNNING
            self._notify_progress()
            
            if not image_files:
                with self._lock:
                    self._progress.state = ProcessingState.COMPLETED
                self._notify_progress()
                return
            
            # Process each image
            for input_path in image_files:
                # Check for cancellation
                if self._cancel_requested.is_set():
                    with self._lock:
                        self._progress.state = ProcessingState.CANCELLED
                    self._notify_progress()
                    return
                
                filename = os.path.basename(input_path)
                with self._lock:
                    self._progress.current_file = filename
                self._notify_progress()
                
                # Generate output path
                output_path = self._generate_output_path(input_path, config)
                
                # Check if output exists and overwrite is disabled
                if os.path.exists(output_path) and not config.overwrite_existing:
                    with self._lock:
                        self._progress.skipped_count += 1
                        self._progress.processed_count += 1
                        self._progress.errors.append({
                            "file": filename,
                            "error": "Output file already exists (overwrite disabled)"
                        })
                    continue
                
                # Build watermarks list for processing
                watermarks_data = []
                for wm in config.watermarks:
                    if wm.path:
                        watermarks_data.append({
                            'path': wm.path,
                            'position': wm.position,
                            'opacity': wm.opacity,
                            'scale': wm.scale,
                            'margin': wm.margin
                        })
                
                # Process the image
                result = process_single_image(
                    input_path=input_path,
                    output_path=output_path,
                    border_thickness=config.border_thickness if config.border_thickness > 0 else None,
                    border_color=config.border_color,
                    watermarks=watermarks_data if watermarks_data else None
                )
                
                with self._lock:
                    self._progress.processed_count += 1
                    if result["success"]:
                        self._progress.success_count += 1
                    else:
                        self._progress.error_count += 1
                        self._progress.errors.append({
                            "file": filename,
                            "error": result["error"]
                        })
                
                self._notify_progress()
            
            # Mark as completed
            with self._lock:
                self._progress.current_file = ""
                self._progress.state = ProcessingState.COMPLETED
            self._notify_progress()
            
        except Exception as e:
            with self._lock:
                self._progress.state = ProcessingState.ERROR
                self._progress.errors.append({
                    "file": "BATCH",
                    "error": f"Fatal error: {type(e).__name__}: {str(e)}"
                })
            self._notify_progress()
        
        finally:
            if self._completion_callback:
                try:
                    self._completion_callback(self.progress)
                except Exception:
                    pass
    
    def start(self, config: ProcessingConfig) -> Optional[str]:
        """
        Start batch processing with the given configuration.
        
        Args:
            config: Processing configuration
            
        Returns:
            Error message if cannot start, None if started successfully
        """
        # Validate configuration
        errors = config.validate()
        if errors:
            return "; ".join(errors)
        
        # Check if already running
        if self.is_running:
            return "Processing is already running"
        
        # Reset state
        with self._lock:
            self._progress = ProcessingProgress()
            self._progress.state = ProcessingState.RUNNING
        
        self._config = config
        self._cancel_requested.clear()
        
        # Start processing in background thread
        self._processing_thread = threading.Thread(
            target=self._process_batch,
            daemon=True,
            name="BatchProcessor"
        )
        self._processing_thread.start()
        
        return None
    
    def cancel(self) -> None:
        """Request cancellation of current processing."""
        self._cancel_requested.set()
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for processing to complete.
        
        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)
            
        Returns:
            True if processing completed, False if timeout reached
        """
        if self._processing_thread:
            self._processing_thread.join(timeout)
            return not self._processing_thread.is_alive()
        return True


# Convenience function for simple batch processing
def process_folder(
    input_folder: str,
    output_folder: str,
    border_thickness: int = 0,
    border_color: str = "#FFFFFF",
    watermarks: Optional[List[WatermarkConfig]] = None,
    progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
) -> ProcessingProgress:
    """
    Process all images in a folder (blocking/synchronous).
    
    Convenience function for CLI or testing.
    
    Args:
        input_folder: Source folder containing images
        output_folder: Destination folder for processed images
        border_thickness: Border thickness in pixels
        border_color: Border color as hex
        watermarks: List of WatermarkConfig objects
        progress_callback: Optional callback for progress updates
        
    Returns:
        Final ProcessingProgress with results
    """
    config = ProcessingConfig(
        input_folder=input_folder,
        output_folder=output_folder,
        border_thickness=border_thickness,
        border_color=border_color,
        watermarks=watermarks or []
    )
    
    processor = BatchProcessor()
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    error = processor.start(config)
    if error:
        progress = ProcessingProgress()
        progress.state = ProcessingState.ERROR
        progress.errors.append({"file": "CONFIG", "error": error})
        return progress
    
    processor.wait_for_completion()
    return processor.progress

