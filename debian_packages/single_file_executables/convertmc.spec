import glob
import os
import shutil

import matplotlib

# helper tools to print list of binary and data files sorted by their size in bytes
from my_pyinstaller_utils import *

# to test run dist/convertmc image tests/res/shieldhit/generated/single/cyl/en_xy_al.bdo

# extract two libraries from Pillow (PIL fork) library, which is used by matplotlib to generate PNG files
# these files may be present in the user filesystem (i.e. via `libpng16-16` package on Debian) resulting in a version conflict
# we will copy these files to the main directory of our executable bundle, so they will take precence over system files

# extract these libraries from Pillow storage
for filename in glob.glob('/opt/python39/lib/python3.9/site-packages/Pillow.libs/*-*.so.*'):
    if 'libpng16' in filename:
        shutil.copy(filename, 'libpng16.so')
    if 'libz' in filename:
        shutil.copy(filename, 'libz.so.1')

a = Analysis([os.path.join('pymchelper', 'run.py')],
             pathex=['.'],
             binaries=[],
             datas=[ # pair of strings: location in system now, the name of the folder to contain the files at run-time.
                 (os.path.join('pymchelper','VERSION'), 'pymchelper'),
                 ('libpng16.so', '.'),  # libraries needed by Pillow
                 ('libz.so.1', '.'),
                 (matplotlib.matplotlib_fname(), 'matplotlib/mpl-data')  # add matplotlibrc file
                 ],
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
    if item[0].startswith('mpl-data'):
        return False
    return True

a.binaries = TOC([item for item in a.binaries if is_wanted_file(item)])
a.datas = TOC([item for item in a.datas if is_wanted_file(item)])

# debugging printouts
print_header("BINARIES")
print_tuple_size(a.binaries, max_items=20)

# debugging printouts
print_header("DATAS")
print_tuple_size(a.datas, max_items=20)


pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# debugging printouts
print_header("PYZ")
print_tuple_size(pyz.toc, max_items=20)


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
print_tuple_size(exe.toc, max_items=20)
