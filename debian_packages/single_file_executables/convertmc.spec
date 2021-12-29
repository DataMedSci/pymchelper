import os

from my_pyinstaller_utils import *

# following https://github.com/FCS-analysis/PyCorrFit/blob/master/freeze_pyinstaller/PyCorrFit_win7.spec
# patch matplotlib rc file to include only one backend which results in smaller size of generated files
import matplotlib
mplrc = matplotlib.matplotlib_fname()
print("rcfile", mplrc)
with open(mplrc) as fd:
    data = fd.readlines()
    print("data", data)
for ii, l in enumerate(data):
    if l.strip().startswith("backend "):
        print("adding data")
        data[ii] = "backend : agg\n"
with open(mplrc, "w") as fd:
    fd.writelines(data)

a = Analysis([os.path.join('pymchelper', 'run.py')],
             pathex=['.'],
             binaries=[],
             datas=[ # pair of strings: location in system now, the name of the folder to contain the files at run-time.
                 (os.path.join('pymchelper','VERSION'), 'pymchelper'),
                 (mplrc, 'matplotlib/mpl-data')
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
    if item[1] == 'matplotlibrc':
        return True
    if item[0].startswith('mpl-data'):
        return False
    return True

# debugging printouts
print_header("OLD BINARIES")
print_tuple_size(a.binaries, max_items=-1)

# debugging printouts
print_header("OLD DATAS")
print_tuple_size(a.datas, max_items=-1)

a.binaries = TOC([item for item in a.binaries if is_wanted_file(item)])
a.datas = TOC([item for item in a.datas if is_wanted_file(item)])


# debugging printouts
print_header("BINARIES")
print_tuple_size(a.binaries, max_items=-1)

# debugging printouts
print_header("DATAS")
print_tuple_size(a.datas, max_items=-1)


pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# debugging printouts
print_header("PYZ")
print_tuple_size(pyz.toc, max_items=-1)


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
print_tuple_size(exe.toc, max_items=-1)
