# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# bytes pretty-printing
UNITS_MAPPING = [
    (1<<50, ' PB'),
    (1<<40, ' TB'),
    (1<<30, ' GB'),
    (1<<20, ' MB'),
    (1<<10, ' KB'),
    (1, (' byte', ' bytes')),
]


def pretty_size(bytes, units=UNITS_MAPPING):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix

import os

def size_b(tuple_item):
    try:
        return os.path.getsize(tuple_item[1])
    except FileNotFoundError:
        return 0

def print_tuple_size(list_of_tuples):
    total_size = 0
    for item in sorted(list_of_tuples, key = size_b, reverse=True):
        size_to_print = pretty_size(size_b(item))
        total_size += size_b(item)
        print(f"item {item} {size_to_print}")
    total_size = pretty_size(total_size)
    print(f"total size {total_size}")

def print_header(name):
    print("-"*120)
    print(" "*60 + name)
    print("-"*120)

a = Analysis(['pymchelper/run.py'],
             pathex=['/home/ubuntu/workspace/pymchelper'],
             binaries=[],
             datas=[('pymchelper/VERSION', 'pymchelper')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['scipy', 'mpl-data/tests/res/shieldhit/executable/shieldhit'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.binaries = TOC([item for item in a.binaries if not item[0].startswith('mpl-data')])
a.datas = TOC([item for item in a.datas if not item[0].startswith('mpl-data')])

print_header("BINARIES")
print_tuple_size(a.binaries)

print_header("DATAS")
print_tuple_size(a.datas)


pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)



print_header("PYZ")
print_tuple_size(pyz.toc)


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='run',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

print_header("EXE")
print_tuple_size(exe.toc)