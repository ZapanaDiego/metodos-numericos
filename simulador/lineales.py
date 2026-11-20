"""Sistemas lineales: LU, Thomas, Jacobi y Gauss-Seidel (Unidad II)."""

from __future__ import annotations

import numpy as np


def lu_solve(A, b, pivot: bool = True):
    """Resuelve ``A x = b`` por eliminación LU con pivoteo parcial opcional."""
    A = np.asarray(A, dtype=float).copy()
    b = np.asarray(b, dtype=float).copy()
    n = A.shape[0]
    if A.shape != (n, n) or b.size != n:
        raise ValueError("Dimensiones incompatibles.")
    for k in range(n):
        if pivot:
            p = k + int(np.argmax(np.abs(A[k:, k])))
            if abs(A[p, k]) < 1e-15:
                raise np.linalg.LinAlgError("Matriz singular")
            if p != k:
                A[[k, p]] = A[[p, k]]
                b[[k, p]] = b[[p, k]]
        elif abs(A[k, k]) < 1e-15:
            raise np.linalg.LinAlgError("Pivote cero; active el pivoteo")
        for i in range(k + 1, n):
            factor = A[i, k] / A[k, k]
            A[i, k] = factor
            A[i, k + 1 :] -= factor * A[k, k + 1 :]
            b[i] -= factor * b[k]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (b[i] - A[i, i + 1 :] @ x[i + 1 :]) / A[i, i]
    return x


def thomas(a, b, c, d):
    """Sistema tridiagonal: ``a`` subdiagonal, ``b`` diagonal, ``c`` superdiagonal."""
    a = np.asarray(a, dtype=float).copy()
    b = np.asarray(b, dtype=float).copy()
    c = np.asarray(c, dtype=float).copy()
    d = np.asarray(d, dtype=float).copy()
    n = b.size
    if a.size != n or c.size != n:
        raise ValueError("a, b y c deben tener el mismo tamaño.")
    cp = np.empty(n)
    dp = np.empty(n)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        if abs(m) < 1e-15:
            raise np.linalg.LinAlgError("Pivote nulo en Thomas")
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.empty(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def es_diagonalmente_dominante(A) -> bool:
    A = np.asarray(A, dtype=float)
    diag = np.abs(np.diag(A))
    resto = np.sum(np.abs(A), axis=1) - diag
    return bool(np.all(diag >= resto))


def jacobi(A, b, x0=None, tol: float = 1e-10, max_iter: int = 500):
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    n = A.shape[0]
    x = np.zeros(n) if x0 is None else np.asarray(x0, dtype=float).copy()
    if np.any(np.abs(np.diag(A)) < 1e-15):
        raise np.linalg.LinAlgError("Diagonal nula en Jacobi")
    D = np.diag(A)
    R = A - np.diag(D)
    historial = []
    for it in range(1, max_iter + 1):
        x_new = (b - R @ x) / D
        err = np.linalg.norm(x_new - x, ord=np.inf)
        historial.append(err)
        if err <= tol:
            return x_new, it, historial
        x = x_new
    raise RuntimeError("Jacobi no convergió")


def gauss_seidel(A, b, x0=None, tol: float = 1e-10, max_iter: int = 500):
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    n = A.shape[0]
    x = np.zeros(n) if x0 is None else np.asarray(x0, dtype=float).copy()
    if np.any(np.abs(np.diag(A)) < 1e-15):
        raise np.linalg.LinAlgError("Diagonal nula en Gauss-Seidel")
    historial = []
    for it in range(1, max_iter + 1):
        x_old = x.copy()
        for i in range(n):
            s = b[i] - A[i, :i] @ x[:i] - A[i, i + 1 :] @ x[i + 1 :]
            x[i] = s / A[i, i]
        err = np.linalg.norm(x - x_old, ord=np.inf)
        historial.append(err)
        if err <= tol:
            return x, it, historial
    raise RuntimeError("Gauss-Seidel no convergió")


def residual(A, x, b) -> float:
    return float(np.linalg.norm(np.asarray(A) @ np.asarray(x) - np.asarray(b)))


def radio_espectral_jacobi(A) -> float:
    A = np.asarray(A, dtype=float)
    D = np.diag(np.diag(A))
    R = A - D
    M = -np.linalg.solve(D, R)
    return float(np.max(np.abs(np.linalg.eigvals(M))))


def operaciones_lu(n: int) -> int:
    return int(2 * n**3 / 3)


def operaciones_thomas(n: int) -> int:
    return int(8 * n)
