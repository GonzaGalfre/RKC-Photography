#!/usr/bin/env python3
"""
Phase 1 CLI Test Script

A minimal command-line interface for testing the core image processing logic.
Use this to verify that the backend works correctly before building the full UI.

Usage Examples:
    # Test with border only
    python test_cli.py --input ./test_images --output ./output --border 20 --border-color "#FF5500"
    
    # Test with watermark only
    python test_cli.py --input ./test_images --output ./output --watermark ./logo.png --wm-position center
    
    # Test with both border and watermark
    python test_cli.py --input ./test_images --output ./output --border 15 --watermark ./logo.png
    
    # Process single image (for quick testing)
    python test_cli.py --single ./photo.jpg --output ./processed.jpg --border 10
"""

import argparse
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.image_processor import (
    process_single_image,
    is_supported_format,
    SUPPORTED_FORMATS
)
from src.batch_processor import (
    BatchProcessor,
    ProcessingConfig,
    ProcessingProgress,
    ProcessingState,
    process_folder
)


def print_progress(progress: ProcessingProgress) -> None:
    """Print progress update to console."""
    if progress.state == ProcessingState.RUNNING:
        pct = progress.progress_percent
        print(f"\r[{pct:5.1f}%] Processing: {progress.current_file[:40]:<40} "
              f"({progress.processed_count}/{progress.total_files})", end='', flush=True)
    elif progress.state == ProcessingState.COMPLETED:
        print()  # New line after progress
        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"{'='*60}")
        print(f"  Total files:    {progress.total_files}")
        print(f"  Successful:     {progress.success_count}")
        print(f"  Errors:         {progress.error_count}")
        print(f"  Skipped:        {progress.skipped_count}")
        
        if progress.errors:
            print(f"\nErrors encountered:")
            for err in progress.errors[:10]:  # Show first 10 errors
                print(f"  - {err['file']}: {err['error']}")
            if len(progress.errors) > 10:
                print(f"  ... and {len(progress.errors) - 10} more errors")
    elif progress.state == ProcessingState.CANCELLED:
        print(f"\n\nProcessing cancelled at {progress.processed_count}/{progress.total_files}")
    elif progress.state == ProcessingState.ERROR:
        print(f"\n\nFatal error occurred!")
        for err in progress.errors:
            print(f"  - {err['file']}: {err['error']}")


def process_single(args) -> int:
    """Process a single image (for quick testing)."""
    print(f"Processing single image: {args.single}")
    print(f"  Output: {args.output}")
    print(f"  Border: {args.border}px, color: {args.border_color}")
    if args.watermark:
        print(f"  Watermark: {args.watermark}, position: {args.wm_position}")
    print()
    
    result = process_single_image(
        input_path=args.single,
        output_path=args.output,
        border_thickness=args.border if args.border > 0 else None,
        border_color=args.border_color,
        watermark_path=args.watermark if args.watermark else None,
        watermark_position=args.wm_position,
        watermark_opacity=args.wm_opacity,
        watermark_scale=args.wm_scale
    )
    
    if result["success"]:
        print(f"✓ Success! Output saved to: {result['output_path']}")
        return 0
    else:
        print(f"✗ Error: {result['error']}")
        return 1


