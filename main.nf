nextflow.enable.dsl=2

/*
 * -------------------------------------------------
 * PPI ANALYSIS PIPELINE
 * -------------------------------------------------
 */

// 1. Default Pipeline Parameters
params.network = "$projectDir/data/human_PPI_v12.0_score400_preferred.graphml"
params.proteins = "$projectDir/data/query_proteins.txt"
params.outdir = "results"
params.louvain_resolution = 1.0

log.info """
PPI PIPELINE EXECUTION
===================================
Global Network : ${params.network}
Query Proteins : ${params.proteins}
Output Dir     : ${params.outdir}
Resolution     : ${params.louvain_resolution}
-----------------------------------
"""

/*
 * PROCESS 1: Extract Subnetwork
 * Script: 01_extract_ppi_net.py
 */
process EXTRACT_SUBNETWORK {
    publishDir "${params.outdir}/01_subnetwork", mode: 'copy'

    input:
    path protein_list
    path global_net

    output:
    path "subnetwork.graphml", emit: graph
    path "missing_proteins.txt", optional: true

    script:
    """
    01_extract_ppi_net.py ${protein_list} ${global_net} subnetwork.graphml
    """
}

/*
 * PROCESS 2: Detect Modules
 * Script: 02_submodule_detection.py 
 */
process DETECT_MODULES {
    publishDir "${params.outdir}/02_modules", mode: 'copy'

    input:
    path subnetwork
    val res

    output:
    path "modularized.graphml", emit: graph
    path "modules_list.xlsx", emit: excel

    script:
    """
    02_submodule_detection.py ${subnetwork} modularized.graphml modules_list.xlsx ${res}
    """
}

/*
 * PROCESS 3: Analyze Hubs
 * Script: 03_hub_analysis.py
 */
process ANALYZE_HUBS {
    publishDir "${params.outdir}/03_hubs", mode: 'copy'

    input:
    path modularized_graph

    output:
    path "network_with_hubs.graphml", emit: graph
    path "intra_modular_hubs.xlsx"
    path "inter_modular_hubs.xlsx"

    script:
    """
    03_hub_analysis.py ${modularized_graph} network_with_hubs.graphml
    """
}

/*
 * PROCESS 4: GO Enrichment
 * Script: 04_go_enrichment_analysis.py
 */
process GO_ENRICHMENT {
    publishDir "${params.outdir}/04_enrichment", mode: 'copy'

    input:
    path modules_xlsx

    output:
    path "enrichment_results_filtered.xlsx"

    script:
    """
    04_go_enrichment_analysis.py ${modules_xlsx} enrichment_results_filtered.xlsx
    """
}

/*
 * WORKFLOW DEFINITION
 * Connecting the steps together
 */
workflow {
    // Step 1
    EXTRACT_SUBNETWORK(params.proteins, params.network)

    // Step 2 (Takes output from Step 1)
    DETECT_MODULES(EXTRACT_SUBNETWORK.out.graph, params.louvain_resolution)

    // Step 3 (Takes output from Step 2)
    ANALYZE_HUBS(DETECT_MODULES.out.graph)

    // Step 4 (Takes Excel output from Step 2)
    GO_ENRICHMENT(DETECT_MODULES.out.excel)
}