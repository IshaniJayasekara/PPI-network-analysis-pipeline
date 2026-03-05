#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Perform KEGG Pathway Enrichment Analysis on a network.
         - Input: .graphml file (Extracts all node names)
         - Source: KEGG
         - Output: Excel file with significant pathways.

Usage:
    python get_kegg_pathways.py <input_network.graphml> <kegg_results.xlsx>
"""

import sys
import pandas as pd
import networkx as nx
from gprofiler import GProfiler
from performance_tracker import PerformanceTracker

def main():
    if len(sys.argv) != 3:
        print("Usage: python get_kegg_pathways.py <input_network.graphml> <kegg_results.xlsx>")
        sys.exit(1)

    input_graph_file = sys.argv[1]
    output_excel_file = sys.argv[2]

    tracker = PerformanceTracker("KEGG Enrichment Analysis")

    # Step 1: Load Network Nodes
    tracker.start_step("Load Network Nodes")
    try:
        G = nx.read_graphml(input_graph_file)
        # Extract protein names (node IDs)
        query_proteins = list(G.nodes())
        print(f"Loaded network with {len(query_proteins)} proteins.")
    except Exception as e:
        print(f"Error loading graph: {e}")
        sys.exit(1)
    tracker.end_step("Load Network Nodes")

    # Step 2: Run g:Profiler (KEGG)
    tracker.start_step("Run KEGG Analysis")
    gp = GProfiler(return_dataframe=True)

    try:
        results = gp.profile(
            organism='hsapiens',
            query=query_proteins,
            sources=['KEGG'],  # Restrict to KEGG pathways
            user_threshold=0.05,
            no_evidences=False
        )
        
        if results.empty:
            print("No significant KEGG pathways found.")
            # Create empty Excel to avoid errors
            pd.DataFrame({'Message': ['No significant pathways found']}).to_excel(output_excel_file, index=False)
            sys.exit(0)

        # Calculate Percentage (Intersections / Total Input Proteins)
        results['Genes_Percentage'] = (results['intersection_size'] / len(query_proteins)) * 100

        # Clean up columns
        final_df = results[[
            'native', 'name', 'p_value', 
            'intersection_size', 'term_size', 'Genes_Percentage', 'intersections'
        ]].copy()
        
        final_df.columns = [
            'KEGG_ID', 'Pathway_Name', 'P_value', 
            'Intersection_Count', 'Pathway_Size', 'Genes_Percentage', 'Proteins_Involved'
        ]

        # Sort by P-value (Most significant first)
        final_df = final_df.sort_values(by='P_value', ascending=True)

        # Step 3: Save to Excel
        final_df.to_excel(output_excel_file, index=False)
        print(f"  - Found {len(final_df)} significant KEGG pathways.")
        print(f"  - Top result: {final_df.iloc[0]['Pathway_Name']} (p={final_df.iloc[0]['P_value']:.2e})")

    except Exception as e:
        print(f"Error during enrichment: {e}")
        sys.exit(1)

    tracker.end_step("Run KEGG Analysis")
    
    tracker.print_summary()
    print(f"\n✓ Analysis Complete.")
    print(f"  Output saved to: {output_excel_file}")

if __name__ == "__main__":
    main()