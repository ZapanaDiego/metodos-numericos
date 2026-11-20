"""I19: sistemas lineales."""

import numpy as np
import pytest

from simulador.lineales import (
    es_diagonalmente_dominante,
    gauss_seidel,
    jacobi,
    lu_solve,
    operaciones_lu,
    operaciones_thomas,
    radio_espectral_jacobi,
    residual,
    thomas,
)


def test_lu_y_metodos_iterativos_coinciden():
    A = np.array([[4.0, -1.0, 0.0], [-1.0, 4.0, -1.0], [0.0, -1.0, 3.0]])
    b = np.array([15.0, 10.0, 10.0])
    exacta = np.linalg.solve(A, b)
    assert lu_solve(A, b) == pytest.approx(exacta, abs=1e-12)
    xj, itj, _ = jacobi(A, b, tol=1e-12)
    xg, itg, _ = gauss_seidel(A, b, tol=1e-12)
    assert xj == pytest.approx(exacta, abs=1e-10)
    assert xg == pytest.approx(exacta, abs=1e-10)
    assert itg < itj
    assert residual(A, xg, b) < 1e-9


def test_thomas_vs_lu():
    n = 50
    a = np.full(n, -1.0)
    b = np.full(n, 4.0)
    c = np.full(n, -1.0)
    a[0] = 0.0
    c[-1] = 0.0
    d = np.ones(n)
    x_t = thomas(a, b, c, d)
    A = np.diag(b) + np.diag(a[1:], -1) + np.diag(c[:-1], 1)
    x_lu = lu_solve(A, d)
    assert x_t == pytest.approx(x_lu, abs=1e-10)
    assert operaciones_thomas(n) < operaciones_lu(n)


def test_pivoteo():
    A = np.array([[0.0, 1.0], [1.0, 0.0]])
    b = np.array([2.0, 3.0])
    with pytest.raises(np.linalg.LinAlgError):
        lu_solve(A, b, pivot=False)
    assert lu_solve(A, b, pivot=True) == pytest.approx([3.0, 2.0])


def test_dominancia_y_divergencia():
    A = np.array([[1.0, 2.0], [2.0, 1.0]])
    b = np.array([1.0, 1.0])
    assert not es_diagonalmente_dominante(A)
    assert radio_espectral_jacobi(A) > 1
    with pytest.raises(RuntimeError):
        jacobi(A, b, max_iter=50)


def test_radio_espectral():
    A = np.array([[4.0, 1.0], [1.0, 3.0]])
    assert es_diagonalmente_dominante(A)
    assert radio_espectral_jacobi(A) < 1
