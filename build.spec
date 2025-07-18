# build.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('F1stream_logo.png', '.'), ('F1stream_logo.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

exe = EXE(
    a.pure,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='VMManagerGCP',
    icon='F1stream_logo.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    clean=True,
    onefile=True
)
