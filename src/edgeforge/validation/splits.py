from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TemporalSplit:
    dev_start: date
    dev_end: date
    validation_start: date
    validation_end: date
    holdout_start: date
    holdout_end: date

    def __post_init__(self) -> None:
        if not (
            self.dev_start <= self.dev_end
            < self.validation_start
            <= self.validation_end
            < self.holdout_start
            <= self.holdout_end
        ):
            raise ValueError("splits must be chronological and non-overlapping")
