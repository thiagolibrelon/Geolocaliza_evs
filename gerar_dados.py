"""
gerar_dados.py
==============
Gera os dois blocos de dados para colar no index.html:

  1. Array `municipios` — todos os 5.570 municípios brasileiros
  2. Paths SVG dos 27 estados — via API oficial IBGE v3

Requisito: Python 3.7+ (tkinter vem incluso)
"""

import csv
import json
import re
import time
import urllib.request
import io
from tkinter import Tk, filedialog
from pathlib import Path

# ── Mapeamento código UF (IBGE) → sigla ──────────────────────────────────────
UF_CODIGOS = {
    11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA',
    16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE',
    24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE',
    29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
    41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT',
    52: 'GO', 53: 'DF',
}

UFS = list(UF_CODIGOS.values())   # 27 siglas


def escolher_pasta_saida():
    """Abre diálogo para selecionar pasta de saída."""
    root = Tk()
    root.withdraw()  # Esconde a janela principal
    root.attributes('-topmost', True)  # Traz para frente

    pasta = filedialog.askdirectory(
        title="Selecione a pasta para salvar os arquivos gerados",
        initialdir=Path.home()  # Começa na pasta do usuário
    )
    root.destroy()

    if not pasta:
        print("❌ Nenhuma pasta selecionada. Operação cancelada.")
        exit(1)

    return Path(pasta)


def baixar_municipios():
    """Baixa o CSV do kelvins e converte para array JS."""
    url = (
        'https://raw.githubusercontent.com/kelvins/'
        'municipios-brasileiros/main/csv/municipios.csv'
    )
    print('  Baixando municípios...', end=' ', flush=True)
    with urllib.request.urlopen(url) as resp:
        conteudo = resp.read().decode('utf-8')
    print('OK')

    linhas = csv.DictReader(io.StringIO(conteudo))
    entradas = []
    for row in linhas:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
        except (ValueError, KeyError):
            continue

        cod_uf = int(row['codigo_uf'])
        uf = UF_CODIGOS.get(cod_uf, '??')
        nome = row['nome'].strip().strip('"')

        entradas.append(
            f'  {{cidade:{json.dumps(nome, ensure_ascii=False)},'
            f'uf:"{uf}",'
            f'latitude:{lat},'
            f'longitude:{lon}}}'
        )

    print(f'  {len(entradas)} municípios processados.')
    return '// COLE ESTE BLOCO no lugar de `const municipios = [...]` no index.html\n' \
           'const municipios = [\n' + ',\n'.join(entradas) + '\n];'


def baixar_estados_svg():
    """Baixa os SVGs e extrai os paths."""
    base_url = (
        'https://servicodados.ibge.gov.br/api/v3/malhas/estados/'
        '{uf}?formato=image/svg%2Bxml&qualidade=minima'
    )
    paths = {}
    total = len(UFS)

    for i, uf in enumerate(UFS, 1):
        url = base_url.format(uf=uf)
        print(f'  [{i:02d}/{total}] {uf}...', end=' ', flush=True)
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                svg = resp.read().decode('utf-8')

            match = re.search(r'<path[^>]+\bd="([^"]+)"', svg)
            if match:
                paths[uf] = match.group(1)
                print('OK')
            else:
                print('sem path encontrado')

            time.sleep(0.3)

        except Exception as e:
            print(f'ERRO: {e}')

    return paths


def gerar_js_estados(paths_por_uf):
    """Gera o bloco JS dos estados."""
    linhas = [
        '// COLE ESTE BLOCO logo após `const municipios = [...]` no index.html',
        '// Cada entrada: { uf, path } — path em unidades IBGE',
        'const estadosSvgPaths = {'
    ]
    for uf, path in sorted(paths_por_uf.items()):
        linhas.append(f'  {uf}: "{path}",')
    linhas.append('};')
    return '\n'.join(linhas)


def main():
    print('\n=== Gerando dados para index.html ===\n')

    # Seleção da pasta
    print("📁 Abrindo seletor de pasta...")
    pasta_saida = escolher_pasta_saida()
    print(f"✅ Pasta selecionada: {pasta_saida}\n")

    # 1. Municípios
    print('[1/2] Municípios')
    js_municipios = baixar_municipios()
    caminho_mun = pasta_saida / "municipios_gerados.js"
    with open(caminho_mun, 'w', encoding='utf-8') as f:
        f.write(js_municipios)
    print(f'  → {caminho_mun.name}\n')

    # 2. Estados SVG
    print('[2/2] Paths SVG dos estados')
    paths = baixar_estados_svg()
    js_estados = gerar_js_estados(paths)
    caminho_est = pasta_saida / "estados_svg.js"
    with open(caminho_est, 'w', encoding='utf-8') as f:
        f.write(js_estados)
    print(f'  → {caminho_est.name} ({len(paths)} estados)\n')

    print('=== Concluído ===')
    print(f'\nArquivos salvos em: {pasta_saida}')


if __name__ == '__main__':
    main()