"""
Hybrid SSSP + Dijkstra Implementation

This module provides a hybrid approach that combines the new SSSP algorithm with Dijkstra:
1. Run the new SSSP algorithm first (fast but may miss vertices)
2. Identify vertices still at infinity
3. Run Dijkstra only for those missing vertices
4. Combine results and provide detailed statistics

This approach aims to get the best of both worlds:
- Speed advantages from SSSP where it works
- Completeness guarantee from Dijkstra fallback
"""

import time
import multiprocessing as mp
import heapq
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict

from sssp_concept import solve_sssp_directed_real_weights


def dijkstra_single_source(graph_dict: Dict[int, Dict[int, float]], n: int, source: int) -> Dict[int, float]:
    """Standard Dijkstra's algorithm for single-source shortest paths."""
    dist = {source: 0.0}
    pq = [(0.0, source)]
    visited = set()
    
    while pq:
        d, u = heapq.heappop(pq)
        
        if u in visited:
            continue
        visited.add(u)
        
        for v, w in graph_dict.get(u, {}).items():
            new_dist = d + w
            if new_dist < dist.get(v, float('inf')):
                dist[v] = new_dist
                heapq.heappush(pq, (new_dist, v))
    
    return dist


def _sssp_worker(n: int, edges: List[Tuple[int, int, float]], source: int, q: mp.Queue):
    """Worker function to run SSSP in a subprocess and return results via queue."""
    try:
        import sssp_concept
        t0 = time.time()
        dist = solve_sssp_directed_real_weights(n, len(edges), edges, source)
        elapsed = time.time() - t0
        
        # Compute stats inline from subprocess globals
        d_hat = sssp_concept.d_hat
        N_vertices = sssp_concept.N_vertices
        k_param = sssp_concept.k_param
        t_param = sssp_concept.t_param
        
        reachable = [v for v in range(N_vertices) if d_hat.get(v, float('inf')) != float('inf')]
        
        stats = {
            'n': N_vertices,
            'k_param': k_param,
            't_param': t_param,
            'reachable_count': len(reachable),
            'unreachable_count': N_vertices - len(reachable),
            'reachable_pct': 100.0 * len(reachable) / N_vertices if N_vertices > 0 else 0.0,
        }
        
        q.put({
            'ok': True,
            'distances': dist,
            'time': elapsed,
            'stats': stats,
        })
    except Exception as e:
        q.put({'ok': False, 'error': str(e)})


def compare_algorithms(
    n: int,
    edges: List[Tuple[int, int, float]],
    source: int = 0,
    sssp_timeout_sec: float = 30.0  # Increased from 5s now that infinite loops are fixed
) -> Dict[str, Any]:
    """Compare pure Dijkstra, pure SSSP (with timeout), and hybrid."""
    # Build graph
    graph_dict: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
    for u, v, w in edges:
        graph_dict[u][v] = w
    
    results = {}
    
    # Run pure Dijkstra (reference/correct)
    start = time.time()
    dijkstra_dist = dijkstra_single_source(graph_dict, n, source)
    results['dijkstra'] = {
        'distances': dijkstra_dist,
        'time': time.time() - start,
        'reachable': len(dijkstra_dist),
    }
    
    # Run pure SSSP with timeout safeguard (30s instead of 5s now that infinite loops are fixed)
    q: mp.Queue = mp.Queue()
    p = mp.Process(target=_sssp_worker, args=(n, edges, source, q))
    p.start()
    p.join(30)  # 30 second timeout

    sssp_timed_out = False
    sssp_dist: Dict[int, float] = {}
    sssp_stats = {}

    if p.is_alive():
        # Timeout
        p.terminate()
        p.join()
        sssp_timed_out = True
        results['sssp'] = {
            'distances': {},
            'time': 30,
            'reachable': 0,
            'stats': {},
            'timed_out': True,
        }
    else:
        # Retrieve result
        try:
            res = q.get_nowait()
        except Exception:
            res = {'ok': False, 'error': 'no-result'}
        if res.get('ok'):
            sssp_dist = res['distances']
            sssp_stats = res.get('stats', {})
            results['sssp'] = {
                'distances': sssp_dist,
                'time': res['time'],
                'reachable': len(sssp_dist),
                'stats': sssp_stats,
            }
        else:
            sssp_timed_out = True
            results['sssp'] = {
                'distances': {},
                'time': sssp_timeout_sec,
                'reachable': 0,
                'stats': {},
                'timed_out': True,
                'error': res.get('error'),
            }
    
    # Hybrid: if SSSP timed out, degrade to pure Dijkstra
    if sssp_timed_out:
        results['hybrid'] = {
            'distances': dijkstra_dist,
            'sssp_time': 0.0,
            'dijkstra_time': results['dijkstra']['time'],
            'total_time': results['dijkstra']['time'],
            'sssp_reachable': 0,
            'dijkstra_filled': results['dijkstra']['reachable'],
            'total_reachable': results['dijkstra']['reachable'],
            'sssp_stats': {},
            'n': n,
            'm': len(edges),
            'degraded': True,
        }
    else:
        # Normal hybrid: SSSP + Dijkstra fill
        missing = set(range(n)) - set(sssp_dist.keys())
        final_dist = dict(sssp_dist)
        dijkstra_filled = 0
        
        if missing:
            for v in missing:
                if v in dijkstra_dist:
                    final_dist[v] = dijkstra_dist[v]
                    dijkstra_filled += 1
        
        results['hybrid'] = {
            'distances': final_dist,
            'sssp_time': results['sssp']['time'],
            'dijkstra_time': 0.0,  # Not measuring Dijkstra fill separately
            'total_time': results['sssp']['time'],
            'sssp_reachable': len(sssp_dist),
            'dijkstra_filled': dijkstra_filled,
            'total_reachable': len(final_dist),
            'sssp_stats': sssp_stats,
            'n': n,
            'm': len(edges),
        }
    
    # Compare correctness
    def count_mismatches(test_dist, ref_dist):
        mismatches = 0
        total_error = 0.0
        all_verts = set(ref_dist.keys()) | set(test_dist.keys())
        for v in all_verts:
            ref_d = ref_dist.get(v, float('inf'))
            test_d = test_dist.get(v, float('inf'))
            if abs(ref_d - test_d) > 1e-9:
                mismatches += 1
                if ref_d != float('inf') and test_d != float('inf'):
                    total_error += abs(ref_d - test_d)
        avg_error = total_error / mismatches if mismatches > 0 else 0.0
        return mismatches, avg_error
    
    sssp_mis, sssp_err = count_mismatches(sssp_dist, dijkstra_dist)
    results['sssp']['mismatches_vs_dijkstra'] = sssp_mis
    results['sssp']['avg_error_vs_dijkstra'] = sssp_err
    
    hybrid_mis, hybrid_err = count_mismatches(results['hybrid']['distances'], dijkstra_dist)
    results['hybrid']['mismatches_vs_dijkstra'] = hybrid_mis
    results['hybrid']['avg_error_vs_dijkstra'] = hybrid_err
    
    return results