def process_batch(args) -> int:
    """Process a folder of images."""
    print(f"Batch Processing")
    print(f"{'='*60}")
    print(f"  Input folder:  {args.input}")
    print(f"  Output folder: {args.output}")
    print(f"  Border: {args.border}px, color: {args.border_color}")
    if args.watermark:
        print(f"  Watermark: {args.watermark}")
        print(f"    Position: {args.wm_position}")
        print(f"    Opacity:  {args.wm_opacity}")
        print(f"    Scale:    {args.wm_scale}%")
    print(f"{'='*60}")
    print()
    
    # Validate input folder
    if not os.path.isdir(args.input):
        print(f"Error: Input folder does not exist: {args.input}")
        return 1
    
    # Create output folder
    os.makedirs(args.output, exist_ok=True)
    
    # Count images
    image_count = sum(1 for f in os.listdir(args.input) 
                      if is_supported_format(os.path.join(args.input, f)))
    print(f"Found {image_count} images to process")
    print(f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
    print()
    
    if image_count == 0:
        print("No supported images found in input folder.")
        return 1
    
    # Process
    final_progress = process_folder(
        input_folder=args.input,
        output_folder=args.output,
        border_thickness=args.border,
        border_color=args.border_color,
        watermark_path=args.watermark if args.watermark else "",
        watermark_position=args.wm_position,
        watermark_opacity=args.wm_opacity,
        watermark_scale=args.wm_scale,
        progress_callback=print_progress
    )
    
    # Print final status
    print_progress(final_progress)
    
    return 0 if final_progress.error_count == 0 else 1


def create_test_structure(args) -> int:
    """Create a test folder structure for testing."""
    test_dir = args.create_test
    
    print(f"Creating test folder structure at: {test_dir}")
    
    # Create folders
    input_dir = os.path.join(test_dir, "input")
    output_dir = os.path.join(test_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a simple test image using ImageMagick via Wand
    try:
        from wand.image import Image
        from wand.color import Color
        from wand.drawing import Drawing
        
        # Create a few test images with different sizes and content
        for i, (w, h, color) in enumerate([
            (800, 600, '#3498db'),   # Blue
            (1200, 800, '#e74c3c'),  # Red
            (640, 480, '#2ecc71'),   # Green
            (1920, 1080, '#9b59b6'), # Purple
            (500, 500, '#f39c12'),   # Orange
        ], 1):
            with Image(width=w, height=h, background=Color(color)) as img:
                # Add some text
                with Drawing() as draw:
                    draw.font_size = 48
                    draw.fill_color = Color('white')
                    draw.text(w // 4, h // 2, f'Test Image {i}')
                    draw.text(w // 4, h // 2 + 60, f'{w}x{h}')
                    draw(img)
                
                img.save(filename=os.path.join(input_dir, f'test_image_{i}.jpg'))
                print(f"  Created: test_image_{i}.jpg ({w}x{h})")
        
        # Create a simple watermark image
        with Image(width=200, height=80, background=Color('transparent')) as wm:
            with Drawing() as draw:
                draw.font_size = 24
                draw.fill_color = Color('white')
                draw.stroke_color = Color('black')
                draw.stroke_width = 1
                draw.text(20, 50, 'WATERMARK')
                draw(wm)
            wm.save(filename=os.path.join(test_dir, 'watermark.png'))
            print(f"  Created: watermark.png (200x80)")
        
        print()
        print(f"Test structure created!")
        print(f"  Input folder:  {input_dir}")
        print(f"  Output folder: {output_dir}")
        print(f"  Watermark:     {os.path.join(test_dir, 'watermark.png')}")
        print()
        print("Example commands to test:")
        print(f"  python test_cli.py --input \"{input_dir}\" --output \"{output_dir}\" --border 20")
        print(f"  python test_cli.py --input \"{input_dir}\" --output \"{output_dir}\" --watermark \"{os.path.join(test_dir, 'watermark.png')}\"")
        
        return 0
        
    except ImportError:
        print("Error: Wand library not installed. Run: pip install wand")
        return 1
    except Exception as e:
        print(f"Error creating test images: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='RKC Photography - Image Processing CLI (Phase 1 Test)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create test images:
    python test_cli.py --create-test ./test_data
    
  Process with border:
    python test_cli.py --input ./input --output ./output --border 20 --border-color "#FFFFFF"
    
  Process with watermark:
    python test_cli.py --input ./input --output ./output --watermark ./logo.png
    
  Process single image:
    python test_cli.py --single ./photo.jpg --output ./processed.jpg --border 10
"""
    )
    
    # Mode selection
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--single', metavar='FILE',
                      help='Process a single image (provide input file path)')
    mode.add_argument('--create-test', metavar='DIR',
                      help='Create test folder structure with sample images')
    
    # Input/Output
    parser.add_argument('--input', '-i', metavar='FOLDER',
                        help='Input folder containing images')
    parser.add_argument('--output', '-o', metavar='FOLDER',
                        help='Output folder for processed images')
    
    # Border settings
    parser.add_argument('--border', '-b', type=int, default=0,
                        help='Border thickness in pixels (default: 0 = no border)')
    parser.add_argument('--border-color', '-c', default='#FFFFFF',
                        help='Border color as hex (default: #FFFFFF = white)')
    
    # Watermark settings
    parser.add_argument('--watermark', '-w', metavar='FILE',
                        help='Watermark image file path')
    parser.add_argument('--wm-position', choices=['center', 'bottom-right'],
                        default='center', help='Watermark position (default: center)')
    parser.add_argument('--wm-opacity', type=float, default=0.5,
                        help='Watermark opacity 0.0-1.0 (default: 0.5)')
    parser.add_argument('--wm-scale', type=float, default=25.0,
                        help='Watermark scale as %% of image (default: 25.0)')
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.create_test:
        return create_test_structure(args)
    
    if args.single:
        if not args.output:
            parser.error("--single requires --output")
        return process_single(args)
    
    # Batch mode
    if not args.input or not args.output:
        parser.error("Batch mode requires --input and --output folders")
    
    return process_batch(args)


if __name__ == '__main__':
    sys.exit(main())

