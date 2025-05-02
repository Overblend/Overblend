# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['home.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\decord.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\avcodec-58.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\avdevice-58.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\avfilter-7.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\avformat-58.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\avutil-56.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\msvcp140.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\postproc-55.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\swresample-3.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\swscale-5.dll', 'decord'), ('C:\\Users\\leman\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\decord\\vcruntime140.dll', 'decord')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow'],
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
    name='home',
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
    icon=['icons\\icon.ico'],
)
