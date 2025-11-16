#!/usr/bin/env python3
"""
LLM-Focused Benchmark Runner for PyToon

Measures token savings across LLM-specific data patterns organized by tiers:
- Tier 1 (Optimal): Large uniform tabular arrays (40-60% expected savings)
- Tier 2 (Good): Nested structures with uniform sub-arrays (25-40% expected)
- Tier 3 (Fair): RAG documents, mixed content (10-25% expected)
- Tier 4 (Skip): Configs, nested hierarchies (use JSON instead)

Generates comprehensive reports with LLM cost impact analysis.
"""

import json
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytoon
from pytoon.utils.tokens import TokenCounter


# LLM pricing ($ per 1M tokens) - typical 2025 rates
LLM_PRICING = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.15, "output": 0.60},
    "gpt-5": {"input": 5.00, "output": 15.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
}


def benchmark_file(filepath: Path) -> dict:
    """Benchmark a single JSON file for TOON efficiency."""
    with open(filepath) as f:
        data = json.load(f)

    counter = TokenCounter()

    # JSON baseline (compact)
    json_str = json.dumps(data, separators=(",", ":"))
    json_bytes = len(json_str.encode("utf-8"))
    json_tokens = counter.count_tokens(json_str)

    # Measure TOON encoding
    start = time.perf_counter()
    try:
        toon_str = pytoon.encode(data)
        encode_success = True
        encode_error = None
    except Exception as e:
        toon_str = ""
        encode_success = False
        encode_error = str(e)
    encode_time = (time.perf_counter() - start) * 1000

    if not encode_success:
        return {
            "file": filepath.name,
            "tier": filepath.parent.name,
            "records": len(data) if isinstance(data, list) else 1,
            "json_bytes": json_bytes,
            "json_tokens": json_tokens,
            "toon_bytes": 0,
            "toon_tokens": 0,
            "savings_pct": 0.0,
            "encode_ms": encode_time,
            "decode_ms": 0.0,
            "roundtrip": "ENCODE_FAIL",
            "error": encode_error,
        }

    toon_bytes = len(toon_str.encode("utf-8"))
    toon_tokens = counter.count_tokens(toon_str)

    # Measure TOON decoding
    start = time.perf_counter()
    try:
        decoded = pytoon.decode(toon_str)
        decode_success = True
        decode_error = None
    except Exception as e:
        decoded = None
        decode_success = False
        decode_error = str(e)
    decode_time = (time.perf_counter() - start) * 1000

    if not decode_success:
        return {
            "file": filepath.name,
            "tier": filepath.parent.name,
            "records": len(data) if isinstance(data, list) else 1,
            "json_bytes": json_bytes,
            "json_tokens": json_tokens,
            "toon_bytes": toon_bytes,
            "toon_tokens": toon_tokens,
            "savings_pct": (1 - toon_tokens / json_tokens) * 100 if json_tokens > 0 else 0,
            "encode_ms": encode_time,
            "decode_ms": decode_time,
            "roundtrip": "DECODE_FAIL",
            "error": decode_error,
        }

    # Roundtrip check
    roundtrip_ok = decoded == data
    savings_pct = (1 - toon_tokens / json_tokens) * 100 if json_tokens > 0 else 0

    return {
        "file": filepath.name,
        "tier": filepath.parent.name,
        "records": len(data) if isinstance(data, list) else 1,
        "json_bytes": json_bytes,
        "json_tokens": json_tokens,
        "toon_bytes": toon_bytes,
        "toon_tokens": toon_tokens,
        "savings_pct": savings_pct,
        "tokens_saved": json_tokens - toon_tokens,
        "encode_ms": encode_time,
        "decode_ms": decode_time,
        "roundtrip": "PASS" if roundtrip_ok else "FAIL",
    }


