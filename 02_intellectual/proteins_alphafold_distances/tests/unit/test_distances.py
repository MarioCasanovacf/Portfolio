"""Property tests for the CA-CA Euclidean distance matrix.

The invariants are the defining properties of a Euclidean distance matrix: it is
symmetric, has a zero diagonal, is non-negative, and reproduces hand-computed
distances on a small fixed point set. No PDB file is needed.
"""

from __future__ import annotations

import numpy as np
import pytest

from distances import compute_distance_matrix, parse_pdb_coordinates


@pytest.mark.unit
def test_distance_matrix_is_symmetric() -> None:
    rng = np.random.default_rng(0)
    coords = rng.uniform(-50.0, 50.0, size=(40, 3))
    d = compute_distance_matrix(coords)
    assert np.allclose(d, d.T, atol=1e-12)


@pytest.mark.unit
def test_distance_matrix_has_zero_diagonal() -> None:
    rng = np.random.default_rng(1)
    coords = rng.uniform(-50.0, 50.0, size=(40, 3))
    d = compute_distance_matrix(coords)
    assert np.allclose(np.diag(d), 0.0, atol=1e-12)


@pytest.mark.unit
def test_distance_matrix_is_non_negative() -> None:
    rng = np.random.default_rng(2)
    coords = rng.uniform(-50.0, 50.0, size=(40, 3))
    d = compute_distance_matrix(coords)
    assert (d >= 0.0).all()


@pytest.mark.unit
def test_distance_matrix_matches_known_distances() -> None:
    # A 3-4-5 right triangle plus the origin: every distance is integer-checkable.
    coords = np.array([
        [0.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [0.0, 4.0, 0.0],
    ])
    d = compute_distance_matrix(coords)
    assert np.isclose(d[0, 1], 3.0)
    assert np.isclose(d[0, 2], 4.0)
    assert np.isclose(d[1, 2], 5.0)  # 3-4-5


@pytest.mark.unit
def test_distance_matrix_shape_matches_input() -> None:
    rng = np.random.default_rng(3)
    coords = rng.uniform(-1.0, 1.0, size=(17, 3))
    d = compute_distance_matrix(coords)
    assert d.shape == (17, 17)


@pytest.mark.unit
def test_parse_pdb_coordinates_keeps_only_ca_atoms(tmp_path) -> None:
    """The parser keeps ATOM records whose atom name is exactly CA — excluding other
    backbone atoms and HETATM records (e.g. a calcium ion also named 'CA')."""
    pdb = (
        "ATOM      1  N   MET A   1      26.000  25.000   2.000  1.00  0.00           N\n"
        "ATOM      2  CA  MET A   1      26.266  25.413   2.842  1.00  0.00           C\n"
        "ATOM      3  C   MET A   1      27.000  26.000   3.000  1.00  0.00           C\n"
        "ATOM      4  CA  GLN A   2      26.850  29.021   3.898  1.00  0.00           C\n"
        "HETATM   99 CA    CA B 200      99.000  99.000  99.000  1.00  0.00          CA\n"
    )
    f = tmp_path / "mini.pdb"
    f.write_text(pdb)
    df = parse_pdb_coordinates(str(f))

    assert len(df) == 2  # only the two CA ATOM records survive
    assert df['Residue_Num'].tolist() == [1, 2]
    assert df['Residue_Name'].tolist() == ['MET', 'GLN']
    # exact fixed-column slice → float, so the parser's offsets are pinned
    assert df.iloc[0][['X', 'Y', 'Z']].tolist() == [26.266, 25.413, 2.842]
