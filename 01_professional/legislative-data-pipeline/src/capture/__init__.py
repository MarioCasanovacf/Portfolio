"""Data capture modules for Mexican legislative sources.

Note: the legacy `capture.diputados.DiputadosScraper` (wrong SITL URLs, no
per-deputy vote capture) was retired 2026-07-05 per the T-106 ingestion fix
spec (research/ingestion_fix_spec.md). The live per-deputy capture path is
`capture.sitl.SitlScraper`.
"""

from capture.dipmex import DipMexClient
from capture.base import BaseScraper

__all__ = ["BaseScraper", "DipMexClient"]
