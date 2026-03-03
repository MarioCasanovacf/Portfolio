import os
import urllib.request
import gzip
import shutil

def fetch_pdb(pdb_id, output_dir="../data"):
    """
    Descarga el archivo de coordenadas atómicas (.pdb) directamente desde
    el Protein Data Bank (RCSB PDB) para su análisis estructural in silico.
    """
    pdb_id = pdb_id.lower()
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{pdb_id}.pdb")
    
    print(f"[*] Solicitando coordenadas estructurales para {pdb_id.upper()} desde PDB...")
    try:
        urllib.request.urlretrieve(url, file_path)
        print(f"[+] Archivo PDB descargado con éxito: {file_path}")
        return file_path
    except Exception as e:
        print(f"[-] Error descargando {pdb_id}: {e}")
        return None

if __name__ == "__main__":
    # 1UBQ es Ubiquitina, una proteína pequeña y estandarizada matemáticamente perfecta
    # para demostrar análisis de distancias geométricas sin sobrecargar la RAM.
    fetch_pdb("1ubq")
