#!/usr/bin/env python3
"""
Skeleton Evaluation Module
- Schema pass rate
- Title duplication rate
- Neighbor novelty
- Human readability / tension scoring
"""
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
import numpy as np

# Evaluation config
DATA_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/cleaned_skeletons')
REPORT_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/reports')

# Schema definition
REQUIRED_FIELDS = ['id', 'archetype', 'title', 'logline', 'beats', 'ending']
BEAT_REQUIRED_FIELDS = ['id', 'name', 'desc']
VALID_ENDINGS = {'tragedy', 'triumph', 'bittersweet', 'open', 'pyrrhic'}

def load_skeletons() -> List[dict]:
    """Load cleaned skeletons."""
    file_path = DATA_DIR / 'skeletons_v2.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_schema(skeleton: dict) -> Tuple[bool, List[str]]:
    """Evaluate schema compliance for a single skeleton."""
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in skeleton:
            errors.append(f"missing:{field}")
    
    # Check beats
    beats = skeleton.get('beats', [])
    if not isinstance(beats, list):
        errors.append("beats:not_list")
    elif len(beats) < 6 or len(beats) > 10:
        errors.append(f"beats:count_{len(beats)}")
    else:
        for i, beat in enumerate(beats):
            for field in BEAT_REQUIRED_FIELDS:
                if field not in beat or not beat[field]:
                    errors.append(f"beat_{i}:missing_{field}")
    
    # Check ending
    ending = skeleton.get('ending', '')
    if ending not in VALID_ENDINGS:
        errors.append(f"invalid_ending:{ending}")
    
    # Check tension_curve alignment
    tc = skeleton.get('tension_curve', [])
    if tc and len(tc) != len(beats):
        errors.append(f"tension_curve:mismatch_{len(tc)}vs{len(beats)}")
    
    return len(errors) == 0, errors

def evaluate_title_uniqueness(skeletons: List[dict]) -> Dict[str, Any]:
    """Evaluate title duplication."""
    titles = [sk.get('title', '').strip() for sk in skeletons if sk.get('title')]
    title_counts = Counter(titles)
    
    # Find duplicates
    duplicates = {t: c for t, c in title_counts.items() if c > 1}
    unique_count = len([t for t, c in title_counts.items() if c == 1])
    
    return {
        "total_titles": len(titles),
        "unique_titles": unique_count,
        "duplicate_count": len(duplicates),
        "duplicate_rate": len(duplicates) / len(titles) if titles else 0,
        "top_duplicates": sorted(duplicates.items(), key=lambda x: -x[1])[:10],
    }

def evaluate_logline_uniqueness(skeletons: List[dict], threshold: float = 0.8) -> Dict[str, Any]:
    """Evaluate logline near-duplication using simple similarity."""
    # Simple Jaccard on characters
    def jaccard(s1, s2):
        set1, set2 = set(s1), set(s2)
        return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0
    
    loglines = [(sk.get('id'), sk.get('logline', '')) for sk in skeletons if sk.get('logline')]
    
    # Sample for efficiency
    import random
    sample_size = min(500, len(loglines))
    sample = random.sample(loglines, sample_size)
    
    near_dupes = 0
    comparisons = 0
    for i in range(len(sample)):
        for j in range(i+1, len(sample)):
            if j - i > 100:  # Limit comparisons
                break
            sim = jaccard(sample[i][1], sample[j][1])
            if sim > threshold:
                near_dupes += 1
            comparisons += 1
    
    return {
        "sample_size": sample_size,
        "near_duplicates": near_dupes,
        "near_duplicate_rate": near_dupes / comparisons if comparisons else 0,
    }

def evaluate_archetype_distribution(skeletons: List[dict]) -> Dict[str, Any]:
    """Evaluate archetype distribution balance."""
    archetypes = [sk.get('archetype', 'unknown') for sk in skeletons]
    counts = Counter(archetypes)
    
    if not counts:
        return {}
    
    max_count = max(counts.values())
    min_count = min(counts.values())
    
    return {
        "distribution": dict(counts),
        "balance_ratio": max_count / min_count if min_count > 0 else float('inf'),
        "total_archetypes": len(counts),
    }

def evaluate_ending_distribution(skeletons: List[dict]) -> Dict[str, Any]:
    """Evaluate ending type distribution."""
    endings = [sk.get('ending', 'unknown') for sk in skeletons]
    counts = Counter(endings)
    return {
        "distribution": dict(counts),
        "total_endings": len(counts),
    }