def print_tier_results(tier_name: str, results: list[dict], expected_range: tuple[float, float]) -> dict:
    """Print results for a single tier with expected range comparison."""
    if not results:
        return {}

    print(f"\n{'=' * 100}")
    tier_display = {
        "tier1_optimal": "TIER 1: LLM-OPTIMAL (Expected 40-60% Savings)",
        "tier2_good": "TIER 2: LLM-GOOD (Expected 25-40% Savings)",
        "tier3_fair": "TIER 3: LLM-FAIR (Expected 10-25% Savings)",
        "tier4_skip": "TIER 4: LLM-SKIP (Recommend JSON Instead)",
    }
    print(tier_display.get(tier_name, tier_name))
    print("=" * 100)

    # Table header
    print(f"{'File':<40} {'Records':>8} {'JSON Tok':>10} {'TOON Tok':>10} {'Savings':>10} {'Roundtrip':>10}")
    print("-" * 100)

    tier_json_tokens = 0
    tier_toon_tokens = 0
    tier_pass = 0

    for result in sorted(results, key=lambda x: -x["savings_pct"]):  # Best savings first
        savings_str = f"{result['savings_pct']:+.1f}%"

        # Color coding based on expected range
        if result["savings_pct"] >= expected_range[0]:
            savings_str = f"\033[92m{savings_str}\033[0m"  # Green - meets/exceeds
        elif result["savings_pct"] >= expected_range[0] * 0.7:
            savings_str = f"\033[93m{savings_str}\033[0m"  # Yellow - close
        else:
            savings_str = f"\033[91m{savings_str}\033[0m"  # Red - below

        roundtrip_str = result["roundtrip"]
        if roundtrip_str == "PASS":
            roundtrip_str = f"\033[92mPASS\033[0m"
            tier_pass += 1
        else:
            roundtrip_str = f"\033[91m{roundtrip_str}\033[0m"

        print(
            f"{result['file']:<40} {result['records']:>8,} {result['json_tokens']:>10,} "
            f"{result['toon_tokens']:>10,} {savings_str:>20} {roundtrip_str:>20}"
        )

        tier_json_tokens += result["json_tokens"]
        tier_toon_tokens += result["toon_tokens"]

    # Tier summary
    tier_overall = (1 - tier_toon_tokens / tier_json_tokens) * 100 if tier_json_tokens > 0 else 0
    tier_avg = sum(r["savings_pct"] for r in results) / len(results)
    tokens_saved = tier_json_tokens - tier_toon_tokens

    print("-" * 100)
    print(f"Tier Summary: {len(results)} files | {tier_pass}/{len(results)} PASS")
    print(f"Average Savings: {tier_avg:.1f}% | Overall Savings: {tier_overall:.1f}%")
    print(f"Total Tokens: {tier_json_tokens:,} JSON -> {tier_toon_tokens:,} TOON ({tokens_saved:,} saved)")

    # Cost impact
    if tokens_saved > 0:
        print("\nLLM Cost Impact (per 1M calls with this dataset):")
        for model, prices in LLM_PRICING.items():
            cost_saved = (tokens_saved / 1_000_000) * prices["input"]
            print(f"  {model}: ${cost_saved:,.2f} saved")

    return {
        "tier": tier_name,
        "files": len(results),
        "pass_rate": tier_pass / len(results) * 100,
        "avg_savings": tier_avg,
        "overall_savings": tier_overall,
        "json_tokens": tier_json_tokens,
        "toon_tokens": tier_toon_tokens,
        "tokens_saved": tokens_saved,
    }


