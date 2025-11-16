#!/usr/bin/env python3
"""
Benchmark Runner for PyToon

Runs comprehensive benchmarks on all sample files, measuring token savings,
encoding/decoding performance, and roundtrip fidelity.
"""

import json
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytoon
from pytoon.utils.tokens import TokenCounter


def benchmark_file(filepath: Path) -> dict:
    """Benchmark a single JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    counter = TokenCounter()

    # JSON baseline
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
            "tier": filepath.name[0],
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
            "tier": filepath.name[0],
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
        "tier": filepath.name[0],
        "json_bytes": json_bytes,
        "json_tokens": json_tokens,
        "toon_bytes": toon_bytes,
        "toon_tokens": toon_tokens,
        "savings_pct": savings_pct,
        "encode_ms": encode_time,
        "decode_ms": decode_time,
        "roundtrip": "PASS" if roundtrip_ok else "FAIL",
    }


def print_results_table(results: list[dict]) -> None:
    """Print formatted results table."""
    print("\n" + "=" * 120)
    print("PYTOON BENCHMARK RESULTS")
    print("=" * 120)

    # Header
    print(
        f"{'File':<40} {'JSON Tokens':>12} {'TOON Tokens':>12} {'Savings':>10} "
        f"{'Enc (ms)':>10} {'Dec (ms)':>10} {'Roundtrip':>10}"
    )
    print("-" * 120)

    # Group by tier
    current_tier = None
    tier_results = []

    for result in sorted(results, key=lambda x: x["file"]):
        tier = result["tier"]

        if tier != current_tier:
            if current_tier is not None:
                print_tier_summary(current_tier, tier_results)
                print("-" * 120)
            current_tier = tier
            tier_results = []

        tier_results.append(result)

        savings_str = f"{result['savings_pct']:+.1f}%"
        if result["savings_pct"] > 30:
            savings_str = f"\033[92m{savings_str}\033[0m"  # Green
        elif result["savings_pct"] < 0:
            savings_str = f"\033[91m{savings_str}\033[0m"  # Red
        elif result["savings_pct"] < 10:
            savings_str = f"\033[93m{savings_str}\033[0m"  # Yellow

        roundtrip_str = result["roundtrip"]
        if roundtrip_str == "PASS":
            roundtrip_str = f"\033[92m{roundtrip_str}\033[0m"
        else:
            roundtrip_str = f"\033[91m{roundtrip_str}\033[0m"

        print(
            f"{result['file']:<40} {result['json_tokens']:>12,} {result['toon_tokens']:>12,} "
            f"{savings_str:>20} {result['encode_ms']:>10.2f} {result['decode_ms']:>10.2f} "
            f"{roundtrip_str:>20}"
        )

    # Last tier summary
    if current_tier is not None:
        print_tier_summary(current_tier, tier_results)

    print("=" * 120)


def print_tier_summary(tier: str, results: list[dict]) -> None:
    """Print summary for a tier."""
    tier_names = {
        "A": "TIER A: TOON Optimal (Expected 40-60%+)",
        "B": "TIER B: TOON Strong (Expected 25-40%)",
        "C": "TIER C: TOON Moderate (Expected 10-25%)",
        "D": "TIER D: Minimal/Negative (Expected 0-15% or worse)",
    }

    if not results:
        return

    avg_savings = sum(r["savings_pct"] for r in results) / len(results)
    total_json_tokens = sum(r["json_tokens"] for r in results)
    total_toon_tokens = sum(r["toon_tokens"] for r in results)
    overall_savings = (
        (1 - total_toon_tokens / total_json_tokens) * 100 if total_json_tokens > 0 else 0
    )
    pass_count = sum(1 for r in results if r["roundtrip"] == "PASS")

    print(f"\n  {tier_names.get(tier, f'TIER {tier}')}")
    print(
        f"  Files: {len(results)} | Avg Savings: {avg_savings:.1f}% | Overall Savings: {overall_savings:.1f}%"
    )
    print(f"  Roundtrip: {pass_count}/{len(results)} PASS\n")


def print_overall_summary(results: list[dict]) -> None:
    """Print overall summary statistics."""
    print("\n" + "=" * 120)
    print("OVERALL SUMMARY")
    print("=" * 120)

    total_files = len(results)
    total_json_tokens = sum(r["json_tokens"] for r in results)
    total_toon_tokens = sum(r["toon_tokens"] for r in results)
    overall_savings = (
        (1 - total_toon_tokens / total_json_tokens) * 100 if total_json_tokens > 0 else 0
    )

    avg_savings = sum(r["savings_pct"] for r in results) / len(results)
    min_savings = min(r["savings_pct"] for r in results)
    max_savings = max(r["savings_pct"] for r in results)

    pass_count = sum(1 for r in results if r["roundtrip"] == "PASS")
    fail_count = total_files - pass_count

    total_encode_time = sum(r["encode_ms"] for r in results)
    total_decode_time = sum(r["decode_ms"] for r in results)

    print(f"Files Benchmarked: {total_files}")
    print(f"Total JSON Tokens: {total_json_tokens:,}")
    print(f"Total TOON Tokens: {total_toon_tokens:,}")
    print(
        f"Overall Token Savings: {overall_savings:.1f}% ({total_json_tokens - total_toon_tokens:,} tokens saved)"
    )
    print()
    print(f"Average Savings per File: {avg_savings:.1f}%")
    print(f"Min Savings: {min_savings:.1f}%")
    print(f"Max Savings: {max_savings:.1f}%")
    print()
    print(
        f"Roundtrip Fidelity: {pass_count}/{total_files} PASS ({pass_count / total_files * 100:.1f}%)"
    )
    if fail_count > 0:
        failed_files = [r["file"] for r in results if r["roundtrip"] != "PASS"]
        print(f"  Failed: {', '.join(failed_files)}")
    print()
    print(f"Total Encoding Time: {total_encode_time:.2f}ms")
    print(f"Total Decoding Time: {total_decode_time:.2f}ms")

    # Tier breakdown
    print("\nTier Breakdown:")
    for tier in ["A", "B", "C", "D"]:
        tier_results = [r for r in results if r["tier"] == tier]
        if tier_results:
            tier_savings = sum(r["savings_pct"] for r in tier_results) / len(tier_results)
            tier_pass = sum(1 for r in tier_results if r["roundtrip"] == "PASS")
            print(
                f"  Tier {tier}: {tier_savings:.1f}% avg savings, {tier_pass}/{len(tier_results)} pass"
            )

    print("=" * 120)


def main() -> None:
    """Run benchmarks on all sample files."""
    samples_dir = Path(__file__).parent / "samples"

    if not samples_dir.exists():
        print(f"Error: Samples directory not found at {samples_dir}")
        print("Run generate_samples.py first to create benchmark files.")
        sys.exit(1)

    json_files = sorted(samples_dir.glob("*.json"))

    if not json_files:
        print(f"Error: No JSON files found in {samples_dir}")
        sys.exit(1)

    print(f"PyToon Benchmark Suite")
    print(f"Found {len(json_files)} benchmark files")
    print()

    results = []
    for i, filepath in enumerate(json_files, 1):
        print(f"[{i}/{len(json_files)}] Benchmarking {filepath.name}...", end=" ", flush=True)
        result = benchmark_file(filepath)
        results.append(result)
        print(f"{result['savings_pct']:+.1f}% | {result['roundtrip']}")

    print_results_table(results)
    print_overall_summary(results)

    # Save results to JSON
    results_file = Path(__file__).parent / "benchmark_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
