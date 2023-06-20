"""Shared types for the executor module."""

# path-like type hint which supports both strings and Path objects
import os
from pathlib import Path


PathLike = str | bytes | Path | os.PathLike