def print_executive_summary(tier_summaries: list[dict], all_results: list[dict]) -> None:
    """Print executive summary with key metrics."""
    print("\n" + "=" * 100)
    print("EXECUTIVE SUMMARY: PyTOON LLM Benchmark Results")
    print("=" * 100)

    # Headline metric: weighted average across Tier 1-3 (LLM use cases)
    llm_tiers = ["tier1_optimal", "tier2_good", "tier3_fair"]
    llm_results = [r for r in all_results if r["tier"] in llm_tiers]

    if llm_results:
        total_json = sum(r["json_tokens"] for r in llm_results)
        total_toon = sum(r["toon_tokens"] for r in llm_results)
        llm_overall = (1 - total_toon / total_json) * 100
        tokens_saved = total_json - total_toon

        print(f"\n{'*' * 70}")
        print(f"  HEADLINE: {llm_overall:.1f}% Token Savings for LLM Use Cases (Tier 1-3)")
        print(f"  {tokens_saved:,} tokens saved across {len(llm_results)} benchmark files")
        print(f"{'*' * 70}")

    # Per-tier breakdown
    print("\nPer-Tier Performance:")
    print("-" * 100)
    print(f"{'Tier':<25} {'Files':>8} {'Pass Rate':>12} {'Avg Savings':>15} {'Overall':>12} {'Tokens Saved':>15}")
    print("-" * 100)

    tier_order = ["tier1_optimal", "tier2_good", "tier3_fair", "tier4_skip"]
    tier_labels = {
        "tier1_optimal": "Tier 1 (Optimal)",
        "tier2_good": "Tier 2 (Good)",
        "tier3_fair": "Tier 3 (Fair)",
        "tier4_skip": "Tier 4 (Skip)",
    }

    for tier in tier_order:
        summary = next((s for s in tier_summaries if s["tier"] == tier), None)
        if summary:
            label = tier_labels.get(tier, tier)
            print(
                f"{label:<25} {summary['files']:>8} {summary['pass_rate']:>11.1f}% "
                f"{summary['avg_savings']:>14.1f}% {summary['overall_savings']:>11.1f}% "
                f"{summary['tokens_saved']:>15,}"
            )

    # Real-world cost impact
    print("\n" + "=" * 100)
    print("REAL-WORLD COST IMPACT (Example Scenarios)")
    print("=" * 100)

    scenarios = [
        ("10K product catalog analysis", "tier1_optimal", 50.0),
        ("100K event stream processing", "tier1_optimal", 55.0),
        ("1K invoice processing batch", "tier2_good", 30.0),
        ("RAG retrieval (50 documents)", "tier3_fair", 15.0),
    ]

    print(f"\n{'Use Case':<35} {'Expected Savings':>18} {'Cost @ $3/1M tokens':>25}")
    print("-" * 80)

    for scenario_name, tier, expected_savings in scenarios:
        # Estimate based on tier performance
        tier_summary = next((s for s in tier_summaries if s["tier"] == tier), None)
        if tier_summary:
            actual_savings = tier_summary["avg_savings"]
            # Simulate 100K tokens input
            tokens_in = 100000
            tokens_saved = tokens_in * (actual_savings / 100)
            cost_saved = (tokens_saved / 1_000_000) * 3.00  # $3/1M tokens
            print(f"{scenario_name:<35} {actual_savings:>17.1f}% ${cost_saved:>24.4f}")

    # Recommendation
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    tier1_summary = next((s for s in tier_summaries if s["tier"] == "tier1_optimal"), None)
    if tier1_summary and tier1_summary["avg_savings"] > 40:
        print("\n  [STRONG] Use TOON for:")
        print("    - Large uniform arrays (user profiles, product catalogs, event streams)")
        print("    - Time-series data (metrics, logs, monitoring)")
        print("    - API response batching (search results, query responses)")
        print(f"    -> Expected savings: {tier1_summary['avg_savings']:.1f}%")

    tier4_summary = next((s for s in tier_summaries if s["tier"] == "tier4_skip"), None)
    if tier4_summary:
        print("\n  [AVOID] Use JSON instead for:")
        print("    - Deeply nested hierarchies (org charts, menu trees)")
        print("    - Heterogeneous configurations (user preferences)")
        print("    - Polymorphic data (highly variable structures)")
        print(f"    -> TOON overhead: {tier4_summary['avg_savings']:.1f}% (not worth encoding cost)")

    print("\n" + "=" * 100)


def main() -> None:
    """Run LLM-focused benchmarks across all tiers."""
    base_dir = Path(__file__).parent

    tier_dirs = {
        "tier1_optimal": (base_dir / "tier1_optimal", (40.0, 60.0)),
        "tier2_good": (base_dir / "tier2_good", (25.0, 40.0)),
        "tier3_fair": (base_dir / "tier3_fair", (10.0, 25.0)),
        "tier4_skip": (base_dir / "tier4_skip", (-5.0, 5.0)),
    }

    # Check directories exist
    missing_dirs = [name for name, (path, _) in tier_dirs.items() if not path.exists()]
    if missing_dirs:
        print(f"Error: Missing tier directories: {', '.join(missing_dirs)}")
        print("Run generate_llm_benchmarks.py first to create benchmark files.")
        sys.exit(1)

    print("=" * 100)
    print("PyTOON LLM-Focused Benchmark Suite")
    print("=" * 100)
    print("\nBenchmarking TOON performance on real-world LLM data patterns...")

    all_results = []
    tier_summaries = []

    for tier_name, (tier_path, expected_range) in tier_dirs.items():
        json_files = sorted(tier_path.glob("*.json"))
        if not json_files:
            print(f"\nWarning: No JSON files found in {tier_path}")
            continue

        print(f"\n[{tier_name}] Benchmarking {len(json_files)} files...")

        tier_results = []
        for i, filepath in enumerate(json_files, 1):
            print(f"  [{i}/{len(json_files)}] {filepath.name}...", end=" ", flush=True)
            result = benchmark_file(filepath)
            tier_results.append(result)
            all_results.append(result)
            print(f"{result['savings_pct']:+.1f}% | {result['roundtrip']}")

        # Print tier results
        tier_summary = print_tier_results(tier_name, tier_results, expected_range)
        if tier_summary:
            tier_summaries.append(tier_summary)

    # Executive summary
    print_executive_summary(tier_summaries, all_results)

    # Save detailed results
    results_file = base_dir / "llm_benchmark_results.json"
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": tier_summaries,
        "details": all_results,
    }
    with open(results_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
