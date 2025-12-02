# RKC Photography

A desktop application for batch image processing with border and watermark support. Built with Python, PyWebView, and ImageMagick.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Batch Processing**: Process hundreds of images at once
- **Border Addition**: Add solid color borders with customizable thickness and color
- **Watermark Overlay**: Add watermark images with adjustable opacity, scale, and position
- **Preview**: Test settings on a sample image before processing
- **Progress Tracking**: Real-time progress with file counts and error reporting
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Screenshots

The application features a modern dark theme with an intuitive three-panel interface:

1. **Settings**: Configure folders, border, watermark, and filename options
2. **Preview**: Test your settings on a sample image
3. **Process**: Start batch processing with progress tracking

## Requirements

### System Requirements

- **Python 3.8 or higher**
- **ImageMagick** (must be installed on your system)

### Installing ImageMagick

**Windows:**
1. Download from https://imagemagick.org/script/download.php
2. During installation, **check "Install development headers and libraries for C and C++"**
3. Restart your terminal/IDE after installation

**macOS:**
```bash
brew install imagemagick
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install libmagickwand-dev
```

**Linux (Fedora):**
```bash
sudo dnf install ImageMagick-devel
```

## Installation

### Option 1: Install from Source

1. **Clone or download this repository:**
   ```bash
   git clone <repository-url>
   cd RKC-Photography
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   > **Note for Python 3.13+**: The requirements use PyQt6 as the WebView backend, which works better with newer Python versions than the default pythonnet backend.

4. **Run the application:**
   ```bash
   python main.py
   ```

### Option 2: Pre-built Executable

If available, download the pre-built executable for your platform from the Releases page. No Python installation required.

## Usage

### Graphical Interface

1. **Launch the application:**
   ```bash
   python main.py
   ```

2. **Configure Settings:**
   - Select an **Input Folder** containing your images
   - Select an **Output Folder** for processed images
   - Configure **Border** settings (thickness, color)
   - Configure **Watermark** settings (image, position, opacity, scale)
   - Optionally set filename prefix/suffix

3. **Preview (Optional):**
   - Switch to the Preview tab
   - Select a sample image
   - View how your settings will look

4. **Process:**
   - Switch to the Process tab
   - Review the summary
   - Click "Start Processing"
   - Monitor progress and view results

### Command Line (Testing/Automation)

A CLI test script is included for testing or automation:

```bash
# Create test images (requires ImageMagick/Wand)
python test_cli.py --create-test ./test_data

# Process with border only
python test_cli.py --input ./input --output ./output --border 20 --border-color "#FFFFFF"

# Process with watermark
python test_cli.py --input ./input --output ./output --watermark ./logo.png --wm-position center

# Process single image
python test_cli.py --single ./photo.jpg --output ./processed.jpg --border 10

# Full help
python test_cli.py --help
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WebP (.webp)

## Configuration Options

### Border Settings
| Option | Description | Default |
|--------|-------------|---------|
| Thickness | Border width in pixels | 0 (disabled) |
| Color | Border color (hex or name) | #FFFFFF (white) |

### Watermark Settings
| Option | Description | Default |
|--------|-------------|---------|
| Image | Path to watermark image | None |
| Position | "center" or "bottom-right" | center |
| Opacity | 0.0 (transparent) to 1.0 (opaque) | 0.5 |
| Scale | Size as % of image smaller dimension | 25% |
| Margin | Pixels from edge (for bottom-right) | 20 |

### Filename Options
| Option | Description | Default |
|--------|-------------|---------|
| Prefix | Text to add before filename | "" |
| Suffix | Text to add after filename (before extension) | "" |
| Overwrite | Overwrite existing files in output | false |

## Building a Standalone Executable

You can create a standalone executable that doesn't require Python to be installed:

### Using PyInstaller

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Create the executable:**
   ```bash
   # Windows
   pyinstaller --name "RKC Photography" --windowed --icon=icon.ico --add-data "ui;ui" main.py
   
   # macOS
   pyinstaller --name "RKC Photography" --windowed --icon=icon.icns --add-data "ui:ui" main.py
   
   # Linux
   pyinstaller --name "RKC Photography" --windowed --add-data "ui:ui" main.py
   ```

