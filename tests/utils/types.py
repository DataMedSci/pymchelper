"""Shared helper types used in tests."""
from typing import Generator, TypeVar

T = TypeVar("T")

YieldFixture = Generator[T, None, None]
