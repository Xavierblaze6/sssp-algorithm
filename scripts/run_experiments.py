"""
Unified Experiment Runner for SSSP Algorithm Comparison

This script:
1. Generates graphs of multiple sizes
2. Runs Dijkstra, SSSP, and Hybrid on each
3. Records comprehensive metrics (time, reachability, errors)
4. Saves results to CSV for analysis and plotting

Usage:
    python scripts/run_experiments.py
    
Output:
    - results/experiment_results.csv: Comprehensive results for all experiments
"""

import os
import csv
import time
from typing import List, Dict, Any
import sys

# Add parent directory to path so we can import root modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_generator import generate_random_graph, save_graph_to_file
from hybrid_sssp import compare_algorithms, dijkstra_single_source
from sssp_concept import solve_sssp_directed_real_weights


def run_single_experiment(
    graph_size: int,
    edge_multiplier: float = 5.0,
    source: int = 0,
    seed: int = None
) -> List[Dict[str, Any]]:
    print(f"\nGenerating graph: n={graph_size}, m={int(graph_size * edge_multiplier)}...", end=" ")
    n = graph_size
    m = int(n * edge_multiplier)
    graph_dict, edges = generate_random_graph(n, m, connected=True, seed=seed)
    print(f"done ({len(edges)} edges)")

    print(f"  Running algorithms...", end=" ", flush=True)
    results = compare_algorithms(n, edges, source)
    print("done")

    rows = []
    rows.append({
        'graph_size': n,
        'num_edges': len(edges),
        'algorithm': 'dijkstra',
        'runtime_ms': results['dijkstra']['time'] * 1000,
        'reachable': results['dijkstra']['reachable'],
        'num_inf': n - results['dijkstra']['reachable'],
        'num_diff_vs_dijkstra': 0,
        'avg_error_vs_dijkstra': 0.0,
        'k_param': None,
        't_param': None,
    })

    sssp_stats = results['sssp'].get('stats', {}) or {}
    sssp_unreachable = sssp_stats.get('unreachable_count', n - results['sssp']['reachable'])
    k_param = sssp_stats.get('k_param')
    t_param = sssp_stats.get('t_param')
    rows.append({
        'graph_size': n,
        'num_edges': len(edges),
        'algorithm': 'sssp',
        'runtime_ms': results['sssp']['time'] * 1000,
        'reachable': results['sssp']['reachable'],
        'num_inf': sssp_unreachable,
        'num_diff_vs_dijkstra': results['sssp']['mismatches_vs_dijkstra'],
        'avg_error_vs_dijkstra': results['sssp']['avg_error_vs_dijkstra'],
        'k_param': k_param,
        't_param': t_param,
    })

    hybrid = results['hybrid']
    rows.append({
        'graph_size': n,
        'num_edges': len(edges),
        'algorithm': 'hybrid',
        'runtime_ms': hybrid['total_time'] * 1000,
        'reachable': hybrid['total_reachable'],
        'num_inf': n - hybrid['total_reachable'],
        'num_diff_vs_dijkstra': hybrid['mismatches_vs_dijkstra'],
        'avg_error_vs_dijkstra': hybrid['avg_error_vs_dijkstra'],
        'k_param': k_param,
        't_param': t_param,
        'sssp_time_ms': hybrid['sssp_time'] * 1000,
        'dijkstra_fill_time_ms': hybrid['dijkstra_time'] * 1000,
        'sssp_reachable': hybrid['sssp_reachable'],
        'dijkstra_filled': hybrid['dijkstra_filled'],
    })

    print(f"  Results: Dijkstra={results['dijkstra']['time']*1000:.1f}ms, "
          f"SSSP={results['sssp']['time']*1000:.1f}ms ({results['sssp']['reachable']}/{n} reach), "
          f"Hybrid={hybrid['total_time']*1000:.1f}ms")
    return rows


