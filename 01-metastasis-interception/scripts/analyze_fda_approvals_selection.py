"""
Analyze FDA approvals to verify our 11-gene selection was complete and non-circular.

This addresses reviewer concern: "Did you test all approvals or just the ones that scored high?"
"""

# FDA approvals data from web agent
q1_2024 = [
    {"drug": "Amivantamab-vmjw", "target": "EGFR", "approval_date": "2024-01", "indication": "NSCLC EGFR exon 20 insertion"},
    {"drug": "Lifileucel (Amtagvi)", "target": "TIL_THERAPY", "approval_date": "2024-02", "indication": "Melanoma - first TIL therapy"},
    {"drug": "Erdafitinib", "target": "FGFR3", "approval_date": "2024-01-18", "indication": "Metastatic urothelial carcinoma"},
    {"drug": "Mirvetuximab soravtansine", "target": "FOLR1", "approval_date": "2024-03", "indication": "Platinum-resistant ovarian cancer"},
    {"drug": "Tepotinib", "target": "MET", "approval_date": "2024-02-15", "indication": "Metastatic NSCLC MET exon 14"},
    {"drug": "Nogapendekin alfa", "target": "IL15", "approval_date": "2024-04-22", "indication": "Bladder cancer"},
    {"drug": "Pegulicianine (Lumisight)", "target": "IMAGING", "approval_date": "2024-04-17", "indication": "Optical imaging agent"},
]

q2_2024 = [
    {"drug": "Tarlatamab (Imdelltra)", "target": "DLL3", "approval_date": "2024-05-16", "indication": "Extensive-stage SCLC"},
    {"drug": "Imetelstat (Rytelo)", "target": "TERT", "approval_date": "2024-06-06", "indication": "Myelodysplastic syndromes"},
    {"drug": "Vorasidenib (Voranigo)", "target": "IDH1/IDH2", "approval_date": "2024-08-06", "indication": "IDH-mutant glioma"},
    {"drug": "Lazertinib (Lazcluze)", "target": "EGFR", "approval_date": "2024-08-19", "indication": "EGFR-mutant NSCLC"},
]

q3_2024 = [
    {"drug": "Selpercatinib", "target": "RET", "approval_date": "2024-09-27", "indication": "RET-mutant medullary thyroid cancer"},
    {"drug": "Durvalumab", "target": "PD_L1", "approval_date": "2024-08", "indication": "LS-SCLC, endometrial cancer"},
    {"drug": "Pembrolizumab", "target": "PD_1", "approval_date": "2024-08", "indication": "Endometrial cancer combinations"},
]

q4_2024 = [
    {"drug": "Zanidatamab (Ziihera)", "target": "ERBB2", "approval_date": "2024-11-20", "indication": "HER2+ biliary tract cancer"},
    {"drug": "Revumenib (Revuforj)", "target": "KMT2A", "approval_date": "2024-11-15", "indication": "Relapsed/refractory acute leukemia"},
    {"drug": "Zenocutuzumab (BIZENGRI)", "target": "NRG1", "approval_date": "2024-12-03", "indication": "NRG1 fusion+ NSCLC/pancreatic"},
    {"drug": "Ensartinib", "target": "ALK", "approval_date": "2024-12-18", "indication": "ALK+ metastatic NSCLC"},
    {"drug": "Inavolisib", "target": "PIK3CA", "approval_date": "2024-10", "indication": "PIK3CA-mutant metastatic breast cancer"},
    {"drug": "Cosibelimab (Unloxcyt)", "target": "PD_L1", "approval_date": "2024-10", "indication": "Metastatic cutaneous SCC"},
]

q1_q2_2025 = [
    {"drug": "Sotorasib + panitumumab", "target": "KRAS_G12C", "approval_date": "2025-Q1", "indication": "KRAS G12C-mutant CRC"},
    {"drug": "Zanubrutinib tablets", "target": "BTK", "approval_date": "2025-Q1", "indication": "CLL/SLL/WM/MCL/MZL/FL"},
    {"drug": "Belzutifan", "target": "HIF2A", "approval_date": "2025-Q2", "indication": "Pheochromocytoma/paraganglioma"},
    {"drug": "Lisocabtagene maraleucel", "target": "CAR_T_CD19", "approval_date": "2024-12", "indication": "Marginal zone lymphoma"},
]

