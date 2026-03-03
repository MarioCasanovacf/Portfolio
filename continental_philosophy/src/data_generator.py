import os
import pandas as pd
import numpy as np

# Determinismo histórico
np.random.seed(42)

def generate_hegelian_corpus(output_dir="../data"):
    """
    Genera un corpus sintético de texto plano representando la fenomenología
    hegeliana y el movimiento de la 'Aufhebung' (sublimación dialéctica).
    """
    os.makedirs(output_dir, exist_ok=True)
    corpus_path = os.path.join(output_dir, "hegel_phenomenology_corpus.txt")
    
    # Texto sintético altamente denso para poner a prueba la centralidad nodal
    texto = (
        "El Ser en sí mismo es puro e indeterminado, pero en su inmediatez inevitablemente "
        "transiciona hacia la Nada. Esta inmediatez del Ser y la Nada encuentra su verdad en "
        "el Devenir. "
        "De igual manera, el Amo arriesga su vida por el reconocimiento, estableciendo el "
        "paradigma del Dominio. El Esclavo rehuye la muerte y abraza el Trabajo, transformando "
        "la Naturaleza objetiva. El Trabajo del Esclavo trasciende el Dominio estancado del Amo. "
        "A través de la Aufhebung, el Trabajo y el Dominio convergen en el Autoconocimiento absoluto. "
        "La Razón supera al Autoconocimiento subjetivo para alcanzar el Espíritu."
    )
    
    with open(corpus_path, "w", encoding="utf-8") as f:
        f.write(texto)
        
    print(f"[+] Corpus Hegeliano generado exitosamente en: {corpus_path}")

def generate_kojeve_agents(output_dir="../data", n_agents=1000):
    """
    Genera una población estocástica inicial de agentes históricos para la
    simulación de Teoría de Juegos Evolutiva de Kojève.
    Asigna distribuciones de 'Deseo de Reconocimiento' y 'Miedo a la Muerte'.
    """
    os.makedirs(output_dir, exist_ok=True)
    agents_path = os.path.join(output_dir, "kojeve_initial_agents.csv")
    
    # Distribución Beta para simular poblaciones asimétricas
    # La mayoría tiene miedo a la muerte (beta(5, 2))
    miedo_muerte = np.random.beta(5, 2, n_agents)
    
    # Deseo de reconocimiento distribuido inverso/normal (alfa>beta)
    deseo_reconocimiento = np.random.beta(2, 5, n_agents) 
    
    df_agents = pd.DataFrame({
        'Agent_ID': np.arange(n_agents),
        'Miedo_a_la_Muerte': miedo_muerte,
        'Deseo_de_Reconocimiento': deseo_reconocimiento
    })
    
    df_agents.to_csv(agents_path, index=False)
    print(f"[+] Entorno Multi-Agente de Kojève ({n_agents} agentes) inicializado en: {agents_path}")

if __name__ == "__main__":
    print("[*] Generando estructuras de datos pre-analíticas...")
    generate_hegelian_corpus()
    generate_kojeve_agents()
