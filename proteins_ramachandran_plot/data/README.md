# Data

## Files

### `1aho.pdb`
Protein Data Bank file for **Scorpion Neurotoxin II** (PDB ID: 1AHO), a small scorpion protein toxin whose structure was determined ab initio. This file contains atomic coordinates used for Ramachandran plot analysis of backbone dihedral angles (phi/psi).

The file is fetched directly from [RCSB PDB](https://www.rcsb.org/structure/1AHO).

## Regeneration

To re-download the PDB file, run from the project root:

```bash
python src/data_fetcher.py
```

This fetches the file from `https://files.rcsb.org/download/1aho.pdb`. An internet connection is required.
