"""Function library extracted verbatim from 03_diagnostics.py (two-way FE OLS with clustered CR1)."""
import numpy as np, pandas as pd
from scipy import stats
def demean2(z, cols, a='ntd_id', t='report_year', w=None, it=500):
    """Two-way within transformation by alternating projections (exact for unbalanced panels at convergence)."""
    M = z[cols].to_numpy(float).copy()
    ga = pd.factorize(z[a])[0]; gt = pd.factorize(z[t])[0]
    ww = np.ones(len(z)) if w is None else np.asarray(w, float)
    for _ in range(it):
        old = M.copy()
        for g in (ga, gt):
            sw = np.bincount(g, ww)
            for j in range(M.shape[1]):
                M[:, j] -= (np.bincount(g, ww * M[:, j]) / sw)[g]
        if np.max(np.abs(M - old)) < 1e-13:
            break
    return M


def fe_ols(z, y, xs, w=None, cr='Kincl'):
    """Two-way FE OLS (optionally weighted) with agency-clustered CR1. Returns dict for xs[0] plus full vectors."""
    z = z.replace([np.inf, -np.inf], np.nan).dropna(subset=[y, *xs]).copy()
    z = z[z.groupby('ntd_id').ntd_id.transform('size') >= 2].reset_index(drop=True)
    wv = None if w is None else z[w].to_numpy(float)
    M = demean2(z, [y, *xs], w=wv)
    Y, X = M[:, 0], M[:, 1:]
    sw = np.ones(len(z)) if wv is None else np.sqrt(wv)
    Xw, Yw = X * sw[:, None], Y * sw
    b = np.linalg.lstsq(Xw, Yw, rcond=None)[0]
    u = Yw - Xw @ b
    G = z.ntd_id.nunique(); N = len(z); Ttot = z.report_year.nunique()
    K = len(xs) + G + Ttot - 1 if cr == 'Kincl' else len(xs) + Ttot
    bread = np.linalg.inv(Xw.T @ Xw)
    codes = pd.factorize(z.ntd_id)[0]
    S = np.zeros((G, len(xs))); np.add.at(S, codes, Xw * u[:, None])
    V = bread @ S.T @ S @ bread * G / (G - 1) * (N - 1) / (N - K)
    se = np.sqrt(np.diag(V)); p = 2 * stats.t.sf(np.abs(b / se), G - 1)
    return {'b': b[0], 'se': se[0], 'p': p[0], 'N': N, 'G': G, 'all_b': b, 'all_se': se, 'z': z, 'X': X, 'Y': Y, 'u': u}


