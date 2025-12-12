"""
Patch for sssp_concept.py to add infinite loop protection
Apply by running: python apply_safety_patch.py
"""

# Read the file
with open('sssp_concept.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patch 1: Add iteration tracking variables
old_1 = """    # Accumulates all complete vertices found within this `BMSSP` call.
    current_U: Set[int] = set()
    # Tracks the boundary `B'_i` from the most recent recursive call.
    last_B_prime_i: float = B_prime_0

    # Calculate the maximum allowed size for `current_U` for this level, to detect "large workload".
    max_U_size_for_level = k_param * (2**(l * t_param))

    # Main loop: Repeats iterations as long as `current_U` is below its threshold and `D` is not empty.
    while len(current_U) < max_U_size_for_level and not D.is_empty():"""

new_1 = """    # Accumulates all complete vertices found within this `BMSSP` call.
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

    # Main loop: Repeats iterations as long as `current_U` is below its threshold and `D` is not empty.
    while len(current_U) < max_U_size_for_level and not D.is_empty():
        iteration_count += 1
        if iteration_count > max_iterations:
            _instr(f"[BMSSP] level={l} BREAK: max_iterations={max_iterations} reached")
            break"""

# Patch 2: Add stall detection
old_2 = """        # Step 3: `Pull` a subset `Si` of `M_param` smallest-distance vertices from `D`,
        # and obtain `Bi`, which is an upper bound for `Si` and a lower bound for the rest of `D`.
        Bi, Si = D.Pull()
        _instr(f"[BMSSP] level={l} Pulled Bi={Bi} Si_count={len(Si)} M_param={M_param}")

        # Heuristic adjustment for tiny Bi values"""

new_2 = """        # Step 3: `Pull` a subset `Si` of `M_param` smallest-distance vertices from `D`,
        # and obtain `Bi`, which is an upper bound for `Si` and a lower bound for the rest of `D`.
        Bi, Si = D.Pull()
        _instr(f"[BMSSP] level={l} iter={iteration_count} Pulled Bi={Bi} Si_count={len(Si)} M_param={M_param}")
        
        # Safety: detect if Bi is not advancing (infinite loop symptom)
        if last_Bi is not None and abs(Bi - last_Bi) < 1e-12 and len(Si) == len(batch_items_to_add if 'batch_items_to_add' in dir() else []):
            stall_count += 1
            if stall_count > 10:
                _instr(f"[BMSSP] level={l} BREAK: Bi stalled at {Bi} for {stall_count} iterations")
                break
        else:
            stall_count = 0
        last_Bi = Bi

        # Heuristic adjustment for tiny Bi values"""

if old_1 in content:
    content = content.replace(old_1, new_1)
    print("✓ Applied Patch 1: Iteration limit")
else:
    print("✗ Patch 1 already applied or code structure changed")

if old_2 in content:
    content = content.replace(old_2, new_2)
    print("✓ Applied Patch 2: Stall detection")
else:
    print("✗ Patch 2 already applied or code structure changed")

# Write back
with open('sssp_concept.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nPatches applied! Test with: python test_diagnostic.py")