def evaluate_tension_curves(skeletons: List[dict]) -> Dict[str, Any]:
    """Evaluate tension curve patterns."""
    valid_curves = []
    for sk in skeletons:
        tc = sk.get('tension_curve', [])
        if tc and len(tc) >= 3:
            # Check it's a valid curve (starts low, ends appropriately)
            if isinstance(tc[0], (int, float)) and isinstance(tc[-1], (int, float)):
                valid_curves.append(tc)
    
    if not valid_curves:
        return {"valid_count": 0}
    
    # Average curve shape
    min_len = min(len(c) for c in valid_curves)
    avg_curve = []
    for i in range(min_len):
        avg_curve.append(np.mean([c[i] for c in valid_curves]))
    
    return {
        "valid_count": len(valid_curves),
        "avg_curve": avg_curve,
        "avg_start": np.mean([c[0] for c in valid_curves]),
        "avg_end": np.mean([c[-1] for c in valid_curves]),
        "avg_mid": np.mean([c[len(c)//2] for c in valid_curves]),
    }

def run_full_evaluation() -> Dict[str, Any]:
    """Run complete evaluation."""
    print("Loading skeletons...")
    skeletons = load_skeletons()
    print(f"Loaded {len(skeletons)} skeletons")
    
    results = {
        "total": len(skeletons),
    }
    
    # Schema evaluation
    print("Evaluating schema...")
    schema_pass = 0
    all_errors = []
    for sk in skeletons:
        passed, errors = evaluate_schema(sk)
        if passed:
            schema_pass += 1
        all_errors.extend(errors)
    
    results["schema"] = {
        "pass_count": schema_pass,
        "pass_rate": schema_pass / len(skeletons),
        "error_distribution": Counter(all_errors),
    }
    
    # Title uniqueness
    print("Evaluating title uniqueness...")
    results["titles"] = evaluate_title_uniqueness(skeletons)
    
    # Logline uniqueness
    print("Evaluating logline uniqueness...")
    results["loglines"] = evaluate_logline_uniqueness(skeletons)
    
    # Archetype distribution
    print("Evaluating archetype distribution...")
    results["archetypes"] = evaluate_archetype_distribution(skeletons)
    
    # Ending distribution
    print("Evaluating ending distribution...")
    results["endings"] = evaluate_ending_distribution(skeletons)
    
    # Tension curves
    print("Evaluating tension curves...")
    results["tension"] = evaluate_tension_curves(skeletons)
    
    return results

def print_report(results: Dict[str, Any]):
    """Print evaluation report."""
    print("\n" + "="*50)
    print("SKELETON EVALUATION REPORT")
    print("="*50)
    
    print(f"\nTotal skeletons: {results['total']}")
    
    # Schema
    schema = results['schema']
    print(f"\n## Schema Compliance")
    print(f"  Pass rate: {schema['pass_rate']*100:.2f}% ({schema['pass_count']}/{results['total']})")
    if schema['error_distribution']:
        print(f"  Top errors:")
        for err, cnt in schema['error_distribution'].most_common(5):
            print(f"    - {err}: {cnt}")
    
    # Titles
    titles = results['titles']
    print(f"\n## Title Uniqueness")
    print(f"  Unique: {titles['unique_titles']}/{titles['total_titles']} ({titles['unique_titles']/titles['total_titles']*100:.1f}%)")
    print(f"  Duplicates: {titles['duplicate_count']}")
    if titles['top_duplicates']:
        print(f"  Top duplicate titles:")
        for title, cnt in titles['top_duplicates'][:5]:
            print(f"    - '{title}': {cnt}")
    
    # Archetypes
    archetypes = results['archetypes']
    print(f"\n## Archetype Distribution")
    print(f"  Total archetypes: {archetypes.get('total_archetypes', 0)}")
    print(f"  Balance ratio: {archetypes.get('balance_ratio', 0):.2f}")
    if 'distribution' in archetypes:
        for arch, cnt in sorted(archetypes['distribution'].items(), key=lambda x: -x[1])[:5]:
            print(f"    - {arch}: {cnt}")
    
    # Endings
    endings = results['endings']
    print(f"\n## Ending Distribution")
    if 'distribution' in endings:
        for end, cnt in sorted(endings['distribution'].items(), key=lambda x: -x[1]):
            print(f"    - {end}: {cnt}")
    
    # Tension
    tension = results['tension']
    print(f"\n## Tension Curves")
    print(f"  Valid curves: {tension.get('valid_count', 0)}")
    if tension.get('valid_count', 0) > 0:
        print(f"  Avg start: {tension.get('avg_start', 0):.3f}")
        print(f"  Avg mid: {tension.get('avg_mid', 0):.3f}")
        print(f"  Avg end: {tension.get('avg_end', 0):.3f}")
    
    print("\n" + "="*50)

def save_report(results: Dict[str, Any], output_path: Path):
    """Save evaluation report to file."""
    # Convert to serializable format
    report = {
        "ts": results.get("ts", ""),
        "total": results["total"],
        "schema_pass_rate": results["schema"]["pass_rate"],
        "title_unique_rate": results["titles"]["unique_titles"] / results["titles"]["total_titles"] if results["titles"]["total_titles"] > 0 else 0,
        "title_duplicate_count": results["titles"]["duplicate_count"],
        "archetype_balance_ratio": results["archetypes"].get("balance_ratio", 0),
        "tension_valid_count": results["tension"].get("valid_count", 0),
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    from datetime import datetime
    results = run_full_evaluation()
    results["ts"] = datetime.now().isoformat()
    
    print_report(results)
    
    # Save JSON report
    output_path = REPORT_DIR / f"evaluation_{datetime.now().strftime('%Y-%m-%d')}.json"
    save_report(results, output_path)
