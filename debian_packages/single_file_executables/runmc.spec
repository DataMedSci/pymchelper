import os

from my_pyinstaller_utils import *

a = Analysis([os.path.join('pymchelper', 'utils', 'runmc.py')],
             pathex=['.'],
             binaries=[],
             datas=[(os.path.join('pymchelper','VERSION'), 'pymchelper')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['scipy'],  # remove unwanted scipy, pytrip98 depends partially on it, but its not needed for our purposes
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

# remove unwanted large files
a.binaries = TOC([item for item in a.binaries if not item[0].startswith('mpl-data')])
a.datas = TOC([item for item in a.datas if not item[0].startswith('mpl-data')])

# debugging printouts
print_header("BINARIES")
print_tuple_size(a.binaries)

# debugging printouts
print_header("DATAS")
print_tuple_size(a.datas)


pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# debugging printouts
print_header("PYZ")
print_tuple_size(pyz.toc)


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='runmc',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)


# debugging printouts
print_header("EXE")
print_tuple_size(exe.toc)