all_approvals = q1_2024 + q2_2024 + q3_2024 + q4_2024 + q1_q2_2025

# Our 11 selected genes
our_11_genes = {
    "RET", "IDH1", "IDH2", "PIK3CA", "ERBB2", "KMT2A", 
    "FGFR3", "NRG1", "FOLR1", "ESR1", "FGFR2"
}

# Training set genes (38 genes from metastasis_interception_rules.json)
training_set_genes = {
    "BRAF", "KRAS", "NRAS", "MAP2K1", "MAP2K2", "RAF1",  # MAPK
    "BRCA1", "BRCA2", "ATM", "CHEK2", "PALB2", "TP",  # HRR
    "SNAI1", "SNAI2", "TWIST1", "ZEB1", "ZEB2", "CDH1",  # EMT_TF
    "MMP2", "MMP9", "MMP14", "CTSD",  # MMP
    "BCL2", "MCL1", "BIRC5",  # CIRCULATION
    "ICAM1", "VCAM1", "SELE", "ITGA4",  # ADHESION
    "CXCR4", "CXCL12", "CCR7", "ITGB1",  # HOMING
    "VEGFA", "VEGFR1", "VEGFR2", "FGF2", "PDGFRB", "HIF1A", "ANGPT2",  # ANGIO
    "PTGS2", "IL6", "TGFB1", "POSTN", "MET"  # COLONIZATION
}

def categorize_approvals():
    """Categorize approvals by type."""
    gene_targeted = []
    immunotherapy_no_gene = []
    car_t_til = []
    other = []
    
    for app in all_approvals:
        target = app["target"]
        if target in ["PD_L1", "PD_1", "CTLA4"]:
            immunotherapy_no_gene.append(app)
        elif target in ["CAR_T_CD19", "TIL_THERAPY"]:
            car_t_til.append(app)
        elif target in ["IMAGING", "IL15"]:
            other.append(app)
        else:
            gene_targeted.append(app)
    
    return gene_targeted, immunotherapy_no_gene, car_t_til, other

def extract_gene_targets(gene_targeted):
    """Extract unique gene targets from gene-targeted approvals."""
    gene_targets = {}
    for app in gene_targeted:
        target = app["target"]
        if "/" in target:  # dual targets like IDH1/IDH2
            for t in target.split("/"):
                if t not in gene_targets:
                    gene_targets[t] = []
                gene_targets[t].append(app)
        else:
            if target not in gene_targets:
                gene_targets[target] = []
            gene_targets[target].append(app)
    return gene_targets

