from edgeforge.data.registry import DATASETS, by_key, by_phase


def test_catalog_has_all_research_layers() -> None:
    phases = {d.phase for d in DATASETS}
    assert {"phase1", "phase2", "phase3", "phase4"} <= phases


def test_cme_target_is_registered() -> None:
    d = by_key("databento-glbx-mdp3")
    assert d.order_ids is True
    assert "CME" in d.market


def test_free_engine_sources_present() -> None:
    keys = {d.key for d in by_phase("phase1")}
    assert {"lobster-sample", "nasdaq-itch-sample", "fi-2010"} <= keys
