import math
import heapq
from bisect import bisect_left, insort
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Union, Any, Optional

# --- Global State for the SSSP computation ---
# These dictionaries store the dynamic state of the shortest path algorithm.
# In a full-fledged library, these would typically be encapsulated within a class.
# Current estimated shortest path distance from source s to vertex v
d_hat: Dict[int, float] = {}
# Predecessor of v on the current estimated shortest path
pred: Dict[int, Optional[int]] = {}
# Number of edges in the current estimated shortest path from s to v
path_alpha: Dict[int, int] = {}

# --- Global Parameters derived from graph size (n) ---
k_param: int = 0      # Parameter k = floor(log^(1/3) n)
t_param: int = 0      # Parameter t = floor(log^(2/3) n)
N_vertices: int = 0   # Total number of vertices in the graph

# --- Type Alias for Graph Representation ---
# The graph is represented as an adjacency list: {u: {v: weight_uv}}
Graph = Dict[int, Dict[int, float]]

# --- Heuristics and Instrumentation Flags ---
# Toggleable options used to quickly test pragmatic fixes without
# permanently altering algorithmic invariants.
HEURISTICS_ENABLED = True
HEURISTICS_SEEDING = True            # seed D with neighbors from W
HEURISTICS_RELAX_INSERT = True      # insert any updated neighbor into D
HEURISTICS_LARGE_M = True           # use larger M in debug/heuristic mode
HEURISTICS_BOUNDARY_EQUALITY = True # use <= for within-bound checks
HEURISTICS_ADJUST_BI = True         # adjust tiny Bi heuristically

# Lightweight instrumentation (minimal, controlled prints)
INSTRUMENT = False
def _instr(msg: str):
    if INSTRUMENT:
        try:
            print(msg)
        except Exception:
            pass

# --- Simplified Lemma 3.3 Data Structure ---



class SimplifiedLemma3_3_DataStructure:
    """
    Ordered mapping implementation to approximate Lemma 3.3 behavior.

    This implementation maintains a sorted list of distinct values and, for each
    value, a mapping of keys that currently have that exact value. It supports
    Insert, BatchPrepend (as repeated inserts), Pull (extract up to M smallest
    keys) and is_empty. This avoids stale heap entries and makes Pull's boundary
    semantics deterministic.
    """

    def __init__(self, M: int, B: float):
        self.M = max(1, int(M))
        self.B = B

        # Sorted list of distinct values present in the structure
        self._values: List[float] = []
        # Map value -> dict of key -> (alpha, pred)
        self._value_to_keys: Dict[float, Dict[int, Tuple[int, int]]] = {}
        # Map key -> value for quick lookup/update
        self._key_to_value: Dict[int, float] = {}

    def _add_to_value_bucket(self, value: float, key: int, alpha: int, pred_v_id: int):
        if value not in self._value_to_keys:
            # insert value in sorted list
            insort(self._values, value)
            self._value_to_keys[value] = {}
        self._value_to_keys[value][key] = (alpha, pred_v_id)
        self._key_to_value[key] = value

    def _remove_key(self, key: int):
        if key not in self._key_to_value:
            return
        old_value = self._key_to_value.pop(key)
        valmap = self._value_to_keys.get(old_value)
        if valmap and key in valmap:
            del valmap[key]
            if not valmap:
                # remove empty bucket
                del self._value_to_keys[old_value]
                idx = bisect_left(self._values, old_value)
                if idx < len(self._values) and self._values[idx] == old_value:
                    self._values.pop(idx)

    def Insert(self, key: int, value: float, alpha: int, pred_v_id: int):
        # If key exists, compare lexicographically similar to previous logic
        if key in self._key_to_value:
            old_value = self._key_to_value[key]
            old_alpha, old_pred = self._value_to_keys[old_value][key]
            # If new is not better, ignore
            if value > old_value:
                return
            if value == old_value:
                if alpha > old_alpha:
                    return
                if alpha == old_alpha and pred_v_id >= old_pred:
                    return
            # remove old entry
            self._remove_key(key)

        # Add to value bucket
        self._add_to_value_bucket(value, key, alpha, pred_v_id)

    def BatchPrepend(self, L_items: List[Tuple[int, float, int, int]]):
        for key, value, alpha, pred_v_id in L_items:
            # These are expected to be small values; use Insert semantics
            self.Insert(key, value, alpha, pred_v_id)

    def Pull(self) -> Tuple[float, Set[int]]:
        S_prime: Set[int] = set()
        pulled_values: List[float] = []

        # Iterate over smallest values and collect keys until M reached
        while self._values and len(S_prime) < self.M:
            smallest_value = self._values[0]
            bucket = self._value_to_keys.get(smallest_value, {})
            # take keys from this bucket
            keys = list(bucket.keys())
            for key in keys:
                if len(S_prime) >= self.M:
                    break
                # remove key from structures
                alpha_pred = bucket.pop(key)
                self._key_to_value.pop(key, None)
                S_prime.add(key)
                pulled_values.append(smallest_value)
            # if bucket emptied, remove value
            if not bucket:
                # remove bucket and the value from sorted list
                del self._value_to_keys[smallest_value]
                self._values.pop(0)

        # Determine boundary x
        if self._values:
            x = self._values[0]
        else:
            if pulled_values:
                x = max(pulled_values) + 1e-12
            else:
                x = self.B

        return x, S_prime

    def is_empty(self) -> bool:
        return len(self._key_to_value) == 0

