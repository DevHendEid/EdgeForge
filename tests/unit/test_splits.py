from datetime import date

import pytest

from edgeforge.validation.splits import TemporalSplit


def test_non_overlapping_split() -> None:
    TemporalSplit(
        date(2024, 1, 1), date(2024, 6, 30),
        date(2024, 7, 1), date(2024, 9, 30),
        date(2024, 10, 1), date(2024, 12, 31),
    )


def test_overlap_rejected() -> None:
    with pytest.raises(ValueError):
        TemporalSplit(
            date(2024, 1, 1), date(2024, 7, 31),
            date(2024, 7, 1), date(2024, 9, 30),
            date(2024, 10, 1), date(2024, 12, 31),
        )
