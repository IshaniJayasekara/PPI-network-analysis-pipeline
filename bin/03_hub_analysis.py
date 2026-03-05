#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Analyze network hubs (Z-score & Participation Coefficient).
         - Intra-modular Hubs: Z >= 1.5, P <= 0.05
         - Inter-modular Hubs: Z >= 1.5, P > 0.05
         - Inputs: Network with 'submodule' attribute
         - Outputs: Annotated GraphML + Excel Reports

Usage:
    python analyze_hubs.py <input_network.graphml> <output_network.graphml>
"""

import sys
import numpy as np
import pandas as pd
import networkx as nx
from performance_tracker import PerformanceTracker

def calculate_z_score(G, module_dict):
    """
    Calculate Within-module degree Z-score.
    Z_i = (k_i - mean_k_s) / sigma_k_s
    """
    z_scores = {}
    
    # Group nodes by module
    modules = {}
    for node, mod_id in module_dict.items():
        if mod_id == 0: continue # Skip unassigned nodes
        modules.setdefault(mod_id, []).append(node)
        
    # Calculate Z for each node
    for mod_id, nodes in modules.items():
        # Get degrees of these nodes restricted to the module
        k_s_values = {}
        for node in nodes:
            # Count neighbors that are also in the SAME module
            internal_degree = sum(1 for neighbor in G.neighbors(node) if module_dict.get(neighbor) == mod_id)
            k_s_values[node] = internal_degree
            
        # Calculate stats for this module
        degrees = list(k_s_values.values())
        mean_k = np.mean(degrees)
        std_k = np.std(degrees)
        
        for node in nodes:
            if std_k == 0:
                # If all nodes have same degree, Z is 0
                z_scores[node] = 0.0
            else:
                z_scores[node] = (k_s_values[node] - mean_k) / std_k
                
    return z_scores

def calculate_participation(G, module_dict):
    """
    Calculate Participation Coefficient (P).
    P_i = 1 - sum((k_is / k_i)^2)
    """
    p_scores = {}
    
    for node in G.nodes():
        mod_id = module_dict.get(node, 0)
        if mod_id == 0: 
            p_scores[node] = 0.0
            continue
            
        total_degree = G.degree[node]
        if total_degree == 0:
            p_scores[node] = 0.0
            continue
            
        # Count links to each module
        module_links = {}
        for neighbor in G.neighbors(node):
            n_mod = module_dict.get(neighbor, 0)
            if n_mod != 0: # We typically only count links to valid modules
                module_links[n_mod] = module_links.get(n_mod, 0) + 1
        
        # Calculate Sum of squares
        sum_sq = 0.0
        for m_links in module_links.values():
            sum_sq += (m_links / total_degree) ** 2
            
        p_scores[node] = 1.0 - sum_sq
        
    return p_scores

def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze_hubs.py <input_with_modules.graphml> <output_annotated.graphml>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Thresholds
    Z_THRESHOLD = 1.5
    P_THRESHOLD = 0.5 # Boundary between Provincial (Intra) and Connector (Inter)

    tracker = PerformanceTracker("Hub Analysis")
    
    # Step 1: Load Network
    tracker.start_step("Load Network")
    G = nx.read_graphml(input_file)
    
    # Extract module assignments (converting to int for safety)
    try:
        module_dict = {n: int(d.get('submodule', 0)) for n, d in G.nodes(data=True)}
    except (ValueError, TypeError):
        print("Error: 'submodule' attribute missing or not an integer in GraphML.")
        sys.exit(1)
        
    print(f"Loaded {len(G)} nodes. Calculating metrics...")
    tracker.end_step("Load Network")
    
    # Step 2: Calculate Metrics
    tracker.start_step("Calculate Z & P")
    z_scores = calculate_z_score(G, module_dict)
    p_scores = calculate_participation(G, module_dict)
    tracker.end_step("Calculate Z & P")
    
    # Step 3: Classify Hubs
    tracker.start_step("Classify Hubs")
    
    hub_type = {}
    intra_hubs_data = []
    inter_hubs_data = []
    
    for node in G.nodes():
        mod = module_dict.get(node, 0)
        if mod == 0:
            hub_type[node] = "Non-hub (Unassigned)"
            continue
            
        z = z_scores.get(node, 0.0)
        p = p_scores.get(node, 0.0)
        
        classification = "Non-hub"
        
        if z >= Z_THRESHOLD:
            if p <= P_THRESHOLD:
                classification = "Intra-modular Hub"
                intra_hubs_data.append({
                    "Protein": node,
                    "Submodule": mod,
                    "Z_score": z,
                    "Participation": p
                })
            else:
                classification = "Inter-modular Hub"
                inter_hubs_data.append({
                    "Protein": node,
                    "Submodule": mod,
                    "Z_score": z,
                    "Participation": p
                })
        
        hub_type[node] = classification
        
    tracker.end_step("Classify Hubs")
    
    # Step 4: Save Network
    tracker.start_step("Save GraphML")
    nx.set_node_attributes(G, z_scores, "z_score")
    nx.set_node_attributes(G, p_scores, "participation")
    nx.set_node_attributes(G, hub_type, "hub_type")
    nx.write_graphml(G, output_file)
    tracker.end_step("Save GraphML")
    
    # Step 5: Save Excel Reports
    tracker.start_step("Save Excel Reports")
    
    # Helper to sort and save
    def save_excel(data_list, filename, sheet_name):
        if not data_list:
            print(f"  - Warning: No {sheet_name} found. Creating empty file.")
            pd.DataFrame().to_excel(filename)
            return

        df = pd.DataFrame(data_list)
        # Sort: Primary = Submodule (Ascending), Secondary = Z-score (Descending)
        df = df.sort_values(by=["Submodule", "Z_score"], ascending=[True, False])
        df.to_excel(filename, index=False)
        print(f"  - Saved {len(df)} {sheet_name} to {filename}")

    save_excel(intra_hubs_data, "intra_modular_hubs.xlsx", "Intra-modular Hubs")
    save_excel(inter_hubs_data, "inter_modular_hubs.xlsx", "Inter-modular Hubs")
    
    tracker.end_step("Save Excel Reports")
    
    # Step 6: Console Summary
    print(f"\n{'='*60}")
    print(f"HUB ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Nodes Analyzed: {len(G)}")
    print(f"Intra-modular Hubs (Provincial): {len(intra_hubs_data)}")
    print(f"Inter-modular Hubs (Connector):  {len(inter_hubs_data)}")
    print(f"{'-'*60}")
    
    # Print top 3 of each category to console
    print("\nTop 3 Intra-modular Hubs (Highest Z):")
    intra_sorted = sorted(intra_hubs_data, key=lambda x: x['Z_score'], reverse=True)[:3]
    for h in intra_sorted:
        print(f"  {h['Protein']} (Mod {h['Submodule']}): Z={h['Z_score']:.2f}, P={h['Participation']:.2f}")
        
    print("\nTop 3 Inter-modular Hubs (Highest P):")
    # For inter, we sort by Participation to see best connectors
    inter_sorted = sorted(inter_hubs_data, key=lambda x: x['Participation'], reverse=True)[:3]
    for h in inter_sorted:
        print(f"  {h['Protein']} (Mod {h['Submodule']}): Z={h['Z_score']:.2f}, P={h['Participation']:.2f}")

    tracker.print_summary()

if __name__ == "__main__":
    main()