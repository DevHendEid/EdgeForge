from __future__ import annotations

import numpy as np


def bootstrap_mean(values: np.ndarray, *, samples: int = 10_000, seed: int = 0) -> np.ndarray:
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("values must be a non-empty 1D array")
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(samples, len(values)), replace=True)
    return draws.mean(axis=1)
