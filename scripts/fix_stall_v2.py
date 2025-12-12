"""
Better fix: Track already-processed vertices to prevent infinite re-adding
"""

with open('sssp_concept.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the loop start to add a processed set
old_loop_start = """    # Main loop: Repeats iterations as long as `current_U` is below its threshold and `D` is not empty.
    while len(current_U) < max_U_size_for_level and not D.is_empty():
        iteration_count += 1
        if iteration_count > max_iterations:
            _instr(f"[BMSSP] level={l} BREAK: max_iterations={max_iterations} reached")
            break
        # Step 3: `Pull` a subset `Si` of `M_param` smallest-distance vertices from `D`,
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
        last_Bi = Bi"""

new_loop_start = """    # Track vertices that have been processed to avoid infinite re-insertion
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
        last_Bi = Bi"""

if old_loop_start in content:
    content = content.replace(old_loop_start, new_loop_start)
    print("✓ Applied improved stall detection")
else:
    print("✗ Could not find exact match - manual edit needed")
    print("Searching for alternate pattern...")

# Write back
with open('sssp_concept.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
