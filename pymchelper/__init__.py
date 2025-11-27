# Version is resolved dynamically from installed metadata; no hardcoded stamping.
try:
    import pymchelper._version as v
    __version__ = v.version
except ImportError:
    __version__ = "0.0.0"  # Fallback version