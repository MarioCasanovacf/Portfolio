import os
import urllib.request

def fetch_pdb(pdb_id, output_dir="../data"):
    """
    Descarga archivo de coordenadas atómicas (.pdb) para el análisis
    de ángulos de torsión (Dihedral Ramachandran Plot) desde cero.
    """
    pdb_id = pdb_id.lower()
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pdb_id}.pdb")
    
    print(f"[*] Solicitando coordenadas estructurales para {pdb_id.upper()} desde PDB...")
    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"[+] Archivo PDB descargado con éxito para Ramachandran Plotting: {file_path}")
        return file_path
    except Exception as e:
        print(f"[-] Error descargando {pdb_id}: {e}")
        return None

if __name__ == "__main__":
    # 1BNA es un dodecámero de ADN clásico, pero para Ramachandran
    # usamos polipéptidos. Volveremos a usar 1UBQ, o 1AHO (Neurotoxina pequeña)
    # para ilustrar bien las láminas Beta y Hélices Alfa.
    fetch_pdb("1aho")
