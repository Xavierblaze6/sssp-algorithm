# Single-source shortest paths in Python (conceptual translation)

A practical, readable translation of a cutting-edge single-source shortest paths (SSSP) algorithm for directed graphs with real non‑negative weights. This repository focuses on clarity and structure over asymptotic optimality, mirroring the original algorithm’s recursion, pivoting, and frontier management while using Pythonic data structures.

This is for people who want to understand the shape of the algorithm, experiment on small to medium graphs, and iterate on ideas—without getting lost in the weeds of specialized, low-level data structures.

---

## Project overview

- **Purpose:** Provide a faithful, educational translation of the algorithm’s logic—recursion, pivot selection, and bounded exploration—so you can read it, run it, and modify it.
- **Status:** Correctness-driven and research-friendly. Not tuned for the original paper’s time bounds.
- **Scope:** Directed graphs with real non‑negative edge weights; adjacency-list representation; global distance and predecessor state.

The original algorithm targets time \(O(m \log^{2/3} n)\) via sophisticated data structures and degree-regularization transformations. This Python version preserves the algorithmic flow but intentionally trades away those structures for maintainability and approachability.

---

## Core components

- **BMSSP:** The bounded multi-source shortest path routine (Algorithm 3). It performs recursive divide-and-conquer over a frontier under a distance bound and a current recursion level.
- **BaseCase:** The base routine for level \(l = 0\) (Algorithm 2). It runs a constrained, Dijkstra-like expansion from a single source to reveal a limited neighborhood under the bound.
- **FindPivots:** The pivot-selection routine (Algorithm 1). It performs a fixed number of relaxations from a set of sources to identify a smaller set of pivot vertices that seed deeper recursive calls.
- **SimplifiedLemma3_3_DataStructure:** A priority-queue–based stand‑in for the specialized block-list + balanced BST structure. It supports inserts, (simulated) batch prepends, and pulls with stale-entry handling.

After the main driver runs, global (or shared) maps contain distances, predecessors, and path lengths:
- **d_hat:** Current best distance estimates from the source(s).
- **pred:** Predecessor pointers for path reconstruction.
- **path_alpha:** Edge counts of the current best paths (used for tie-breaking).

For parameterization, the algorithm computes:
- \(k = \lfloor \log^{1/3} n \rfloor\) and \(t = \lfloor \log^{2/3} n \rfloor\), derived from the vertex count \(n\).

---

## Design choices and simplifications

- **Data structure substitution:**  
  **What the paper does:** A block-based linked list indexed by a self-balancing BST gives near-optimal amortized bounds for Insert, BatchPrepend, and Pull.  
  **What this code does:** Uses `heapq` as a min-priority queue and tracks decrease-keys by inserting new entries and discarding stale ones on extract. This preserves correctness and simplicity, but not the original amortized guarantees.

- **Tie-breaking approximation:**  
  **What the paper assumes:** Unique path lengths with a lexicographic rule over tuples like \((\text{length}, \alpha, v_\alpha, \dots, v_1)\).  
  **What this code does:** Compares tuples \((\text{distance}, \text{path length}, \text{predecessor id})\). This enforces deterministic updates and practical uniqueness without carrying full path sequences.

