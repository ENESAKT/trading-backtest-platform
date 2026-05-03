import numpy as np


def generate_heatmap_data(grid_results: list[dict], p1_key: str, p2_key: str, metric: str = 'net_profit') -> dict:
    """
    Generates a 2D matrix (heatmap) from 1D grid search results for two parameters.
    
    Returns:
        dict: {
            "x_axis": list of p1 values (sorted),
            "y_axis": list of p2 values (sorted),
            "z_matrix": 2D list of metric values where z_matrix[y][x] corresponds to y_axis[y], x_axis[x]
        }
    """
    if not grid_results:
        return {"x_axis": [], "y_axis": [], "z_matrix": []}

    p1_vals = sorted(list(set(r['params'].get(p1_key) for r in grid_results if p1_key in r['params'])))
    p2_vals = sorted(list(set(r['params'].get(p2_key) for r in grid_results if p2_key in r['params'])))

    if not p1_vals or not p2_vals:
        return {"x_axis": p1_vals, "y_axis": p2_vals, "z_matrix": []}

    # Build lookup
    lookup = {}
    for r in grid_results:
        p1 = r['params'].get(p1_key)
        p2 = r['params'].get(p2_key)
        if p1 is not None and p2 is not None:
            lookup[(p1, p2)] = r.get(metric, 0.0)

    z_matrix = []
    for p2 in p2_vals:
        row = []
        for p1 in p1_vals:
            row.append(lookup.get((p1, p2), 0.0))
        z_matrix.append(row)

    return {
        "x_axis": p1_vals,
        "y_axis": p2_vals,
        "z_matrix": z_matrix
    }

def find_stable_region(grid_results: list[dict], p1_key: str, p2_key: str, metric: str = 'net_profit', threshold: float = 0.8) -> dict:
    """
    Analyzes grid results to find a 'stable region' rather than just a single max peak.
    A parameter combination is considered stable if its neighbors also yield good results.
    
    Args:
        grid_results: List of backtest result dicts.
        p1_key: Name of the first parameter.
        p2_key: Name of the second parameter.
        metric: The metric to optimize (default: net_profit).
        threshold: The threshold (relative to the global max) to consider a neighbor 'good'. (e.g. 0.8 = 80%)
        
    Returns:
        dict: Information about the most stable parameter set.
    """
    if not grid_results:
        return {}

    heatmap = generate_heatmap_data(grid_results, p1_key, p2_key, metric)
    x_axis = heatmap['x_axis']
    y_axis = heatmap['y_axis']
    z = np.array(heatmap['z_matrix'])

    if z.size == 0:
        return {}

    global_max = np.max(z)
    if global_max <= 0:
        # If no positive profit, fallback to simple max
        idx = np.unravel_index(np.argmax(z, axis=None), z.shape)
        return {
            "best_p1": x_axis[idx[1]],
            "best_p2": y_axis[idx[0]],
            "stable_score": 0,
            "metric_value": float(z[idx]),
            "global_max": float(global_max)
        }

    # Calculate stability scores
    stability_matrix = np.zeros_like(z, dtype=float)
    rows, cols = z.shape

    cutoff = global_max * threshold

    for r in range(rows):
        for c in range(cols):
            val = z[r, c]
            if val < cutoff:
                continue

            # Check neighbors (including diagonals)
            neighbors_val = 0
            neighbor_count = 0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        neighbors_val += z[nr, nc]
                        neighbor_count += 1

            if neighbor_count > 0:
                avg_neighbor = neighbors_val / neighbor_count
                # Stability score: combinations of own value and neighbors value
                stability_matrix[r, c] = (val * 0.5) + (avg_neighbor * 0.5)

    best_idx = np.unravel_index(np.argmax(stability_matrix, axis=None), stability_matrix.shape)

    if stability_matrix[best_idx] == 0:
        # No stable region found, fallback to max
        best_idx = np.unravel_index(np.argmax(z, axis=None), z.shape)

    return {
        "best_p1": x_axis[best_idx[1]],
        "best_p2": y_axis[best_idx[0]],
        "stable_score": float(stability_matrix[best_idx]),
        "metric_value": float(z[best_idx]),
        "global_max": float(global_max)
    }
