#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Detect submodules using Louvain (seed=1).
         - Excel Output: Columns as "Submodule 1", "Submodule 2"...
         - Graph Output: Nodes have "submodule" attribute.


Usage:
    python 02_sumodule_detection.py SCA-cognition-gutbrain.graphml SCA-cognition-gutbrain-submoduled.graphml submodules_list.xlsx 1.0
"""

import sys
import networkx as nx
import pandas as pd
from performance_tracker import PerformanceTracker

def main():
    if len(sys.argv) != 5:
        print("Usage: python detect_modules.py <input_graphml> <output_graphml> <output_xlsx> <resolution>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_graph_file = sys.argv[2]
    output_excel_file = sys.argv[3]
    try:
        resolution = float(sys.argv[4])
    except ValueError:
        print("Error: Resolution must be a number.")
        sys.exit(1)

    tracker = PerformanceTracker("Louvain Module Detection")

    # Step 1: Load Network
    tracker.start_step("Load Network")
    G = nx.read_graphml(input_file)
    print(f"Loaded network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    tracker.end_step("Load Network")

    # Step 2: Run Louvain
    tracker.start_step("Run Louvain Algorithm")
    
    # Filter for connected nodes
    nodes_with_edges = [n for n, d in G.degree() if d > 0]
    G_active = G.subgraph(nodes_with_edges)
    
    print(f"Running Louvain (res={resolution}, seed=1)...")
    
    # Set seed to 1 as requested
    communities = nx.community.louvain_communities(
        G_active, 
        weight='weight', 
        resolution=resolution, 
        seed=1
    )
    
    tracker.end_step("Run Louvain Algorithm")

    # Step 3: Process Modules
    tracker.start_step("Process Modules")
    
    # Initialize all nodes with submodule = 0
    module_assignment = {n: 0 for n in G.nodes()}
    
    # Filter valid modules (>3 nodes)
    valid_modules = [c for c in communities if len(c) > 3]
    
    # Sort modules by size (largest first)
    valid_modules.sort(key=len, reverse=True)
    
    print(f"  - Found {len(valid_modules)} valid modules (>3 nodes)")
    
    # Assign IDs and prepare data for Excel
    excel_data = {}
    
    for idx, comm in enumerate(valid_modules, start=1):
        col_name = f"Submodule {idx}"
        
        # Sort proteins inside the module by degree (highest degree at top)
        # This keeps the list organized even without a visible Degree column
        sorted_proteins = sorted(list(comm), key=lambda x: G.degree[x], reverse=True)
        
        # Update graph assignment
        for node in comm:
            module_assignment[node] = idx
            
        # Store for Excel (using pd.Series handles unequal list lengths)
        excel_data[col_name] = pd.Series(sorted_proteins)

    tracker.end_step("Process Modules")

    # Step 4: Save GraphML
    tracker.start_step("Save GraphML")
    nx.set_node_attributes(G, module_assignment, "submodule")
    nx.write_graphml(G, output_graph_file)
    tracker.end_step("Save GraphML")

    # Step 5: Save Excel
    tracker.start_step("Save Excel")
    
    if excel_data:
        # pd.concat is the standard way to merge Series into a DataFrame
        df = pd.DataFrame(excel_data)
        
        # Replace NaN with empty string for a clean look
        df = df.fillna("")
        
        df.to_excel(output_excel_file, index=False)
        print(f"  - Excel saved: {len(df.columns)} module columns.")
    else:
        print("  - Warning: No valid modules found.")
        pd.DataFrame().to_excel(output_excel_file)

    tracker.end_step("Save Excel")
    tracker.print_summary()

if __name__ == "__main__":
    main()