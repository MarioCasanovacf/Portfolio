"""Data capture modules for Mexican legislative sources."""

from capture.diputados import DiputadosScraper
from capture.dipmex import DipMexClient
from capture.base import BaseScraper

__all__ = ["BaseScraper", "DiputadosScraper", "DipMexClient"]
