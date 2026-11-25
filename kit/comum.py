"""Funções comuns dos kits do contabilidade2027 (formatação pt-BR, leitura de CSV, números com origem)."""
import csv
import json
from pathlib import Path


class ErroDados(Exception):
    pass


# ---------- formatação pt-BR ----------
def brl(v):
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-R$ " if v < 0 else "R$ ") + s


def pct(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def num(texto, arquivo, linha, campo):
    t = str(texto).strip().replace("R$", "").replace(" ", "")
    if t == "":
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        raise ErroDados(f"{arquivo} linha {linha}: '{campo}' não é número ('{texto}')")


def ler_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        amostra = f.read(2048)
        f.seek(0)
        sep = ";" if amostra.count(";") >= amostra.count(",") else ","
        return list(csv.DictReader(f, delimiter=sep))


# ---------- registro de números com origem ----------
class Numeros:
    def __init__(self):
        self.itens = {}

    def add(self, chave, valor, tipo, origem):
        texto = brl(valor) if tipo == "brl" else pct(valor) if tipo == "pct" else str(valor)
        self.itens[chave] = {"valor": round(valor, 4) if isinstance(valor, float) else valor,
                             "texto": texto, "origem": origem}
        return texto




def carregar_empresa(pasta, padroes):
    f = Path(pasta) / "empresa.json"
    if not f.exists():
        raise ErroDados(f"falta {f}")
    emp = {**padroes, **json.loads(f.read_text(encoding="utf-8"))}
    if emp.get("regime") not in ("simples", "presumido", "real"):
        raise ErroDados("empresa.json: 'regime' deve ser simples, presumido ou real")
    return emp


def gravar(saida, dados, nome_md, texto_md, extras=None):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    (saida / nome_md).write_text(texto_md, encoding="utf-8")
    for nome, conteudo in (extras or {}).items():
        (saida / nome).write_text(conteudo, encoding="utf-8")


# ---------- preço e margem por item (mesma conta no Diagnóstico e no Preço certo) ----------
# Método do markup: o preço cobre o custo direto, a comissão/taxa (var), os outros impostos sobre a
# venda (out: ISS/ICMS, IR/CSLL do Presumido, ou o DAS no Simples), o rateio das despesas fixas (fix),
# o imposto sobre o consumo (imp_preco: % do preço hoje; t: CBS+IBS de 2027 com crédito sobre ccred)
# e o lucro. Todas as frações são do preço (0,10 = 10%).

def margem_item(P, c, var=0.0, out=0.0, fix=0.0, imp_preco=0.0, t=0.0, ccred=0.0):
    """Lucro por venda ÷ preço, depois de custo, comissão/taxa, impostos e rateio das despesas fixas."""
    imposto = P * imp_preco + (P - ccred) * t
    return (P - c - P * (var + out + fix) - imposto) / P


def preco_para_margem(m, c, var=0.0, out=0.0, fix=0.0, imp_preco=0.0, t=0.0, ccred=0.0):
    """Preço que dá a margem m. None quando os percentuais somam 100% ou mais (não há preço que feche)."""
    den = 1 - var - out - fix - imp_preco - t - m
    return (c - ccred * t) / den if den > 0 else None


def fracoes_estrutura(empresa, receita, outros_impostos, despesas_operacionais):
    """Frações do preço para os outros impostos sobre a venda e o rateio das despesas fixas.
    Vêm do mensal.csv (÷ receita), ou de empresa.json (outros_impostos_pct, rateio_fixas_pct) quando informados."""
    o = empresa.get("outros_impostos_pct")
    f = empresa.get("rateio_fixas_pct")
    out = o / 100 if o is not None else (outros_impostos / receita if receita else 0.0)
    fix = f / 100 if f is not None else (despesas_operacionais / receita if receita else 0.0)
    return out, fix
