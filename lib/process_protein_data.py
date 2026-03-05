#!/usr/bin/env python3
"""
Date: 2026.01.30
Author: Ishani Jayasekara
Purpose: GO Annotation Filter by evidence codes (IEA, NAS, etc.) and remove redundant protein records

Input - plain text file directly downloaded from AMIGO2
Output - xlsx file including processed data

Usage:
    python process_protein_data.py <gaf_file> <exclude_codes>
Example:
    python process_protein_data.py goa_subset.gaf "IEA,NAS"
"""

import pandas as pd
import sys
import os
from pathlib import Path
from performance_tracker import PerformanceTracker, print_system_info


# ------------------------------------------------------------
def generate_output_filename(input_file):
    return f"{Path(input_file).name}_processed.xlsx"


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
    # STEP 1: Load plain GAF (no headers)
    # ------------------------------------------------------------
    tracker.start_step("Load GAF file")

    df = pd.read_csv(
        input_file,
        sep="\t",
        header=None,
        comment="!",
        dtype=str
    )

    tracker.end_step("Load GAF file")

    # ------------------------------------------------------------
    # STEP 2: Assign GAF 2.x columns
    # ------------------------------------------------------------
    gaf_columns = [
        "DB",
        "UniProtKB",
        "Gene_Symbol",
        "Qualifier",
        "GO_Term",
        "Reference",
        "Evidence",
        "With_From",
        "Aspect",
        "DB_Object_Name",
        "DB_Object_Synonym",
        "DB_Object_Type",
        "Taxon",
        "Date",
        "Assigned_By",
        "Annotation_Extension",
        "Gene_Product_Form_ID"
    ]

    df = df.iloc[:, :len(gaf_columns)]
    df.columns = gaf_columns

    # ------------------------------------------------------------
    # STEP 3: Clean & filter evidence
    # ------------------------------------------------------------
    df["Evidence"] = df["Evidence"].str.upper().str.strip()

    tracker.start_step("Filter evidence codes")
    filtered_df = df[~df["Evidence"].isin(exclude_codes)].copy()
    tracker.end_step("Filter evidence codes")

    # ------------------------------------------------------------
    # STEP 4: AGGREGATE TO ONE ROW PER PROTEIN
    # ------------------------------------------------------------
    tracker.start_step("Aggregate to protein level")

    protein_df = (
        filtered_df
        .groupby("UniProtKB", as_index=False)
        .agg({
            "Gene_Symbol": "first",
            "GO_Term": lambda x: "|".join(sorted(set(x))),
            "Aspect": lambda x: "|".join(sorted(set(x))),
            "Evidence": lambda x: "|".join(sorted(set(x))),
            "Reference": lambda x: "|".join(sorted(set(x.dropna()))),
            "Taxon": "first"
        })
    )

    protein_df["GO_Annotation_Count"] = (
        filtered_df.groupby("UniProtKB")["GO_Term"].nunique().values
    )

    tracker.end_step("Aggregate to protein level")

    # ------------------------------------------------------------
    # STEP 5: Save output
    # ------------------------------------------------------------
    tracker.start_step("Save results")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        protein_df.to_excel(writer, "Protein_Level_Annotations", index=False)
        filtered_df.to_excel(writer, "All_Filtered_Rows", index=False)

    tracker.end_step("Save results")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------
    tracker.print_summary()
    tracker.save_metrics(metrics_file)

    print(f"\n✓ PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Unique proteins: {protein_df['UniProtKB'].nunique():,}")
    print(f"Output file: {output_file}\n")


if __name__ == "__main__":
    main()