# --- Algorithm 2: Base Case of BMSSP (Mini Dijkstra) ---
# PAPER REFERENCE: Algorithm 2 from "Breaking the Sorting Barrier" (Duan et al., 2025)
# PURPOSE: Base case of recursion at level l=0. Performs limited Dijkstra exploration.
# METHOD: Multi-source Dijkstra from S, stops after finding k+1 vertices or exhausting heap.
#         Returns boundary B' and complete set U.


def BaseCase(B: float, S: Set[int], graph: Graph) -> Tuple[float, Set[int]]:
    """
    Algorithm 2: Base Case of BMSSP.
    Runs a mini Dijkstra-like algorithm seeded from the vertices in `S`.
    The original implementation expected `S` to be a singleton; here we accept
    multi-source seeds and run a concurrent multi-source Dijkstra until at most
    `k_param + 1` distinct vertices are finalized or the heap is exhausted.

    Args:
        B: The upper bound for distances to consider.
        S: A set of seed vertices (may be singleton or multiple).
        graph: The graph adjacency list.

    Returns:
        A tuple `(B_prime, U)`, where `B_prime` is a new boundary and `U` is the set of
        complete vertices found in this base case.
    
    BEHAVIOR:
    - Explores up to k+1 vertices from sources S
    - If finds exactly k or fewer: B' = B, U = all found
    - If finds k+1 or more: B' = distance of (k+1)-th vertex, U = vertices with dist < B'
    """

    # `U0` accumulates vertices whose true distances (relative to the seeds in `S` and `B`) are found.
    U0: Set[int] = set()

    # Priority queue for Dijkstra's: (current_dist, current_path_alpha, vertex_id, pred_id_in_heap)
    H: List[Tuple[float, int, int, int]] = []

    # Seed the heap with all vertices in S using their current global estimates.
    for x in S:
        x_pred = pred.get(x)
        if x_pred is None:
            x_pred = -1
        heapq.heappush(H, (d_hat.get(x, float('inf')), path_alpha.get(x, float('inf')), x, x_pred))

    # `candidates` temporarily stores distances of vertices added to `U0` before filtering by `B_prime`.
    candidates: Dict[int, float] = {}

    # Loop until the heap is empty or `k_param + 1` distinct vertices have been added to `U0`.
    while H and len(U0) < k_param + 1:
        current_d, current_alpha, u, current_pred_u = heapq.heappop(H)

        # Skip this entry if a shorter/better path to `u` has already been found and processed globally.
        # This handles "stale" entries in the heap from conceptual decrease-key operations.
        actual_pred_u = pred.get(u)
        if actual_pred_u is None:
            actual_pred_u = -1
        if current_d > d_hat.get(u, float('inf')) or \
           (current_d == d_hat.get(u, float('inf')) and current_alpha > path_alpha.get(u, float('inf'))) or \
           (current_d == d_hat.get(u, float('inf')) and current_alpha == path_alpha.get(u, float('inf')) and current_pred_u > actual_pred_u):
            continue

        # If `u` is already in `U0`, it means its shortest path has already been finalized in this base case.
        if u in U0:
            continue

        U0.add(u)
        # Record its distance for later `B_prime` calculation
        candidates[u] = current_d

        # Relax outgoing edges from `u`
        for v, weight_uv in graph.get(u, {}).items():
            new_dist = current_d + weight_uv
            new_alpha = current_alpha + 1

            # Only consider paths whose total distance is strictly less than `B`.
            if new_dist < B:
                # Check relaxation condition `dÌ‚[u] + wuv <= dÌ‚[v]` and apply tie-breaking.
                current_v_d = d_hat.get(v, float('inf'))
                current_v_alpha = path_alpha.get(v, float('inf'))
                # Use float('inf') for comparison if `pred[v]` is None
                current_v_pred = pred.get(v, float('inf'))

                update_needed = False
                if new_dist < current_v_d:
                    update_needed = True
                elif new_dist == current_v_d:
                    if new_alpha < current_v_alpha:  # Prefer shorter path in terms of number of edges
                        update_needed = True
                    elif new_alpha == current_v_alpha and u < current_v_pred:  # Tie-breaking on predecessor ID
                        update_needed = True

                if update_needed:
                    d_hat[v] = new_dist
                    path_alpha[v] = new_alpha
                    pred[v] = u
                    # Push (dist, alpha, vertex, its_pred) to heap
                    heapq.heappush(H, (new_dist, new_alpha, v, u))

    # Determine the returned `B_prime` and final `U` based on the size of `U0`.
    B_prime: float
    final_U: Set[int]

    if len(U0) <= k_param:  # If we found `k_param` or fewer vertices (i.e., we exhausted reachable nodes or `B`)
        B_prime = B  # The boundary remains as the initial `B`.
        final_U = U0  # All found vertices are considered part of `U`.
    else:
        # Otherwise (we found `k_param + 1` or more vertices), `B_prime` is the distance of the
        # `(k_param + 1)`-th smallest distance found in `U0`.
        sorted_distances = sorted(candidates.values())
        if len(sorted_distances) > k_param:
            # The (k+1)-th smallest distance
            B_prime = sorted_distances[k_param]
        else:
            # Fallback, should ideally not be reached if `len(U0) > k_param`.
            # If it occurs, it indicates an edge case in exact `k+1` selection or distance ties.
            B_prime = max(sorted_distances) if sorted_distances else B

        # `U` consists of vertices in `U0` whose distances are strictly less than `B_prime`.
        final_U = {v for v, dist in candidates.items() if dist < B_prime}

    return B_prime, final_U