def analyze_selection():
    """Analyze our 11-gene selection against all FDA approvals."""
    gene_targeted, immunotherapy_no_gene, car_t_til, other = categorize_approvals()
    gene_targets = extract_gene_targets(gene_targeted)
    
    print("=" * 80)
    print("FDA ONCOLOGY APPROVAL ANALYSIS (2024-2025)")
    print("=" * 80)
    print(f"\nTotal approvals identified: {len(all_approvals)}")
    print(f" - Gene-targeted therapies: {len(gene_targeted)}")
    print(f" - Immunotherapy (no specific gene): {len(immunotherapy_no_gene)}")
    print(f" - CAR-T/TIL therapies: {len(car_t_til)}")
    print(f" - Other (imaging, cytokines): {len(other)}")
    
    print("\n" + "=" * 80)
    print("GENE-TARGETED THERAPIES ANALYSIS")
    print("=" * 80)
    print(f"\nUnique gene targets: {len(gene_targets)}")
    
    # Categorize each gene target
    in_our_11 = []
    in_training_set = []
    not_selected = []
    excluded_categories = []
    
    for gene, apps in sorted(gene_targets.items()):
        is_metastatic = any("metastatic" in app["indication"].lower() or 
                           "metastasis" in app["indication"].lower() 
                           for app in apps)
        
        if gene in our_11_genes:
            in_our_11.append((gene, apps, is_metastatic))
        elif gene in training_set_genes:
            in_training_set.append((gene, apps, is_metastatic))
        elif not is_metastatic:
            excluded_categories.append((gene, apps, "Non-metastatic indication"))
        else:
            not_selected.append((gene, apps, is_metastatic))
    
    print("\n" + "=" * 80)
    print("OUR 11 SELECTED GENES")
    print("=" * 80)
    print(f"\nGenes in our prospective validation (n={len(in_our_11)}):")
    for gene, apps, is_met in in_our_11:
        print(f"\n  ✅ {gene}:")
        for app in apps:
            metastatic_marker = " [METASTATIC]" if is_met else ""
            print(f"     - {app['drug']} ({app['approval_date']}): {app['indication']}{metastatic_marker}")
    
    print("\n" + "=" * 80)
    print("EXCLUDED: IN TRAINING SET")
    print("=" * 80)
    print(f"\nGenes already in 38-gene training set (n={len(in_training_set)}):")
    for gene, apps, is_met in in_training_set:
        print(f"\n  ⚠️  {gene} (EXCLUDED - in training set):")
        for app in apps:
            metastatic_marker = " [METASTATIC]" if is_met else ""
            print(f"     - {app['drug']} ({app['approval_date']}): {app['indication']}{metastatic_marker}")
    
    print("\n" + "=" * 80)
    print("EXCLUDED: NON-METASTATIC INDICATIONS")
    print("=" * 80)
    print(f"\nGenes with non-metastatic indications (n={len(excluded_categories)}):")
    for gene, apps, reason in excluded_categories:
        print(f"\n  ⚠️  {gene} (EXCLUDED - {reason}):")
        for app in apps:
            print(f"     - {app['drug']} ({app['approval_date']}): {app['indication']}")
    
    print("\n" + "=" * 80)
    print("NOT SELECTED: METASTATIC BUT NOT IN OUR 11")
    print("=" * 80)
    print(f"\nGenes with metastatic indications but not selected (n={len(not_selected)}):")
    for gene, apps, is_met in not_selected:
        print(f"\n  ❓ {gene} (NOT SELECTED):")
        for app in apps:
            metastatic_marker = " [METASTATIC]" if is_met else ""
            print(f"     - {app['drug']} ({app['approval_date']}): {app['indication']}{metastatic_marker}")
        print(f"     ⚠️  Why not selected? Need to verify exclusion criteria.")
    
    print("\n" + "=" * 80)
    print("SELECTION SUMMARY")
    print("=" * 80)
    print(f"\nTotal gene-targeted approvals: {len(gene_targeted)}")
    print(f"  ✅ Selected for validation: {len(in_our_11)}")
    print(f"  ⚠️  Excluded (in training set): {len(in_training_set)}")
    print(f"  ⚠️  Excluded (non-metastatic): {len(excluded_categories)}")
    print(f"  ❓ Not selected (metastatic): {len(not_selected)}")
    
    if len(not_selected) > 0:
        print(f"\n⚠️  WARNING: {len(not_selected)} metastatic gene targets were not selected.")
        print("   Need to verify why these were excluded.")
        print("   Possible reasons:")
        print("   - Not FDA-approved (only clinical trials?)")
        print("   - Approval date outside 2023-2025 window?")
        print("   - Different selection criteria used?")
    
    return {
        "total_approvals": len(all_approvals),
        "gene_targeted": len(gene_targeted),
        "in_our_11": len(in_our_11),
        "in_training_set": len(in_training_set),
        "excluded_non_metastatic": len(excluded_categories),
        "not_selected_metastatic": len(not_selected),
        "not_selected_genes": [gene for gene, _, _ in not_selected]
    }

if __name__ == "__main__":
    results = analyze_selection()
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
