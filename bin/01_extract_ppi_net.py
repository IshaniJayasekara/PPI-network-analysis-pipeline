#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Extract PPI network module strictly for proteins found in the global network.
         Proteins not found in the global network are DISCARDED.

Input:
    1. Text file with STRING preferred protein names (one per line)
    2. Global organismal PPI network in .graphml format

Output:
    1. Extracted PPI subnetwork (containing only found proteins)
    2. missing_proteins.txt (list of dropped proteins)
"""

import sys
import os
import networkx as nx
from performance_tracker import PerformanceTracker

def load_protein_list(file_path):
    """Load protein list from text file"""
    with open(file_path, "r") as f:
        proteins = {line.strip() for line in f if line.strip()}
    return proteins

def main():
    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "  python 01_extract_ppi_network.py "
            "<protein_list.txt> <global_ppi.graphml> <output_subnetwork.graphml>"
        )
        sys.exit(1)

    protein_list_file = sys.argv[1]
    global_ppi_file = sys.argv[2]
    output_file = sys.argv[3]
    missing_report_file = "missing_proteins.txt"

    tracker = PerformanceTracker("PPI Subnetwork Extraction")

    # Step 1: Load protein list
    tracker.start_step("Load protein list")
    proteins_of_interest = load_protein_list(protein_list_file)
    tracker.end_step("Load protein list")

    print(f"Input query proteins: {len(proteins_of_interest)}")

    # Step 2: Load global PPI network
    tracker.start_step("Load global PPI network")
    G = nx.read_graphml(global_ppi_file)
    tracker.end_step("Load global PPI network")

    print(f"Global network: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    # Step 3: Filter Valid Nodes
    tracker.start_step("Filter valid nodes")
    
    global_nodes = set(G.nodes())
    
    # Only keep proteins that exist in the global graph
    valid_proteins = proteins_of_interest.intersection(global_nodes)
    
    # Identify dropped proteins
    dropped_proteins = proteins_of_interest - global_nodes
    
    tracker.end_step("Filter valid nodes")

    print(f"  - Keeping {len(valid_proteins)} proteins (found in network)")
    print(f"  - Dropping {len(dropped_proteins)} proteins (not found)")

    # Step 4: Extract the subnetwork
    tracker.start_step("Extract subnetwork")
    # We only create the subgraph for the valid proteins.
    # Dropped proteins are ignored completely.
    subgraph = G.subgraph(valid_proteins).copy()
    tracker.end_step("Extract subnetwork")

    # Step 5: Write missing report (Optional but recommended)
    if dropped_proteins:
        with open(missing_report_file, "w") as f:
            f.write("The following proteins were dropped because they were not found in the global network:\n")
            f.write("=================================================================================\n")
            for p in sorted(list(dropped_proteins)):
                f.write(f"{p}\n")
        print(f"  [Info] List of dropped proteins saved to: {missing_report_file}")

    # Step 6: Save GraphML
    tracker.start_step("Write output file")
    nx.write_graphml(subgraph, output_file)
    tracker.end_step("Write output file")

    tracker.print_summary()
    
    print(f"\n✓ Process Complete.")
    print(f"  Output File: {output_file}")
    print(f"  Final Network Size: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")

if __name__ == "__main__":
    main()