# --- Algorithm 1: Finding Pivots ---
# PAPER REFERENCE: Algorithm 1 from "Breaking the Sorting Barrier" (Duan et al., 2025)
# PURPOSE: Identify "pivot" vertices from complete sources S whose shortest-path subtrees
#          contain many vertices. Pivots will seed recursive calls in BMSSP.
# METHOD: Performs k Bellman-Ford relaxation steps, builds implicit forest F via pred[],
#         then counts subtree sizes to identify pivots with >= k vertices.


def FindPivots(B: float, S: Set[int], graph: Graph) -> Tuple[Set[int], Set[int]]:
    """
    Algorithm 1: Finding Pivots.
    Performs `k_param` steps of relaxation from vertices in `S` and identifies a set of "pivots" `P`.
    A pivot is a source vertex in `S` whose shortest path tree (within the relaxed subgraph)
    contains at least `k_param` vertices. It also returns `W`, the set of all vertices
    whose `d_hat` values were potentially updated or considered during this phase.

    Args:
        B: The upper bound for distances.
        S: The set of complete source vertices.
        graph: The graph adjacency list.

    Returns:
        A tuple `(P, W)`, where `P` is the set of pivot vertices, and `W` is the set of
        vertices encountered/updated during the `k_param` relaxation steps.
    
    KNOWN LIMITATIONS:
    - For small graphs (n < 100), k_param may be very small (1-2), limiting pivot detection
    - Frontier W may not expand efficiently if graph has bottlenecks
    """
    global d_hat, pred, path_alpha, k_param

    W: Set[int] = set(S)  # `W` initially contains all source vertices `S`.

    # `Wi_current_step` tracks the set of vertices whose outgoing edges will be relaxed in the *current* iteration.
    Wi_current_step: Set[int] = set(S)

    # Perform `k_param` steps of Bellman-Ford-like relaxation.
    # This phase updates global `d_hat` values for reachable vertices within the bound `B`.
    for i in range(k_param):  # `i` from 0 to `k_param - 1` for `k_param` steps
        # Vertices whose edges will be relaxed in the next step
        next_Wi: Set[int] = set()
        for u in Wi_current_step:
            if u not in graph:
                continue  # No outgoing edges from u
            for v, weight_uv in graph[u].items():
                new_dist = d_hat[u] + weight_uv
                new_alpha = path_alpha[u] + 1

                # Apply relaxation condition `dÌ‚[u] + wuv <= dÌ‚[v]` with tie-breaking.
                current_v_d = d_hat.get(v, float('inf'))
                current_v_alpha = path_alpha.get(v, float('inf'))
                # Using float('inf') for comparison if `pred[v]` is None
                current_v_pred = pred.get(v, float('inf'))

                update_needed = False
                if new_dist < current_v_d:
                    update_needed = True
                elif new_dist == current_v_d:
                    # Prefer shorter path (fewer edges)
                    if new_alpha < current_v_alpha:
                        update_needed = True
                    elif new_alpha == current_v_alpha and u < current_v_pred:  # Tie-breaking on predecessor ID
                        update_needed = True

                if update_needed:
                    d_hat[v] = new_dist
                    path_alpha[v] = new_alpha
                    pred[v] = u

                # Add v to W and next_Wi if within bound, regardless of whether it was updated
                # The vertex is "visited" during these k steps from S
                if HEURISTICS_ENABLED and HEURISTICS_BOUNDARY_EQUALITY:
                    within_bound = d_hat.get(v, float('inf')) <= B
                else:
                    within_bound = d_hat.get(v, float('inf')) < B
                if within_bound:
                    next_Wi.add(v)
                    W.add(v)

        # Move to the next set of vertices for relaxation.
        Wi_current_step = next_Wi.copy()
        _instr(f"[FindPivots] after step={i} Wi_next_size={len(Wi_current_step)} W_size={len(W)}")

        # Check condition: if `|W| > k_param * |S|`, then `S` itself becomes the pivot set `P`.
        if len(W) > k_param * len(S):
            P = set(S)
            return P, W

    # If the `k_param` steps loop completes without early exit, then `|W| <= k_param * |S|`.
    # Now, identify pivots `P`. A vertex `u` in `S` is a pivot if it's the root of a shortest path
    # tree (implied by `d_hat` and `pred` values) that contains at least `k_param` vertices within `W`.

    # Build an adjacency list representing the implicit forest `F` (formed by `(pred[v], v)` edges).
    # This forest connects vertices within `W` back to their predecessors, which may be in `S` or `W`.
    F_adj: Dict[int, List[int]] = defaultdict(list)
    for v_node in W:
        p_node = pred.get(v_node)
        # Add edge (p_node, v_node) to F if `p_node` is relevant (in `S` or `W`).
        if p_node is not None and (p_node in W or p_node in S):
            F_adj[p_node].append(v_node)

    P: Set[int] = set()  # The set of identified pivots.

    # *** CRITICAL FIX (Bug #1 from analysis) ***
    # ORIGINAL BUG: Used a shared `nodes_already_counted_in_pivot_dfs` set across all pivots,
    # which caused nodes reachable from multiple pivots to only be counted for the first pivot.
    # 
    # CORRECT BEHAVIOR: Each pivot's subtree should be counted independently. A node can appear
    # in multiple pivot subtrees via different paths in the implicit forest F.
    # 
    # FIX: Create a fresh visited set for each pivot's DFS to count its subtree independently.

    def dfs_calculate_subtree_size(current_node: int, visited_for_this_pivot: Set[int]) -> int:
        """
        Helper function to calculate the size of a subtree within the forest `F` rooted at `current_node`.
        Uses a per-pivot visited set to allow nodes to be counted in multiple pivot subtrees.
        
        Args:
            current_node: Root of the current subtree
            visited_for_this_pivot: Set tracking nodes already visited in THIS pivot's DFS
        
        Returns:
            Size of the subtree rooted at current_node
        """
        if current_node in visited_for_this_pivot:
            return 0  # Node already visited in this particular pivot's subtree traversal

        visited_for_this_pivot.add(current_node)
        size = 1  # Count the `current_node` itself

        for neighbor in F_adj[current_node]:
            size += dfs_calculate_subtree_size(neighbor, visited_for_this_pivot)

        return size

    # Iterate through each vertex in `S` that is also part of `W` (meaning it was processed).
    for s_root in S:
        if s_root in W:
            # Create a fresh visited set for this pivot's subtree calculation
            visited_for_this_pivot: Set[int] = set()
            
            # Calculate the size of the subtree rooted at `s_root` within `F`.
            # This accounts for all reachable nodes from `s_root` via `pred` links within `W`.
            subtree_size = dfs_calculate_subtree_size(s_root, visited_for_this_pivot)

            # If the subtree size is `k_param` or more, `s_root` is a pivot.
            if subtree_size >= k_param:
                P.add(s_root)

    return P, W


