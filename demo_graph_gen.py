"""
Graph Generation Demo

- Generates three graphs (random, sparse, layered)
- Saves and loads from disk to show dataset pipeline
- Runs compare_algorithms (SSSP vs Dijkstra) on each
- Prints concise, narration-friendly results

Run:
  python demo_graph_gen.py
"""
from __future__ import annotations
from typing import List, Tuple

from graph_generator import (
    generate_random_graph,
    generate_sparse_graph,
    generate_layered_graph,
    save_graph_to_file,
    load_graph_from_file,
)
from hybrid_sssp import compare_algorithms


def run_case(title: str, make_graph_fn, save_as: str, *args, **kwargs) -> None:
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)

    # Generate in-memory graph and edges
    graph, edges = make_graph_fn(*args, **kwargs)
    n = len(graph)
    m = len(edges)

    # Save to file
    save_graph_to_file(edges, n, save_as)

    # Load from file
    n2, m2, edges2 = load_graph_from_file(save_as)

    # Run compare (30s timeout safety)
    res = compare_algorithms(n2, edges2, source=0, sssp_timeout_sec=30)

    # Pretty print
    d_time = res['dijkstra']['time']
    d_reach = res['dijkstra']['reachable']

    s = res['sssp']
    s_time = s.get('time', 0.0)
    s_reach = s.get('reachable', 0)
    s_timed_out = s.get('timed_out', False)

    print(f"Graph file: {save_as} | n={n2}, m={m2}")
    print(f"Dijkstra : time={d_time:.4f}s, reachable={d_reach}")
    if s_timed_out:
        print(f"SSSP     : TIMED OUT at {s_time:.0f}s (hybrid would use Dijkstra)")
    else:
        print(f"SSSP     : time={s_time:.4f}s, reachable={s_reach}")


if __name__ == "__main__":
    # 1) Random connected graph
    run_case(
        title="Random connected graph (n=200, m=400)",
        make_graph_fn=generate_random_graph,
        save_as="graph_random_200x400.txt",
        n=200,
        m=400,
        seed=42,
    )

    # 2) Sparse graph with average out-degree ~3
    run_case(
        title="Sparse graph (n=300, avg_degree=3)",
        make_graph_fn=generate_sparse_graph,
        save_as="graph_sparse_300x3.txt",
        n=300,
        avg_degree=3.0,
        seed=7,
    )

    # 3) Layered DAG
    run_case(
        title="Layered DAG (layers=5, v/layer=20, forward=3)",
        make_graph_fn=generate_layered_graph,
        save_as="graph_layered_5x20.txt",
        num_layers=5,
        vertices_per_layer=20,
        forward_edges_per_vertex=3,
        seed=99,
    )
