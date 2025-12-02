from typing import Dict, Any
import sssp_concept

def get_sssp_statistics() -> Dict[str, Any]:
    """Get diagnostic statistics about the most recent SSSP run."""
    d_hat = sssp_concept.d_hat
    path_alpha = sssp_concept.path_alpha
    N_vertices = sssp_concept.N_vertices
    k_param = sssp_concept.k_param
    t_param = sssp_concept.t_param
    
    reachable = [v for v in range(N_vertices) if d_hat.get(v, float('inf')) != float('inf')]
    unreachable = [v for v in range(N_vertices) if d_hat.get(v, float('inf')) == float('inf')]
    
    stats = {
        'n': N_vertices,
        'k_param': k_param,
        't_param': t_param,
        'reachable_count': len(reachable),
        'unreachable_count': len(unreachable),
        'reachable_pct': 100.0 * len(reachable) / N_vertices if N_vertices > 0 else 0.0,
    }
    
    if reachable:
        finite_dists = [d_hat[v] for v in reachable]
        finite_alphas = [path_alpha[v] for v in reachable if path_alpha.get(v, float('inf')) != float('inf')]
        
        stats['max_distance'] = max(finite_dists)
        stats['avg_distance'] = sum(finite_dists) / len(finite_dists)
        
        if finite_alphas:
            stats['avg_path_length'] = sum(finite_alphas) / len(finite_alphas)
            stats['max_path_length'] = max(finite_alphas)
        else:
            stats['avg_path_length'] = 0.0
            stats['max_path_length'] = 0
    else:
        stats['max_distance'] = None
        stats['avg_distance'] = None
        stats['avg_path_length'] = None
        stats['max_path_length'] = None
    
    return stats


def print_sssp_statistics():
    """Print diagnostic statistics about the most recent SSSP run."""
    stats = get_sssp_statistics()
    print("\n" + "="*60)
    print("SSSP ALGORITHM STATISTICS")
    print("="*60)
    print(f"Graph size (n):           {stats['n']}")
    print(f"Parameters:               k={stats['k_param']}, t={stats['t_param']}")
    print(f"Reachable vertices:       {stats['reachable_count']}/{stats['n']} ({stats['reachable_pct']:.1f}%)")
    print(f"Unreachable (INF):        {stats['unreachable_count']}")
    
    if stats['max_distance'] is not None:
        print(f"Max distance found:       {stats['max_distance']:.4f}")
        print(f"Avg distance:             {stats['avg_distance']:.4f}")
    
    if stats['avg_path_length'] is not None:
        print(f"Avg path length (edges):  {stats['avg_path_length']:.2f}")
        print(f"Max path length:          {stats['max_path_length']}")
    
    print("="*60)
