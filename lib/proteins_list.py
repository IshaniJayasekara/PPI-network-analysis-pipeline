#!/usr/bin/env python3
"""
Date: 2026.02.02
Author: Ishani Jayasekara
Purpose: Prepare the final list of proteins to extract PPIs from global organism PPI network

Input:
    1. STRING mapping file (tsv/csv/xlsx) containing column 'preferredName'
    2. 0–N Excel files with sheet 'Protein_Level_Annotations'
       and column 'Gene_Symbol'

Output:
    Text file containing merged, unique protein names

Usage: 
"""

import sys
import os
import pandas as pd
from performance_tracker import PerformanceTracker


def load_mapping_file(file_path):
    """Load STRING mapping file and extract preferredName column"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".tsv", ".txt"]:
        df = pd.read_csv(file_path, sep="\t")
    elif ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported mapping file format: {ext}")

    if "preferredName" not in df.columns:
        raise ValueError("Column 'preferredName' not found in mapping file")

    return set(df["preferredName"].dropna().astype(str))


def load_annotation_excel(file_path):
    """Load Protein_Level_Annotations sheet and extract Gene_Symbol"""
    df = pd.read_excel(file_path, sheet_name="Protein_Level_Annotations")

    if "Gene_Symbol" not in df.columns:
        raise ValueError(
            f"Column 'Gene_Symbol' not found in {file_path}"
        )

    return set(df["Gene_Symbol"].dropna().astype(str))


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python process_protein_data.py <string_mapping_file> "
            "[annotation_1.xlsx ... annotation_N.xlsx] "
            "[--out output_file.txt]"
        )
        sys.exit(1)

    # Default output file
    output_file = "input_protein_list.txt"

    # Handle optional --out argument
    if "--out" in sys.argv:
        out_index = sys.argv.index("--out")
        try:
            output_file = sys.argv[out_index + 1]
        except IndexError:
            raise ValueError("Please provide a filename after --out")

        # Remove --out and filename from argument list
        args = sys.argv[1:out_index]
    else:
        args = sys.argv[1:]

    mapping_file = args[0]
    excel_files = args[1:]  # 0–N Excel files

    tracker = PerformanceTracker("Protein List Preparation")

    # Load STRING mapping file
    tracker.start_step("Load STRING mapping file")
    mapping_proteins = load_mapping_file(mapping_file)
    tracker.end_step("Load STRING mapping file")

    all_annotation_proteins = set()

    # Load annotation Excel files (if any)
    if excel_files:
        for i, excel_file in enumerate(excel_files, start=1):
            step_name = f"Load annotation Excel file {i}: {os.path.basename(excel_file)}"
            tracker.start_step(step_name)
            proteins = load_annotation_excel(excel_file)
            all_annotation_proteins.update(proteins)
            tracker.end_step(step_name)
    else:
        print("ℹ No annotation Excel files provided — using STRING mapping only")

    # Merge and deduplicate
    tracker.start_step("Merge and deduplicate protein lists")
    final_proteins = sorted(mapping_proteins | all_annotation_proteins)
    tracker.end_step("Merge and deduplicate protein lists")

    # Print protein count
    print(f"Number of proteins in final list: {len(final_proteins)}")

    # Write output
    tracker.start_step("Write output file")
    with open(output_file, "w") as f:
        for protein in final_proteins:
            f.write(f"{protein}\n")
    tracker.end_step("Write output file")

    tracker.print_summary()

    print(f"✓ Successfully wrote  {len(final_proteins)} proteins list to: {output_file}")


if __name__ == "__main__":
    main()
