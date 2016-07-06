# -*- mode: python -*-

block_cipher = None

# run pyinstaller bdo2txt.spec --onefile

a = Analysis(['pymchelper/bdo2txt.py'],
             pathex=['.'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

def print_size(inp):
    sorted_by_size = sorted(inp, key=lambda x: os.path.getsize(x[1]))
    for x in sorted_by_size:
        print(os.path.getsize(x[1])/1000000.0,x[0])
    print("total size", sum( os.path.getsize(x[1])/1000000.0 for x in sorted_by_size ) )

# libtiff.5.dylib','numpy.random.mtrand','_decimal','libjpeg.9.dylib

a.pure = [x for x in a.pure if not x[0].startswith("libpng")]
a.pure = [x for x in a.pure if not x[0].startswith("_codecs_jp")]
a.pure = [x for x in a.pure if not x[0].startswith("_codecs_hk")]
a.pure = [x for x in a.pure if not x[0].startswith("_codecs_cn")]
a.pure = [x for x in a.pure if not x[0].startswith("_codecs_kr")]
a.pure = [x for x in a.pure if not x[0].startswith("_ssl")]
a.pure = [x for x in a.pure if not x[0].startswith("_codecs_tw")]
a.pure = [x for x in a.pure if not x[0].startswith("_curses")]
a.pure = [x for x in a.pure if not x[0].startswith("_socket")]
a.pure = [x for x in a.pure if not x[0].startswith("_json")]
a.pure = [x for x in a.pure if not x[0].startswith("_tkinter")]


a.binaries = [x for x in a.binaries if not x[0].startswith("libjpeg")]
a.binaries = [x for x in a.binaries if not x[0].startswith("matplotlib.backends._macosx")]
a.binaries = [x for x in a.binaries if not x[0].startswith("_decimal")]
a.binaries = [x for x in a.binaries if not x[0].startswith("libwebp")]
a.binaries = [x for x in a.binaries if not x[0].startswith("libtiff")]
a.binaries = [x for x in a.binaries if not x[0].startswith("libncursesw")]
a.binaries = [x for x in a.binaries if not x[0].startswith("pyexpat")]
a.binaries = [x for x in a.binaries if not x[0].startswith("numpy.random.mtrand")]
a.binaries = [x for x in a.binaries if not x[0].startswith("numpy.random.mtrand")]

a.datas = [x for x in a.datas if not x[0].startswith("mpl-data/sample_data")]
a.datas = [x for x in a.datas if not x[0].startswith("mpl-data/images")]
a.datas = [x for x in a.datas if not x[0].startswith("mpl-data/sample_data")]
a.datas = [x for x in a.datas if not x[0].startswith("mpl-data/sample_data")]

#print("total size", sum( os.path.getsize(x[1])/1000000.0 for x in newb ) )

print("------ pure")
print_size(a.pure)

print("------ binaries")
print_size(a.binaries)

print("------ zipped_data")
print_size(a.zipped_data)

print("------ scripts")
print_size(a.scripts)

print("------ zipfiles")
print_size(a.zipfiles)

print("------ datas")
print_size(a.datas)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='bdo2txt',
          debug=False,
          strip=False,
          upx=True,
          console=True )
