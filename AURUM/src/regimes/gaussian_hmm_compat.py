"""Python-3.14-compatible Gaussian Markov regime model.

This is AURUM's local fallback when ``hmmlearn`` has no wheel for the running
Python.  It estimates Gaussian emission regimes with scikit-learn's
GaussianMixture and estimates a Laplace-smoothed Markov transition matrix from
the fitted latent sequence.  It intentionally exposes only the small API
surface AURUM uses (fit/predict/predict_proba/score and HMM parameters).

It is an engineering compatibility model, not a claim of equivalence to
Baum-Welch training in hmmlearn.  MARS-CVaR's governed signature algorithm is
independent of this fallback and continues to use explicit regime-transition
probabilities and walk-forward evidence.
"""
from __future__ import annotations

from types import SimpleNamespace
import numpy as np
from sklearn.mixture import GaussianMixture


class GaussianHMMCompat:
    def __init__(self, n_components: int = 3, covariance_type: str = "diag", n_iter: int = 500, random_state: int | None = None):
        if covariance_type not in {"diag", "full"}:
            raise ValueError("GaussianHMMCompat supports diag or full covariance")
        self.n_components = int(n_components)
        self.covariance_type = covariance_type
        self.n_iter = int(n_iter)
        self.random_state = random_state
        self._gmm = GaussianMixture(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            max_iter=self.n_iter,
            random_state=self.random_state,
            reg_covar=1e-6,
        )
        self.monitor_ = SimpleNamespace(converged=False)

    def fit(self, x: np.ndarray):
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or len(x) < self.n_components:
            raise ValueError("x must be a 2D array with at least n_components observations")
        self._gmm.fit(x)
        labels = self._gmm.predict(x)
        self.startprob_ = np.full(self.n_components, 1.0 / self.n_components)
        self.startprob_[labels[0]] += 1.0
        self.startprob_ /= self.startprob_.sum()
        counts = np.ones((self.n_components, self.n_components), dtype=float)  # Laplace smoothing
        for a, b in zip(labels[:-1], labels[1:]):
            counts[int(a), int(b)] += 1.0
        self.transmat_ = counts / counts.sum(axis=1, keepdims=True)
        self.means_ = np.asarray(self._gmm.means_, dtype=float)
        self.covars_ = np.asarray(self._gmm.covariances_, dtype=float)
        self.monitor_.converged = bool(self._gmm.converged_)
        return self

    def _compute_log_likelihood(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        # sklearn exposes weighted component log probabilities. Remove the
        # mixture prior to obtain per-state emission log likelihoods.
        weighted = self._gmm._estimate_weighted_log_prob(x)
        return weighted - np.log(np.asarray(self._gmm.weights_) + 1e-15)

    @staticmethod
    def _logsumexp(v: np.ndarray, axis: int | None = None) -> np.ndarray:
        m = np.max(v, axis=axis, keepdims=True)
        out = m + np.log(np.sum(np.exp(v - m), axis=axis, keepdims=True))
        if axis is None:
            return np.asarray(out).reshape(())
        return np.squeeze(out, axis=axis)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        ll = self._compute_log_likelihood(x)
        n = len(x)
        log_alpha = np.empty((n, self.n_components), dtype=float)
        log_alpha[0] = np.log(self.startprob_ + 1e-15) + ll[0]
        log_alpha[0] -= self._logsumexp(log_alpha[0])
        log_t = np.log(self.transmat_ + 1e-15)
        for t in range(1, n):
            for j in range(self.n_components):
                log_alpha[t, j] = ll[t, j] + self._logsumexp(log_alpha[t-1] + log_t[:, j])
            log_alpha[t] -= self._logsumexp(log_alpha[t])
        return np.exp(log_alpha)

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(x), axis=1).astype(int)

    def score(self, x: np.ndarray) -> float:
        x = np.asarray(x, dtype=float)
        return float(np.sum(self._gmm.score_samples(x)))
