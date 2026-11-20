import numpy as np, pandas as pd
from scipy import optimize, special, stats
from numpy.polynomial.hermite_e import hermegauss

def fit_ri_binomial(df, y, n, X, group, nq=30):
    """Random-intercept logistic (binomial) GLMM by ML, Gauss-Hermite quadrature."""
    d = df[df[n] > 0].copy()
    Xm = d[X].to_numpy(float); yv = d[y].to_numpy(float); nv = d[n].to_numpy(float)
    g = pd.factorize(d[group])[0]; G = g.max()+1
    nodes, w = hermegauss(nq); w = w/np.sqrt(2*np.pi)
    lc = special.gammaln(nv+1)-special.gammaln(yv+1)-special.gammaln(nv-yv+1)
    def nll(p):
        beta, ls = p[:-1], p[-1]; sd = np.exp(ls)
        eta = Xm@beta
        e = eta[:,None] + sd*nodes[None,:]
        ll = lc[:,None] + yv[:,None]*e - nv[:,None]*np.logaddexp(0,e)
        S = np.zeros((G,nq)); np.add.at(S, g, ll)
        m = S.max(1, keepdims=True)
        return -np.sum(m[:,0] + np.log(np.exp(S-m)@w))
    p0 = np.zeros(len(X)+1); p0[-1] = np.log(0.5)
    r = optimize.minimize(nll, p0, method='BFGS')
    r = optimize.minimize(nll, r.x, method='Nelder-Mead', options={'maxiter':20000,'xatol':1e-8,'fatol':1e-10}) if not r.success else r
    # numerical Hessian
    k=len(r.x); H=np.zeros((k,k)); h=1e-4
    for i in range(k):
        for j in range(k):
            ei=np.eye(k)[i]*h; ej=np.eye(k)[j]*h
            H[i,j]=(nll(r.x+ei+ej)-nll(r.x+ei-ej)-nll(r.x-ei+ej)+nll(r.x-ei-ej))/(4*h*h)
    V=np.linalg.inv(H)
    return dict(beta=r.x[:-1], V=V[:-1,:-1], sd=np.exp(r.x[-1]), nll=r.fun, X=X, nobs=len(d), ngroups=G, ok=r.success)

def contrast(fit, c, label):
    c=np.asarray(c,float); est=c@fit['beta']; se=np.sqrt(c@fit['V']@c)
    z=est/se; p=2*stats.norm.sf(abs(z))
    return dict(contrast=label, logOR=est, se=se, OR=np.exp(est), lo=np.exp(est-1.96*se), hi=np.exp(est+1.96*se), z=z, p=p)
