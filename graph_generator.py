"""
Graph Generator for SSSP Algorithm

This script generates random directed graphs with non-negative real weights
in the format expected by the sssp_concept.py implementation.

The algorithm expects:
- Vertex IDs: integers from 0 to n-1
- Graph format: Dict[int, Dict[int, float]] (adjacency list)
- Edges: directed with non-negative weights
"""

import random
import math
from typing import Dict, List, Tuple


def generate_random_graph(
    n: int,
    m: int,
    min_weight: float = 0.1,
    max_weight: float = 10.0,
    connected: bool = True,
    seed: int = None
) -> Tuple[Dict[int, Dict[int, float]], List[Tuple[int, int, float]]]:
    """
    Generate a random directed graph.
    
    Args:
        n: Number of vertices
        m: Number of edges
        min_weight: Minimum edge weight
        max_weight: Maximum edge weight
        connected: If True, ensures graph is weakly connected from vertex 0
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (graph_dict, edges_list)
        - graph_dict: Adjacency list format {u: {v: weight}}
        - edges_list: List of tuples (u, v, weight)
    """
    if seed is not None:
        random.seed(seed)
    
    if m < n - 1 and connected:
        raise ValueError(f"Cannot create connected graph with {n} vertices and only {m} edges. Need at least {n-1} edges.")
    
    if m > n * (n - 1):
        raise ValueError(f"Too many edges. Maximum for {n} vertices is {n * (n - 1)}")
    
    graph: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
    edges: List[Tuple[int, int, float]] = []
    edge_set = set()
    
    # If connected, first create a spanning tree from vertex 0
    if connected and n > 1:
        # Create a random permutation of vertices
        vertices = list(range(1, n))
        random.shuffle(vertices)
        
        # Connect each vertex to a random earlier vertex in the tree
        for i, v in enumerate(vertices):
            # Choose a random vertex from 0 to current tree size
            u = random.choice([0] + vertices[:i])
            weight = random.uniform(min_weight, max_weight)
            
            graph[u][v] = weight
            edges.append((u, v, weight))
            edge_set.add((u, v))
    
    # Add remaining random edges
    edges_to_add = m - len(edges)
    attempts = 0
    max_attempts = m * 10
    
    while len(edges) < m and attempts < max_attempts:
        u = random.randint(0, n - 1)
        v = random.randint(0, n - 1)
        
        # No self-loops, no duplicate edges
        if u != v and (u, v) not in edge_set:
            weight = random.uniform(min_weight, max_weight)
            graph[u][v] = weight
            edges.append((u, v, weight))
            edge_set.add((u, v))
        
        attempts += 1
    
    if len(edges) < m:
        print(f"Warning: Could only generate {len(edges)} edges out of {m} requested")
    
    return graph, edges


def generate_sparse_graph(n: int, avg_degree: float = 3.0, **kwargs) -> Tuple[Dict[int, Dict[int, float]], List[Tuple[int, int, float]]]:
    """
    Generate a sparse graph with approximately the specified average out-degree.
    
    Args:
        n: Number of vertices
        avg_degree: Average out-degree per vertex
        **kwargs: Additional arguments passed to generate_random_graph
        
    Returns:
        Tuple of (graph_dict, edges_list)
    """
    m = int(n * avg_degree)
    return generate_random_graph(n, m, **kwargs)


def generate_dense_graph(n: int, edge_probability: float = 0.3, **kwargs) -> Tuple[Dict[int, Dict[int, float]], List[Tuple[int, int, float]]]:
    """
    Generate a dense graph where each possible edge exists with given probability.
    
    Args:
        n: Number of vertices
        edge_probability: Probability of each edge existing (0 to 1)
        **kwargs: Additional arguments passed to generate_random_graph
        
    Returns:
        Tuple of (graph_dict, edges_list)
    """
    max_edges = n * (n - 1)
    m = int(max_edges * edge_probability)
    return generate_random_graph(n, m, **kwargs)


def generate_path_graph(n: int, min_weight: float = 0.1, max_weight: float = 10.0, seed: int = None) -> Tuple[Dict[int, Dict[int, float]], List[Tuple[int, int, float]]]:
    """
    Generate a simple path graph 0 -> 1 -> 2 -> ... -> n-1
    
    Args:
        n: Number of vertices
        min_weight: Minimum edge weight
        max_weight: Maximum edge weight
        seed: Random seed
        
    Returns:
        Tuple of (graph_dict, edges_list)
    """
    if seed is not None:
        random.seed(seed)
    
    graph: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
    edges: List[Tuple[int, int, float]] = []
    
    for i in range(n - 1):
        weight = random.uniform(min_weight, max_weight)
        graph[i][i + 1] = weight
        edges.append((i, i + 1, weight))
    
    return graph, edges


