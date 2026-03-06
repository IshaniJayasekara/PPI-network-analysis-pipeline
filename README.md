# PPI Network Analysis Pipeline

A **Nextflow DSL2 workflow** for automated analysis of **protein–protein interaction (PPI) networks**.

Given a **global PPI network** and a **list of query proteins**, the pipeline performs:

- Query-specific **subnetwork extraction**
- **Community detection** using the Louvain algorithm
- Identification of **hub proteins**
- **Gene Ontology (GO) enrichment analysis** of detected modules

The pipeline is designed for **reproducible, scalable network analysis** using **Nextflow** and **Docker**.

---

# Pipeline Overview

The workflow executes four sequential steps:

| Step | Process | Script | Description |
|-----|-----|-----|-----|
| 1 | Extract Subnetwork | `01_extract_ppi_net.py` | Builds a subnetwork from query proteins |
| 2 | Detect Modules | `02_submodule_detection.py` | Detects network communities using Louvain clustering |
| 3 | Hub Analysis | `03_hub_analysis.py` | Identifies intra- and inter-modular hub proteins |
| 4 | GO Enrichment | `04_go_enrichment_analysis.py` | Performs functional enrichment of module protein sets |

The workflow is defined in **`main.nf`**.

---

# Repository Structure

```

PPI-network-analysis-pipeline/
│
├── main.nf
├── nextflow.config
├── Dockerfile
│
├── bin/                      # Python scripts used in pipeline
│   ├── 01_extract_ppi_net.py
│   ├── 02_submodule_detection.py
│   ├── 03_hub_analysis.py
│   └── 04_go_enrichment_analysis.py
│
├── data/                     # Example input files
├── lib/   
├── tests/               
├── results/                  # Output directory
└── README.md

````

---

# Requirements

- **Nextflow** ≥ 22
- **Docker** (recommended)
- Linux or macOS environment

The Docker container installs required Python dependencies:

- networkx
- pandas
- numpy
- scipy
- openpyxl
- gprofiler-official
- psutil

---

# Installation

Clone the repository:

```bash
git clone https://github.com/IshaniJayasekara/PPI-network-analysis-pipeline.git
cd PPI-network-analysis-pipeline
````

Build the Docker image:

```bash
docker build -t ppi-network-analysis docker/
```

---

# Inputs

The pipeline requires two input files.

## Global PPI Network

A **GraphML file** containing the global interaction network.

Example:

```
data/human_PPI_v12.0_score400_preferred.graphml
```

---

## Query Proteins

A **plain text file** with one protein identifier per line.

Example:

```
TP53
AKT1
EGFR
MYC
```

Protein identifiers must match those used in the network file.

---

# Running the Pipeline

Run the pipeline using default parameters:

```bash
nextflow run main.nf
```

Run with custom parameters:

```bash
nextflow run main.nf \
  --network /path/to/network.graphml \
  --proteins /path/to/query_proteins.txt \
  --outdir results_custom \
  --louvain_resolution 1.0
```

---

# Parameters

| Parameter              | Description                                 | Default                                           |
| ---------------------- | ------------------------------------------- | ------------------------------------------------- |
| `--network`            | Global PPI network (GraphML)                | `data/human_PPI_v12.0_score400_preferred.graphml` |
| `--proteins`           | Query protein list                          | `data/query_proteins.txt`                         |
| `--outdir`             | Output directory                            | `results`                                         |
| `--louvain_resolution` | Resolution parameter for Louvain clustering | `1.0`                                             |

Higher resolution values generally produce **more but smaller modules**.

---

# Output

Results are written to the directory specified by `--outdir`.

## Subnetwork

```
01_subnetwork/
```

Outputs:

* `subnetwork.graphml`
* `missing_proteins.txt`

---

## Module Detection

```
02_modules/
```

Outputs:

* `modularized.graphml`
* `modules_list.xlsx`

---

## Hub Analysis

```
03_hubs/
```

Outputs:

* `network_with_hubs.graphml`
* `intra_modular_hubs.xlsx`
* `inter_modular_hubs.xlsx`

---

## GO Enrichment

```
04_enrichment/
```

Outputs:

* `enrichment_results_filtered.xlsx`

---

# Reproducibility

The pipeline uses **Docker containers** to ensure reproducible execution across different computing environments.

Nextflow manages workflow execution, enabling reproducible runs on:

* local machines
* HPC clusters
* cloud environments

---

# Author

**Ishani Jayasekara**
BSc (Hons) Bioinformatics
University of Colombo

---


