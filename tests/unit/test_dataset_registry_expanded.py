from edgeforge.data.registry import DATASETS, by_key


def test_dataset_keys_are_unique() -> None:
    keys = [item.key for item in DATASETS]
    assert len(keys) == len(set(keys))


def test_high_priority_sources_are_registered() -> None:
    required = {
        "databento-glbx-mdp3",
        "cme-datamine",
        "cme-mdp-sample",
        "rithmic-cme",
        "bmll-l3-futures",
        "lobster-sample",
        "nasdaq-itch-sample",
        "fi-2010",
        "moex-full-order-book-sample",
        "okx-l2",
        "binance-public",
        "hyperliquid-l2",
    }
    assert required.issubset({item.key for item in DATASETS})


def test_github_research_sources_are_registered() -> None:
    github_keys = {
        "github-cme-mdp",
        "github-nautilus-databento",
        "github-fx-options-vrp",
        "github-deep6",
        "github-nq-quant",
        "github-ml4t",
        "github-databento-python",
    }
    assert github_keys.issubset({item.key for item in DATASETS})


def test_databento_is_order_level_capable() -> None:
    assert by_key("databento-glbx-mdp3").order_ids is True


def test_l2_is_not_mislabeled_as_order_level() -> None:
    assert by_key("okx-l2").order_ids is False
    assert by_key("binance-public").order_ids is False
    assert by_key("hyperliquid-l2").order_ids is False
