#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Generate global PPI network in .graphml format from STRING files using Preferred Names
"""
import networkx as nx
import pandas as pd
import gzip
import sys
import re
import os
from performance_tracker import PerformanceTracker, print_system_info

def extract_version_from_filename(filename):
    """
    Extract STRING database version from filename
    Example: 9606.protein.links.v12.0.txt.gz -> v12.0
    """
    match = re.search(r'v(\d+\.\d+)', filename)
    if match:
        return match.group(0)  # Returns 'v12.0'
    return 'vUnknown'

def generate_output_filename(organism, version, score, output_dir='.'):
    """
    Generate output filename based on organism, version, and score
    Format: <organism>_PPI_<version>_score<score>.graphml
    Example: human_PPI_v12.0_score400.graphml
    """
    base_name = f"{organism}_PPI_{version}_cs{score}"
    graphml_file = os.path.join(output_dir, f"{base_name}.graphml")
    return graphml_file, base_name

def main():
    # Check arguments
    if len(sys.argv) != 5:
        print("Usage: python script.py <ppi_file.gz> <protein_info_file.gz> <organism_name> <score>", flush=True)
        print("\nIMPORTANT: Use the 'protein.info' file for the second argument to get preferred names.", flush=True)
        print("\nExample:", flush=True)
        print("  python script.py 9606.protein.links.v12.0.txt.gz 9606.protein.info.v12.0.txt.gz human 400", flush=True)
        sys.exit(1)
    
    # Parse arguments
    ppi_file = sys.argv[1]
    info_file = sys.argv[2] # Changed from aliases_file to info_file
    organism = sys.argv[3]
    score = int(sys.argv[4])
    
    # Extract version from PPI filename
    version = extract_version_from_filename(ppi_file)
    
    # Generate output filenames
    out_file, base_name = generate_output_filename(organism, version, score)
    metrics_file = f"{base_name}_metrics.json"
    
    # Print configuration
    print(f"\n{'='*70}", flush=True)
    print(f"PPI Network Generation Configuration (Preferred Names)", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"Organism: {organism}", flush=True)
    print(f"STRING Version: {version}", flush=True)
    print(f"Combined Score Threshold: {score}", flush=True)
    print(f"Mapping File: {info_file}", flush=True)
    print(f"Output File: {out_file}", flush=True)
    print(f"{'='*70}\n", flush=True)
    
    # Print system info
    print_system_info()
    
    # Initialize performance tracker
    tracker = PerformanceTracker(f"PPI Network Generation - {organism} ({version})")
    
    # Step 1: Load PPI data
    tracker.start_step("Load PPI data")
    with gzip.open(ppi_file, 'rt') as f:
        ppi = pd.read_csv(f, sep=' ')
    
    # Filter interactions
    initial_count = len(ppi)
    ppi = ppi[(ppi['protein1'] != ppi['protein2']) & (ppi['combined_score'] >= score)]
    print(f"  Filtered {initial_count:,} -> {len(ppi):,} interactions (score >= {score})", flush=True)
    tracker.end_step("Load PPI data")
    
    # Step 2: Load Protein Info (Preferred Names)
    tracker.start_step("Load Protein Info")
    with gzip.open(info_file, 'rt') as f:
        # STRING info files are TSV with headers: #string_protein_id, preferred_name, ...
        info = pd.read_csv(f, sep='\t')
    
    # Rename the first column to remove the hash if present (e.g. '#string_protein_id' -> 'string_protein_id')
    info.rename(columns={info.columns[0]: 'string_protein_id'}, inplace=True)
    
    # Create dictionary mapping ID -> Preferred Name
    # We strip whitespace just in case
    name_map = info.set_index('string_protein_id')['preferred_name'].to_dict()
    
    print(f"  Loaded {len(name_map):,} preferred names", flush=True)
    tracker.end_step("Load Protein Info")
    
    # Step 3: Build network
    tracker.start_step("Build network")
    G = nx.Graph()
    
    missing_names = 0
    for _, r in ppi.iterrows():
        p1 = r['protein1']
        p2 = r['protein2']
        
        # Get preferred names, fallback to ID if missing
        name1 = name_map.get(p1, p1)
        name2 = name_map.get(p2, p2)
        
        if name1 == p1 or name2 == p2:
            missing_names += 1

        G.add_edge(
            name1,
            name2,
            weight=r['combined_score'] / 1000.0
        )
            
    print(f"  Created network: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges", flush=True)
    if missing_names > 0:
        print(f"  Warning: {missing_names:,} lookups failed (used ID instead of name)", flush=True)
        
    tracker.end_step("Build network")
    
    # Step 4: Save network
    tracker.start_step("Save GraphML")
    nx.write_graphml(G, out_file)
    print(f"  Saved to: {out_file}", flush=True)
    tracker.end_step("Save GraphML")
    
    # Print summary
    tracker.print_summary()
    
    # Final output
    print(f"\n{'='*70}", flush=True)
    print(f"✓ PIPELINE COMPLETED SUCCESSFULLY", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"Organism: {organism}", flush=True)
    print(f"Network: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges", flush=True)
    print(f"Output: {out_file}", flush=True)
    print(f"Metrics: {metrics_file}", flush=True)
    print(f"{'='*70}\n", flush=True)
    
    # Save metrics JSON
    tracker.save_metrics(metrics_file)

if __name__ == '__main__':
    main()