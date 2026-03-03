#!/usr/bin/env python3
"""
Anti-prefix leakage text conversion for skeleton embedding.
Implements multiple strategies to prevent label/prefix leakage.
"""
import random
from typing import Any


def beat_text(b: dict) -> str:
    """Extract beat name and description."""
    name = (b.get('name') or '').strip()
    desc = (b.get('desc') or '').strip()
    if name and desc:
        return f"{name}: {desc}"
    return name or desc or ""


def skeleton_to_dsl(sk: dict, seed: int = None) -> str:
    """
    DSL format - fixed field keys, reduces prefix bias.
    Format: [BEATS] B1=... | B2=... | ... [END]=... [STAKE]=...
    All samples start with same prefix [BEATS], reducing theme leakage.
    """
    if seed:
        random.seed(seed)
    
    beats = sk.get('beats') or []
    bt = [beat_text(b) for b in beats if isinstance(b, dict) and ((b.get('name') or '').strip() or (b.get('desc') or '').strip())]
    if not bt:
        bt = [sk.get('logline', '').strip()]
    
    # Build beats section
    beats_parts = [f"B{i+1}={b}" for i, b in enumerate(bt)]
    beats_str = " | ".join(beats_parts)
    
    ending = sk.get('ending', '')
    stakes = sk.get('stakes', '')
    tc = sk.get('tension_curve') or []
    tc_str = ",".join(map(str, tc[:len(bt)])) if tc else ""
    
    # DSL format - fixed order, same prefix
    parts = [
        f"[BEATS] {beats_str}",
        f"[END]{ending}",
        f"[STAKE]{stakes}",
    ]
    if tc_str:
        parts.append(f"[TC]{tc_str}")
    
    return " ".join(parts)


def skeleton_to_structure_only(sk: dict) -> str:
    """
    Structure-only: removes archetype completely.
    Only beats + relations (implied by order) + ending.
    Use this for 'true' structure embedding.
    """
    beats = sk.get('beats') or []
    bt = [beat_text(b) for b in beats if isinstance(b, dict) and ((b.get('name') or '').strip() or (b.get('desc') or '').strip())]
    if not bt:
        bt = [sk.get('logline', '').strip()]
    
    ending = sk.get('ending', '')
    # No archetype, no stakes - just structure
    return " -> ".join(bt) + f" || END:{ending}"


def skeleton_to_shuffled_template(sk: dict, seed: int = None) -> str:
    """
    Random template order to further reduce prefix effects.
    """
    if seed:
        random.seed(seed)
    
    beats = sk.get('beats') or []
    bt = [beat_text(b) for b in beats if isinstance(b, dict) and ((b.get('name') or '').strip() or (b.get('desc') or '').strip())]
    if not bt:
        bt = [sk.get('logline', '').strip()]
    
    ending = sk.get('ending', '')
    stakes = sk.get('stakes', '')
    archetype = sk.get('archetype', '')
    
    # Random template selection
    templates = [
        f"BEATS: {' | '.join(bt)} . END: {ending} . STAKES: {stakes}",
        f"STRUCTURE: {' ; '.join(bt)} // OUTCOME: {ending} // RISK: {stakes}",
        f"【BEATS】{' → '.join(bt)} 【/END】{ending} 【/STAKES】{stakes}",
    ]
    
    return random.choice(templates)


def skeleton_to_dual_vector(sk: dict):
    """
    Returns both structure vector and theme vector separately.
    Use: score = 0.8*sim(v_struct) + 0.2*sim(v_theme)
    """
    # Structure: beats only (no archetype)
    struct_text = skeleton_to_structure_only(sk)
    
    # Theme: archetype + tags only
    archetype = sk.get('archetype', '')
    tags = sk.get('style_tags') or []
    theme_text = f"TYPE:{archetype} TAGS:{' '.join(tags)}"
    
    return struct_text, theme_text


# Backward compatibility
def skeleton_to_text(sk, mode='full'):
    """Legacy function - redirects to new anti-leakage modes."""
    if mode == 'full':
        return skeleton_to_dsl(sk)
    if mode == 'short':
        return skeleton_to_structure_only(sk)
    if mode == 'meta':
        beats = sk.get('beats') or []
        bt = [beat_text(b) for b in beats if isinstance(b, dict)]
        tc = sk.get('tension_curve') or []
        return f"节拍数:{len(bt)}; 张力:{','.join(map(str, tc[:9]))}"
    return skeleton_to_dsl(sk)


def skeleton_to_dsl_v2(sk: dict) -> str:
    """
    Narrative Physics DSL v2 - encodes full structural parameters.
    Works with both legacy skeletons and new NP skeletons.
    
    Format: [L=n] [C=x.xx] [R=n] [T=type] [E=type] [N=n] [B=beat1,beat2,...]
    """
    beats = sk.get('beats', [])
    params = sk.get('structure_params', {})
    
    # Extract key structural parameters
    L = params.get('L', len(beats))  # beats count
    
    # Extract C (climax position) - try multiple sources
    C = None
    if 'C' in params:
        C = params.get('C')
    elif 'climax_position' in sk:
        C = sk.get('climax_position')
    elif sk.get('tension_curve'):
        # Infer from tension_curve
        tc = sk.get('tension_curve')
        max_idx = tc.index(max(tc))
        C = max_idx / len(tc) if tc else 0.5
    else:
        C = 0.5
    
    R = params.get('R', len(sk.get('turning_points', [])))  # reversals
    T = params.get('Tshape', 'na')  # tension shape
    E = sk.get('ending', 'open')  # ending
    N = len(beats)  # actual beats count
    
    # Get tension values - try multiple sources
    # 1. For NP: beats have 'tension' field
    # 2. For known_works: use 'tension_curve' field
    tension_curve = sk.get('tension_curve', [])
    
    # Build beat sequence (compact)
    beat_roles = []
    for i, b in enumerate(beats):
        if isinstance(b, dict):
            role = b.get('role', 'progress')[:3]  # short role
            
            # Try to get tension from multiple sources
            tension = None
            if 'tension' in b:
                # NP format: beats have 'tension' field
                tension = b.get('tension', 0.5)
            elif tension_curve and i < len(tension_curve):
                # known_works format: use tension_curve
                tension = tension_curve[i]
            
            if tension is None:
                tension = 0.5
            
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


if __name__ == "__main__":
    import json
    # Test with sample skeleton
    sample = json.loads(Path("data/raw_skeletons/sk_1000.json").read_text())
    
    print("=== DSL Format (anti-prefix) ===")
    print(skeleton_to_dsl(sample))
    print()
    print("=== Structure Only (no archetype) ===")
    print(skeleton_to_structure_only(sample))
    print()
    print("=== Dual Vector ===")
    s, t = skeleton_to_dual_vector(sample)
    print(f"STRUCT: {s[:100]}...")
    print(f"THEME: {t}")
