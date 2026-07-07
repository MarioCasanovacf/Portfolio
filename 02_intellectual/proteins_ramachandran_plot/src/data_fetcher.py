import os
import urllib.request


def fetch_pdb(pdb_id, output_dir="data"):
    """
    Download an atomic-coordinate file (.pdb) for from-scratch
    dihedral-angle analysis (Ramachandran plot).
    """
    pdb_id = pdb_id.lower()
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pdb_id}.pdb")

    print(f"[*] Requesting structural coordinates for {pdb_id.upper()} from PDB...")
    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"[+] PDB file downloaded successfully for Ramachandran plotting: {file_path}")
        return file_path
    except Exception as e:
        print(f"[-] Error downloading {pdb_id}: {e}")
        return None


if __name__ == "__main__":
    # 1BNA is the classic DNA dodecamer, but for Ramachandran plots we need
    # polypeptides. We use 1UBQ or 1AHO (a small neurotoxin) to clearly
    # illustrate beta sheets and alpha helices.
    fetch_pdb("1aho")
