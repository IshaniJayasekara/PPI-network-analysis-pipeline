#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Extract a sub-network connecting a specific set of proteins.
         - Finds interactions between query proteins.
         - Finds SHORTEST PATHS for non-interacting query proteins.
         - Preserves all node attributes (submodule, hub status, etc.).

Usage:
    python extract_paths.py <input_network.graphml> <query_proteins.txt> <output_paths.graphml>
"""

import sys
import networkx as nx
from itertools import combinations
from performance_tracker import PerformanceTracker

def load_protein_list(file_path):
    """Load protein list from text file (one per line)."""
    with open(file_path, "r") as f:
        proteins = {line.strip() for line in f if line.strip()}
    return proteins

def main():
    if len(sys.argv) != 4:
        print("Usage: python extract_paths.py <input_network.graphml> <query_proteins.txt> <output_paths.graphml>")
        sys.exit(1)

    input_graph = sys.argv[1]
    protein_list_file = sys.argv[2]
    output_graph = sys.argv[3]

    tracker = PerformanceTracker("Path Extraction")

    # Step 1: Load Network
    tracker.start_step("Load Network")
    G = nx.read_graphml(input_graph)
    print(f"Loaded network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    tracker.end_step("Load Network")

    # Step 2: Load and Validate Query Proteins
    tracker.start_step("Validate Query Proteins")
    query_proteins = load_protein_list(protein_list_file)
    
    # Check which proteins are actually in the graph
    valid_proteins = [p for p in query_proteins if p in G.nodes()]
    missing = query_proteins - set(valid_proteins)
    
    print(f"Query proteins provided: {len(query_proteins)}")
    print(f"  - Found in network: {len(valid_proteins)}")
    if missing:
        print(f"  - Missing/Ignored: {len(missing)}")
        
    if len(valid_proteins) < 2:
        print("Error: Need at least 2 valid proteins to find paths.")
        sys.exit(1)
        
    tracker.end_step("Validate Query Proteins")

    # Step 3: Find Shortest Paths
    tracker.start_step("Calculate Shortest Paths")
    
    # We start with the query proteins themselves
    nodes_to_keep = set(valid_proteins)
    
    # Generate all possible pairs of valid proteins
    pairs = list(combinations(valid_proteins, 2))
    print(f"Analyzing {len(pairs)} pairs for connectivity...")
    
    paths_found = 0
    no_paths = 0
    
    for source, target in pairs:
        try:
            # shortest_path returns a list of nodes [source, p1, p2, ..., target]
            # We use unweighted path (BFS) to find the minimum number of hops (simplest bridge)
            path = nx.shortest_path(G, source=source, target=target)
            
            # Add all nodes in this path to our collection
            nodes_to_keep.update(path)
            paths_found += 1
            
        except nx.NetworkXNoPath:
            no_paths += 1
            # If no path exists (graph is disconnected), we just ignore this pair
            continue
            
    print(f"  - Connected pairs: {paths_found}")
    print(f"  - Disconnected pairs: {no_paths}")
    print(f"  - Total nodes in extracted network: {len(nodes_to_keep)} (Query + Bridge proteins)")
    
    tracker.end_step("Calculate Shortest Paths")

    # Step 4: Extract Subgraph
    tracker.start_step("Extract Subgraph")
    
    # Create the subgraph
    # .copy() is essential to create a standalone graph object
    # This automatically preserves ALL attributes (submodule, hub_type, z_score, etc.)
    H = G.subgraph(nodes_to_keep).copy()
    
    tracker.end_step("Extract Subgraph")

    # Step 5: Save Output
    tracker.start_step("Save GraphML")
    nx.write_graphml(H, output_graph)
    tracker.end_step("Save GraphML")

    tracker.print_summary()
    
    print(f"\n✓ Process Complete.")
    print(f"  Output saved to: {output_graph}")
    print(f"  Final Network: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

if __name__ == "__main__":
    main()