def BMSSP(l: int, B: float, S: Set[int], graph: Graph) -> Tuple[float, Set[int]]:
    # Algorithm 3: Bounded Multi-Source Shortest Path (BMSSP)
    global d_hat, pred, path_alpha, k_param, t_param, N_vertices

    # Base case of the recursion: when level `l` is 0.
    if l == 0:
        return BaseCase(B, S, graph)

    # Step 1: Find Pivots. This identifies `P` (a smaller set of key sources) and `W` (processed vertices).
    P, W = FindPivots(B, S, graph)
    _instr(f"[BMSSP] level={l} B={B} |S|={len(S)} |P|={len(P)} |W|={len(W)}")

    # Step 2: Initialize the specialized data structure `D` (from Lemma 3.3).
    # `M_param` is determined by the current level `l` and parameter `t_param`.
    # Ensure power is non-negative and M >= 1
    # Heuristic option to use larger M in practical testing
    if HEURISTICS_ENABLED and HEURISTICS_LARGE_M:
        M_param = max(64, 2**((l - 1) * t_param)) if (l - 1) * t_param >= 0 else 64
    else:
        M_param = 2**((l - 1) * t_param) if (l - 1) * t_param >= 0 else 1
    D = SimplifiedLemma3_3_DataStructure(M_param, B)

    # Insert the identified pivots `P` into `D`.
    for x in P:
        # `d_hat[x]` for `x` in `P` is assumed to be its true (complete) distance from source `s`.
        D.Insert(x, d_hat[x], path_alpha[x], pred.get(x, -1))

    # Optional heuristic: seed D with neighbors from W to bootstrap propagation
    if HEURISTICS_ENABLED and HEURISTICS_SEEDING:
        seeded = 0
        for w in list(W):
            if w in graph:
                for v_nb, w_nb in graph[w].items():
                    if v_nb not in D._key_to_value:
                        dv = d_hat.get(v_nb, float('inf'))
                        if dv != float('inf'):
                            D.Insert(v_nb, dv, path_alpha.get(v_nb, 0), pred.get(v_nb, -1))
                            seeded += 1
        _instr(f"[BMSSP Seed] seeded_neighbors_from_W={seeded} D_keys_after_seed={len(D._key_to_value)}")

    # Initialize variables for the main loop of this `BMSSP` call.
    if not P:
        B_prime_0 = B  # If no pivots, effectively no progress past initial boundary
    else:
        # Initial boundary for the first iteration (B'_0)
        B_prime_0 = min(d_hat[x] for x in P)

    # Accumulates all complete vertices found within this `BMSSP` call.
    current_U: Set[int] = set()
    # Tracks the boundary `B'_i` from the most recent recursive call.
    last_B_prime_i: float = B_prime_0

    # Calculate the maximum allowed size for `current_U` for this level, to detect "large workload".
    max_U_size_for_level = k_param * (2**(l * t_param))

    # Safety: limit iterations to prevent infinite loops
    max_iterations = max(1000, N_vertices * 10)
    iteration_count = 0
    last_Bi = None
    stall_count = 0

    # Track vertices that have been processed to avoid infinite re-insertion
    processed_vertices: Set[int] = set()

    # Main loop: Repeats iterations as long as `current_U` is below its threshold and `D` is not empty.
    while len(current_U) < max_U_size_for_level and not D.is_empty():
        iteration_count += 1
        if iteration_count > max_iterations:
            _instr(f"[BMSSP] level={l} BREAK: max_iterations={max_iterations} reached")
            break
        # Step 3: `Pull` a subset `Si` of `M_param` smallest-distance vertices from `D`,
        # and obtain `Bi`, which is an upper bound for `Si` and a lower bound for the rest of `D`.
        Bi, Si = D.Pull()
        _instr(f"[BMSSP] level={l} iter={iteration_count} Pulled Bi={Bi} Si_count={len(Si)} M_param={M_param}")
        
        # Safety: detect if we're pulling the same vertices repeatedly
        Si_set = set(Si)
        if Si_set.issubset(processed_vertices):
            stall_count += 1
            if stall_count > 5:
                _instr(f"[BMSSP] level={l} BREAK: Pulling same {len(Si)} vertices repeatedly (stall={stall_count})")
                break
        else:
            stall_count = 0
            processed_vertices.update(Si_set)
        last_Bi = Bi

        # Heuristic adjustment for tiny Bi values
        if HEURISTICS_ENABLED and HEURISTICS_ADJUST_BI and Bi < 1e-9:
            min_pos = float('inf')
            for u_si in Si:
                for v_nb, w_nb in graph.get(u_si, {}).items():
                    cand = d_hat.get(u_si, float('inf')) + w_nb
                    if cand > d_hat.get(u_si, float('inf')) and cand < min_pos:
                        min_pos = cand
            if min_pos < float('inf'):
                _instr(f"[BMSSP AdjustBi] original Bi={Bi} adjusted to {min_pos}")
                Bi = min_pos
            else:
                max_pulled = max((d_hat.get(u_si, 0.0) for u_si in Si), default=0.0)
                Bi = max_pulled + 1e-12
                _instr(f"[BMSSP AdjustBi] fallback Bi={Bi}")

        # Step 4: Make a recursive call to `BMSSP` for the next lower level (`l-1`).
        # The recursive call uses `Bi` as its upper bound and `Si` as its source set.
        B_prime_i, Ui = BMSSP(l - 1, Bi, Si, graph)
        # Add the complete vertices found by the recursive call to `current_U`.
        current_U.update(Ui)
        last_B_prime_i = B_prime_i  # Update the last recorded `B'_i`.

        # Step 5: Relax edges from all newly completed vertices in `Ui`.
        # Propagate distance updates.
        # Collects items for batch prepending
        K_batch_prepend: List[Tuple[int, float, int, int]] = []

        for u_completed in Ui:
            if u_completed not in graph:
                continue  # No outgoing edges
            for v_neighbor, weight_uv in graph[u_completed].items():
                new_dist = d_hat[u_completed] + weight_uv
                new_alpha = path_alpha[u_completed] + 1

                # Apply relaxation and tie-breaking rules, similar to Dijkstra's.
                current_v_d = d_hat.get(v_neighbor, float('inf'))
                current_v_alpha = path_alpha.get(v_neighbor, float('inf'))
                current_v_pred = pred.get(v_neighbor, float('inf'))

                update_needed = False
                if new_dist < current_v_d:
                    update_needed = True
                elif new_dist == current_v_d:
                    if new_alpha < current_v_alpha:
                        update_needed = True
                    elif new_alpha == current_v_alpha and u_completed < current_v_pred:
                        update_needed = True

                if update_needed:
                    d_hat[v_neighbor] = new_dist
                    path_alpha[v_neighbor] = new_alpha
                    pred[v_neighbor] = u_completed

                    # Heuristic: relax insertion may place all updated neighbors into D
                    if HEURISTICS_ENABLED and HEURISTICS_RELAX_INSERT:
                        D.Insert(v_neighbor, d_hat[v_neighbor], path_alpha[v_neighbor], pred[v_neighbor])
                    else:
                        # Distinguish where to place `v_neighbor` based on its new distance.
                        # If distance falls into the current `[Bi, B)` range, directly insert to `D`.
                        if Bi <= new_dist < B:
                            D.Insert(
                                v_neighbor, d_hat[v_neighbor], path_alpha[v_neighbor], pred[v_neighbor])
                        # If distance falls into the `[B'_i, Bi)` range, add to `K` for batch prepending.
                        elif B_prime_i <= new_dist < Bi:
                            K_batch_prepend.append(
                                (v_neighbor, d_hat[v_neighbor], path_alpha[v_neighbor], pred[v_neighbor]))

        # Step 6: `BatchPrepend` collected items to `D`.
        # This includes vertices from `K_batch_prepend` and any vertices from `Si`
        # whose true distances (`d_hat[x_si]`) are now confirmed to be in the `[B'_i, Bi)` range.
        batch_items_to_add: List[Tuple[int, float, int, int]] = list(
            K_batch_prepend)
        for x_si in Si:
            # `x_si` was pulled from `D` but its precise distance was finalized by `BMSSP(l-1, Bi, Si)`.
            # If `d(x_si)` (which is now `d_hat[x_si]`) falls within `[B'_i, Bi)`, it needs to be "re-inserted"
            # at a higher priority for the current `BMSSP` call.
            if d_hat.get(x_si, float('inf')) >= B_prime_i and d_hat.get(x_si, float('inf')) < Bi:
                batch_items_to_add.append(
                    (x_si, d_hat[x_si], path_alpha[x_si], pred.get(x_si, -1)))

        D.BatchPrepend(batch_items_to_add)
        _instr(f"[BMSSP] level={l} After BatchPrepend: batch_added={len(batch_items_to_add)} current_U_size={len(current_U)} D_keys={len(D._key_to_value)}")

    # Determine the final `B_prime` to be returned by this `BMSSP` call.
    final_return_B_prime: float
    if D.is_empty():  # If the loop finished because `D` is empty, it's a "successful execution".
        final_return_B_prime = B
    else:  # If the loop finished because `|current_U|` exceeded `max_U_size_for_level`, it's a "partial execution due to large workload".
        # In this case, `B_prime` is set to the `B'_i` from the last completed iteration.
        # The paper says `min{B'i, B}`
        final_return_B_prime = min(last_B_prime_i, B)

    # Finally, `U` must also include vertices from `W` (returned by `FindPivots`)
    # that are complete (`d_hat[x_w]` is true distance) and within the `final_return_B_prime`.
    # Vertices in `W` are already complete (true distances found) due to `FindPivots` properties.
    for x_w in W:
        if d_hat.get(x_w, float('inf')) < final_return_B_prime:
            current_U.add(x_w)

    return final_return_B_prime, current_U

