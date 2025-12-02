"""
Plot Results from SSSP Experiments

Reads experiment_results.csv and generates plots for presentation:
1. Runtime vs graph size (all algorithms)
2. Number of INF vertices vs graph size
3. Coverage (% reachable) vs graph size
4. Speedup comparison (Hybrid vs Dijkstra)

Usage:
    python plot_results.py [input_csv]
    
Output:
    - PNG files saved to plots/ directory
"""

import csv
import sys
from collections import defaultdict
from typing import List, Dict, Any

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Install with: pip install matplotlib")
    print("Plots will not be generated, but you can still view the CSV data.")


def load_results(filename: str) -> List[Dict[str, Any]]:
    """Load experiment results from CSV."""
    results = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['trial', 'graph_size', 'num_edges', 'runtime_ms', 'reachable', 
                        'num_inf', 'num_diff_vs_dijkstra', 'avg_error_vs_dijkstra',
                        'k_param', 't_param', 'sssp_time_ms', 'dijkstra_fill_time_ms',
                        'sssp_reachable', 'dijkstra_filled']:
                if key in row and row[key] and row[key] != '':
                    try:
                        if key in ['k_param', 't_param', 'trial', 'graph_size', 'num_edges', 
                                   'reachable', 'num_inf', 'num_diff_vs_dijkstra', 
                                   'sssp_reachable', 'dijkstra_filled']:
                            row[key] = int(float(row[key]))
                        else:
                            row[key] = float(row[key])
                    except ValueError:
                        row[key] = None
            results.append(row)
    return results


def aggregate_by_size_and_algo(results: List[Dict[str, Any]]) -> Dict[int, Dict[str, Dict[str, float]]]:
    """
    Aggregate results by graph size and algorithm (averaging over trials).
    
    Returns:
        {size: {algorithm: {metric: value}}}
    """
    by_size_algo = defaultdict(lambda: defaultdict(list))
    
    for row in results:
        size = row['graph_size']
        algo = row['algorithm']
        by_size_algo[(size, algo)].append(row)
    
    aggregated = defaultdict(lambda: defaultdict(dict))
    
    for (size, algo), rows in by_size_algo.items():
        # Average over trials
        aggregated[size][algo] = {
            'runtime_ms': sum(r['runtime_ms'] for r in rows) / len(rows),
            'reachable': sum(r['reachable'] for r in rows) / len(rows),
            'num_inf': sum(r['num_inf'] for r in rows) / len(rows),
            'num_diff': sum(r['num_diff_vs_dijkstra'] for r in rows) / len(rows),
            'avg_error': sum(r['avg_error_vs_dijkstra'] for r in rows) / len(rows),
            'graph_size': size,
        }
        
        # Hybrid-specific
        if algo == 'hybrid' and 'sssp_time_ms' in rows[0] and rows[0]['sssp_time_ms'] is not None:
            aggregated[size][algo]['sssp_time_ms'] = sum(r['sssp_time_ms'] for r in rows) / len(rows)
            aggregated[size][algo]['dijkstra_fill_time_ms'] = sum(r['dijkstra_fill_time_ms'] for r in rows) / len(rows)
            aggregated[size][algo]['sssp_reachable'] = sum(r['sssp_reachable'] for r in rows) / len(rows)
            aggregated[size][algo]['dijkstra_filled'] = sum(r['dijkstra_filled'] for r in rows) / len(rows)
    
    return aggregated


