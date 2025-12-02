"""
Reference Dijkstra Implementation
Compare results with the SSSP algorithm to identify correctness issues
"""

import sys
sys.path.insert(0, '/mnt/project')
import heapq
from collections import defaultdict
from sssp_concept import solve_sssp_directed_real_weights

def dijkstra(n, edges, source):
    """Standard Dijkstra's algorithm - O(m + n log n) time"""
    # Build adjacency list
    graph = defaultdict(dict)
    for u, v, w in edges:
        graph[u][v] = w

    # Initialize
    dist = {source: 0.0}
    pred = {source: None}
    pq = [(0.0, source)]
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        # Relax outgoing edges
        for v, w in graph[u].items():
            new_dist = d + w
            if new_dist < dist.get(v, float('inf')):
                dist[v] = new_dist
                pred[v] = u
                heapq.heappush(pq, (new_dist, v))

    return dist, pred

def reconstruct_path(pred, source, target):
    """Reconstruct path from source to target"""
    if target not in pred:
        return None
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = pred.get(curr)
    path.reverse()
    return path

def compare_algorithms(n, edges, source):
    """Compare Dijkstra with SSSP algorithm"""
    print("=" * 70)
    print("ALGORITHM COMPARISON")
    print("=" * 70)

    # Run Dijkstra (correct reference)
    print("\n1. Running Dijkstra's algorithm (CORRECT reference)...")
    dijkstra_dist, dijkstra_pred = dijkstra(n, edges, source)

    # Run SSSP algorithm
    print("2. Running SSSP algorithm (implementation to test)...")
    sssp_dist = solve_sssp_directed_real_weights(n, len(edges), edges, source)

    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)

    print(f"\nGraph: {n} vertices, {len(edges)} edges")
    print(f"Source: {source}")

    print("\nEdges:")
    for u, v, w in sorted(edges):
        print(f"  {u} -> {v} (weight {w})")

    print("\n" + "-" * 70)
    print(f"{'Vertex':<10} {'Dijkstra':<15} {'SSSP':<15} {'Match':<10} {'Path (Dijkstra)'}")
    print("-" * 70)

    all_vertices = set(range(n))
    mismatches = []

    for v in sorted(all_vertices):
        dijk_dist = dijkstra_dist.get(v, float('inf'))
        sssp_dist_val = sssp_dist.get(v, float('inf'))

        match = "✓" if abs(dijk_dist - sssp_dist_val) < 1e-9 else "✗"

        # Format distances
        dijk_str = f"{dijk_dist:.4f}" if dijk_dist != float('inf') else "unreachable"
        sssp_str = f"{sssp_dist_val:.4f}" if sssp_dist_val != float('inf') else "unreachable"

        # Get path
        path = reconstruct_path(dijkstra_pred, source, v)
        path_str = " -> ".join(map(str, path)) if path else "none"

        print(f"{v:<10} {dijk_str:<15} {sssp_str:<15} {match:<10} {path_str}")

        if abs(dijk_dist - sssp_dist_val) >= 1e-9:
            mismatches.append((v, dijk_dist, sssp_dist_val))

    print("-" * 70)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    dijkstra_reachable = len([v for v in dijkstra_dist if dijkstra_dist[v] != float('inf')])
    sssp_reachable = len([v for v in sssp_dist if sssp_dist[v] != float('inf')])

    print(f"Dijkstra found {dijkstra_reachable}/{n} reachable vertices")
    print(f"SSSP found {sssp_reachable}/{n} reachable vertices")

    if mismatches:
        print(f"\n❌ FAILURE: {len(mismatches)} mismatched distances")
        print("\nMismatches:")
        for v, dijk, sssp in mismatches:
            print(f"  Vertex {v}: Dijkstra={dijk:.4f}, SSSP={sssp:.4f}")
    else:
        print("\n✓ SUCCESS: All distances match!")

    return len(mismatches) == 0

# Test cases
if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEST CASE 1: Simple Graph (from starter.py)")
    print("="*70)

    edges1 = [
        (0, 1, 1.0),
        (0, 2, 4.0),
        (1, 2, 2.0),
        (1, 3, 5.0),
        (2, 3, 1.0),
    ]
    success1 = compare_algorithms(4, edges1, 0)

    print("\n\n" + "="*70)
    print("TEST CASE 2: Disconnected Graph")
    print("="*70)

    edges2 = [
        (0, 1, 1.0),
        (1, 2, 2.0),
        (3, 4, 1.0),
    ]
    success2 = compare_algorithms(5, edges2, 0)

    print("\n\n" + "="*70)
    print("TEST CASE 3: Linear Chain")
    print("="*70)

    edges3 = [
        (0, 1, 1.0),
        (1, 2, 1.0),
        (2, 3, 1.0),
        (3, 4, 1.0),
    ]
    success3 = compare_algorithms(5, edges3, 0)

    print("\n\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Test 1 (Simple): {'PASS' if success1 else 'FAIL'}")
    print(f"Test 2 (Disconnected): {'PASS' if success2 else 'FAIL'}")
    print(f"Test 3 (Linear): {'PASS' if success3 else 'FAIL'}")