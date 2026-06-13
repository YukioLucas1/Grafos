import requests
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from itertools import combinations
from pathlib import Path

# =====================================
# CONFIGURAÇÕES
# =====================================

ANO_INICIAL = 2016
ANO_FINAL = 2026

BASE_URL = "https://api.jolpi.ca/ergast/f1"

# Pasta de saída
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================================
# GRAFO
# =====================================

G = nx.Graph()

# Histórico de companheiros
companheiros = defaultdict(list)

# =====================================
# FUNÇÕES
# =====================================

def pegar_corridas(ano):
    """
    Retorna todas as corridas do ano.
    """
    url = f"{BASE_URL}/{ano}.json"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        return (
            data["MRData"]
            ["RaceTable"]
            ["Races"]
        )

    except Exception as e:
        print(f"[ERRO] Temporada {ano}: {e}")
        return []


def pegar_resultados_gp(ano, rodada):
    """
    Obtém os resultados de um GP.
    Apenas pilotos que realmente correram.
    """
    url = f"{BASE_URL}/{ano}/{rodada}/results.json"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        races = (
            data["MRData"]
            ["RaceTable"]
            ["Races"]
        )

        if not races:
            return []

        return races[0]["Results"]

    except Exception:
        return []


# =====================================
# MONTAR GRAFO
# =====================================

for ano in range(ANO_INICIAL, ANO_FINAL + 1):

    print(f"\n========== {ano} ==========")

    corridas = pegar_corridas(ano)

    if not corridas:
        print("Sem dados.")
        continue

    for corrida in corridas:

        rodada = corrida["round"]
        nome_gp = corrida["raceName"]

        print(f"GP: {nome_gp}")

        resultados = pegar_resultados_gp(
            ano,
            rodada
        )

        # Agrupar pilotos por equipe
        equipes = defaultdict(list)

        for resultado in resultados:

            piloto = resultado["Driver"]

            nome_piloto = (
                piloto["givenName"]
                + " "
                + piloto["familyName"]
            )

            equipe = (
                resultado["Constructor"]["name"]
            )

            equipes[equipe].append(
                nome_piloto
            )

            # Adiciona nó
            G.add_node(nome_piloto)

        # Criar conexões reais
        for equipe, pilotos in equipes.items():

            if len(pilotos) >= 2:

                for p1, p2 in combinations(
                    pilotos, 2
                ):

                    # Sem peso
                    G.add_edge(p1, p2)

                    companheiros[
                        tuple(sorted((p1, p2)))
                    ].append(
                        f"{ano} - {nome_gp}"
                    )

                    print(
                        f"  {p1} ↔ {p2}"
                    )

# =====================================
# ESTATÍSTICAS
# =====================================

print("\n========== ESTATÍSTICAS ==========")

print(
    f"Pilotos: "
    f"{G.number_of_nodes()}"
)

print(
    f"Conexões: "
    f"{G.number_of_edges()}"
)

mais_conectado = max(
    G.degree,
    key=lambda x: x[1]
)

print(
    "\nPiloto com mais companheiros:"
)

print(
    f"{mais_conectado[0]}"
)

print(
    f"Companheiros: "
    f"{mais_conectado[1]}"
)

# =====================================
# GERAR IMAGEM DO GRAFO
# =====================================

print("\nGerando imagem...")

plt.figure(figsize=(22, 16))

pos = nx.spring_layout(
    G,
    seed=42,
    k=0.55
)

# tamanho proporcional ao grau
node_sizes = [
    250 + 100 * G.degree(node)
    for node in G.nodes()
]

nx.draw_networkx_nodes(
    G,
    pos,
    node_size=node_sizes,
    alpha=0.9
)

nx.draw_networkx_edges(
    G,
    pos,
    alpha=0.30
)

nx.draw_networkx_labels(
    G,
    pos,
    font_size=8
)

plt.title(
    "F1 Team Teammate Network (2016–2026)",
    fontsize=18
)

plt.axis("off")

png_path = OUTPUT_DIR / "grafo_f1.png"

plt.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Imagem salva: {png_path}")

# =====================================
# EXPORTAR PARA GEPHI
# =====================================

gexf_path = OUTPUT_DIR / "grafo_f1_2016_2026.gexf"

nx.write_gexf(
    G,
    gexf_path
)

print(
    f"\nArquivo Gephi salvo:"
)

print(gexf_path)

print("\nFinalizado.")