3. **Find the executable:**
   - The executable will be in `dist/RKC Photography/`
   - On Windows: `dist/RKC Photography/RKC Photography.exe`
   - On macOS: `dist/RKC Photography.app`

### PyInstaller Spec File (Advanced)

For more control, create a `RKC-Photography.spec` file:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui', 'ui')],
    hiddenimports=['wand', 'wand.image', 'wand.color', 'wand.drawing'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RKC Photography',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RKC Photography',
)
```

Then build with:
```bash
pyinstaller RKC-Photography.spec
```

**Note:** ImageMagick must still be installed on the target system, as the Wand library requires the ImageMagick DLLs/libraries at runtime.

## Project Structure

```
RKC-Photography/
├── main.py                 # Application entry point
├── test_cli.py             # CLI for testing Phase 1 logic
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── src/
│   ├── __init__.py         # Package init
│   ├── image_processor.py  # Core image processing (border, watermark)
│   ├── batch_processor.py  # Batch processing with progress
│   ├── config.py           # Configuration loading/saving
│   └── api.py              # PyWebView API bridge
└── ui/
    ├── index.html          # Main UI structure
    ├── styles.css          # Styling (dark theme)
    └── app.js              # Frontend JavaScript
```

## Architecture

### Phase 1: Core Logic (Backend)

- **image_processor.py**: Low-level image operations using Wand (ImageMagick binding)
- **batch_processor.py**: Iterator over folders, progress tracking, error collection
- **config.py**: Persistent settings storage (JSON in user's app data directory)

### Phase 2: User Interface (Frontend)

- **PyWebView**: Renders HTML/CSS/JS in a native desktop window
- **api.py**: Exposes Python functions to JavaScript via `window.pywebview.api`
- **ui/**: Static HTML/CSS/JS assets for the interface

### Design Decisions

1. **Wand over subprocess**: Using the Wand library instead of calling ImageMagick CLI provides better error handling, memory management, and a more Pythonic API.

2. **PyWebView over HTTP**: Using PyWebView's native JS-Python bridge instead of a local HTTP server simplifies the architecture and avoids port conflicts.

3. **One-by-one processing**: Images are processed sequentially to minimize memory usage, especially important for large batches.

4. **Threaded processing**: Batch processing runs in a background thread to keep the UI responsive.

## Troubleshooting

### "ImageMagick is not installed" Error

- **Windows**: Make sure you checked "Install development headers and libraries" during ImageMagick installation
- **Windows**: Try restarting your computer after installing ImageMagick
- **macOS/Linux**: Ensure the ImageMagick development libraries are installed, not just the CLI tools

### Window appears blank or doesn't load

- Check that the `ui/` folder exists and contains `index.html`
- Try running with debug mode: `python main.py --debug`
- Check the console for JavaScript errors

### Images not processing

- Verify the input folder contains supported image formats
- Check the output folder has write permissions
- Review the error log in the Results section

### Slow processing

- Processing speed depends on image size and your CPU
- Large images (20+ megapixels) will take longer
- SSD storage significantly improves processing speed

## Development

### Running in Debug Mode

```bash
python main.py --debug
```

This opens browser developer tools for debugging JavaScript.

### Testing Backend Logic

Use the CLI test script to verify backend functionality:

```bash
# Create test images
python test_cli.py --create-test ./test_data

# Run a test batch
python test_cli.py -i ./test_data/input -o ./test_data/output --border 20 --watermark ./test_data/watermark.png
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Credits

- [PyWebView](https://pywebview.flowrl.com/) - Lightweight cross-platform WebView
- [Wand](https://docs.wand-py.org/) - Python binding for ImageMagick
- [ImageMagick](https://imagemagick.org/) - Image manipulation library
- Fonts: [Cormorant Garamond](https://fonts.google.com/specimen/Cormorant+Garamond), [Outfit](https://fonts.google.com/specimen/Outfit) via Google Fonts