# --- Main SSSP Algorithm Entry Point ---


def solve_sssp_directed_real_weights(n_val: int, m_val: int, edges: List[Tuple[int, int, float]], source: int) -> Dict[int, float]:
    # Implements the O(m log^(2/3) n)-time SSSP algorithm from Duan et al. (2025)
    global d_hat, pred, path_alpha, k_param, t_param, N_vertices

    N_vertices = n_val  # Store the total number of vertices globally.

    # Initialize global state for the SSSP problem.
    d_hat.clear()
    pred.clear()
    path_alpha.clear()

    # Build the graph adjacency list and initialize all vertex distances to infinity.
    graph: Dict[int, Dict[int, float]] = defaultdict(dict)
    for u, v, weight in edges:
        graph[u][v] = weight
        # Ensure all vertices referenced in edges are initialized.
        # It's better to iterate through `range(N_vertices)` to include isolated vertices too.

    # Initialize d_hat, path_alpha, and pred for all vertices
    for v_id in range(N_vertices):
        d_hat[v_id] = float('inf')
        path_alpha[v_id] = float('inf')
        pred[v_id] = None

    # Initialize the source vertex `s` with distance 0 and path length 0.
    d_hat[source] = 0.0
    path_alpha[source] = 0

    # Calculate parameters `k` and `t` based on `n` (total number of vertices).
    # `log^(1/3) n` means (log base 2 of n)^(1/3).
    # Ensure `n` is at least 2 for logarithm calculations to be meaningful.
    n_for_log_calc = max(2, N_vertices)
    k_param = math.floor(math.log(n_for_log_calc, 2)**(1/3))
    t_param = math.floor(math.log(n_for_log_calc, 2)**(2/3))

    # Ensure `k_param` and `t_param` are at least 1 to avoid issues like division by zero
    # or creating zero-sized data structures or iterations.
    k_param = max(1, k_param)
    t_param = max(1, t_param)

    # Calculate the maximum recursion level `l_max_level` for the top-level call.
    l_max_level = math.ceil(math.log(n_for_log_calc, 2) /
                            t_param) if n_for_log_calc > 1 else 0

    # Make the main call to the `BMSSP` algorithm.
    # The initial call uses the highest level, the source vertex `s`, and an infinite upper bound.
    final_boundary, final_complete_vertices_U = BMSSP(
        l_max_level, float('inf'), {source}, graph)

    # According to the paper, at the top level call, `U` will contain all vertices,
    # and their shortest paths will have been found (assuming all vertices are reachable from `s`).

    # Filter `d_hat` to include only reachable vertices with finite distances.
    result_distances = {v: d_hat[v] for v in range(N_vertices) if d_hat[v] != float('inf')}
    return result_distances