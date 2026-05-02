import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

GRAPH_NODES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo", "1y"]

# Only smaller to larger
GRAPH_EDGES = {
    "1m": ["5m"],
    "5m": ["15m"],
    "15m": ["30m"],
    "30m": ["1h"],
    "1h": ["4h"],
    "4h": ["1d"],
    "1d": ["1w", "1mo", "1y"]
}

def can_derive(source_tf: str, target_tf: str) -> bool:
    """Check if target_tf can be derived from source_tf using the graph"""
    try:
        source_idx = GRAPH_NODES.index(source_tf)
        target_idx = GRAPH_NODES.index(target_tf)
        return source_idx < target_idx
    except ValueError:
        return False

def get_possible_sources(target_tf: str) -> List[str]:
    """Get list of timeframes that can be used to generate the target"""
    sources = []
    for source, targets in GRAPH_EDGES.items():
        if target_tf in targets:
            sources.append(source)
    return sources