- **Graph degree transformation:**  
  **What the paper uses:** A classical transformation to make in/out-degrees constant, producing a graph \(G'\) with \(O(m)\) vertices and edges.  
  **What this code does:** Operates directly on the input graph. If your graph has high-degree vertices, asymptotic claims from the paper will not directly transfer unless you preprocess the graph.

---

## Installation

- **Requirements:** Python 3.9+; no mandatory external dependencies.
- **Get started:**  
  - **Clone:** `git clone <this-repo-url>`  
  - **Run tests/examples:** Use the quick start below or add your own graph.

---

## Quick start

```python
# Example usage with adjacency-list graph: graph[u] = {v: weight_uv}
from sssp_concept import BMSSP, BaseCase, FindPivots, SimplifiedLemma3_3_DataStructure

# A small directed graph with non-negative weights
graph = {
    's': {'a': 1.0, 'b': 4.0},
    'a': {'b': 2.0, 'c': 5.0},
    'b': {'c': 1.0},
    'c': {}
}

# Global-like state (shared maps)
d_hat = {}       # distance estimates
pred = {}        # predecessors
path_alpha = {}  # edge counts along best-known paths

# Parameters derived from n = |V|
n = len(graph)
# In the implementation, k and t are computed internally from n.

# Initialize
source = 's'
S = {source}
B = float('inf')   # upper bound on distances to explore
l = 2              # recursion level (choose based on n/log-scale)

# Run
BMSSP(graph, l, B, S, d_hat, pred, path_alpha)

# Read results
print("Distances:", d_hat)
print("Predecessors:", pred)
print("Path lengths:", path_alpha)

# Reconstruct the path from s to c
def path_to(v):
    p = []
    while v in pred or v == source:
        p.append(v)
        if v == source:
            break
        v = pred[v]
    return list(reversed(p))

print("Path s→c:", path_to('c'))
```

- **Graph format:** `dict[Any, dict[Any, float]]`
- **Distance bound:** **B** controls how far the recursion is allowed to expand. Use `float('inf')` for unbounded.
- **Level:** **l** acts like the recursion budget. Higher values allow deeper divide-and-conquer; modest values often suffice for small graphs.

---

## API overview

### BMSSP

- **Role:** Recursive bounded multi-source expansion with pivoting and frontier maintenance.
- **Signature:**  
  **BMSSP(graph, l, B, S, d_hat, pred, path_alpha)**
- **Inputs:**  
  - **graph:** Adjacency list mapping `u -> {v: w}`  
  - **l:** Current recursion level  
  - **B:** Distance upper bound  
  - **S:** Set of “complete” sources for this stage
- **State:** Updates `d_hat`, `pred`, `path_alpha` in place.

### BaseCase

- **Role:** Level-zero bounded exploration with a Dijkstra-like loop to reveal the nearest vertices within the bound.
- **Signature:**  
  **BaseCase(graph, B, s, d_hat, pred, path_alpha)**
- **Behavior:** Limited relaxations from a single source `s` under `B`, honoring tie-breaking.

### FindPivots

- **Role:** Perform \(k\) relaxation steps from `S` to pick a smaller set of pivot vertices for deeper recursion.
- **Signature:**  
  **FindPivots(graph, S, d_hat, path_alpha, k)**
- **Output:** A subset of vertices to seed the next recursion.

### SimplifiedLemma3_3_DataStructure

- **Role:** Manage the frontier set with priorities supporting inserts, simulated batch prepends, and pulls.
- **Key operations:**  
  - **insert(key, priority):** Add or update entries (supports decrease-key by staleness checks).  
  - **pull():** Extract the current minimum non-stale entry.  
  - **batch_prepend(items):** Push a batch of items; implemented as multiple inserts.  
  - **empty():** Check emptiness.

---

## Performance and limitations

- **Asymptotics:** This translation does not realize the original bound \(O(m \log^{2/3} n)\) due to the simplified frontier data structure and omission of degree-regularization preprocessing.
- **Practicality:** For small and moderate graphs, it provides clean structure, understandable recursion, and correctness with deterministic tie-breaking.
- **Hot spots:** Priority-queue churn from “decrease-key via insert” and Python-level recursion can dominate runtime on larger graphs. Tailor `l`, `B`, and your graph size accordingly.

---

## Implementation notes

- **Uniqueness of updates:** The tuple comparison \((\text{distance}, \text{path length}, \text{predecessor id})\) enforces deterministic choices and avoids oscillation when equal-length alternatives exist.
- **Global state:** `d_hat`, `pred`, and `path_alpha` are shared and monotonically improve. Initialize them once and reuse across calls when composing multi-stage runs.
- **Non-negative weights:** Negative edges are unsupported. If you need those, use Bellman–Ford–style routines or reweighting schemes.

---

## Testing and examples

- **Smoke test:** Try the quick start graph and verify shortest paths against a standard Dijkstra implementation on the same graph.
- **Edge cases:**  
  - **Disconnected:** Ensure unreachable nodes remain absent from `d_hat`.  
  - **Zero weights:** Verify that tie-breaking still yields consistent predecessors.  
  - **Multiple sources:** Seed `S` with several sources and confirm the minima across them.

---

## Roadmap

- **Data-structure upgrades:** Experiment with a block-list layer on top of arrays and a balanced tree to approach the paper’s amortized bounds.
- **Graph preprocessing:** Add degree-regularization transformation to more closely track the theoretical setting.
- **Iterative variants:** Replace recursion with iterative layering to improve Python call overhead and stack depth control.

---

## License

- **License:** MIT (or your preferred license). Add the LICENSE file and update this section accordingly.

---

## A note for readers

This code is an invitation: to read, tinker, and form an intuition for how powerful SSSP ideas can be reimagined in a high-level language. If you adapt the data structure, tweak the pivoting, or bolt on preprocessing, you’ll feel where the theory tugs the implementation—and where pragmatism wins.