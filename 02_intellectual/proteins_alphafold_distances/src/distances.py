"""Alpha-carbon coordinate parsing and the CA-CA Euclidean distance matrix.

The structural fingerprint in ``notebooks/01_AlphaFold_Spatial_Distances.ipynb`` is
the N x N matrix of pairwise alpha-carbon distances. The parser and the matrix
builder live here so the heatmap and the unit tests run the same code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import distance_matrix


def parse_pdb_coordinates(filepath: str) -> pd.DataFrame:
    """Extract the alpha-carbon (CA) coordinates from a PDB file.

    Only ``ATOM`` records whose atom name is ``CA`` are kept — the one-atom-per-residue
    trace of the backbone. Non-structural metadata is ignored.
    """
    ca_atoms = []
    with open(filepath) as file:
        for line in file:
            # Coordinate records in PDB format always start with ATOM
            if line.startswith('ATOM') and line[12:16].strip() == 'CA':
                residue_num = int(line[22:26].strip())
                residue_name = line[17:20].strip()

                # Orthogonal coordinates for X, Y, Z in Angstroms
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())

                ca_atoms.append({
                    'Residue_Num': residue_num,
                    'Residue_Name': residue_name,
                    'X': x, 'Y': y, 'Z': z
                })

    return pd.DataFrame(ca_atoms)


def compute_distance_matrix(coords: np.ndarray) -> np.ndarray:
    """Return the symmetric N x N matrix of pairwise Euclidean distances.

    ``coords`` is an (N, 3) array of CA positions. The result is symmetric with a
    zero diagonal by construction.
    """
    return distance_matrix(coords, coords)
