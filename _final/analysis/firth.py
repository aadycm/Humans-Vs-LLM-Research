import numpy as np
def firth_logit(X, y, n=None, iters=200, tol=1e-9):
    """Firth (Jeffreys-penalized) binomial logistic regression. y = successes, n = trials."""
    X = np.asarray(X, float); y = np.asarray(y, float); n = np.ones_like(y) if n is None else np.asarray(n, float)
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b)); W = n * p * (1 - p)
        I = X.T @ (X * W[:, None]); Ii = np.linalg.inv(I)
        h = W * np.einsum('ij,jk,ik->i', X, Ii, X)          # leverages
        U = X.T @ (y - n * p + h * (0.5 - p))
        step = Ii @ U; b += step
        if np.max(np.abs(step)) < tol: break
    p = 1 / (1 + np.exp(-X @ b)); W = n * p * (1 - p)
    V = np.linalg.inv(X.T @ (X * W[:, None]))
    return b, V
