"""
Quick test to verify saturation adjustment with Wand.
Run this script to test if Wand's modulate function works correctly.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from wand.image import Image


def test_saturation():
    """Test saturation adjustment on a test image."""
    
    # Find any image file in the current directory or common locations
    test_paths = [
        "test_image.jpg",
        "test_image.png",
        "sample.jpg",
        "sample.png",
    ]
    
    test_image = None
    for path in test_paths:
        if os.path.exists(path):
            test_image = path
            break
    
    if not test_image:
        print("No test image found. Please provide a test image.")
        print("Creating a simple test image...")
        
        # Create a simple colored test image
        with Image(width=200, height=200, background='red') as img:
            # Add some color variation
            img.save(filename='test_generated.png')
            test_image = 'test_generated.png'
            print(f"Created test image: {test_image}")
    
    print(f"\nUsing test image: {test_image}")
    print("-" * 50)
    
    # Test different saturation values
    saturation_values = [0, 50, 100, 150, 200]
    
    for sat in saturation_values:
        output_file = f"test_output_sat_{sat}.png"
        
        with Image(filename=test_image) as img:
            print(f"\nTesting saturation={sat}")
            print(f"  Image size: {img.width}x{img.height}")
            print(f"  Image format: {img.format}")
            
            # Apply saturation
            if sat != 100:
                print(f"  Applying modulate(brightness=100.0, saturation={float(sat)}, hue=100.0)")
                img.modulate(brightness=100.0, saturation=float(sat), hue=100.0)
            else:
                print(f"  Skipping modulate (saturation=100 means no change)")
            
            # Save output
            img.save(filename=output_file)
            print(f"  Saved to: {output_file}")
    
    print("\n" + "=" * 50)
    print("Test complete! Check the output files:")
    for sat in saturation_values:
        print(f"  - test_output_sat_{sat}.png")
    print("\nIf saturation=0 shows a grayscale image, Wand is working correctly.")


def test_with_real_image(image_path: str):
    """Test saturation on a specific image."""
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return
    
    print(f"Testing with image: {image_path}")
    
    with Image(filename=image_path) as img:
        print(f"Original size: {img.width}x{img.height}")
        
        # Test grayscale (saturation=0)
        img.modulate(brightness=100.0, saturation=0.0, hue=100.0)
        img.save(filename="test_grayscale.png")
        print("Saved grayscale version to: test_grayscale.png")
        
    with Image(filename=image_path) as img:
        # Test high saturation
        img.modulate(brightness=100.0, saturation=200.0, hue=100.0)
        img.save(filename="test_vivid.png")
        print("Saved high saturation version to: test_vivid.png")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_with_real_image(sys.argv[1])
    else:
        test_saturation()

