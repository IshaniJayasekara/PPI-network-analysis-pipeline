#!/usr/bin/env python3
"""
Date: 2026.03.12
Author: Ishani Jayasekara
Purpose: Automated GO Annotation Filter & Aggregator. 
         Handles varying GAF formats (14-17+ columns) and addresses float/NaN errors.

Usage:
    python process_protein_data.py <gaf_file> <exclude_codes>
"""

import pandas as pd
import sys
import os
from pathlib import Path
from performance_tracker import PerformanceTracker, print_system_info

# ------------------------------------------------------------
def generate_output_filename(input_file):
    return f"{Path(input_file).stem}_processed.xlsx"

# ------------------------------------------------------------
def safe_join(series):
    """
    Bioinformatics cleanup: Removes NaNs, converts everything to string,
    strips whitespace, removes duplicates, and joins with '|'.
    """
    # Filter out nulls/NaNs and empty strings, then convert all to string
    clean_items = [
        str(item).strip() 
        for item in series 
        if pd.notna(item) and str(item).strip() != ""
    ]
    # Return unique, sorted items joined by pipe
    return "|".join(sorted(set(clean_items)))

# ------------------------------------------------------------
def validate_data(df, required_cols):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"❌ Error: Missing essential columns: {missing}")
        sys.exit(1)

# ------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("Usage: python process_protein_data.py <gaf_file> <exclude_codes>")
        sys.exit(1)

    input_file = sys.argv[1]
    exclude_codes = [c.strip().upper() for c in sys.argv[2].split(",")]

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    output_file = generate_output_filename(input_file)
    metrics_file = output_file.replace(".xlsx", "_metrics.json")

    print(f"\n{'='*70}")
    print("GO Annotation Filtering Configuration")
    print(f"{'='*70}")
    print(f"Input File: {input_file}")
    print(f"Exclude Evidence Codes: {exclude_codes}")
    print(f"{'='*70}\n")

    print_system_info()
    tracker = PerformanceTracker("GO Annotation Filtering")

    # ------------------------------------------------------------
    # STEP 1: Load GAF
    # ------------------------------------------------------------
    tracker.start_step("Load GAF file")
    
    df = pd.read_csv(
        input_file,
        sep="\t",
        header=None,
        comment="!",
        dtype=str,
        low_memory=False
    )
    
    tracker.end_step("Load GAF file")

    # ------------------------------------------------------------
    # STEP 2: Assign GAF columns dynamically
    # ------------------------------------------------------------
    gaf_columns = [
        "DB", "UniProtKB", "Gene_Symbol", "Qualifier", "GO_Term",
        "Reference", "Evidence", "With_From", "Aspect",
        "DB_Object_Name", "DB_Object_Synonym", "DB_Object_Type",
        "Taxon", "Date", "Assigned_By", "Annotation_Extension",
        "Gene_Product_Form_ID"
    ]

    actual_col_count = df.shape[1]
    df.columns = gaf_columns[:actual_col_count]
    print(f"ℹ️  Detected {actual_col_count} columns in GAF file.")

    validate_data(df, ["UniProtKB", "GO_Term", "Evidence"])

    # ------------------------------------------------------------
    # STEP 3: Filter Evidence Codes
    # ------------------------------------------------------------
    tracker.start_step("Filter evidence codes")
    
    # Clean evidence column for comparison
    df["Evidence"] = df["Evidence"].str.upper().str.strip()
    filtered_df = df[~df["Evidence"].isin(exclude_codes)].copy()
    
    tracker.end_step("Filter evidence codes")

    # ------------------------------------------------------------
    # STEP 4: Aggregate to Protein Level
    # ------------------------------------------------------------
    tracker.start_step("Aggregate to protein level")

    # Group by Protein ID and apply safe_join
    protein_df = (
        filtered_df
        .groupby("UniProtKB", as_index=False)
        .agg({
            "Gene_Symbol": "first",
            "GO_Term": safe_join,
            "Aspect": safe_join,
            "Evidence": safe_join,
            "Reference": safe_join,
            "Taxon": "first"
        })
    )

    # Calculate Unique GO counts accurately
    counts = filtered_df.groupby("UniProtKB")["GO_Term"].nunique().reset_index()
    counts.columns = ["UniProtKB", "GO_Annotation_Count"]
    protein_df = protein_df.merge(counts, on="UniProtKB", how="left")

    tracker.end_step("Aggregate to protein level")

    # ------------------------------------------------------------
    # STEP 5: Save Output
    # ------------------------------------------------------------
    tracker.start_step("Save results")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        protein_df.to_excel(writer, "Protein_Level_Annotations", index=False)
        filtered_df.to_excel(writer, "All_Filtered_Rows", index=False)

    tracker.end_step("Save results")

    tracker.print_summary()
    tracker.save_metrics(metrics_file)

    print(f"\n✓ PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Unique proteins: {len(protein_df):,}")
    print(f"Output: {output_file}\n")


if __name__ == "__main__":
    main()