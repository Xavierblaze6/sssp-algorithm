"""
Summary report of SSSP algorithm performance
"""
import csv

print("=" * 80)
print("SSSP ALGORITHM PERFORMANCE SUMMARY")
print("=" * 80)
print()

with open('experiment_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    results = list(reader)

# Group by size
by_size = {}
for row in results:
    n = int(row['graph_size'])
    if n not in by_size:
        by_size[n] = {}
    algo = row['algorithm']
    by_size[n][algo] = row

print("Performance Comparison:")
print("-" * 80)
print(f"{'Size':<10} {'SSSP Time':<15} {'Dijk Time':<15} {'Coverage':<15} {'Status'}")
print("-" * 80)

for n in sorted(by_size.keys()):
    sssp = by_size[n]['sssp']
    dijk = by_size[n]['dijkstra']
    
    sssp_time = float(sssp['runtime_ms'])
    dijk_time = float(dijk['runtime_ms'])
    
    sssp_reachable = int(sssp['reachable'])
    total_vertices = int(sssp['graph_size'])
    coverage_pct = (sssp_reachable / total_vertices) * 100
    
    # Status
    if sssp_time > 5000:
        status = "[TIMEOUT]"
        speedup = "---"
    elif sssp_time < dijk_time:
        speedup = f"{dijk_time/sssp_time:.2f}x slower"
        status = "[SLOW]"
    else:
        speedup = f"{sssp_time/dijk_time:.2f}x slower"
        status = "[SLOW]"
    
    print(f"{n:<10} {sssp_time:<15.2f} {dijk_time:<15.2f} {coverage_pct:<14.1f}% {status}")

print("-" * 80)
print()
print("Key Findings:")
print("-" * 80)

# Calculate averages for successful cases
successful = [(int(r['graph_size']), float(r['runtime_ms'])) for r in results 
              if r['algorithm'] == 'sssp' and float(r['runtime_ms']) < 5000]

if successful:
    avg_n = sum(n for n, _ in successful) / len(successful)
    avg_time = sum(t for _, t in successful) / len(successful)
    print(f"✓ Successfully completed on {len(successful)} graph sizes")
    print(f"✓ Average time for successful runs: {avg_time:.2f}ms on graphs of avg size {avg_n:.0f}")
    
timed_out = sum(1 for r in results if r['algorithm'] == 'sssp' and float(r['runtime_ms']) >= 5000)
if timed_out:
    print(f"✗ Timed out on {timed_out} graph sizes (n ≥ 5000)")

print()
print("Algorithm Behavior:")
print("-" * 80)
for n in sorted(by_size.keys()):
    sssp = by_size[n]['sssp']
    coverage = int(sssp['reachable']) / int(sssp['graph_size']) * 100
    
    if n <= 100:
        print(f"n={n:5d}: Excellent coverage ({coverage:.0f}%), fast completion")
    elif n <= 1000:
        print(f"n={n:5d}: Good performance but coverage drops to {coverage:.0f}%")
    else:
        print(f"n={n:5d}: Algorithm encounters stalls, breaks early for safety")

print()
print("=" * 80)
