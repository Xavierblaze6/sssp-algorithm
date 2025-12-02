"""
Fill unreachable vertices in NEW SSSP output with Dijkstra distances.

This script reads the SSSP and Dijkstra distance files and creates new output files
where unreachable vertices (marked as 'inf' in SSSP) are filled with Dijkstra distances.

Usage: python fill_sssp_with_dijkstra.py
"""

import os


def fill_distances(sssp_file, dijkstra_file, output_file):
    """
    Read SSSP and Dijkstra distance files, fill inf values with Dijkstra distances.
    """
    # Load SSSP distances
    sssp_dist = {}
    with open(sssp_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split()
            vertex = int(parts[0])
            dist_str = parts[1]
            if dist_str == 'inf':
                sssp_dist[vertex] = float('inf')
            else:
                sssp_dist[vertex] = float(dist_str)
    
    # Load Dijkstra distances
    dijkstra_dist = {}
    with open(dijkstra_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split()
            vertex = int(parts[0])
            dist_str = parts[1]
            if dist_str == 'inf':
                dijkstra_dist[vertex] = float('inf')
            else:
                dijkstra_dist[vertex] = float(dist_str)
    
    # Fill inf values with Dijkstra distances
    filled_dist = {}
    for vertex in sssp_dist:
        if sssp_dist[vertex] == float('inf'):
            filled_dist[vertex] = dijkstra_dist.get(vertex, float('inf'))
        else:
            filled_dist[vertex] = sssp_dist[vertex]
    
    # Write output
    with open(output_file, 'w') as f:
        f.write('# vertex distance (NEW SSSP filled with Dijkstra for inf)\n')
        for vertex in sorted(filled_dist.keys()):
            d = filled_dist[vertex]
            if d == float('inf'):
                f.write(f"{vertex} inf\n")
            else:
                f.write(f"{vertex} {d:.6f}\n")
    
    # Count filled vertices
    original_reach = sum(1 for d in sssp_dist.values() if d != float('inf'))
    filled_reach = sum(1 for d in filled_dist.values() if d != float('inf'))
    filled_count = filled_reach - original_reach
    
    return {
        'original_reach': original_reach,
        'filled_reach': filled_reach,
        'filled_count': filled_count,
        'total': len(filled_dist)
    }


if __name__ == '__main__':
    files = ['1k', '5k', '10k']
    
    print("Filling SSSP unreachable vertices with Dijkstra distances:\n")
    
    for base in files:
        sssp_file = f"newsssp_{base}_distances.txt"
        dijkstra_file = f"dijkstra_{base}_distances.txt"
        output_file = f"newsssp_{base}_filled_distances.txt"
        
        if not os.path.exists(sssp_file):
            print(f"Skip {base}: {sssp_file} not found")
            continue
        if not os.path.exists(dijkstra_file):
            print(f"Skip {base}: {dijkstra_file} not found")
            continue
        
        stats = fill_distances(sssp_file, dijkstra_file, output_file)
        
        print(f"{base}.txt:")
        print(f"  Original SSSP reach: {stats['original_reach']}/{stats['total']}")
        print(f"  Filled reach: {stats['filled_reach']}/{stats['total']}")
        print(f"  Filled vertices: {stats['filled_count']}")
        print(f"  Output: {output_file}\n")
    
    print("Done!")
