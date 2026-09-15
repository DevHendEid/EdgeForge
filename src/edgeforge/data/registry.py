from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    key: str
    name: str
    grade: str
    purpose: str
    access: str
    license_note: str
    url: str
    phase: str
    market: str
    order_ids: bool
    bundled: bool = False


DATASETS: tuple[DatasetSpec, ...] = (
    DatasetSpec("lobster-sample", "LOBSTER public sample files", "L3-like visible order events + synchronized book", "deterministic replay, parser tests, queue/order lifecycle tests", "free public sample", "Use official public samples only; never redistribute paid LOBSTER history.", "https://data.lobsterdata.com/info/DataSamples.php", "phase1", "NASDAQ equities", True),
    DatasetSpec("nasdaq-itch-sample", "Nasdaq TotalView-ITCH public samples", "native order-event feed", "binary parser, lifecycle semantics, visible-book reconstruction", "free official samples where offered", "Preserve Nasdaq provenance/terms; do not infer CME economics from equities.", "https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/", "phase1", "NASDAQ equities", True),
    DatasetSpec("fi-2010", "FI-2010 benchmark", "normalized L2 benchmark", "ML, leakage-safe CV, forecasting and feature-pipeline benchmarks", "free academic dataset", "Normalized specifically so original exchange messages cannot be reconstructed.", "https://etsin.fairdata.fi/dataset/73eb48d7-4dbc-4a10-a52a-da745b47a649", "phase1", "Nasdaq Nordic equities", False),
    DatasetSpec("bats-pitch-samples", "BATS PITCH / FullDepth samples", "order-event / full-depth samples", "additional parser and replay regression corpus", "small public samples in open-source repositories", "Treat as development fixtures; keep original repository/license attribution.", "https://github.com/bigfatwhale/orderbook", "phase1", "US equities", True),
    DatasetSpec("okx-l2", "OKX historical high-resolution L2", "price-level depth", "large-scale snapshot/delta replay, sequence and storage stress tests", "free official historical data", "Aggregated depth is not MBO; retain exchange provenance and terms.", "https://www.okx.com/historical-data", "phase2", "crypto", False),
    DatasetSpec("binance-public", "Binance public historical market data", "trades / bars / selected depth sources", "large free corpus for throughput, partitioning and trade-flow features", "free official archive/API", "Do not label aggregated depth as MBO.", "https://data.binance.vision/", "phase2", "crypto", False),
    DatasetSpec("bybit-public", "Bybit public historical market data", "trades / order-book products where available", "cross-venue normalization and stress testing", "free public historical data", "Verify product-specific redistribution terms and exact depth semantics.", "https://public.bybit.com/", "phase2", "crypto", False),
    DatasetSpec("hyperliquid-l2", "Hyperliquid official historical L2 archive", "price-level depth", "large historical replay corpus and snapshot/delta recovery tests", "public archive; transfer cost may apply", "Not CME-like FIFO MBO; preserve source metadata.", "https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data", "phase2", "crypto perpetuals", False),
    DatasetSpec("coinbase-live-l2", "Coinbase public live L2", "price-level depth", "record a clean forward corpus and test live-to-historical parity", "free public live feed", "Self-recorded L2 is not historical MBO; exchange terms still apply.", "https://docs.cdp.coinbase.com/advanced-trade/docs/ws-channels", "phase2", "crypto", False),
    DatasetSpec("polymarket-orderbook", "Polymarket public order-book archive", "large L2/event archive", "storage, streaming, partitioning and feature-engineering scale tests", "free public research archive", "Use only the clearly licensed public archive and preserve attribution.", "https://huggingface.co/datasets", "phase2", "prediction markets", False),
    DatasetSpec("cme-mdp-sample", "Official CME MDP/MBO samples", "CME-native MBO/MBP sample", "CME adapter validation and protocol-specific regression tests", "official samples when available", "Do not redistribute licensed CME commercial history.", "https://www.cmegroup.com/market-data.html", "phase3", "CME futures", True),
    DatasetSpec("dxfeed-samples", "dxFeed historical sample data", "trades / quotes / price-level or full-depth samples", "format-adapter validation and independent cross-checks", "free sample files", "Sample scope varies by venue/product; inspect before treating as L3.", "https://dxfeed.com/order-historical-market-data/sample-data/", "phase3", "multi-asset including futures samples", False),
    DatasetSpec("algoseek-sandbox", "AlgoSeek sandbox/sample data", "futures tick / MBP depth samples", "CME futures validation without buying a full archive", "free sandbox/sample where offered", "MBP is aggregated; no FIFO order identity unless explicitly documented.", "https://www.algoseek.com/", "phase3", "CME futures", False),
    DatasetSpec("databento-glbx-mdp3", "Databento GLBX.MDP3", "CME MBO / MBP / TBBO / trades / bars / definitions", "first genuine NQ/ES/YM/RTY/CL/GC MBO validation corpus", "usage-based; research reports note signup historical credit", "Licensed CME data: never commit or redistribute raw history.", "https://databento.com/datasets/GLBX.MDP3", "phase3", "CME/CBOT/NYMEX/COMEX", True),
    DatasetSpec("rithmic-cme", "Rithmic CME market data", "live MBO / depth / historical capabilities", "secondary CME feed for cross-vendor checks if trial/access is available", "trial/subscription; exact historical MBO span must be verified", "Do not assume old tick history equals order-level MBO history.", "https://www.rithmic.com/", "phase3", "CME Group futures", True),
    DatasetSpec("nq-long-ohlcv", "NQ long-history intraday OHLCV", "bars", "long-horizon robustness, walk-forward, regimes and coarse strategy screening", "free samples / free sources first; paid fallback only if justified", "Bars cannot validate queue-sensitive execution or microstructure fills.", "https://github.com/teaceo-debug/DEEP6", "phase4", "NQ futures", False),
    DatasetSpec("first-rate-nq-sample", "FirstRate Data NQ samples", "intraday OHLCV", "independent long-history NQ bar validation when samples suffice", "free samples; full history paid", "Use samples only in zero-cost mode; preserve provider terms.", "https://firstratedata.com/", "phase4", "NQ futures", False),
    DatasetSpec("cboe-vix", "CBOE VIX historical data", "volatility/regime context", "regime labels, volatility conditioning and stress-period stratification", "public historical series where offered", "Context data only; not execution data.", "https://www.cboe.com/tradable_products/vix/vix_historical_data/", "phase4", "US volatility", False),
    DatasetSpec("fred-macro", "FRED macroeconomic series", "macro context", "rates, inflation, liquidity and macro-regime features", "free public API/download", "Respect publication/revision timing to avoid look-ahead leakage.", "https://fred.stlouisfed.org/", "phase4", "macroeconomic", False),
    DatasetSpec("official-economic-calendars", "Official Fed/BLS/BEA release calendars", "event timestamps", "FOMC, CPI, NFP and macro-event tagging for event-regime analysis", "free official publication calendars", "Store release-time provenance and vintage; never backfill revised values into historical decisions.", "https://www.bls.gov/schedule/", "phase4", "macroeconomic events", False),
)


def by_phase(phase: str) -> tuple[DatasetSpec, ...]:
    return tuple(item for item in DATASETS if item.phase == phase)


def by_key(key: str) -> DatasetSpec:
    for item in DATASETS:
        if item.key == key:
            return item
    raise KeyError(key)
