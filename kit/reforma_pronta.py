#!/usr/bin/env python3
"""Reforma Tributária Pronta — kit aberto do INEMA (não oficial).

Confere se o cadastro, o sistema, os fornecedores e os contratos de UMA empresa (um CNPJ)
estão prontos para a CBS e o IBS de 2027, e monta o plano de adequação com prazos.

Uso:  python3 kit/reforma_pronta.py <pasta-do-cliente> [--saida <pasta>] [--hoje AAAA-MM-DD]

Arquivos da pasta (os mesmos do Diagnóstico + dois específicos):
  empresa.json       obrigatório  (o mesmo do Diagnóstico)
  itens.csv          obrigatório  item;tipo;codigo;cst;cclasstrib;reducao_pct;vendas_ano
                                  tipo = produto (código NCM, 8 dígitos) ou servico (código NBS, 9 dígitos)
  fornecedores.csv   opcional     fornecedor;regime;compras_ano   (regime = regular, simples ou mei)
  prontidao.json     opcional     respostas sim/não sobre sistema, notas, contratos, preços e equipe

Gera em saida/reforma-pronta/ (para não apagar o dados.json do Diagnóstico, que fica em saida/): plano.md (o plano em linguagem simples), pendencias.csv (uma linha por pendência)
e dados.json (todos os números, cada um com a origem). Só lê e confere: não chama internet nem IA.
O kit confere o FORMATO e a coerência dos códigos; se o código é o certo para o item, quem diz
é o contador, com a tabela oficial ou o teste do motor da calculadora-da-reforma.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import ErroDados, Numeros, carregar_empresa, gravar, ler_csv, num, pct  # noqa: E402

VERSAO = "1.0.0"
PADROES = {"vendas_para_empresas_pct": 0}

PERGUNTAS = [
    ("erp_atualizado", "O sistema de notas (ERP ou emissor) já tem os campos novos da CBS e do IBS (CST e cClassTrib)"),
    ("nota_teste", "Já foi emitida uma nota de teste com a CBS e o IBS destacados"),
    ("cadastro_revisado", "O cadastro de produtos e serviços (NCM/NBS) foi revisado"),
    ("contratos_revisados", "Os contratos longos têm cláusula de repasse de tributo"),
    ("precos_revisados", "Os preços de 2027 foram revisados com o imposto novo"),
    ("equipe_treinada", "A equipe de faturamento sabe o que muda na nota"),
]

REDUCOES_USUAIS = {0, 30, 60, 100}


def digitos(t):
    return "".join(ch for ch in str(t) if ch.isdigit())


def carregar(pasta):
    pasta = Path(pasta)
    emp = carregar_empresa(pasta, PADROES)
    f = pasta / "itens.csv"
    if not f.exists():
        raise ErroDados(f"falta {f} (lista de produtos e serviços com os códigos)")
    itens = []
    for i, r in enumerate(ler_csv(f), start=2):
        for c in ("item", "tipo", "codigo", "cst", "cclasstrib", "reducao_pct", "vendas_ano"):
            if c not in r:
                raise ErroDados(f"itens.csv: falta a coluna '{c}'")
        tipo = r["tipo"].strip().lower().replace("ç", "c")
        if tipo not in ("produto", "servico"):
            raise ErroDados(f"itens.csv linha {i}: tipo deve ser produto ou servico ('{r['tipo']}')")
        itens.append({"item": r["item"].strip(), "tipo": tipo, "codigo": r["codigo"].strip(),
                      "cst": r["cst"].strip(), "cclasstrib": r["cclasstrib"].strip(),
                      "reducao_pct": num(r["reducao_pct"], "itens.csv", i, "reducao_pct"),
                      "vendas_ano": num(r["vendas_ano"], "itens.csv", i, "vendas_ano"), "_linha": i})
    if not itens:
        raise ErroDados("itens.csv está vazio")
    forn = []
    if (pasta / "fornecedores.csv").exists():
        for i, r in enumerate(ler_csv(pasta / "fornecedores.csv"), start=2):
            reg = r.get("regime", "").strip().lower()
            if reg not in ("regular", "simples", "mei"):
                raise ErroDados(f"fornecedores.csv linha {i}: regime deve ser regular, simples ou mei ('{reg}')")
            forn.append({"fornecedor": r["fornecedor"].strip(), "regime": reg,
                         "compras_ano": num(r["compras_ano"], "fornecedores.csv", i, "compras_ano")})
    pront = {}
    if (pasta / "prontidao.json").exists():
        pront = json.loads((pasta / "prontidao.json").read_text(encoding="utf-8"))
    return emp, itens, forn, pront


def conferir_item(it):
    """Devolve a lista de pendências (campo, problema, o que fazer) de um item."""
    p = []
    cod = digitos(it["codigo"])
    if not cod:
        p.append(("codigo", "sem código " + ("NCM" if it["tipo"] == "produto" else "NBS"),
                  "preencher o código do item no cadastro"))
    elif it["tipo"] == "produto" and len(cod) != 8:
        p.append(("codigo", f"NCM com {len(cod)} dígitos (o certo são 8)", "corrigir o NCM no cadastro"))
    elif it["tipo"] == "servico" and len(cod) != 9:
        p.append(("codigo", f"NBS com {len(cod)} dígitos (o certo são 9)", "corrigir o código NBS no cadastro"))
    cst = digitos(it["cst"])
    if not cst:
        p.append(("cst", "sem CST da CBS/IBS", "definir o CST do item"))
    elif len(cst) != 3:
        p.append(("cst", f"CST com {len(cst)} dígitos (o certo são 3)", "corrigir o CST"))
    cct = digitos(it["cclasstrib"])
    if not cct:
        p.append(("cclasstrib", "sem cClassTrib", "definir a classificação tributária (cClassTrib) do item"))
    elif len(cct) != 6:
        p.append(("cclasstrib", f"cClassTrib com {len(cct)} dígitos (o certo são 6)", "corrigir o cClassTrib"))
    elif len(cst) == 3 and cct[:3] != cst:
        p.append(("cclasstrib", f"cClassTrib {cct} não começa pelo CST {cst}",
                  "conferir o par CST/cClassTrib na tabela oficial"))
    red = it["reducao_pct"]
    if red and red not in REDUCOES_USUAIS:
        p.append(("reducao_pct", f"redução de {pct(red, 0)} fora das faixas usuais (30%, 60% ou 100%)",
                  "conferir a redução da atividade na lei"))
    if red and cst == "000":
        p.append(("reducao_pct", "redução informada com CST 000, que é tributação integral",
                  "conferir: com redução, o CST costuma ser o de alíquota reduzida (200)"))
    if not red and cst == "200":
        p.append(("reducao_pct", "CST 200 (alíquota reduzida) sem redução informada", "conferir a redução do item"))
    if red and not cct:
        p.append(("reducao_pct", "redução informada sem cClassTrib que a justifique",
                  "definir o cClassTrib da redução, ou tirar a redução"))
    return p


def proxima_janela_simples(hoje):
    """A opção do Simples pelo regime regular do IBS/CBS é feita em setembro e março (LC 123, art. 13, § 10)."""
    if hoje.month < 3:
        return dt.date(hoje.year, 3, 1), dt.date(hoje.year, 7, 1)
    if hoje.month < 9:
        return dt.date(hoje.year, 9, 1), dt.date(hoje.year + 1, 1, 1)
    return dt.date(hoje.year + 1, 3, 1), dt.date(hoje.year + 1, 7, 1)


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def planejar(emp, itens, forn, pront, hoje):
    N = Numeros()
    total = sum(i["vendas_ano"] for i in itens)
    pend = []
    itens_pend = 0
    vendas_pend = 0.0
    for it in itens:
        ps = conferir_item(it)
        it["pendencias"] = ps
        if ps:
            itens_pend += 1
            vendas_pend += it["vendas_ano"]
            for campo, prob, fazer in ps:
                pend.append({"item": it["item"], "linha": it["_linha"], "campo": campo, "problema": prob, "o_que_fazer": fazer})
    N.add("itens_total", len(itens), "int", "itens.csv (número de linhas)")
    N.add("itens_ok", len(itens) - itens_pend, "int", "itens sem pendência de formato")
    N.add("itens_pend", itens_pend, "int", "itens com ao menos uma pendência")
    N.add("pendencias", len(pend), "int", "soma das pendências de todos os itens")
    N.add("vendas_total", total, "brl", "soma de vendas_ano em itens.csv")
    N.add("vendas_pend", vendas_pend, "brl", "vendas_ano dos itens com pendência")
    N.add("vendas_pend_pct", vendas_pend / total * 100 if total else 0.0, "pct", "vendas_pend ÷ vendas_total")

    # itens que somam 80% das vendas: os primeiros a passar no motor oficial
    ordem = sorted(itens, key=lambda x: -x["vendas_ano"])
    acum, top = 0.0, []
    for it in ordem:
        if total and acum / total >= 0.8:
            break
        top.append(it)
        acum += it["vendas_ano"]
    N.add("itens_80", len(top), "int", "menor número de itens que soma 80% das vendas (do maior para o menor)")
    N.add("itens_80_pct", acum / total * 100 if total else 0.0, "pct", "fatia das vendas desses itens")

    # fornecedores: crédito limitado quando o fornecedor é do Simples ou MEI
    fsum = {}
    if forn:
        compras = sum(f["compras_ano"] for f in forn)
        lim = sum(f["compras_ano"] for f in forn if f["regime"] in ("simples", "mei"))
        N.add("compras_total", compras, "brl", "soma de compras_ano em fornecedores.csv")
        N.add("compras_simples", lim, "brl", "compras de fornecedores do Simples ou MEI")
        N.add("compras_simples_pct", lim / compras * 100 if compras else 0.0, "pct", "compras_simples ÷ compras_total")
        maiores = sorted([f for f in forn if f["regime"] in ("simples", "mei")], key=lambda x: -x["compras_ano"])[:5]
        for k, f in enumerate(maiores):
            N.add(f"forn_{k}_compras", f["compras_ano"], "brl", f"fornecedores.csv: {f['fornecedor']}")
        fsum = {"maiores_simples": maiores}

    # prontidão do sistema, notas, contratos, preços e equipe
    respostas = []
    for chave, texto in PERGUNTAS:
        v = pront.get(chave)
        estado = "sim" if v is True else "não" if v is False else "não respondido"
        respostas.append({"chave": chave, "texto": texto, "estado": estado})
    sim = sum(1 for r in respostas if r["estado"] == "sim")
    N.add("pront_sim", sim, "int", "respostas 'sim' em prontidao.json")
    N.add("pront_total", len(PERGUNTAS), "int", "perguntas de prontidão")

    # janela do Simples
    simples = None
    if emp["regime"] == "simples":
        jan, vale = proxima_janela_simples(hoje)
        simples = {"janela": f"{MESES[jan.month - 1]} de {jan.year}", "vale": f"{MESES[vale.month - 1]} de {vale.year}"}
        N.add("vendas_empresas_pct", float(emp["vendas_para_empresas_pct"]), "pct", "empresa.json (vendas_para_empresas_pct)")

    # prioridades: do que pesa mais nas vendas para o que pesa menos
    prio = []
    top_pend = [it for it in top if it["pendencias"]]
    if top_pend:
        v = sum(it["vendas_ano"] for it in top_pend)
        N.add("vendas_top_pend", v, "brl", "vendas dos itens de maior venda que têm pendência")
        nomes = ", ".join(it["item"] for it in top_pend[:3])
        prio.append({"texto": f"Corrigir primeiro o cadastro de {nomes}: "
                              + ("é um dos itens" if len(top_pend) == 1 else "estão entre os itens")
                              + f" de maior venda, com pendência ({N.itens['vendas_top_pend']['texto']} de vendas por ano).",
                     "chave": "vendas_top_pend"})
    elif pend:
        prio.append({"texto": f"Corrigir as {N.itens['pendencias']['texto']} pendências de cadastro (lista em pendencias.csv).",
                     "chave": "pendencias"})
    nao = [r for r in respostas if r["estado"] != "sim"]
    if any(r["chave"] in ("erp_atualizado", "nota_teste") for r in nao):
        prio.append({"texto": "Emitir uma nota de teste com a CBS e o IBS antes de janeiro e conferir os valores no motor oficial da Receita.",
                     "chave": "pront_sim"})
    if fsum.get("maiores_simples") and N.itens["compras_simples_pct"]["valor"] >= 20:
        prio.append({"texto": f"Conversar com os fornecedores do Simples: {N.itens['compras_simples_pct']['texto']} das compras vêm deles, "
                              "e o crédito dessas compras é limitado ao que eles pagam no Simples.",
                     "chave": "compras_simples_pct"})
    if simples and emp["vendas_para_empresas_pct"] >= 50:
        prio.append({"texto": f"Decidir na janela de {simples['janela']} se vale recolher a CBS/IBS fora do DAS: "
                              f"{N.itens['vendas_empresas_pct']['texto']} das vendas são para empresas.",
                     "chave": "vendas_empresas_pct"})
    if any(r["chave"] == "contratos_revisados" for r in nao):
        prio.append({"texto": "Revisar os contratos longos e incluir a cláusula de repasse de tributo.", "chave": "pront_total"})
    if any(r["chave"] == "precos_revisados" for r in nao):
        prio.append({"texto": "Revisar os preços de 2027 (kit Preço certo na Reforma).", "chave": "pront_total"})
    prio.append({"texto": "Refazer este plano quando o Senado fixar a alíquota de referência e a cada versão nova da tabela oficial.",
                 "chave": "itens_total"})
    prio = prio[:3]

    return {"versao": VERSAO, "kit": "reforma_pronta", "hoje": hoje.isoformat(),
            "empresa": {k: emp.get(k) for k in ("nome", "regime", "atividade")},
            "numeros": N.itens, "pendencias": pend, "itens_80": [it["item"] for it in top],
            "fornecedores": fsum, "prontidao": respostas, "simples": simples, "prioridades": prio}


def plano_md(d):
    T = lambda k: d["numeros"][k]["texto"]
    e = d["empresa"]
    L = [f"# Reforma Tributária Pronta — {e.get('nome', 'Empresa')}", "",
         f"Regime: {e['regime']}. Conferido em {dt.date.fromisoformat(d['hoje']).strftime('%d/%m/%Y')}. "
         "Este plano confere o formato e a coerência dos cadastros; se cada código é o certo para o item, quem confirma é o seu contador, "
         "com a tabela oficial ou o motor da Receita. Kit aberto do INEMA, não oficial.", "",
         "## 1. Como está a prontidão",
         f"- Cadastro: {T('itens_ok')} de {T('itens_total')} itens sem pendência. Os {T('itens_pend')} itens com pendência somam {T('vendas_pend')} de vendas por ano ({T('vendas_pend_pct')} do total).",
         f"- Sistema, notas, contratos e preços: {T('pront_sim')} de {T('pront_total')} respostas \"sim\".",
         f"- Os {T('itens_80')} itens de maior venda somam {T('itens_80_pct')} das vendas: são os primeiros a conferir no motor oficial.", ""]
    L.append("## 2. Pendências do cadastro")
    if d["pendencias"]:
        for p in d["pendencias"][:15]:
            L.append(f"- {p['item']}: {p['problema']} → {p['o_que_fazer']}.")
        if len(d["pendencias"]) > 15:
            L.append(f"- A lista completa ({T('pendencias')} pendências) está em pendencias.csv.")
    else:
        L.append("- Nenhuma pendência de formato. Falta só conferir os itens de maior venda no motor oficial.")
    L.append("")
    L.append("## 3. Fornecedores e crédito")
    if d["fornecedores"]:
        L.append(f"- Das compras de {T('compras_total')} por ano, {T('compras_simples')} ({T('compras_simples_pct')}) vêm de fornecedores do Simples ou MEI. "
                 "O crédito dessas compras é limitado ao que o fornecedor paga no Simples (LC 214, art. 47).")
        for k, f in enumerate(d["fornecedores"]["maiores_simples"]):
            L.append(f"- {f['fornecedor']} ({f['regime']}): {T(f'forn_{k}_compras')} por ano.")
    else:
        L.append("- Sem fornecedores.csv: o plano não avaliou o crédito das compras.")
    if d["simples"]:
        L.append(f"- Esta empresa é do Simples: {T('vendas_empresas_pct')} das vendas são para empresas. A opção de recolher a CBS/IBS fora do DAS "
                 f"é feita em setembro e março; a próxima janela é {d['simples']['janela']}, para valer a partir de {d['simples']['vale']}.")
    L.append("")
    L.append("## 4. Sistema, notas, contratos e equipe")
    for r in d["prontidao"]:
        marca = {"sim": "✅", "não": "❌", "não respondido": "❔"}[r["estado"]]
        L.append(f"- {marca} {r['texto']}: {r['estado']}.")
    L.append("")
    L.append("## 5. Plano por prazo")
    L.append("- **Até 15/12/2026:** o Senado fixa a alíquota de referência da CBS. Refazer as simulações com o número oficial.")
    L.append("- **Até 31/12/2026:** cadastro sem pendências, sistema atualizado e uma nota de teste emitida e conferida.")
    L.append("- **Janeiro de 2027:** a CBS passa a ser cobrada no lugar do PIS e da Cofins. Conferir as primeiras notas reais no motor oficial.")
    if d["simples"]:
        L.append(f"- **{d['simples']['janela'].capitalize()}:** janela da opção do Simples pelo regime regular da CBS/IBS.")
    L.append("")
    L.append("## 6. Suas 3 prioridades")
    for i, p in enumerate(d["prioridades"], 1):
        L.append(f"{i}. {p['texto']}")
    L.append("")
    L.append(f"---\nOrigem de cada número: `dados.json`. Lista completa: `pendencias.csv`. Kit Reforma Tributária Pronta v{d['versao']} (INEMA, não oficial).")
    return "\n".join(L) + "\n"


def pendencias_csv(d):
    linhas = ["item;linha_itens_csv;campo;problema;o_que_fazer"]
    for p in d["pendencias"]:
        linhas.append(";".join([p["item"], str(p["linha"]), p["campo"], p["problema"], p["o_que_fazer"]]))
    return "\n".join(linhas) + "\n"


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else pasta / "saida" / "reforma-pronta"  # não apaga o dados.json do Diagnóstico
    hoje = dt.date.fromisoformat(argv[argv.index("--hoje") + 1]) if "--hoje" in argv else dt.date.today()
    try:
        d = planejar(*carregar(pasta), hoje)
    except ErroDados as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    gravar(saida, d, "plano.md", plano_md(d), {"pendencias.csv": pendencias_csv(d)})
    print(f"ok: {saida/'plano.md'}, {saida/'pendencias.csv'} e {saida/'dados.json'} "
          f"({len(d['pendencias'])} pendências, {len(d['prioridades'])} prioridades)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
