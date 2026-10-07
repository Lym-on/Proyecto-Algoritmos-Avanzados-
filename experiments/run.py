#!/usr/bin/env python3
"""
Reproducible experiment runner.

Runs benchmark across multiple configurations and saves results to CSV/JSON.
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark import run_experiment, ExperimentResult
from workloads import get_workload_config


DEFAULT_SIZES = [100, 500, 1000, 2000, 5000]
DEFAULT_QUERIES = 5000
DEFAULT_SEEDS = [42, 123, 456, 789, 999]
DEFAULT_LAMBDAS = [0.0, 0.1, 1.0, 10.0]
DEFAULT_WORKLOADS = [
    ("uniform", {}),
    ("locality", {"hot_fraction": 0.2, "query_hot_fraction": 0.8}),
    ("zipf", {"alpha": 0.5}),
    ("zipf", {"alpha": 1.0}),
    ("zipf", {"alpha": 1.5}),
    ("zipf", {"alpha": 2.0}),
    ("sequential_asc", {}),
    ("sequential_desc", {}),
    ("sequential_zigzag", {}),
    ("hot_switch", {"switch_every": 1000, "hot_fraction": 0.1}),
]


def run_all_experiments(
    sizes: List[int] = None,
    queries: int = DEFAULT_QUERIES,
    seeds: List[int] = None,
    lambdas: List[float] = None,
    workloads: List[tuple] = None,
    output_dir: str = "results"
) -> List[ExperimentResult]:
    """Run all experiment combinations and return list of results."""
    if sizes is None:
        sizes = DEFAULT_SIZES
    if seeds is None:
        seeds = DEFAULT_SEEDS
    if lambdas is None:
        lambdas = DEFAULT_LAMBDAS
    if workloads is None:
        workloads = DEFAULT_WORKLOADS

    os.makedirs(output_dir, exist_ok=True)
    all_results = []
    total = len(sizes) * len(seeds) * len(lambdas) * len(workloads)
    count = 0

    for n_blocks in sizes:
        tx_per_block = max(1, 5000 // n_blocks)  # keep total tx ~5000
        for seed in seeds:
            for lambda_val in lambdas:
                for workload_name, workload_params in workloads:
                    count += 1
                    print(f"[{count}/{total}] n_blocks={n_blocks}, seed={seed}, λ={lambda_val}, workload={workload_name}")
                    try:
                        results = run_experiment(
                            n_blocks=n_blocks,
                            tx_per_block=tx_per_block,
                            n_queries=queries,
                            seed=seed,
                            workload=workload_name,
                            workload_params=workload_params,
                            lambda_val=lambda_val
                        )
                        # Add config metadata
                        for r in results:
                            r_dict = vars(r)
                            r_dict.update({
                                "n_blocks": n_blocks,
                                "tx_per_block": tx_per_block,
                                "lambda": lambda_val,
                            })
                            all_results.append(r)
                    except Exception as e:
                        print(f"  ERROR: {e}")
    
    return all_results


def save_results_csv(results: List[ExperimentResult], output_dir: str = "results"):
    """Save results to CSV."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = Path(output_dir) / f"experiment_results_{timestamp}.csv"
    
    if not results:
        print("No results to save")
        return
    
    fieldnames = list(vars(results[0]).keys())
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(vars(r))
    print(f"Results saved to {filename}")
    return filename


def save_results_json(results: List[ExperimentResult], output_dir: str = "results"):
    """Save results to JSON with metadata."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = Path(output_dir) / f"experiment_results_{timestamp}.json"
    
    data = {
        "metadata": {
            "timestamp": timestamp,
            "total_experiments": len(results),
        },
        "results": [vars(r) for r in results]
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {filename}")
    return filename


def save_manifest(output_dir: str = "results", **config):
    """Save experiment manifest with configuration."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = Path(output_dir) / f"manifest_{timestamp}.json"
    config["timestamp"] = timestamp
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    return filename


def main():
    parser = argparse.ArgumentParser(description="Run reproducible tree benchmark experiments")
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES,
                        help="Blockchain sizes (number of blocks)")
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES,
                        help="Number of queries per experiment")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS,
                        help="Random seeds for repetitions")
    parser.add_argument("--lambdas", type=float, nargs="+", default=DEFAULT_LAMBDAS,
                        help="Lambda values for reorganization cost")
    parser.add_argument("--workloads", nargs="+", default=None,
                        help="Workload names (default: all)")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--quick", action="store_true",
                        help="Run quick test with reduced parameters")
    args = parser.parse_args()

    if args.quick:
        sizes = [100, 500]
        seeds = [42]
        lambdas = [1.0]
        workloads = [("uniform", {}), ("zipf", {"alpha": 1.0}), ("locality", {})]
    else:
        sizes = args.sizes
        seeds = args.seeds
        lambdas = args.lambdas
        if args.workloads:
            workloads = [(w, get_workload_config(w)) for w in args.workloads]
        else:
            workloads = DEFAULT_WORKLOADS

    print("Starting experiment run...")
    print(f"Sizes: {sizes}")
    print(f"Seeds: {seeds}")
    print(f"Lambdas: {lambdas}")
    print(f"Workloads: {[w[0] for w in workloads]}")
    print(f"Queries per experiment: {args.queries}")
    print()

    start = time.time()
    results = run_all_experiments(
        sizes=sizes,
        queries=args.queries,
        seeds=seeds,
        lambdas=lambdas,
        workloads=workloads,
        output_dir=args.output
    )
    elapsed = time.time() - start

    print(f"\nCompleted {len(results)} algorithm runs in {elapsed:.1f}s")

    # Save results
    csv_file = save_results_csv(results, args.output)
    json_file = save_results_json(results, args.output)
    manifest_file = save_manifest(args.output,
        sizes=sizes,
        queries=args.queries,
        seeds=seeds,
        lambdas=lambdas,
        workloads=[w[0] for w in workloads],
        total_results=len(results),
        elapsed_seconds=elapsed
    )

    print(f"\nOutput files:")
    print(f"  CSV: {csv_file}")
    print(f"  JSON: {json_file}")
    print(f"  Manifest: {manifest_file}")


if __name__ == "__main__":
    main()