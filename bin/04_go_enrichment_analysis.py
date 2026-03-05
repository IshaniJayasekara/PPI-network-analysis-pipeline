#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Perform GO Enrichment Analysis (GO:BP Only).
         - FILTER: Only keeps terms where Genes_Percentage > 75.0
         - Input: Excel file with columns "Submodule 1", "Submodule 2", etc.
         - Output: Single Excel file with one sheet per submodule.

Usage:
    python run_enrichment.py <modules_list.xlsx> <enrichment_results_filtered.xlsx>
"""

import sys
import pandas as pd
from gprofiler import GProfiler
from performance_tracker import PerformanceTracker

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_enrichment.py <modules_list.xlsx> <output_file.xlsx>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Filter Threshold
    PERCENTAGE_THRESHOLD = 75.0

    tracker = PerformanceTracker("GO Enrichment (>75%)")

    # Step 1: Load Submodules
    tracker.start_step("Load Submodules")
    try:
        df_modules = pd.read_excel(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    print(f"Loaded input file with {len(df_modules.columns)} submodules.")
    tracker.end_step("Load Submodules")

    # Initialize g:Profiler
    gp = GProfiler(return_dataframe=True)

    # Step 2: Run Analysis & Save
    tracker.start_step("Run g:Profiler & Save")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        for column in df_modules.columns:
            submodule_name = str(column)
            print(f"Processing {submodule_name}...")

            # Extract protein list
            query_proteins = df_modules[column].dropna().astype(str).tolist()
            query_proteins = [p for p in query_proteins if p.strip() != ""]

            if not query_proteins:
                continue

            try:
                # Run Enrichment (GO:BP only)
                results = gp.profile(
                    organism='hsapiens',
                    query=query_proteins,
                    sources=['GO:BP'],
                    user_threshold=0.05,
                    no_evidences=False
                )
                
                if results.empty:
                    print(f"  - No significant terms found (raw).")
                    pd.DataFrame({'Message': ['No significant terms found']}).to_excel(writer, sheet_name=submodule_name[:31])
                    continue

                # Calculate Percentage
                results['Genes_Percentage'] = (results['intersection_size'] / len(query_proteins)) * 100

                # --- FILTERING STEP ---
                # Keep only terms where percentage > 75.0
                results = results[results['Genes_Percentage'] > PERCENTAGE_THRESHOLD]

                if results.empty:
                    print(f"  - No terms > {PERCENTAGE_THRESHOLD}% found.")
                    pd.DataFrame({'Message': [f'No terms > {PERCENTAGE_THRESHOLD}%']}).to_excel(writer, sheet_name=submodule_name[:31])
                    continue

                # Select and Rename Columns
                final_df = results[[
                    'source', 'native', 'name', 'p_value', 
                    'intersection_size', 'term_size', 'Genes_Percentage', 'intersections'
                ]].copy()
                
                final_df.columns = [
                    'Source', 'Term_ID', 'Term_Name', 'P_value', 
                    'Intersection_Count', 'Term_Size', 'Genes_Percentage', 'Intersecting_Proteins'
                ]

                # Sort by P-value ascending
                final_df = final_df.sort_values(by='P_value', ascending=True)

                # Write to Sheet
                sheet_name = submodule_name[:31]
                final_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"  - Saved {len(final_df)} filtered terms to '{sheet_name}'.")

            except Exception as e:
                print(f"  - Error processing {submodule_name}: {e}")

    tracker.end_step("Run g:Profiler & Save")
    
    tracker.print_summary()
    print(f"\n✓ Analysis Complete.")
    print(f"  Output saved to: {output_file}")

if __name__ == "__main__":
    main()