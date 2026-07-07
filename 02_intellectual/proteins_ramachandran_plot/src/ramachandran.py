"""Backbone parsing and dihedral (phi/psi) geometry for the Ramachandran plot.

Pure vector-calculus implementation: no chemistry packages. The torsion angle is
computed from atomic coordinates via cross products and a two-argument arctangent,
exactly as derived in ``notebooks/01_Ramachandran_Plot_Generator.ipynb``. The
notebook imports these functions so the plotted angles and the tested angles come
from a single source of truth.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def extract_backbone(filepath: str) -> pd.DataFrame:
    """Parse the backbone N / CA / C atoms from a PDB file.

    Only the three repetitive backbone atoms that define the phi/psi torsion
    planes are kept; everything else in the structure is ignored.
    """
    atoms = []
    with open(filepath) as f:
        for line in f:
            if line.startswith('ATOM'):
                atom_name = line[12:16].strip()
                if atom_name in ['N', 'CA', 'C']:
                    res_num = int(line[22:26].strip())
                    res_name = line[17:20].strip()
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])

                    atoms.append({
                        'Residue': res_num,
                        'Name': res_name,
                        'Atom': atom_name,
                        'Coors': np.array([x, y, z])
                    })
    return pd.DataFrame(atoms)


def compute_dihedral(p0, p1, p2, p3) -> float:
    """Signed torsion angle (degrees) of the four points p0-p1-p2-p3.

    Pure geometric determinism: the angle between the plane spanned by the first
    two bond vectors and the plane spanned by the last two, signed via atan2.
    """
    b1 = p1 - p0
    b2 = p2 - p1
    b3 = p3 - p2

    n1 = np.cross(b1, b2)  # Normal vector of the first plane
    n2 = np.cross(b2, b3)  # Normal vector of the second plane

    # Orthogonal projections for the directional arctan (atan2)
    m1 = np.cross(n1, b2 / np.linalg.norm(b2))

    x = np.dot(n1, n2)
    y = np.dot(m1, n2)

    return np.degrees(np.arctan2(y, x))


def build_ramachandran(df: pd.DataFrame) -> tuple[list[float], list[float]]:
    """Walk the residue sequence and measure the phi/psi pair at each interior residue.

    Phi uses (C_prev, N, CA, C); psi uses (N, CA, C, N_next). The first and last
    residues are skipped because they lack a full set of neighbouring atoms.
    """
    phi_angles = []
    psi_angles = []

    # Residues change sequentially.
    residues = df['Residue'].unique()

    for i in range(1, len(residues) - 1):  # Exclude first and last to have full bonds
        r_prev = residues[i - 1]
        r_curr = residues[i]
        r_next = residues[i + 1]

        try:
            # Phi Coordinates (C_prev, N, CA, C)
            C_prev = df[(df.Residue == r_prev) & (df.Atom == 'C')]['Coors'].values[0]
            N_curr = df[(df.Residue == r_curr) & (df.Atom == 'N')]['Coors'].values[0]
            CA_curr = df[(df.Residue == r_curr) & (df.Atom == 'CA')]['Coors'].values[0]
            C_curr = df[(df.Residue == r_curr) & (df.Atom == 'C')]['Coors'].values[0]

            # Psi Coordinates (N, CA, C, N_next)
            N_next = df[(df.Residue == r_next) & (df.Atom == 'N')]['Coors'].values[0]

            # Algebra
            phi = compute_dihedral(C_prev, N_curr, CA_curr, C_curr)
            psi = compute_dihedral(N_curr, CA_curr, C_curr, N_next)

            phi_angles.append(phi)
            psi_angles.append(psi)
        except AttributeError:  # Padding for missing residues
            continue

    return phi_angles, psi_angles
