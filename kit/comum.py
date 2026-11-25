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
