from edgeforge.quality.sequence import SequenceTracker


def test_gap_detection() -> None:
    t = SequenceTracker()
    for n in [1, 2, 5, 5, 4]: t.observe(n)
    assert t.stats.gaps == 2
    assert t.stats.duplicates == 1
    assert t.stats.regressions == 1
