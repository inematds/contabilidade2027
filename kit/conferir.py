#!/usr/bin/env python3
"""Confere se todo número do relatório final existe no dados.json.

A IA reescreve o relatório-base em linguagem mais simples. Este script garante
que ela não inventou nem arredondou número: cada valor em R$, cada % e cada
número com vírgula decimal tem que estar no dados.json.

Uso:  python3 kit/conferir.py <relatorio.md> <dados.json>
Sai com 0 se tudo confere, 1 se achar número sem origem (e lista quais).
"""
import json
import re
import sys

PADRAO = re.compile(r"-?R\$\s?-?\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d+)?%|\d+,\d+")


APROX = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mil|milhão|milhões|bilhão|bilhões)\b", re.I)
UNIDADE = re.compile(r"\b(\d+)\s*(?:dias|meses)\b")


def normal(t):
    return t.replace(" ", "").replace("-R$", "R$").replace("R$-", "R$")


NOMES = ("item", "fornecedor", "cliente", "categoria", "nome", "atividade")


def nomes(dados):
    """Nomes de item, fornecedor e categoria: podem ter número ("Fio 2,5 mm") e não são valores calculados."""
    achados = set()

    def anda(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in NOMES and isinstance(v, str):
                    achados.add(v)
                else:
                    anda(v)
        elif isinstance(x, list):
            for v in x:
                anda(v)
    anda(dados)
    return sorted(achados, key=len, reverse=True)


def conferir(texto, dados):
    for nome in nomes(dados):
        texto = texto.replace(nome, " ")
    validos = set()
    for item in dados["numeros"].values():
        validos.add(normal(item["texto"]))
        validos.add(normal(item["texto"]).lstrip("-"))  # o padrão de busca não pega o sinal de menos
    inteiros = {item["texto"] for item in dados["numeros"].values() if isinstance(item["valor"], int)}
    sem_origem = []
    for m in PADRAO.finditer(texto):
        if normal(m.group()) not in validos:
            sem_origem.append(m.group())
    # arredondamento por extenso ("62 mil", "1,2 milhão") é proibido: copie o valor exato
    for m in APROX.finditer(texto):
        sem_origem.append(m.group())
    # quantidade com unidade ("20 dias", "6 meses") tem que existir no dados.json
    for m in UNIDADE.finditer(texto):
        if m.group(1) not in inteiros and int(m.group(1)) > 1:
            sem_origem.append(m.group())
    return sem_origem


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    texto = open(argv[0], encoding="utf-8").read()
    dados = json.load(open(argv[1], encoding="utf-8"))
    sem = conferir(texto, dados)
    if sem:
        print("NÚMERO SEM ORIGEM no relatório (não está no dados.json):")
        for s in sorted(set(sem)):
            print(f"  {s}")
        return 1
    print("ok: todos os números do relatório estão no dados.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
