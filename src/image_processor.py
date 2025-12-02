"""
Image Processing Module

Core image manipulation functions using Wand (ImageMagick binding).
Supports adding borders and watermarks to images.

Design Decision: Using Wand instead of subprocess + CLI because:
- More Pythonic API with proper error handling
- Better memory management with context managers
- Type safety and IDE support
- Easier to handle image metadata and formats
"""

import os
from typing import Tuple, Optional, Literal, List
from wand.image import Image
from wand.color import Color
from wand.exceptions import WandException


# Supported image formats (lowercase extensions)
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}


def is_supported_format(filepath: str) -> bool:
    """
    Check if the file has a supported image format extension.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        True if the file extension is supported, False otherwise
    """
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_FORMATS


def adjust_saturation(
    image: Image,
    saturation: int = 100
) -> None:
    """
    Adjust the saturation of an image (in-place modification).
    
    Args:
        image: Wand Image object to modify
        saturation: Saturation level as percentage (0-200)
            - 0 = Grayscale (no color)
            - 100 = Original saturation (no change)
            - 200 = Double saturation (very vibrant)
            
    Raises:
        ValueError: If saturation is outside valid range
    """
    if not (0 <= saturation <= 200):
        raise ValueError(f"Saturation must be between 0 and 200, got {saturation}")
    
    # modulate() expects float percentages: brightness, saturation, hue
    # 100.0 = no change for all three parameters
    image.modulate(brightness=100.0, saturation=float(saturation), hue=100.0)


def add_border(
    image: Image,
    thickness: int,
    color: str = "#FFFFFF"
) -> None:
    """
    Add a solid color border around an image (in-place modification).
    
    Args:
        image: Wand Image object to modify
        thickness: Border thickness in pixels (must be positive)
        color: Border color as hex string (e.g., "#FFFFFF") or color name
        
    Raises:
        ValueError: If thickness is not positive
        WandException: If color is invalid
    """
    if thickness <= 0:
        raise ValueError(f"Border thickness must be positive, got {thickness}")
    
    # Create border color
    border_color = Color(color)
    
    # Add border using ImageMagick's border operation
    # This extends the image canvas and fills the new area with the border color
    image.border(border_color, thickness, thickness)


# Valid watermark positions
WATERMARK_POSITIONS = (
    "top-left", "top", "top-right",
    "left", "center", "right",
    "bottom-left", "bottom", "bottom-right"
)


def add_watermark(
    image: Image,
    watermark_path: str,
    position: Literal["top-left", "top", "top-right", "left", "center", "right", "bottom-left", "bottom", "bottom-right"] = "center",
    opacity: float = 0.5,
    scale_percent: float = 25.0,
    margin: int = 20
) -> None:
    """
    Overlay a watermark image onto the main image (in-place modification).
    
    Args:
        image: Wand Image object to modify
        watermark_path: Path to the watermark image file
        position: Where to place the watermark:
            - "top-left", "top", "top-right"
            - "left", "center", "right"
            - "bottom-left", "bottom", "bottom-right"
        opacity: Watermark opacity (0.0 = transparent, 1.0 = opaque)
        scale_percent: Scale watermark to this percentage of the main image's smaller dimension
        margin: Margin in pixels from edges
        
    Raises:
        FileNotFoundError: If watermark file doesn't exist
        ValueError: If position is invalid or parameters are out of range
        WandException: If watermark cannot be loaded
    """
    if not os.path.exists(watermark_path):
        raise FileNotFoundError(f"Watermark file not found: {watermark_path}")
    
    if position not in WATERMARK_POSITIONS:
        raise ValueError(f"Invalid position: {position}. Use one of {WATERMARK_POSITIONS}")
    
    if not (0.0 <= opacity <= 1.0):
        raise ValueError(f"Opacity must be between 0.0 and 1.0, got {opacity}")
    
    if not (1.0 <= scale_percent <= 100.0):
        raise ValueError(f"Scale percent must be between 1.0 and 100.0, got {scale_percent}")
    
    # Load watermark image
    with Image(filename=watermark_path) as watermark:
        # Calculate scaled size based on main image dimensions
        main_smaller_dim = min(image.width, image.height)
        target_size = int(main_smaller_dim * (scale_percent / 100.0))
        
        # Maintain aspect ratio when scaling
        wm_ratio = watermark.width / watermark.height
        if watermark.width > watermark.height:
            new_width = target_size
            new_height = int(target_size / wm_ratio)
        else:
            new_height = target_size
            new_width = int(target_size * wm_ratio)
        
        # Resize watermark
        watermark.resize(new_width, new_height)
        
        # Apply opacity (transparency)
        if opacity < 1.0:
            watermark.evaluate(operator='multiply', value=opacity, channel='alpha')
        
        # Calculate horizontal position
        if position in ("top-left", "left", "bottom-left"):
            x = margin
        elif position in ("top", "center", "bottom"):
            x = (image.width - watermark.width) // 2
        else:  # top-right, right, bottom-right
            x = image.width - watermark.width - margin
        
        # Calculate vertical position
        if position in ("top-left", "top", "top-right"):
            y = margin
        elif position in ("left", "center", "right"):
            y = (image.height - watermark.height) // 2
        else:  # bottom-left, bottom, bottom-right
            y = image.height - watermark.height - margin
        
        # Ensure position is not negative
        x = max(0, x)
        y = max(0, y)
        
        # Composite watermark onto main image
        image.composite(watermark, left=x, top=y)


