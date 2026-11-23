# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Microsoft_Office_App_Services.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PIL._avif', 'PIL._webp', 'PIL._imagingtk', 'PIL._imagingcms', 'unittest', 'test', 'multiprocessing', 'sqlite3', 'pydoc', 'pdb', 'difflib', 'doctest', 'asyncio', 'tkinter.test', 'xml', 'xmlrpc', 'pyexpat', 'decimal', '_decimal', '_lzma', '_bz2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Microsoft Office-App-Services',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info_client.txt',
    icon=['ms_office.ico'],
)
