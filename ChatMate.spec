# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x: block_cipher / cipher= removed entirely

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("config.yaml", "."),
    ],
    hiddenimports=[
        "markdown2",
        "yaml",
        "dotenv",
        "anthropic",
        "openai",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "scipy", "PIL"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ChatMate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX is unreliable on macOS arm64
    console=False,      # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,   # Unsigned — no dev cert required
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="ChatMate",
)

app = BUNDLE(
    coll,
    name="ChatMate.app",
    icon="assets/ChatMate.icns",
    bundle_identifier="com.chatmate.app",
    info_plist={
        "CFBundleName": "ChatMate",
        "CFBundleDisplayName": "ChatMate",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,  # Supports dark mode
        "LSMinimumSystemVersion": "12.0",
    },
)