def process_single_image(
    input_path: str,
    output_path: str,
    border_thickness: Optional[int] = None,
    border_color: str = "#FFFFFF",
    saturation: Optional[int] = None,
    watermarks: Optional[List[dict]] = None,
    preserve_format: bool = True
) -> dict:
    """
    Process a single image: apply saturation, border and/or watermarks, then save.
    
    This function handles the complete pipeline for one image:
    1. Load the image
    2. Apply saturation adjustment (if specified)
    3. Apply border (if specified)
    4. Apply watermarks (if specified) - multiple watermarks supported
    5. Save to output path
    
    Args:
        input_path: Path to the source image
        output_path: Path where processed image will be saved
        border_thickness: Border thickness in pixels (None = no border)
        border_color: Border color as hex string
        saturation: Saturation level 0-200 (100 = original, None = no change)
        watermarks: List of watermark configs, each with keys:
            - path: Path to watermark image
            - position: One of the 9 positions
            - opacity: 0.0-1.0
            - scale: Percentage of image size
            - margin: Pixels from edges
        preserve_format: If True, keep original format; if False, save as PNG
        
    Returns:
        dict with keys:
            - success: bool indicating if processing succeeded
            - input_path: the input path
            - output_path: the output path (where saved)
            - error: error message if success is False, None otherwise
    """
    result = {
        "success": False,
        "input_path": input_path,
        "output_path": output_path,
        "error": None
    }
    
    try:
        # Validate input file exists and is supported
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not is_supported_format(input_path):
            raise ValueError(f"Unsupported image format: {os.path.splitext(input_path)[1]}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Load and process image
        with Image(filename=input_path) as img:
            # Apply saturation adjustment first (before border/watermarks)
            if saturation is not None and saturation != 100:
                adjust_saturation(img, saturation)
            
            # Apply border (so watermarks go on top of border)
            if border_thickness is not None and border_thickness > 0:
                add_border(img, border_thickness, border_color)
            
            # Apply all watermarks in order
            if watermarks:
                for wm in watermarks:
                    if wm.get('path'):
                        add_watermark(
                            img,
                            wm['path'],
                            position=wm.get('position', 'center'),
                            opacity=wm.get('opacity', 0.5),
                            scale_percent=wm.get('scale', 25.0),
                            margin=wm.get('margin', 20)
                        )
            
            # Save the processed image
            img.save(filename=output_path)
        
        result["success"] = True
        
    except FileNotFoundError as e:
        result["error"] = str(e)
    except ValueError as e:
        result["error"] = str(e)
    except WandException as e:
        result["error"] = f"ImageMagick error: {str(e)}"
    except PermissionError as e:
        result["error"] = f"Permission denied: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {type(e).__name__}: {str(e)}"
    
    return result


def generate_preview(
    input_path: str,
    border_thickness: Optional[int] = None,
    border_color: str = "#FFFFFF",
    saturation: Optional[int] = None,
    watermarks: Optional[List[dict]] = None,
    max_preview_size: int = 800
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Generate a preview of the processed image as PNG bytes (for display in UI).
    
    The preview is scaled down if larger than max_preview_size to save memory.
    
    Args:
        input_path: Path to the source image
        border_thickness: Border thickness in pixels
        border_color: Border color as hex
        saturation: Saturation level 0-200 (100 = original, None = no change)
        watermarks: List of watermark configs (same format as process_single_image)
        max_preview_size: Maximum width or height for preview
        
    Returns:
        Tuple of (image_bytes, error_message)
        - On success: (PNG bytes, None)
        - On failure: (None, error message string)
    """
    try:
        if not os.path.exists(input_path):
            return None, f"File not found: {input_path}"
        
        if not is_supported_format(input_path):
            return None, f"Unsupported format: {os.path.splitext(input_path)[1]}"
        
        with Image(filename=input_path) as img:
            # Debug logging
            print(f"[DEBUG] generate_preview image_processor:")
            print(f"  - saturation param: {saturation}")
            print(f"  - will apply saturation: {saturation is not None and saturation != 100}")
            
            # Apply saturation adjustment first
            if saturation is not None and saturation != 100:
                print(f"  - APPLYING saturation: {saturation}")
                adjust_saturation(img, saturation)
            
            # Apply border
            if border_thickness is not None and border_thickness > 0:
                add_border(img, border_thickness, border_color)
            
            # Apply all watermarks
            if watermarks:
                for wm in watermarks:
                    if wm.get('path'):
                        add_watermark(
                            img,
                            wm['path'],
                            position=wm.get('position', 'center'),
                            opacity=wm.get('opacity', 0.5),
                            scale_percent=wm.get('scale', 25.0),
                            margin=wm.get('margin', 20)
                        )
            
            # Scale down for preview if needed
            if img.width > max_preview_size or img.height > max_preview_size:
                ratio = min(max_preview_size / img.width, max_preview_size / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img.resize(new_width, new_height)
            
            # Convert to PNG bytes
            img.format = 'png'
            return img.make_blob(), None
            
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)}"