def generate_layered_graph(
    num_layers: int,
    vertices_per_layer: int,
    forward_edges_per_vertex: int = 2,
    min_weight: float = 0.1,
    max_weight: float = 10.0,
    seed: int = None
) -> Tuple[Dict[int, Dict[int, float]], List[Tuple[int, int, float]]]:
    """
    Generate a layered DAG (directed acyclic graph).
    Edges only go from layer i to layer i+1.
    
    Args:
        num_layers: Number of layers
        vertices_per_layer: Vertices in each layer
        forward_edges_per_vertex: Number of edges from each vertex to next layer
        min_weight: Minimum edge weight
        max_weight: Maximum edge weight
        seed: Random seed
        
    Returns:
        Tuple of (graph_dict, edges_list)
    """
    if seed is not None:
        random.seed(seed)
    
    n = num_layers * vertices_per_layer
    graph: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
    edges: List[Tuple[int, int, float]] = []
    
    for layer in range(num_layers - 1):
        layer_start = layer * vertices_per_layer
        next_layer_start = (layer + 1) * vertices_per_layer
        
        for i in range(vertices_per_layer):
            u = layer_start + i
            # Connect to random vertices in next layer
            targets = random.sample(
                range(next_layer_start, next_layer_start + vertices_per_layer),
                min(forward_edges_per_vertex, vertices_per_layer)
            )
            
            for v in targets:
                weight = random.uniform(min_weight, max_weight)
                graph[u][v] = weight
                edges.append((u, v, weight))
    
    return graph, edges


def save_graph_to_file(edges: List[Tuple[int, int, float]], n: int, filename: str):
    """
    Save graph to a text file in edge list format.
    
    Format:
    Line 1: n m (number of vertices and edges)
    Following lines: u v weight
    
    Args:
        edges: List of edges (u, v, weight)
        n: Number of vertices
        filename: Output filename
    """
    m = len(edges)
    
    with open(filename, 'w') as f:
        f.write(f"{n} {m}\n")
        for u, v, weight in edges:
            f.write(f"{u} {v} {weight}\n")
    
    print(f"Graph saved to {filename}: {n} vertices, {m} edges")


def load_graph_from_file(filename: str) -> Tuple[int, int, List[Tuple[int, int, float]]]:
    """
    Load graph from a text file.
    
    Args:
        filename: Input filename
        
    Returns:
        Tuple of (n, m, edges)
    """
    with open(filename, 'r') as f:
        first_line = f.readline().strip().split()
        n, m = int(first_line[0]), int(first_line[1])
        
        edges = []
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                u, v, weight = int(parts[0]), int(parts[1]), float(parts[2])
                edges.append((u, v, weight))
    
    print(f"Graph loaded from {filename}: {n} vertices, {len(edges)} edges")
    return n, m, edges


def edges_to_graph_dict(edges: List[Tuple[int, int, float]], n: int) -> Dict[int, Dict[int, float]]:
    """
    Convert edge list to adjacency list format.
    
    Args:
        edges: List of edges (u, v, weight)
        n: Number of vertices
        
    Returns:
        Adjacency list {u: {v: weight}}
    """
    graph: Dict[int, Dict[int, float]] = {i: {} for i in range(n)}
    for u, v, weight in edges:
        graph[u][v] = weight
    return graph


# Example usage
if __name__ == "__main__":
    print("=== Graph Generator Examples ===\n")
    
    # Example 1: Small random graph
    print("1. Small random connected graph (10 vertices, 20 edges):")
    graph, edges = generate_random_graph(10, 20, seed=42)
    print(f"   Generated {len(edges)} edges")
    print(f"   Sample edges: {edges[:3]}")
    
    # Example 2: Sparse graph
    print("\n2. Sparse graph (100 vertices, avg degree 3):")
    graph, edges = generate_sparse_graph(100, avg_degree=3.0, seed=42)
    print(f"   Generated {len(edges)} edges")
    
    # Example 3: Path graph
    print("\n3. Path graph (20 vertices):")
    graph, edges = generate_path_graph(20, seed=42)
    print(f"   Generated {len(edges)} edges")
    
    # Example 4: Layered graph
    print("\n4. Layered DAG (5 layers, 10 vertices per layer):")
    graph, edges = generate_layered_graph(5, 10, forward_edges_per_vertex=3, seed=42)
    print(f"   Generated {len(edges)} edges")
    
    # Example 5: Save and load
    print("\n5. Saving and loading:")
    save_graph_to_file(edges, 50, "/home/claude/example_graph.txt")
    n, m, loaded_edges = load_graph_from_file("/home/claude/example_graph.txt")
    print(f"   Loaded: {n} vertices, {m} edges")
    
    print("\n=== Examples Complete ===")
