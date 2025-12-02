"""
Quick diagnostic test to understand why SSSP hangs on n=50
"""
import time
from graph_generator import generate_random_graph
from sssp_concept import solve_sssp_directed_real_weights
import sssp_concept

# Test with small graph first
print("Testing n=10 (should be fast)...")
graph_dict, edges = generate_random_graph(10, 50, connected=True, seed=42)

# Enable instrumentation
sssp_concept.INSTRUMENT = True

t0 = time.time()
try:
    result = solve_sssp_directed_real_weights(10, len(edges), edges, 0)
    elapsed = time.time() - t0
    print(f"\nCompleted n=10 in {elapsed:.3f}s")
    print(f"Found {len(result)}/10 vertices")
    print(f"k_param={sssp_concept.k_param}, t_param={sssp_concept.t_param}")
except Exception as e:
    print(f"ERROR: {e}")

# Now try n=50 with timeout monitoring
print("\n" + "="*60)
print("Testing n=50 with instrumentation...")
print("="*60)
graph_dict, edges = generate_random_graph(50, 250, connected=True, seed=42)

t0 = time.time()
max_time = 2.0  # 2 second test
try:
    result = solve_sssp_directed_real_weights(50, len(edges), edges, 0)
    elapsed = time.time() - t0
    print(f"\nCompleted n=50 in {elapsed:.3f}s")
    print(f"Found {len(result)}/50 vertices")
    print(f"k_param={sssp_concept.k_param}, t_param={sssp_concept.t_param}")
except KeyboardInterrupt:
    elapsed = time.time() - t0
    print(f"\n\nInterrupted after {elapsed:.3f}s")
    print(f"k_param={sssp_concept.k_param}, t_param={sssp_concept.t_param}")
