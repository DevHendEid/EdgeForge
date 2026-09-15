from __future__ import annotations


def imbalance(bid_size: int, ask_size: int) -> float:
    total = bid_size + ask_size
    return 0.0 if total == 0 else (bid_size - ask_size) / total


def microprice(best_bid: int, bid_size: int, best_ask: int, ask_size: int) -> float:
    total = bid_size + ask_size
    if total == 0:
        return (best_bid + best_ask) / 2
    return (best_ask * bid_size + best_bid * ask_size) / total
