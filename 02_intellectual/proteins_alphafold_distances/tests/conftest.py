"""Shared pytest fixtures for proteins_alphafold_distances."""

import sys
from pathlib import Path

# Allow tests to import the flat src/ module without a full package install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
