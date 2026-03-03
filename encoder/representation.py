#!/usr/bin/env python3
"""
Unified representation layer for story skeletons.
All analysis scripts should use these entry points.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

# Version: 1.0.0
__version__ = "1.0.0"


def get_tc_floats(tc) -> List[float]:
    """Extract float values from tension curve."""
    result = []
    for t in tc:
        if isinstance(t, (int, float)):
            result.append(float(t))
        elif isinstance(t, dict) and 'tension' in t:
            result.append(float(t['tension']))
    return result


# ============ Entry 1: DSL v2 (for embedding) ============
def to_dsl_v2(sk: dict) -> str:
    """
    Narrative Physics DSL v2 - encodes full structural parameters.
    Works with both legacy skeletons and new NP skeletons.
    
    Format: [L=n] [C=x.xx] [R=n] [T=type] [E=type] [N=n] [B=beat1,beat2,...]
    
    Returns:
        str: DSL representation for embedding
    """
    beats = sk.get('beats', [])
    params = sk.get('structure_params', {})
    
    # L
    L = params.get('L', len(beats))
    
    # C (climax position) - multiple sources
    C = None
    if 'C' in params:
        C = params.get('C')
    elif 'climax_position' in sk:
        C = sk.get('climax_position')
    elif sk.get('tension_curve'):
        tc = get_tc_floats(sk.get('tension_curve'))
        if tc:
            max_idx = tc.index(max(tc))
            C = max_idx / len(tc) if tc else 0.5
    else:
        C = 0.5
    
    # R
    R = params.get('R', len(sk.get('turning_points', [])))
    
    # Tshape
    T = params.get('Tshape', 'na')
    
    # E (ending)
    E = sk.get('ending', 'open')
    
    # N
    N = len(beats)
    
    # Tension values - multiple sources
    tension_curve = sk.get('tension_curve', [])
    if tension_curve:
        tensions = get_tc_floats(tension_curve)
    else:
        tensions = [b.get('tension', 0.5) for b in beats if isinstance(b, dict)]
    
    # Build beat sequence
    beat_roles = []
    for i, b in enumerate(beats):
        if isinstance(b, dict):
            role = b.get('role', 'progress')[:3]
            tension = tensions[i] if i < len(tensions) else 0.5
            beat_roles.append(f"{role}:{tension:.1f}")
    
    # Construct DSL
    parts = [
        f"[L={L}]",
        f"[C={C:.2f}]",
        f"[R={R}]",
        f"[T={T}]",
        f"[E={E}]",
        f"[N={N}]",
    ]
    
    if beat_roles:
        parts.append(f"[B={','.join(beat_roles)}]")
    
    return ' '.join(parts)


# ============ Entry 2: Features (for structured analysis) ============
def to_features(sk: dict) -> Dict[str, Any]:
    """
    Extract structural features as a dictionary.
    Useful for classification, regression, etc.
    
    Returns:
        dict: {L, C, R, Tshape, E, N, peaks, ...}
    """
    beats = sk.get('beats', [])
    params = sk.get('structure_params', {})
    tension_curve = sk.get('tension_curve', [])
    
    # Extract tension values
    if tension_curve:
        tensions = get_tc_floats(tension_curve)
    else:
        tensions = [b.get('tension', 0.5) for b in beats if isinstance(b, dict)]
    
    # Basic parameters
    L = params.get('L', len(beats))
    
    # C calculation
    C = None
    if 'C' in params:
        C = params.get('C')
    elif 'climax_position' in sk:
        C = sk.get('climax_position')
    elif tensions:
        max_idx = tensions.index(max(tensions))
        C = max_idx / len(tensions) if tensions else 0.5
    else:
        C = 0.5
    
    R = params.get('R', len(sk.get('turning_points', [])))
    T = params.get('Tshape', 'na')
    E = sk.get('ending', 'open')
    
    # Peak count (v1)
    peaks = _peak_count_v1(tensions)
    
    # Total variation
    tv = _tv_norm(tensions)
    
    # Second derivative energy
    sde = _second_diff_energy(tensions)
    
    return {
        'L': L,
        'C': C,
        'R': R,
        'Tshape': T,
        'E': E,
        'N': len(beats),
        'peaks': peaks,
        'tv': tv,
        'sde': sde,
    }


# ============ Entry 3: Hover text (for visualization) ============
def to_hover(sk: dict) -> str:
    """
    Generate hover text for visualization/debugging.
    Does NOT participate in embedding.
    """
    # Use features for cleaner output
    f = to_features(sk)
    
    archetype = sk.get('archetype', '')
    if isinstance(archetype, list):
        archetype = archetype[0] if archetype else 'unknown'
    
    title = sk.get('title', sk.get('id', 'unknown'))
    
    return f"{title}\n[{archetype}] L={f['L']} C={f['C']:.2f} R={f['R']} peaks={f['peaks']}"


# ============ Internal metrics (versioned) ============

def _peak_count_v1(tc: List[float], q: float = 0.8) -> int:
    """Peak count detector v1."""
    if len(tc) < 3:
        return 0
    vals = np.array(tc)
    max_val = max(vals)
    threshold = q * max_val
    peaks = 0
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i-1] and vals[i] > vals[i+1] and vals[i] >= threshold:
            peaks += 1
    return peaks


def _tv_norm(tc: List[float]) -> float:
    """Total Variation v1."""
    if len(tc) < 2:
        return 0
    vals = np.array(tc)
    return np.sum(np.abs(np.diff(vals))) / (len(vals) - 1)


def _second_diff_energy(tc: List[float]) -> float:
    """Second derivative energy v1."""
    if len(tc) < 3:
        return 0
    vals = np.array(tc)
    diffs = np.diff(vals)
    diff2 = np.diff(diffs)
    return np.sum(diff2**2) / (len(vals) - 2)


# ============ Convenience functions ============

def load_and_encode(dataset_path: str, dsl_version: str = 'v2'):
    """Load skeletons and encode with specified version."""
    import pandas as pd
    from sentence_transformers import SentenceTransformer
    
    if dataset_path.endswith('.json'):
        with open(dataset_path) as f:
            skeletons = json.load(f)
    else:
        # Assume directory
        skeletons = [json.loads(f.read_text()) for f in Path(dataset_path).glob('*.json')]
    
    if dsl_version == 'v2':
        texts = [to_dsl_v2(s) for s in skeletons]
    else:
        raise ValueError(f"Unknown DSL version: {dsl_version}")
    
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(texts, show_progress_bar=True)
    
    return skeletons, embeddings


if __name__ == "__main__":
    # Test with sample
    sample = {
        "id": "test_001",
        "archetype": "英雄成长",
        "beats": [
            {"role": "setup", "tension": 0.2},
            {"role": "progress", "tension": 0.5},
            {"role": "climax", "tension": 0.9},
            {"role": "resolution", "tension": 0.3},
        ],
        "ending": "closed",
        "structure_params": {"L": 4, "C": 0.67, "R": 1, "Tshape": "hill"}
    }
    
    print("DSL:", to_dsl_v2(sample))
    print("Features:", to_features(sample))
    print("Hover:", to_hover(sample))
