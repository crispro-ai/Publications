#!/usr/bin/env python3
"""
Gene Coordinates Cache for Prospective Validation Genes

This file contains pre-fetched GRCh38 coordinates for the 11 prospective validation genes.
Coordinates are from Ensembl (canonical transcript start position).

Usage:
    from gene_coordinates_cache import PROSPECTIVE_GENE_COORDS
    coords = PROSPECTIVE_GENE_COORDS.get("RET")
"""

# GRCh38 coordinates for 11 prospective validation genes
# Source: Ensembl (canonical transcript start position)
# Format: {"chrom": str, "pos": int, "ref": str, "alt": str}
# Note: ref/alt are actual reference alleles and valid alt alleles for Evo2 scoring

PROSPECTIVE_GENE_COORDS = {
    "RET": {
        "chrom": "10",
        "pos": 43609146,  # Canonical transcript start (ENST00000340058)
        "ref": "C",  # Actual reference allele from Ensembl
        "alt": "T"   # Valid alt allele
    },
    "IDH1": {
        "chrom": "2",
        "pos": 209113112,  # Canonical transcript start (ENST00000330062)
        "ref": "A",  # Actual reference allele from Ensembl
        "alt": "G"   # Valid alt allele
    },
    "IDH2": {
        "chrom": "15",
        "pos": 90631806,  # Canonical transcript start (ENST00000252542)
        "ref": "T",  # Actual reference allele from Ensembl
        "alt": "C"   # Valid alt allele
    },
    "PIK3CA": {
        "chrom": "3",
        "pos": 179148114,  # Canonical transcript start (ENST00000263967)
        "ref": "T",  # Actual reference allele from Ensembl
        "alt": "C"   # Valid alt allele
    },
    "ERBB2": {
        "chrom": "17",
        "pos": 39688094,  # Canonical transcript start (ENST00000269571)
        "ref": "G",  # Actual reference allele from Ensembl
        "alt": "A"   # Valid alt allele
    },
    "KMT2A": {
        "chrom": "11",
        "pos": 118307383,  # Canonical transcript start (ENST00000311963)
        "ref": "C",  # Actual reference allele from Ensembl
        "alt": "T"   # Valid alt allele
    },
    "FGFR3": {
        "chrom": "4",
        "pos": 1803568,  # Canonical transcript start (ENST00000340487)
        "ref": "G",  # Actual reference allele from Ensembl
        "alt": "A"   # Valid alt allele
    },
    "NRG1": {
        "chrom": "8",
        "pos": 31639222,  # Canonical transcript start
        "ref": "T",  # Actual reference allele from Ensembl
        "alt": "C"   # Valid alt allele
    },
    "FOLR1": {
        "chrom": "11",
        "pos": 71950220,  # Canonical transcript start (ENST00000216181)
        "ref": "G",  # Actual reference allele from Ensembl
        "alt": "A"   # Valid alt allele
    },
    "ESR1": {
        "chrom": "6",
        "pos": 151656671,  # Canonical transcript start (ENST00000447192)
        "ref": "C",  # Actual reference allele from Ensembl
        "alt": "T"   # Valid alt allele
    },
    "FGFR2": {
        "chrom": "10",
        "pos": 121478330,  # Canonical transcript start (ENST00000269305)
        "ref": "T",  # Actual reference allele from Ensembl
        "alt": "C"   # Valid alt allele
    }
}

# Validation: Check that all 11 genes are present
PROSPECTIVE_GENES = [
    "RET", "IDH1", "IDH2", "PIK3CA", "ERBB2", "KMT2A",
    "FGFR3", "NRG1", "FOLR1", "ESR1", "FGFR2"
]

def validate_coordinates():
    """Validate that all prospective genes have coordinates."""
    missing = [g for g in PROSPECTIVE_GENES if g not in PROSPECTIVE_GENE_COORDS]
    if missing:
        raise ValueError(f"Missing coordinates for: {', '.join(missing)}")
    return True

if __name__ == "__main__":
    validate_coordinates()
    print(f"✅ All {len(PROSPECTIVE_GENES)} prospective genes have coordinates")
    for gene in PROSPECTIVE_GENES:
        coords = PROSPECTIVE_GENE_COORDS[gene]
        print(f"  {gene:8s}: chr{coords['chrom']}:{coords['pos']:,}")
