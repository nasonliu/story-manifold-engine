#!/usr/bin/env python3
"""
Structural metrics with versioned protocols.
All metrics should be accessed through here for reproducibility.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

__version__ = "1.0.0"


# ============ Climax Estimation Protocols ============

def climax_argmax_v1(tc: List[float]) -> float:
    """
    Climax estimation v1: raw argmax.
    Simple but sensitive to noise.
    """
    if not tc:
        return 0.5
    tc_vals = [float(t) if isinstance(t, (int, float)) else 0.5 for t in tc]
    if len(tc_vals) < 2:
        return 0.5
    return tc_vals.index(max(tc_vals)) / (len(tc_vals) - 1)


def climax_argmax_smooth_v1(tc: List[float], window: int = 3) -> float:
    """
    Climax estimation v1 with smoothing.
    Args:
        tc: tension curve
        window: smoothing window size (3, 5, etc.)
    """
    if not tc:
        return 0.5
    tc_vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    if len(tc_vals) < window:
        return climax_argmax_v1(tc_vals)
    
    # Simple moving average
    kernel = np.ones(window) / window
    tc_smooth = np.convolve(tc_vals, kernel, mode='same')
    
    if len(tc_smooth) < 2:
        return 0.5
    return np.argmax(tc_smooth) / (len(tc_smooth) - 1)


def climax_weighted_v1(tc: List[float], q: float = 0.8) -> float:
    """
    Climax estimation v1: weighted centroid of high-tension region.
    More robust to plateaus.
    Args:
        tc: tension curve
        q: quantile threshold (e.g., 0.8 = top 20% tension)
    """
    if not tc:
        return 0.5
    tc_vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    if len(tc_vals) < 2:
        return 0.5
    
    threshold = q * np.max(tc_vals)
    weights = np.maximum(0, tc_vals - threshold)
    
    if np.sum(weights) == 0:
        return climax_argmax_v1(tc_vals)
    
    weighted_sum = np.sum(np.arange(len(tc_vals)) * weights)
    return weighted_sum / np.sum(weights) / (len(tc_vals) - 1)


def climax_cross_v1(tc: List[float], q: float = 0.85) -> float:
    """
    Climax estimation v1: first time crossing threshold.
    More like "entering the finale".
    """
    if not tc:
        return 0.5
    tc_vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    if len(tc_vals) < 2:
        return 0.5
    
    threshold = q * np.max(tc_vals)
    for i, t in enumerate(tc_vals):
        if t >= threshold:
            return i / (len(tc_vals) - 1)
    
    return climax_argmax_v1(tc_vals)


# ============ Peak Detection Protocols ============

def peaks_count_v1(tc: List[float], q: float = 0.8) -> int:
    """
    Peak count v1: number of significant local maxima.
    Args:
        tc: tension curve
        q: height threshold as fraction of max (0.8 = 80% of peak)
    """
    if len(tc) < 3:
        return 0
    vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    max_val = np.max(vals)
    threshold = q * max_val
    
    peaks = 0
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i-1] and vals[i] > vals[i+1] and vals[i] >= threshold:
            peaks += 1
    return peaks


def peaks_count_v2(tc: List[float], height: float = 0.7, distance: int = 2) -> int:
    """
    Peak count v2: scipy-style peak detection.
    Args:
        tc: tension curve
        height: absolute height threshold
        distance: minimum distance between peaks
    """
    if len(tc) < 3:
        return 0
    vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    
    peaks = []
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i-1] and vals[i] > vals[i+1] and vals[i] >= height:
            # Check minimum distance
            if not peaks or (i - peaks[-1]) >= distance:
                peaks.append(i)
    
    return len(peaks)


# ============ Complexity Metrics ============

def complexity_tv_v1(tc: List[float]) -> float:
    """
    Total Variation v1: measure of curve roughness.
    """
    if len(tc) < 2:
        return 0.0
    vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    return float(np.sum(np.abs(np.diff(vals))) / (len(vals) - 1))


def complexity_second_diff_v1(tc: List[float]) -> float:
    """
    Second derivative energy v1: measure of acceleration changes.
    """
    if len(tc) < 3:
        return 0.0
    vals = np.array([float(t) if isinstance(t, (int, float)) else 0.5 for t in tc])
    diffs = np.diff(vals)
    diff2 = np.diff(diffs)
    return float(np.sum(diff2**2) / (len(vals) - 2))


def complexity_drift_v1(tc: List[float], smooth_window: int = 3) -> float:
    """
    Drift v1: difference between raw and smoothed climax estimation.
    Measures stability of climax detection.
    """
    c_raw = climax_argmax_v1(tc)
    c_smooth = climax_argmax_smooth_v1(tc, smooth_window)
    return abs(c_raw - c_smooth)


# ============ Unified Interface ============

def compute_all_metrics(tc: List[float]) -> Dict[str, Any]:
    """
    Compute all metrics for a tension curve.
    Returns dict with version info.
    """
    return {
        'version': __version__,
        'climax_argmax': climax_argmax_v1(tc),
        'climax_smooth': climax_argmax_smooth_v1(tc),
        'climax_weighted': climax_weighted_v1(tc),
        'climax_cross': climax_cross_v1(tc),
        'peaks_v1': peaks_count_v1(tc),
        'peaks_v2': peaks_count_v2(tc),
        'complexity_tv': complexity_tv_v1(tc),
        'complexity_second_diff': complexity_second_diff_v1(tc),
        'complexity_drift': complexity_drift_v1(tc),
    }


# ============ Protocol Registry ============

PROTOCOLS = {
    'climax': {
        'v1_argmax': climax_argmax_v1,
        'v1_smooth': climax_argmax_smooth_v1,
        'v1_weighted': climax_weighted_v1,
        'v1_cross': climax_cross_v1,
    },
    'peaks': {
        'v1': peaks_count_v1,
        'v2': peaks_count_v2,
    },
    'complexity': {
        'v1_tv': complexity_tv_v1,
        'v1_second_diff': complexity_second_diff_v1,
        'v1_drift': complexity_drift_v1,
    },
}


if __name__ == "__main__":
    # Test
    test_tc = [0.1, 0.3, 0.5, 0.8, 0.6, 0.9, 0.4, 0.2]
    print(compute_all_metrics(test_tc))
