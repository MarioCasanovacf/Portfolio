"""Property tests for the dihedral-angle geometry behind the Ramachandran plot.

The invariant under test is exactness against hand-constructed geometries whose
torsion angle is known analytically, plus the range guarantee of atan2. These pin
the vector-calculus implementation without depending on any PDB file.
"""

from __future__ import annotations

import numpy as np
import pytest

from ramachandran import build_ramachandran, compute_dihedral

# Each case places the central bond p1->p2 along +x and orients the outer bonds so
# the signed torsion is known by construction.
KNOWN_GEOMETRIES = [
    # (p0, p1, p2, p3, expected_degrees)
    ([0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], 0.0),    # cis, planar
    ([0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, -1.0, 0.0], 180.0),  # trans, planar
    ([0.0, -1.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 1.0], 90.0),   # +90 out of plane
    ([0.0, -1.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, -1.0], -90.0),  # -90 out of plane
]


@pytest.mark.unit
@pytest.mark.parametrize("p0, p1, p2, p3, expected", KNOWN_GEOMETRIES)
def test_dihedral_matches_known_geometry(p0, p1, p2, p3, expected) -> None:
    angle = compute_dihedral(np.array(p0), np.array(p1), np.array(p2), np.array(p3))
    # 180 and -180 are the same physical angle; compare on the circle.
    diff = abs((angle - expected + 180.0) % 360.0 - 180.0)
    assert diff < 1e-9, f"expected {expected}deg, got {angle}deg"


@pytest.mark.unit
def test_dihedral_is_invariant_under_reversal() -> None:
    """The torsion around p1-p2 equals the torsion around p2-p1: reversing the
    four-atom order returns the same signed angle (IUPAC convention)."""
    p0 = np.array([0.0, -1.0, 0.0])
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([1.0, 0.0, 0.0])
    p3 = np.array([1.0, 0.0, 1.0])
    forward = compute_dihedral(p0, p1, p2, p3)
    reverse = compute_dihedral(p3, p2, p1, p0)
    assert np.isclose(forward, reverse, atol=1e-9)


@pytest.mark.unit
def test_dihedral_output_is_in_principal_range() -> None:
    rng = np.random.default_rng(0)
    for _ in range(200):
        pts = rng.uniform(-5.0, 5.0, size=(4, 3))
        angle = compute_dihedral(*pts)
        assert -180.0 <= angle <= 180.0


@pytest.mark.unit
def test_build_ramachandran_wires_correct_atom_quartets() -> None:
    """build_ramachandran must feed phi = dihedral(C_prev, N, CA, C) and
    psi = dihedral(N, CA, C, N_next). Verified against direct compute_dihedral calls,
    so an atom-wiring bug (axis swap, wrong neighbour) would be caught."""
    import pandas as pd

    rng = np.random.default_rng(1)
    coords = {}
    rows = []
    for res in (1, 2, 3):
        for atom in ('N', 'CA', 'C'):
            c = rng.uniform(-10.0, 10.0, size=3)
            coords[(res, atom)] = c
            rows.append({'Residue': res, 'Name': 'ALA', 'Atom': atom, 'Coors': c})
    df = pd.DataFrame(rows)

    phis, psis = build_ramachandran(df)
    assert len(phis) == 1 and len(psis) == 1  # only residue 2 has full neighbouring bonds

    expected_phi = compute_dihedral(coords[(1, 'C')], coords[(2, 'N')], coords[(2, 'CA')], coords[(2, 'C')])
    expected_psi = compute_dihedral(coords[(2, 'N')], coords[(2, 'CA')], coords[(2, 'C')], coords[(3, 'N')])
    assert np.isclose(phis[0], expected_phi, atol=1e-9)
    assert np.isclose(psis[0], expected_psi, atol=1e-9)
