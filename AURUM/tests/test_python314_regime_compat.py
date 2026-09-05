import numpy as np

from src.regimes.gaussian_hmm_compat import GaussianHMMCompat


def test_python314_gaussian_markov_fallback_is_stochastic():
    rng=np.random.default_rng(42)
    x=np.vstack([rng.normal(-1,0.2,(30,2)), rng.normal(1,0.2,(30,2))])
    m=GaussianHMMCompat(n_components=2,covariance_type="diag",n_iter=100,random_state=42).fit(x)
    p=m.predict_proba(x)
    assert p.shape==(60,2)
    assert np.allclose(p.sum(axis=1),1.0,atol=1e-8)
    assert np.allclose(m.transmat_.sum(axis=1),1.0,atol=1e-12)
    assert m.predict(x).shape==(60,)
