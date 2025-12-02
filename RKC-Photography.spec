# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for RKC Photography

Build with:
    pyinstaller RKC-Photography.spec

The output will be in dist/RKC Photography/
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),  # Include UI assets
    ],
    hiddenimports=[
        'wand',
        'wand.image',
        'wand.color',
        'wand.drawing',
        'wand.exceptions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

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
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment and set icon path if you have an icon:
    # icon='icon.ico',  # Windows
    # icon='icon.icns', # macOS
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

# macOS-specific: Create an app bundle
# Uncomment the following for macOS .app bundle:
# app = BUNDLE(
#     coll,
#     name='RKC Photography.app',
#     icon='icon.icns',
#     bundle_identifier='com.rkc.photography',
#     info_plist={
#         'NSHighResolutionCapable': True,
#         'CFBundleShortVersionString': '1.0.0',
#     },
# )

