"""Optional dependency shims to avoid duplicate try-import blocks.

This centralizes optional imports (aiohttp, geopy) so that modules can simply
import the resolved symbols and keep pylint from flagging duplicate-code.
"""
from __future__ import annotations

try:  # pylint: disable=unused-import
    import aiohttp  # type: ignore
except ImportError:  # pragma: no cover
    aiohttp = None  # type: ignore

try:  # pylint: disable=unused-import
    from geopy.exc import GeocoderServiceError, GeocoderTimedOut  # type: ignore
    from geopy.geocoders import Nominatim  # type: ignore
except ImportError:  # pragma: no cover
    GeocoderServiceError = GeocoderTimedOut = Exception  # type: ignore
    Nominatim = None  # type: ignore

__all__ = [
    "aiohttp",
    "Nominatim",
    "GeocoderServiceError",
    "GeocoderTimedOut",
]
