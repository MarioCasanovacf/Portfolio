import os
import urllib.request


def fetch_pdb(pdb_id, output_dir="data"):
    """
    Download an atomic-coordinate file (.pdb) directly from the
    Protein Data Bank (RCSB PDB) for in-silico structural analysis.
    """
    pdb_id = pdb_id.lower()
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pdb_id}.pdb")

    print(f"[*] Requesting structural coordinates for {pdb_id.upper()} from PDB...")
    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"[+] PDB file downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"[-] Error downloading {pdb_id}: {e}")
        return None


if __name__ == "__main__":
    # 1UBQ is ubiquitin: a small, well-standardized protein, mathematically
    # ideal for demonstrating geometric distance analysis without overloading RAM.
    fetch_pdb("1ubq")
