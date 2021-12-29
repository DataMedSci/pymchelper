import os

from my_pyinstaller_utils import *

a = Analysis([os.path.join('pymchelper', 'run.py')],
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
def is_wanted_file(item):
    '''Return True if the item is related to the file we want to include'''
    if 'mpl-data/matplotlibrc' in item[1]:
        return True
    if item[0].startswith('mpl-data'):
        return False
    return True
a.binaries = TOC([item for item in a.binaries if is_wanted_file(item)])
a.datas = TOC([item for item in a.datas if is_wanted_file(item)])

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
          name='convertmc',
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
