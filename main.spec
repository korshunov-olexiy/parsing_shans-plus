# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['d:\\WORK1\\parsing_shans-plus'],
             binaries=[],
             datas=[('c:\\Users\\<set_to_username_here>\\AppData\\Roaming\\Python\\Python39\\site-packages\\pyppeteer-0.2.5.dist-info\\', 'pyppeteer-0.2.5.dist-info\\')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['build_exe.cmd','parsing_shans-plus.iss','config.ini'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='parsing_shans-plus.exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=None,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='main.ico' )
