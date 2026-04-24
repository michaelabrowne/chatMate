# -*- mode: python ; coding: utf-8 -*-
# Windows build — no BUNDLE section, produces an onedir .exe

a = Analysis(
    ["main.py"],
    pathex=[],
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=None,
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