def run_all_experiments(
    graph_sizes: List[int] = None,
    edge_multiplier: float = 5.0,
    num_trials: int = 1,
    output_file: str = "results/experiment_results.csv",
    save_graphs: bool = False
) -> List[Dict[str, Any]]:
    if graph_sizes is None:
        graph_sizes = [50, 100, 500, 1000, 5000, 10000]

    print("="*70)
    print("SSSP ALGORITHM EXPERIMENTS")
    print("="*70)
    print(f"Graph sizes: {graph_sizes}")
    print(f"Edge multiplier: {edge_multiplier}x (m = n * {edge_multiplier})")
    print(f"Trials per size: {num_trials}")
    print(f"Output file: {output_file}")
    print("="*70)

    all_rows = []
    for size_idx, size in enumerate(graph_sizes):
        print(f"\n[{size_idx+1}/{len(graph_sizes)}] Testing graph size n={size}")
        print("-"*70)
        for trial in range(num_trials):
            seed = 42 + size + trial
            if num_trials > 1:
                print(f"  Trial {trial+1}/{num_trials}")
            try:
                rows = run_single_experiment(size, edge_multiplier, source=0, seed=seed)
                for row in rows:
                    row['trial'] = trial + 1
                all_rows.extend(rows)
            except Exception as e:
                print(f"  ERROR in trial {trial+1}: {e}")
                import traceback
                traceback.print_exc()

    if all_rows:
        print(f"\n{'='*70}")
        print(f"Writing results to {output_file}...")
        # Ensure results directory exists
        out_dir = os.path.dirname(output_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        fieldnames = ['trial', 'graph_size', 'num_edges', 'algorithm', 'runtime_ms', 
                      'reachable', 'num_inf', 'num_diff_vs_dijkstra', 'avg_error_vs_dijkstra',
                      'k_param', 't_param', 'sssp_time_ms', 'dijkstra_fill_time_ms',
                      'sssp_reachable', 'dijkstra_filled']
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✓ Saved {len(all_rows)} result rows to {output_file}")
        print("="*70)
    return all_rows


def print_summary_table(results: List[Dict[str, Any]]):
    by_size = {}
    for row in results:
        size = row['graph_size']
        if size not in by_size:
            by_size[size] = {'dijkstra': [], 'sssp': [], 'hybrid': []}
        by_size[size][row['algorithm']].append(row)

    print("\n" + "="*100)
    print("SUMMARY TABLE (averaged over trials)")
    print("="*100)
    print(f"{'Size':<8} {'Algo':<10} {'Time(ms)':<12} {'Reachable':<12} {'INF':<8} {'Diff vs Dijk':<15} {'k/t':<10}")
    print("-"*100)

    for size in sorted(by_size.keys()):
        for algo in ['dijkstra', 'sssp', 'hybrid']:
            rows = by_size[size][algo]
            if not rows:
                continue
            avg_time = sum(r['runtime_ms'] for r in rows) / len(rows)
            avg_reach = sum(r['reachable'] for r in rows) / len(rows)
            avg_inf = sum(r['num_inf'] for r in rows) / len(rows)
            avg_diff = sum(r['num_diff_vs_dijkstra'] for r in rows) / len(rows)
            k_param = rows[0].get('k_param', '')
            t_param = rows[0].get('t_param', '')
            kt_str = f"{k_param}/{t_param}" if k_param else ""
            print(f"{size:<8} {algo:<10} {avg_time:<12.2f} {avg_reach:<12.1f} {avg_inf:<8.1f} {avg_diff:<15.1f} {kt_str:<10}")
        print()
    print("="*100)


if __name__ == "__main__":
    GRAPH_SIZES = [50, 100, 500, 1000, 5000, 10000]
    EDGE_MULTIPLIER = 5.0
    NUM_TRIALS = 1
    OUTPUT_FILE = "results/experiment_results.csv"

    if len(sys.argv) > 1:
        try:
            GRAPH_SIZES = [int(x) for x in sys.argv[1].split(',')]
            print(f"Using custom graph sizes: {GRAPH_SIZES}")
        except:
            print(f"Usage: python scripts/run_experiments.py [sizes]")
            print(f"  sizes: comma-separated list, e.g., '50,100,500'")
            print(f"Using default: {GRAPH_SIZES}")

    results = run_all_experiments(
        graph_sizes=GRAPH_SIZES,
        edge_multiplier=EDGE_MULTIPLIER,
        num_trials=NUM_TRIALS,
        output_file=OUTPUT_FILE
    )

    if results:
        print_summary_table(results)
        print(f"\n✓ Experiments complete!")
        print(f"  Results saved to: {OUTPUT_FILE}")
        print(f"  Total experiments: {len(results)}")
        print(f"\nNext steps:")
        print(f"  1. Analyze results: python scripts/analyze_results.py")
        print(f"  2. Generate plots: python scripts/plot_results.py results/experiment_results.csv")