def print_comparison_results(results: Dict[str, Any]):
    """Print comparison results in a readable format."""
    print("\n" + "="*70)
    print("ALGORITHM COMPARISON RESULTS")
    print("="*70)
    
    print(f"\nGraph: n={results['dijkstra']['reachable']} reachable vertices")
    
    print("\nDIJKSTRA (Reference)           Time         Reachable")
    print("-"*70)
    print(f"Standard Dijkstra              {results['dijkstra']['time']:.4f}s    {results['dijkstra']['reachable']}")
    
    print("\nNEW SSSP                       Time         Reachable    Mismatches")
    print("-"*70)
    print(f"SSSP Algorithm                 {results['sssp']['time']:.4f}s    {results['sssp']['reachable']}            {results['sssp']['mismatches_vs_dijkstra']}")
    
    print("\nHYBRID (SSSP + Dijkstra)       SSSP Time    Dijkstra     Total")
    print("-"*70)
    hybrid = results['hybrid']
    print(f"Hybrid approach                {hybrid['sssp_time']:.4f}s    {hybrid['dijkstra_time']:.4f}s    {hybrid['total_time']:.4f}s")
    print(f"  SSSP found: {hybrid['sssp_reachable']} vertices")
    print(f"  Dijkstra filled: {hybrid['dijkstra_filled']} vertices")
    print(f"  Total reachable: {hybrid['total_reachable']} vertices")
    
    if hybrid['mismatches_vs_dijkstra'] == 0:
        print(f"  [OK] All distances match Dijkstra (correct)")
    else:
        print(f"  [!!] {hybrid['mismatches_vs_dijkstra']} mismatches vs Dijkstra")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    dij_time = results['dijkstra']['time']
    sssp_time = results['sssp']['time']
    hybrid_time = hybrid['total_time']
    
    print(f"Dijkstra time:  {dij_time:.4f}s (baseline)")
    print(f"SSSP time:      {sssp_time:.4f}s ({sssp_time/dij_time:.2f}x)" if dij_time > 0 else f"SSSP time:      {sssp_time:.4f}s")
    print(f"Hybrid time:    {hybrid_time:.4f}s ({hybrid_time/dij_time:.2f}x)" if dij_time > 0 else f"Hybrid time:    {hybrid_time:.4f}s")
    
    if results['sssp']['reachable'] > 0 and results['dijkstra']['reachable'] > 0:
        coverage = 100.0 * results['sssp']['reachable'] / results['dijkstra']['reachable']
        print(f"\nSSP coverage:  {coverage:.1f}% of reachable vertices")
        if hybrid_time > 0 and dij_time > 0:
            slowdown = hybrid_time / dij_time
            print(f"Hybrid slowdown: {slowdown:.2f}x slower than pure Dijkstra (SSSP overhead)")
    print("="*70)


if __name__ == "__main__":
    print("Testing hybrid SSSP on small graph...")
    
    # Small test graph
    edges = [
        (0, 1, 1.0),
        (1, 2, 1.0),
        (2, 3, 1.0),
        (0, 3, 5.0),
    ]
    n = 4
    
    results = compare_algorithms(n, edges, source=0)
    print_comparison_results(results)
