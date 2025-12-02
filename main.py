#!/usr/bin/env python3
"""
RKC Photography - Desktop Image Processing Application

Main entry point that launches the PyWebView-based GUI application.

Usage:
    python main.py           # Normal launch
    python main.py --debug   # Debug mode (opens browser dev tools)

Requirements:
    - Python 3.8+
    - PyWebView 4.0+
    - Wand (ImageMagick Python binding)
    - ImageMagick must be installed on the system
"""

import os
import sys
import argparse
import webview

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.api import Api


def get_ui_path() -> str:
    """
    Get the path to the UI directory.
    
    Handles both development (running from source) and packaged (PyInstaller) scenarios.
    """
    # When packaged with PyInstaller, files are in _MEIPASS
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = PROJECT_ROOT
    
    return os.path.join(base_path, 'ui')


def check_dependencies() -> list:
    """
    Check if all required dependencies are available.
    
    Returns:
        List of error messages (empty if all dependencies are OK)
    """
    errors = []
    
    # Check PyWebView
    try:
        import webview
    except ImportError:
        errors.append("PyWebView is not installed. Run: pip install pywebview")
    
    # Check Wand (ImageMagick binding)
    try:
        from wand.image import Image
        # Try to create a small test image to verify ImageMagick is working
        with Image(width=1, height=1, background='white') as img:
            pass
    except ImportError:
        errors.append("Wand is not installed. Run: pip install wand")
    except Exception as e:
        if 'MagickWand' in str(e) or 'DLL' in str(e) or 'library' in str(e).lower():
            errors.append(
                "ImageMagick is not installed or not properly configured.\n"
                "  Windows: Download from https://imagemagick.org/script/download.php\n"
                "           Check 'Install development headers and libraries' during installation\n"
                "  macOS: brew install imagemagick\n"
                "  Linux: sudo apt-get install libmagickwand-dev"
            )
        else:
            errors.append(f"Wand/ImageMagick error: {e}")
    
    return errors


def create_error_html(errors: list) -> str:
    """Create an HTML page displaying dependency errors."""
    error_items = '\n'.join(f'<li><pre>{error}</pre></li>' for error in errors)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>RKC Photography - Error</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: #1a1a1a;
                color: #f5f5f5;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            .error-box {{
                max-width: 600px;
                background: #2a2a2a;
                border: 1px solid #f87171;
                border-radius: 12px;
                padding: 32px;
            }}
            h1 {{
                color: #f87171;
                margin-top: 0;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 16px;
            }}
            pre {{
                background: #1a1a1a;
                padding: 12px;
                border-radius: 6px;
                overflow-x: auto;
                white-space: pre-wrap;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h1>⚠️ Missing Dependencies</h1>
            <p>The following dependencies are required but not properly installed:</p>
            <ul>{error_items}</ul>
            <p>Please install the missing dependencies and restart the application.</p>
        </div>
    </body>
    </html>
    """


def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='RKC Photography - Image Processing Application')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Check dependencies first
    dependency_errors = check_dependencies()
    
    if dependency_errors:
        # Show error window if dependencies are missing
        print("ERROR: Missing dependencies:")
        for error in dependency_errors:
            print(f"  - {error}")
        print("\nShowing error dialog...")
        
        window = webview.create_window(
            title='RKC Photography - Error',
            html=create_error_html(dependency_errors),
            width=700,
            height=500,
            resizable=True
        )
        webview.start(debug=True)
        sys.exit(1)
    
    # Get UI path
    ui_path = get_ui_path()
    index_html = os.path.join(ui_path, 'index.html')
    
    if not os.path.exists(index_html):
        print(f"ERROR: UI files not found at {ui_path}")
        print("Make sure the 'ui' folder exists and contains index.html")
        sys.exit(1)
    
    # Create API instance
    api = Api()
    
    # Create the main window
    window = webview.create_window(
        title='RKC Photography',
        url=index_html,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
        text_select=False,
        background_color='#0d0d0d'  # Match app background
    )
    
    # Set window reference in API for callbacks
    api.set_window(window)
    
    # Start the application
    # Use Qt backend on Windows to avoid pythonnet dependency issues with newer Python versions
    # Other options: 'edgechromium', 'cef', 'mshtml', 'qt' (auto-detected)
    webview.start(debug=args.debug, gui='qt')


if __name__ == '__main__':
    main()

