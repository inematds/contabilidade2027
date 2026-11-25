#!/usr/bin/env python3
"""Preço certo na Reforma — kit aberto do INEMA (não oficial).

Para cada produto ou serviço: a margem de hoje, a margem em 2027 com a CBS/IBS (dois cenários),
o preço mínimo (margem zero), o preço-alvo (margem que a empresa quer) e o desconto máximo
que ainda mantém a margem-alvo.

Uso:  python3 kit/preco_certo.py <pasta-do-cliente> [--saida <pasta>]

Arquivos da pasta (os mesmos do Diagnóstico):
  empresa.json   obrigatório  regime, margem_alvo_pct, cenarios_cbs_pct, reducao_aliquota_pct;
                              no Simples, aliquota_simples_pct (a alíquota efetiva do DAS, do PGDAS-D)
  mensal.csv     obrigatório  dá o PIS/Cofins efetivo de hoje e a parte do custo que gera crédito
  produtos.csv   obrigatório  item;preco;custo_direto;qtd_mes  e, se tiver:
                              custo_com_credito (R$ do custo que gera crédito), comissao_pct, taxa_pct
                              (cartão, marketplace, gateway)

Gera em saida/: precos.md (a tabela explicada), precos.csv e dados.json (cada número com a origem).
Só lê e calcula. Tudo de 2027 é SIMULADO: a alíquota de referência da CBS ainda não é a definitiva.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import ErroDados, Numeros, brl, carregar_empresa, gravar, ler_csv, num, pct  # noqa: E402
import diagnostico as D  # noqa: E402  (reaproveita a leitura do mensal.csv)

VERSAO = "1.0.0"
PADROES = {**D.PADROES, "aliquota_simples_pct": None}


def carregar(pasta):
    pasta = Path(pasta)
    emp = carregar_empresa(pasta, PADROES)
    _, mensal, _, _ = D.carregar(pasta)
    f = pasta / "produtos.csv"
    if not f.exists():
        raise ErroDados(f"falta {f} (lista de produtos ou serviços com preço e custo)")
    itens = []
    for i, r in enumerate(ler_csv(f), start=2):
        for c in ("item", "preco", "custo_direto"):
            if c not in r:
                raise ErroDados(f"produtos.csv: falta a coluna '{c}'")
        it = {"item": r["item"].strip(), "_linha": i,
              "preco": num(r["preco"], "produtos.csv", i, "preco"),
              "custo": num(r["custo_direto"], "produtos.csv", i, "custo_direto"),
              "qtd": num(r.get("qtd_mes", "0"), "produtos.csv", i, "qtd_mes"),
              "comissao": num(r.get("comissao_pct", "0"), "produtos.csv", i, "comissao_pct") / 100,
              "taxa": num(r.get("taxa_pct", "0"), "produtos.csv", i, "taxa_pct") / 100,
              "custo_cred": None}
        if (r.get("custo_com_credito") or "").strip():
            it["custo_cred"] = num(r["custo_com_credito"], "produtos.csv", i, "custo_com_credito")
        if it["preco"] <= 0:
            raise ErroDados(f"produtos.csv linha {i}: preço tem que ser maior que zero")
        itens.append(it)
    if not itens:
        raise ErroDados("produtos.csv está vazio")
    if emp["regime"] == "simples" and emp.get("aliquota_simples_pct") is None:
        raise ErroDados("empresa.json: no Simples, informe aliquota_simples_pct (a alíquota efetiva do DAS, do PGDAS-D)")
    return emp, mensal, itens


def preco_para_margem(c_liq, var, t, m):
    """Preço P tal que (P − custo − P·var − (P − custo_cred)·t) / P = m, com c_liq = custo − custo_cred·t."""
    den = 1 - var - t - m
    return c_liq / den if den > 0 else None


def calcular(emp, mensal, itens):
    N = Numeros()
    receita = sum(m["receita"] for m in mensal)
    compras = sum(m["compras_com_credito"] for m in mensal)
    custo = sum(m["custo_direto"] for m in mensal)
    pis_cof = sum(m["pis_cofins_pago"] for m in mensal)
    alvo = emp["margem_alvo_pct"] / 100
    regular = emp["regime"] in ("presumido", "real")
    red = emp["reducao_aliquota_pct"] / 100
    if regular:
        imp_hoje = pis_cof / receita if receita else 0.0
        fc = min(1.0, compras / custo) if custo else 0.0
        N.add("imp_hoje_pct", imp_hoje * 100, "pct", "PIS/Cofins pagos ÷ receita (mensal.csv)")
        N.add("fator_credito_pct", fc * 100, "pct", "compras_com_credito ÷ custo_direto (mensal.csv); usado quando o item não informa custo_com_credito")
        cenarios = sorted(emp["cenarios_cbs_pct"], reverse=True)  # o maior primeiro (cenário principal)
    else:
        imp_hoje = emp["aliquota_simples_pct"] / 100
        fc = 0.0
        N.add("imp_hoje_pct", imp_hoje * 100, "pct", "alíquota efetiva do DAS (empresa.json, aliquota_simples_pct)")
        cenarios = []
    N.add("margem_alvo", alvo * 100, "pct", "empresa.json (margem_alvo_pct)")
    for a in cenarios:
        N.add(f"aliq_{str(a).replace('.', '_')}", a, "pct", "cenário de alíquota de referência (empresa.json)")

    linhas = []
    for j, it in enumerate(itens):
        P, c, var = it["preco"], it["custo"], it["comissao"] + it["taxa"]
        ccred = it["custo_cred"] if it["custo_cred"] is not None else c * fc
        k = f"p{j}"
        m_hoje = (P - c - P * var - P * imp_hoje) / P
        N.add(f"{k}_preco", P, "brl", f"produtos.csv linha {it['_linha']}")
        N.add(f"{k}_margem_hoje", m_hoje * 100, "pct", "(preço − custo − comissão/taxa − imposto de hoje) ÷ preço")
        res = {"item": it["item"], "k": k, "preco": P, "qtd": it["qtd"], "margem_hoje": m_hoje, "cen": []}
        if regular:
            for a in cenarios:
                t = a / 100 * (1 - red)
                m27 = (P - c - P * var - (P - ccred) * t) / P
                c_liq = c - ccred * t
                p0 = preco_para_margem(c_liq, var, t, 0.0)
                pa = preco_para_margem(c_liq, var, t, alvo)
                kk = f"{k}_{str(a).replace('.', '_')}"
                N.add(f"{kk}_margem", m27 * 100, "pct", f"margem em 2027 com {pct(a)}: (preço − custo − comissão/taxa − (preço − custo com crédito) × alíquota) ÷ preço")
                if p0:
                    N.add(f"{kk}_preco_min", p0, "brl", "preço com margem zero no cenário")
                if pa:
                    N.add(f"{kk}_preco_alvo", pa, "brl", f"preço que dá a margem-alvo de {pct(alvo * 100, 0)} no cenário")
                    desc = max(0.0, 1 - pa / P)
                    N.add(f"{kk}_desc_max", desc * 100, "pct", "desconto máximo sobre o preço de hoje que ainda mantém a margem-alvo")
                res["cen"].append({"aliq": a, "kk": kk, "margem": m27, "preco_min": p0, "preco_alvo": pa})
        else:
            pa = preco_para_margem(c, var, imp_hoje, alvo)
            p0 = preco_para_margem(c, var, imp_hoje, 0.0)
            if p0:
                N.add(f"{k}_preco_min", p0, "brl", "preço com margem zero (alíquota do DAS)")
            if pa:
                N.add(f"{k}_preco_alvo", pa, "brl", f"preço que dá a margem-alvo de {pct(alvo * 100, 0)} (alíquota do DAS)")
                N.add(f"{k}_desc_max", max(0.0, 1 - pa / P) * 100, "pct", "desconto máximo que ainda mantém a margem-alvo")
            res["simples"] = {"preco_min": p0, "preco_alvo": pa}
        linhas.append(res)

    # prioridades: itens abaixo da margem-alvo no cenário principal, ordenados pelo dinheiro que falta por ano
    prio = []
    abaixo = []
    for r in linhas:
        if regular:
            c0 = r["cen"][0]
            m, pa, chave_pa = c0["margem"], c0["preco_alvo"], f"{c0['kk']}_preco_alvo"
        else:
            m, pa, chave_pa = r["margem_hoje"], r["simples"]["preco_alvo"], f"{r['k']}_preco_alvo"
        if pa and m < alvo:
            falta = max(0.0, (pa - r["preco"]) * r["qtd"] * 12)
            N.add(f"{r['k']}_falta_ano", falta, "brl", "(preço-alvo − preço de hoje) × qtd_mes × 12")
            abaixo.append((falta, r, chave_pa, m))
    abaixo.sort(key=lambda x: -x[0])
    for falta, r, chave_pa, m in abaixo[:2]:
        prio.append({"texto": f"Rever o preço de {r['item']}: para a margem-alvo, ele precisa ir de {N.itens[r['k'] + '_preco']['texto']} "
                              f"para {N.itens[chave_pa]['texto']} ({N.itens[r['k'] + '_falta_ano']['texto']} por ano, na quantidade de hoje).",
                     "chave": chave_pa})
    negativos = [r for r in linhas if (r["cen"][0]["margem"] if regular else r["margem_hoje"]) < 0]
    if negativos:
        prio.append({"texto": "Parar de vender abaixo do custo: " + ", ".join(r["item"] for r in negativos) + " fica com margem negativa.",
                     "chave": "margem_alvo"})
    if regular:
        prio.append({"texto": "Pedir aos fornecedores a nota com a CBS/IBS destacada: o crédito sobre o custo é o que segura o preço em 2027.",
                     "chave": "fator_credito_pct"})
    else:
        prio.append({"texto": f"Conferir todo mês a alíquota efetiva do DAS (hoje {N.itens['imp_hoje_pct']['texto']}): ela muda com a receita "
                              "dos últimos doze meses, e com ela o preço mínimo.", "chave": "imp_hoje_pct"})
    prio.append({"texto": "Refazer a tabela quando o Senado fixar a alíquota de referência e a cada reajuste de custo.", "chave": "margem_alvo"})
    prio = prio[:3]
    N.add("itens_total", len(linhas), "int", "produtos.csv (número de linhas)")
    N.add("itens_abaixo", len(abaixo), "int", "itens abaixo da margem-alvo no cenário principal")
    return {"versao": VERSAO, "kit": "preco_certo", "empresa": {k: emp.get(k) for k in ("nome", "regime", "atividade")},
            "regular": regular, "cenarios": cenarios, "numeros": N.itens, "linhas": linhas, "prioridades": prio}


def precos_md(d):
    T = lambda k: d["numeros"][k]["texto"] if k in d["numeros"] else "—"
    e = d["empresa"]
    L = [f"# Preço certo na Reforma — {e.get('nome', 'Empresa')}", ""]
    if d["regular"]:
        L.append(f"Regime: {e['regime']}. Margem-alvo: {T('margem_alvo')}. Números de 2027 = **SIMULADO**, nos cenários de alíquota de referência de "
                 + " e ".join(T('aliq_' + str(a).replace('.', '_')) for a in d["cenarios"])
                 + f" (o primeiro é o principal). O imposto de hoje é o PIS/Cofins efetivo da empresa ({T('imp_hoje_pct')} da receita).")
        L.append(f"Premissa: crédito sobre a parte do custo informada em custo_com_credito ou, sem ela, sobre {T('fator_credito_pct')} do custo "
                 "(a fatia das compras da empresa que gera crédito). Base = preço informado (simplificação). Kit aberto do INEMA, não oficial.")
    else:
        L.append(f"Regime: Simples. Margem-alvo: {T('margem_alvo')}. Imposto = alíquota efetiva do DAS ({T('imp_hoje_pct')}); "
                 "este kit não prevê mudança no DAS em 2027. Kit aberto do INEMA, não oficial.")
    L.append("")
    L.append("## Item por item")
    for r in d["linhas"]:
        k = r["k"]
        L.append(f"### {r['item']}")
        L.append(f"- Preço de hoje: {T(k + '_preco')}. Margem hoje: {T(k + '_margem_hoje')}.")
        if d["regular"]:
            for c in r["cen"]:
                kk = c["kk"]
                L.append(f"- Com {T('aliq_' + str(c['aliq']).replace('.', '_'))}: margem {T(kk + '_margem')}; preço mínimo {T(kk + '_preco_min')}; "
                         f"preço-alvo {T(kk + '_preco_alvo')}; desconto máximo sobre o preço de hoje {T(kk + '_desc_max')}.")
        else:
            L.append(f"- Preço mínimo {T(k + '_preco_min')}; preço-alvo {T(k + '_preco_alvo')}; desconto máximo sobre o preço de hoje {T(k + '_desc_max')}.")
    L.append("")
    L.append("## Suas 3 prioridades")
    for i, p in enumerate(d["prioridades"], 1):
        L.append(f"{i}. {p['texto']}")
    L.append("")
    L.append("Como ler: preço mínimo = margem zero (abaixo dele, cada venda dá prejuízo). Preço-alvo = o preço que dá a margem que a empresa quer. "
             "Desconto máximo = quanto dá para baixar o preço de hoje sem sair da margem-alvo (0,0% quando o preço já está abaixo).")
    L.append("")
    L.append(f"---\nOrigem de cada número: `dados.json`. Tabela: `precos.csv`. Kit Preço certo na Reforma v{d['versao']} (INEMA, não oficial).")
    return "\n".join(L) + "\n"


def precos_csv(d):
    n = d["numeros"]
    v = lambda k: f"{n[k]['valor']:.2f}".replace(".", ",") if k in n else ""
    if d["regular"]:
        cab = ["item", "preco", "margem_hoje_pct"]
        for a in d["cenarios"]:
            s = str(a).replace(".", "_")
            cab += [f"margem_{s}_pct", f"preco_min_{s}", f"preco_alvo_{s}", f"desconto_max_{s}_pct"]
    else:
        cab = ["item", "preco", "margem_hoje_pct", "preco_min", "preco_alvo", "desconto_max_pct"]
    L = [";".join(cab)]
    for r in d["linhas"]:
        k = r["k"]
        row = [r["item"], v(k + "_preco"), v(k + "_margem_hoje")]
        if d["regular"]:
            for c in r["cen"]:
                kk = c["kk"]
                row += [v(kk + "_margem"), v(kk + "_preco_min"), v(kk + "_preco_alvo"), v(kk + "_desc_max")]
        else:
            row += [v(k + "_preco_min"), v(k + "_preco_alvo"), v(k + "_desc_max")]
        L.append(";".join(row))
    return "\n".join(L) + "\n"


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else pasta / "saida"
    try:
        d = calcular(*carregar(pasta))
    except ErroDados as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    gravar(saida, d, "precos.md", precos_md(d), {"precos.csv": precos_csv(d)})
    print(f"ok: {saida/'precos.md'}, {saida/'precos.csv'} e {saida/'dados.json'} "
          f"({len(d['linhas'])} itens, {d['numeros']['itens_abaixo']['valor']} abaixo da margem-alvo)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
