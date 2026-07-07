"""Spatial autocorrelation diagnostics for model residuals.

The one dependency this project would otherwise reach for here (`esda`/`libpysal`,
the standard implementation of Moran's I) is not installed in the shared venv and
this project does not get to add it unilaterally. Global Moran's I over a k-nearest-
neighbor spatial weight matrix is a handful of lines of linear algebra, so it is
implemented directly here — used by both the notebook and `tests/unit/test_pipeline.py`,
so the number reported in the notebook is exercised by the same code the test suite
checks against a case with a known answer.

Reference: Moran, P.A.P. (1950), "Notes on Continuous Stochastic Phenomena",
Biometrika 37(1/2). The KNN-weights + permutation-inference approach here follows
the standard treatment in Anselin (1995) / the `esda` package's `Moran` class,
without depending on it.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from sklearn.neighbors import NearestNeighbors


def _knn_row_standardized_weights(lat: np.ndarray, lon: np.ndarray, k: int) -> sp.csr_matrix:
    """Build an n x n row-standardized SPARSE spatial weight matrix from the k
    nearest neighbors of each point in (lat, lon) space. Row-standardized means
    each row sums to 1, so S0 (the sum of all weights) equals n. Sparse because a
    dense n x n matrix is infeasible for a test fold of a few thousand houses
    (and outright impossible for the full 21,613-row dataset): with only k
    nonzeros per row, memory and the permutation loop below both scale as O(n*k)
    instead of O(n^2)."""
    coords = np.column_stack([lat, lon])
    n = len(coords)
    nn = NearestNeighbors(n_neighbors=k + 1).fit(coords)  # +1: a point is its own nearest neighbor
    _, idx = nn.kneighbors(coords)
    neighbors = idx[:, 1:]  # drop self, shape (n, k)
    rows = np.repeat(np.arange(n), k)
    cols = neighbors.ravel()
    data = np.full(n * k, 1.0 / k)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))


def morans_i(
    values: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    k: int = 8,
    n_permutations: int = 999,
    random_state: int = 0,
) -> tuple[float, float]:
    """Global Moran's I for `values` (typically model residuals) over a k-nearest-
    neighbor spatial weight matrix on (lat, lon).

    Returns (I, p_value). The p-value is permutation-based (Monte Carlo, following
    the standard practice in spatial statistics rather than the asymptotic normal
    approximation, which is less reliable for irregular KNN weight structures):
    values are shuffled across locations `n_permutations` times, holding the
    weight matrix fixed, and the p-value is the two-sided fraction of permuted I
    values at least as extreme as the observed one.

    I > 0 with a small p-value means nearby points have similar residuals more
    often than chance — i.e., the model has left spatially structured signal on
    the table. I near 0 means residuals look spatially random, which is the
    result a well-specified model's residuals should give.
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    W = _knn_row_standardized_weights(np.asarray(lat), np.asarray(lon), k)

    def _compute_i(z: np.ndarray) -> float:
        z_centered = z - z.mean()
        numerator = z_centered @ W @ z_centered
        denominator = (z_centered**2).sum()
        return (n / W.sum()) * numerator / denominator

    observed_i = _compute_i(x)

    rng = np.random.default_rng(random_state)
    permuted_i = np.empty(n_permutations)
    for p in range(n_permutations):
        permuted_i[p] = _compute_i(rng.permutation(x))

    p_value = (np.sum(np.abs(permuted_i) >= abs(observed_i)) + 1) / (n_permutations + 1)
    return float(observed_i), float(p_value)
