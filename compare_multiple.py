"""
Compare NEW SSSP with Dijkstra on multiple graph files.

Usage: run from workspace folder containing the graph files (e.g. 1k.txt, 5k.txt)
This script prints times, reachable counts, and writes per-graph output files:
 - newsssp_<basename>_distances.txt
 - dijkstra_<basename>_distances.txt

"""
import os
import time
import heapq
from typing import List, Tuple

import sssp_concept
from sssp_concept import solve_sssp_directed_real_weights


def load_edges(path: str) -> Tuple[int, List[Tuple[int,int,float]]]:
    edges = []
    n = None
    with open(path, 'r') as f:
        header = f.readline().strip()
        # Try to infer n from filename if header isn't useful
        for line in f:
            parts = line.split()
            if not parts:
                continue
            u = int(parts[0]); v = int(parts[1]); w = float(parts[2])
            edges.append((u, v, w))
    # infer n as max vertex id + 1
    maxv = 0
    for u,v,_ in edges:
        maxv = max(maxv, u, v)
    n = maxv + 1
    return n, edges


def dijkstra(graph_dict, n, source):
    dist = {source: 0.0}
    pq = [(0.0, source)]
    while pq:
        d,u = heapq.heappop(pq)
        if d > dist.get(u, float('inf')):
            continue
        for v,w in graph_dict.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def run_on_file(filename: str):
    n, edges = load_edges(filename)
    m = len(edges)
    base = os.path.splitext(os.path.basename(filename))[0]
    print(f"\n{base}.txt: {n} vertices, {m} edges")

    # Run new SSSP
    start = time.time()
    sssp_dist = solve_sssp_directed_real_weights(n, m, edges, source=0)
    sssp_time = time.time() - start
    sssp_reach = len(sssp_dist)

    print(f"NEW SSSP: time={sssp_time:.4f}s reachable={sssp_reach}/{n}")

    # Build adjacency for Dijkstra
    graph_dict = {i: {} for i in range(n)}
    for u,v,w in edges:
        graph_dict[u][v] = w

    start = time.time()
    dijk_dist = dijkstra(graph_dict, n, 0)
    dijk_time = time.time() - start
    dijk_reach = len(dijk_dist)

    print(f"Dijkstra: time={dijk_time:.4f}s reachable={dijk_reach}/{n}")

    # Save outputs (SSSP-only and Dijkstra-only)
    base = os.path.splitext(os.path.basename(filename))[0]
    out_sssp = os.path.join(os.path.dirname(filename), f"newsssp_{base}_distances.txt")
    with open(out_sssp, 'w') as f:
        f.write('# vertex distance (NEW SSSP only)\n')
        for i in range(n):
            d = sssp_dist.get(i, float('inf'))
            if d == float('inf'):
                f.write(f"{i} inf\n")
            else:
                f.write(f"{i} {d:.6f}\n")

    out_dijk = os.path.join(os.path.dirname(filename), f"dijkstra_{base}_distances.txt")
    with open(out_dijk, 'w') as f:
        f.write('# vertex distance (Dijkstra)\n')
        for i in range(n):
            d = dijk_dist.get(i, float('inf'))
            if d == float('inf'):
                f.write(f"{i} inf\n")
            else:
                f.write(f"{i} {d:.6f}\n")

    # Print short sample and stats
    sample_keys = sorted(sssp_dist.keys())[:10]
    print(f" SSSP: time={sssp_time:.4f}s reach={sssp_reach}/{n} | Dijkstra: time={dijk_time:.4f}s reach={dijk_reach}/{n}")

    return {
        'file': filename,
        'n': n,
        'm': m,
        'sssp_time': sssp_time,
        'sssp_reach': sssp_reach,
        'dijk_time': dijk_time,
        'dijk_reach': dijk_reach,
        'out_sssp': out_sssp,
        'out_dijk': out_dijk,
    }


if __name__ == '__main__':
    # files to run
    files = ['1k.txt', '5k.txt', '10k.txt']

    # Define configurations to test by toggling flags in the sssp_concept module
    configs = [
        {
            'name': 'baseline',
            'HEURISTICS_ENABLED': False,
            'HEURISTICS_SEEDING': False,
            'HEURISTICS_RELAX_INSERT': False,
            'HEURISTICS_LARGE_M': False,
            'HEURISTICS_BOUNDARY_EQUALITY': False,
            'HEURISTICS_ADJUST_BI': False,
        },
    ]

    all_results = []
    for cfg in configs:
        print(f"\nConfig: {cfg['name']}")

        # Apply config flags into sssp_concept module
        for k, v in cfg.items():
            if hasattr(sssp_concept, k):
                setattr(sssp_concept, k, v)

        cfg_results = []
        for fn in files:
            path = os.path.join(os.path.dirname(__file__), fn)
            if not os.path.exists(path):
                print(f"File not found: {path} - skipping")
                continue
            res = run_on_file(path)
            res['config'] = cfg['name']
            cfg_results.append(res)
        all_results.append((cfg['name'], cfg_results))

    print('\n' + '='*60)
    print('Summary:')
    for cfg_name, cfg_results in all_results:
        print(f"\nConfig: {cfg_name}")
        for r in cfg_results:
            print(f" {os.path.basename(r['file'])}: SSSP {r['sssp_time']:.4f}s reach={r['sssp_reach']}/{r['n']}; Dijkstra {r['dijk_time']:.4f}s reach={r['dijk_reach']}/{r['n']}")
    print('='*60)