def plot_runtime_comparison(data: Dict, output_file: str = "plots/runtime_comparison.png"):
    """Plot runtime vs graph size for all algorithms."""
    if not HAS_MATPLOTLIB:
        return
    
    sizes = sorted(data.keys())
    
    # Extract data for each algorithm
    algorithms = ['dijkstra', 'sssp', 'hybrid']
    algo_data = {algo: [] for algo in algorithms}
    
    for size in sizes:
        for algo in algorithms:
            if algo in data[size]:
                algo_data[algo].append(data[size][algo]['runtime_ms'])
            else:
                algo_data[algo].append(None)
    
    # Create plot
    plt.figure(figsize=(10, 6))
    
    colors = {'dijkstra': '#2E86AB', 'sssp': '#A23B72', 'hybrid': '#F18F01'}
    markers = {'dijkstra': 'o', 'sssp': 's', 'hybrid': '^'}
    labels = {'dijkstra': 'Dijkstra', 'sssp': 'New SSSP', 'hybrid': 'Hybrid (SSSP+Dijkstra)'}
    
    for algo in algorithms:
        if any(v is not None for v in algo_data[algo]):
            plt.plot(sizes, algo_data[algo], marker=markers[algo], 
                     label=labels[algo], color=colors[algo], linewidth=2, markersize=8)
    
    plt.xlabel('Graph Size (n vertices)', fontsize=12)
    plt.ylabel('Runtime (milliseconds)', fontsize=12)
    plt.title('Algorithm Runtime Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def plot_inf_vertices(data: Dict, output_file: str = "plots/inf_vertices.png"):
    """Plot number of INF vertices vs graph size."""
    if not HAS_MATPLOTLIB:
        return
    
    sizes = sorted(data.keys())
    
    # Extract data for SSSP and Hybrid
    sssp_inf = [data[size]['sssp']['num_inf'] if 'sssp' in data[size] else 0 for size in sizes]
    hybrid_inf = [data[size]['hybrid']['num_inf'] if 'hybrid' in data[size] else 0 for size in sizes]
    
    plt.figure(figsize=(10, 6))
    
    plt.plot(sizes, sssp_inf, marker='s', label='SSSP (before fill)', 
             color='#A23B72', linewidth=2, markersize=8)
    plt.plot(sizes, hybrid_inf, marker='^', label='Hybrid (after Dijkstra fill)', 
             color='#F18F01', linewidth=2, markersize=8)
    
    plt.xlabel('Graph Size (n vertices)', fontsize=12)
    plt.ylabel('Number of INF Vertices', fontsize=12)
    plt.title('Unreachable Vertices (INF) by Algorithm', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def plot_coverage(data: Dict, output_file: str = "plots/coverage.png"):
    """Plot coverage (% reachable) vs graph size."""
    if not HAS_MATPLOTLIB:
        return
    
    sizes = sorted(data.keys())
    
    # Calculate coverage percentage
    dijkstra_coverage = []
    sssp_coverage = []
    hybrid_coverage = []
    
    for size in sizes:
        total = size
        
        if 'dijkstra' in data[size]:
            dijkstra_coverage.append(100.0 * data[size]['dijkstra']['reachable'] / total)
        else:
            dijkstra_coverage.append(None)
        
        if 'sssp' in data[size]:
            sssp_coverage.append(100.0 * data[size]['sssp']['reachable'] / total)
        else:
            sssp_coverage.append(None)
        
        if 'hybrid' in data[size]:
            hybrid_coverage.append(100.0 * data[size]['hybrid']['reachable'] / total)
        else:
            hybrid_coverage.append(None)
    
    plt.figure(figsize=(10, 6))
    
    plt.plot(sizes, dijkstra_coverage, marker='o', label='Dijkstra', 
             color='#2E86AB', linewidth=2, markersize=8)
    plt.plot(sizes, sssp_coverage, marker='s', label='SSSP', 
             color='#A23B72', linewidth=2, markersize=8)
    plt.plot(sizes, hybrid_coverage, marker='^', label='Hybrid', 
             color='#F18F01', linewidth=2, markersize=8)
    
    plt.xlabel('Graph Size (n vertices)', fontsize=12)
    plt.ylabel('Coverage (% Reachable)', fontsize=12)
    plt.title('Algorithm Coverage: Reachable Vertices', fontsize=14, fontweight='bold')
    plt.ylim(0, 105)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def plot_speedup(data: Dict, output_file: str = "plots/speedup_comparison.png"):
    """Plot speedup of SSSP and Hybrid vs Dijkstra baseline."""
    if not HAS_MATPLOTLIB:
        return
    
    sizes = sorted(data.keys())
    
    sssp_speedup = []
    hybrid_speedup = []
    
    for size in sizes:
        dijk_time = data[size]['dijkstra']['runtime_ms']
        
        if 'sssp' in data[size]:
            sssp_time = data[size]['sssp']['runtime_ms']
            sssp_speedup.append(dijk_time / sssp_time if sssp_time > 0 else 1.0)
        else:
            sssp_speedup.append(None)
        
        if 'hybrid' in data[size]:
            hybrid_time = data[size]['hybrid']['runtime_ms']
            hybrid_speedup.append(dijk_time / hybrid_time if hybrid_time > 0 else 1.0)
        else:
            hybrid_speedup.append(None)
    
    plt.figure(figsize=(10, 6))
    
    # Horizontal line at speedup=1 (baseline)
    plt.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, label='Dijkstra baseline', alpha=0.5)
    
    plt.plot(sizes, sssp_speedup, marker='s', label='SSSP speedup', 
             color='#A23B72', linewidth=2, markersize=8)
    plt.plot(sizes, hybrid_speedup, marker='^', label='Hybrid speedup', 
             color='#F18F01', linewidth=2, markersize=8)
    
    plt.xlabel('Graph Size (n vertices)', fontsize=12)
    plt.ylabel('Speedup vs Dijkstra (×)', fontsize=12)
    plt.title('Runtime Speedup Comparison (Dijkstra = 1.0×)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def plot_hybrid_breakdown(data: Dict, output_file: str = "plots/hybrid_breakdown.png"):
    """Plot stacked bar chart showing SSSP vs Dijkstra fill time in hybrid approach."""
    if not HAS_MATPLOTLIB:
        return
    
    sizes = sorted(data.keys())
    
    sssp_times = []
    dijkstra_fill_times = []
    
    for size in sizes:
        if 'hybrid' in data[size]:
            hybrid_data = data[size]['hybrid']
            if 'sssp_time_ms' in hybrid_data:
                sssp_times.append(hybrid_data['sssp_time_ms'])
                dijkstra_fill_times.append(hybrid_data['dijkstra_fill_time_ms'])
            else:
                sssp_times.append(0)
                dijkstra_fill_times.append(0)
        else:
            sssp_times.append(0)
            dijkstra_fill_times.append(0)
    
    plt.figure(figsize=(10, 6))
    
    x = range(len(sizes))
    width = 0.6
    
    plt.bar(x, sssp_times, width, label='SSSP Phase', color='#A23B72')
    plt.bar(x, dijkstra_fill_times, width, bottom=sssp_times, 
            label='Dijkstra Fill Phase', color='#F18F01')
    
    plt.xlabel('Graph Size (n vertices)', fontsize=12)
    plt.ylabel('Runtime (milliseconds)', fontsize=12)
    plt.title('Hybrid Algorithm Time Breakdown', fontsize=14, fontweight='bold')
    plt.xticks(x, [str(s) for s in sizes])
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def generate_all_plots(input_csv: str = "experiment_results.csv", output_dir: str = "plots"):
    """Generate all plots from experiment results."""
    import os
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load and aggregate data
    print(f"\nLoading results from {input_csv}...")
    results = load_results(input_csv)
    print(f"  Loaded {len(results)} result rows")
    
    print(f"\nAggregating data by size and algorithm...")
    data = aggregate_by_size_and_algo(results)
    print(f"  Found {len(data)} unique graph sizes")
    
    if not HAS_MATPLOTLIB:
        print("\nSkipping plots (matplotlib not installed)")
        return
    
    # Generate plots
    print(f"\nGenerating plots to {output_dir}/...")
    
    plot_runtime_comparison(data, f"{output_dir}/runtime_comparison.png")
    plot_inf_vertices(data, f"{output_dir}/inf_vertices.png")
    plot_coverage(data, f"{output_dir}/coverage.png")
    plot_speedup(data, f"{output_dir}/speedup_comparison.png")
    plot_hybrid_breakdown(data, f"{output_dir}/hybrid_breakdown.png")
    
    print(f"\n✓ All plots generated successfully!")
    print(f"  Location: {output_dir}/")
    print(f"\nPlots created:")
    print(f"  1. runtime_comparison.png - Runtime vs graph size")
    print(f"  2. inf_vertices.png - Unreachable vertices")
    print(f"  3. coverage.png - Coverage percentage")
    print(f"  4. speedup_comparison.png - Speedup vs Dijkstra")
    print(f"  5. hybrid_breakdown.png - Hybrid time breakdown")


if __name__ == "__main__":
    input_file = "experiment_results.csv"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    try:
        generate_all_plots(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
        print(f"Please run 'python run_experiments.py' first to generate results.")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating plots: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
