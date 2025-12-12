import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hybrid_sssp import compare_algorithms
from graph_generator import generate_random_graph

if __name__ == '__main__':
    for n in [50, 100, 200]:
        _, edges = generate_random_graph(n, n * 2, seed=42)
        r = compare_algorithms(n, edges, 0, 30)
        
        sssp_status = "TIMED OUT" if r['sssp'].get('timed_out') else "OK"
        print(f"n={n:4d}: SSSP {sssp_status:9s} in {r['sssp']['time']:6.3f}s, found {r['sssp']['reachable']:4d}/{r['dijkstra']['reachable']:4d} vertices")
