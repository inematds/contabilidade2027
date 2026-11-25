#!/usr/bin/env python3
"""Painel do Empresário — kit aberto do INEMA (não oficial).

O fechamento do mês em texto simples para o dono da empresa: o resultado do mês (DRE gerencial),
a comparação com o mês anterior e com a média, o caixa projetado para os próximos 3 meses,
o que está a receber e a pagar, os recebíveis vencidos, os alertas e o que fazer este mês.

Uso:  python3 kit/painel.py <pasta-do-cliente> [--saida <pasta>] [--hoje AAAA-MM-DD]

Arquivos da pasta (os mesmos do Diagnóstico + dois opcionais):
  empresa.json, mensal.csv      obrigatórios (o último mês do mensal.csv é o mês do painel)
  despesas.csv                  opcional (despesa fora do padrão)
  contas_receber.csv            opcional  cliente;valor;vencimento   (vencimento AAAA-MM-DD ou DD/MM/AAAA)
  contas_pagar.csv              opcional  fornecedor;valor;vencimento

Gera em saida/painel/ (para não apagar o dados.json do Diagnóstico, que fica em saida/): painel.md (para mandar ao cliente ou ler na reunião) e dados.json.
Só lê e calcula. A projeção é uma estimativa simples (média dos últimos 3 meses + contas lançadas).
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import ErroDados, Numeros, carregar_empresa, gravar, ler_csv, num, pct  # noqa: E402
import diagnostico as D  # noqa: E402

VERSAO = "1.0.0"


def data(t, arq, linha):
    t = t.strip()
    try:
        if "/" in t:
            d, m, a = t.split("/")
            return dt.date(int(a), int(m), int(d))
        return dt.date.fromisoformat(t)
    except ValueError:
        raise ErroDados(f"{arq} linha {linha}: vencimento inválido ('{t}'); use AAAA-MM-DD ou DD/MM/AAAA")


def contas(pasta, nome, quem):
    f = Path(pasta) / nome
    if not f.exists():
        return None
    out = []
    for i, r in enumerate(ler_csv(f), start=2):
        out.append({quem: r[quem].strip(), "valor": num(r["valor"], nome, i, "valor"),
                    "venc": data(r["vencimento"], nome, i)})
    return out


def carregar(pasta):
    emp, mensal, despesas, _ = D.carregar(pasta)
    return emp, mensal, despesas, contas(pasta, "contas_receber.csv", "cliente"), contas(pasta, "contas_pagar.csv", "fornecedor")


def variacao(a, b):
    return (a - b) / abs(b) * 100 if b else 0.0


def painel(emp, mensal, despesas, receber, pagar, hoje):
    N = Numeros()
    # despesas.csv só vale se tiver o mesmo mês do painel; senão o alerta seria de um mês velho
    ult_desp = despesas[-1]["mes"] if despesas else None
    desp_ok = bool(despesas) and any(x["mes"] == mensal[-1]["mes"] for x in despesas)
    diag = D.diagnosticar(emp, mensal, despesas if desp_ok else [], [])   # mesmas contas do Diagnóstico (split, despesas fora do padrão)
    m = mensal[-1]
    ant = mensal[-2]
    hist = mensal[:-1]
    lucro = lambda x: x["receita"] - x["custo_direto"] - x["despesas_operacionais"] - x["pis_cofins_pago"] - x["outros_impostos"]
    margem = lambda x: lucro(x) / x["receita"] * 100 if x["receita"] else 0.0
    mes = m["mes"]
    N.add("mes", mes, "int", f"último mês de mensal.csv (linha {m['_linha']})")

    # DRE gerencial do mês
    bruta = m["receita"] - m["custo_direto"]
    impostos = m["pis_cofins_pago"] + m["outros_impostos"]
    N.add("receita", m["receita"], "brl", f"mensal.csv {mes}")
    N.add("custo", m["custo_direto"], "brl", f"mensal.csv {mes}")
    N.add("bruta", bruta, "brl", "receita − custo_direto")
    N.add("despesas", m["despesas_operacionais"], "brl", f"mensal.csv {mes}")
    N.add("impostos", impostos, "brl", "pis_cofins_pago + outros_impostos")
    N.add("lucro", lucro(m), "brl", "receita − custo − despesas − impostos")
    N.add("margem", margem(m), "pct", "lucro ÷ receita")

    # comparações
    med_rec = sum(x["receita"] for x in hist) / len(hist)
    med_luc = sum(lucro(x) for x in hist) / len(hist)
    med_mar = sum(margem(x) for x in hist) / len(hist)
    for k, v, o in (("var_rec_ant", variacao(m["receita"], ant["receita"]), f"receita de {mes} contra {ant['mes']}"),
                    ("var_rec_med", variacao(m["receita"], med_rec), f"receita de {mes} contra a média dos {len(hist)} meses anteriores"),
                    ("var_luc_ant", variacao(lucro(m), lucro(ant)), f"lucro de {mes} contra {ant['mes']}")):
        N.add(k, v, "pct", o)
        N.add(k + "_abs", abs(v), "pct", o + " (sem o sinal)")
    N.add("janela_dias", 30, "int", "janela de curto prazo do painel")
    N.add("meses_media", 3, "int", "meses usados na média da projeção")
    N.add("margem_media", med_mar, "pct", f"margem média dos {len(hist)} meses anteriores")
    N.add("meses_hist", len(hist), "int", "meses anteriores usados nas médias")
    N.add("margem_dif", margem(m) - med_mar, "pct", "margem do mês − margem média (pontos percentuais)")
    N.add("lucro_medio", med_luc, "brl", f"lucro médio dos {len(hist)} meses anteriores")

    # caixa: projeção pela variação REAL do saldo (o lucro não é caixa: retiradas, parcelas e investimentos saem fora do DRE)
    ult3 = mensal[-3:]
    ent = sum(x["receita"] for x in ult3) / 3
    sai = sum(x["custo_direto"] + x["despesas_operacionais"] + x["pis_cofins_pago"] + x["outros_impostos"] for x in ult3) / 3
    base = mensal[-4:] if len(mensal) >= 4 else mensal
    deltas = [b["saldo_caixa_fim"] - a["saldo_caixa_fim"] for a, b in zip(base, base[1:])]
    var_saldo = sum(deltas) / len(deltas) if deltas else 0.0
    luc3 = sum(lucro(x) for x in ult3) / 3
    N.add("saldo", m["saldo_caixa_fim"], "brl", f"saldo_caixa_fim de {mes}")
    N.add("entrada_media", ent, "brl", "receita média dos 3 últimos meses")
    N.add("saida_media", sai, "brl", "saídas médias dos 3 últimos meses (custo + despesas + impostos)")
    N.add("var_saldo", var_saldo, "brl", f"variação média do saldo_caixa_fim nos últimos {len(deltas)} meses")
    N.add("var_saldo_abs", abs(var_saldo), "brl", "variação média do saldo, sem o sinal")
    N.add("lucro_3m", luc3, "brl", "lucro médio dos 3 últimos meses")
    N.add("meses_var", len(deltas), "int", "meses usados na variação do saldo")
    fim = dt.date(int(mes.split("/")[1]), int(mes.split("/")[0]), 1)
    proj = []
    saldo = m["saldo_caixa_fim"]
    for k in range(1, 4):
        a, mm = fim.year + (fim.month - 1 + k) // 12, (fim.month - 1 + k) % 12 + 1
        rot = f"{mm:02d}/{a}"
        saldo += var_saldo
        N.add(f"proj_{k}", saldo, "brl", f"saldo + variação média do saldo × {k}  ({rot})")
        proj.append({"mes": rot, "saldo": saldo, "k": k})
    negativo = [p for p in proj if p["saldo"] < 0]
    # o resultado e o caixa contam histórias diferentes? (lucro positivo e saldo caindo)
    diverge = luc3 > 0 and var_saldo < luc3 * 0.5 and luc3 - var_saldo >= 1000
    if diverge:
        N.add("fora_dre", luc3 - var_saldo, "brl", "lucro médio − variação média do saldo: dinheiro que saiu fora do resultado")

    # contas a receber e a pagar
    rec = {}
    if receber is not None:
        venc = [c for c in receber if c["venc"] < hoje]
        prox = [c for c in receber if hoje <= c["venc"] <= hoje + dt.timedelta(days=30)]
        N.add("receber_vencido", sum(c["valor"] for c in venc), "brl", f"contas_receber.csv com vencimento antes de {hoje:%d/%m/%Y}")
        N.add("receber_vencido_qtd", len(venc), "int", "quantidade de contas vencidas")
        N.add("receber_30", sum(c["valor"] for c in prox), "brl", "a receber nos próximos 30 dias")
        maiores = sorted(venc, key=lambda c: -c["valor"])[:3]
        for i, c in enumerate(maiores):
            N.add(f"venc_{i}", c["valor"], "brl", f"contas_receber.csv: {c['cliente']}, venceu em {c['venc']:%d/%m/%Y}")
            N.add(f"venc_{i}_dias", (hoje - c["venc"]).days, "int", "dias de atraso")
        rec = {"vencidos": [{"cliente": c["cliente"], "i": i} for i, c in enumerate(maiores)]}
    if pagar is not None:
        prox = [c for c in pagar if hoje <= c["venc"] <= hoje + dt.timedelta(days=30)]
        venc = [c for c in pagar if c["venc"] < hoje]
        N.add("pagar_30", sum(c["valor"] for c in prox), "brl", "a pagar nos próximos 30 dias")
        N.add("pagar_vencido", sum(c["valor"] for c in venc), "brl", f"contas_pagar.csv com vencimento antes de {hoje:%d/%m/%Y}")
    if receber is not None and pagar is not None:
        N.add("folga_30", m["saldo_caixa_fim"] + N.itens["receber_30"]["valor"] - N.itens["pagar_30"]["valor"], "brl",
              "saldo + a receber em 30 dias − a pagar em 30 dias")

    # split payment (mesma conta do Diagnóstico)
    if "split_giro" in diag["numeros"]:
        N.itens["split_giro"] = diag["numeros"]["split_giro"]
        ch = diag["reforma"]["pior"]["chave"]
        N.itens["split_aliq"] = diag["numeros"][f"cbs_{ch}_aliq"]

    # alertas
    alertas = []
    if N.itens["margem_dif"]["valor"] <= -3:
        alertas.append(f"A margem caiu: {N.itens['margem']['texto']} no mês, contra {N.itens['margem_media']['texto']} de média.")
    for f in diag["despesas_fora"][:2]:
        i = f["i"]
        N.itens[f"desp_{i}_acima"] = diag["numeros"][f"desp_{i}_acima"]
        alertas.append(f"{f['categoria']} ficou {N.itens[f'desp_{i}_acima']['texto']} acima da média.")
    if rec.get("vencidos"):
        alertas.append(f"Há {N.itens['receber_vencido']['texto']} a receber já vencidos ({N.itens['receber_vencido_qtd']['texto']} contas).")
    folego = m["saldo_caixa_fim"] / sai if sai else 0.0
    N.add("folego", round(folego, 2), "int", "saldo ÷ saídas médias (meses de saídas que o caixa cobre)")
    N.itens["folego"]["texto"] = f"{folego:.2f}".replace(".", ",")
    curto = folego < 0.5
    if curto:
        alertas.append(f"O caixa cobre só {N.itens['folego']['texto']} mês de saídas: qualquer atraso de cliente aperta.")
    if despesas and not desp_ok:
        alertas.append(f"O despesas.csv vai só até {ult_desp}: atualize com {mes} para o painel conferir as despesas do mês.")
    if diverge:
        alertas.append(f"O resultado e o caixa não batem: nos últimos 3 meses sobraram em média {N.itens['lucro_3m']['texto']} por mês no resultado, mas o saldo "
                       + ("caiu" if var_saldo < 0 else "subiu só") + f" {N.itens['var_saldo_abs']['texto']} por mês. A diferença, de cerca de {N.itens['fora_dre']['texto']} por mês, pode ser cliente pagando "
                       "mais tarde, estoque, fornecedor pago antes, retirada dos sócios, parcela de empréstimo ou investimento: vale conferir.")
    if negativo:
        alertas.append(f"O caixa projetado fica negativo em {negativo[0]['mes']} ({N.itens['proj_' + str(negativo[0]['k'])]['texto']}), "
                       "se nada mudar.")
    if "folga_30" in N.itens and N.itens["folga_30"]["valor"] < 0:
        alertas.append(f"Nos próximos 30 dias sai mais do que entra: folga de {N.itens['folga_30']['texto']}.")

    # o que fazer este mês
    fazer = []
    if rec.get("vencidos"):
        c0 = rec["vencidos"][0]
        fazer.append(f"Cobrar {c0['cliente']}: {N.itens['venc_0']['texto']} vencidos há {N.itens['venc_0_dias']['texto']} dias.")
    if diverge:
        fazer.append("Conferir com o dono por que o caixa não acompanhou o resultado: clientes atrasando, estoque, retiradas, parcelas ou investimentos.")
    if negativo or ("folga_30" in N.itens and N.itens["folga_30"]["valor"] < 0):
        fazer.append("Rever as saídas dos próximos meses ou antecipar recebimentos: o caixa projetado aperta.")
    if curto:
        fazer.append(f"Montar uma reserva de caixa: hoje o saldo cobre só {N.itens['folego']['texto']} mês de saídas.")
    if diag["despesas_fora"]:
        f0 = diag["despesas_fora"][0]
        fazer.append(f"Entender por que {f0['categoria']} subiu e decidir se continua.")
    if N.itens["margem_dif"]["valor"] <= -3:
        fazer.append("Rever preços e custos dos itens que mais vendem (kit Preço certo na Reforma).")
    if receber is None or pagar is None:
        fazer.append("Lançar as contas a receber e a pagar no próximo painel: assim a folga dos próximos 30 dias aparece.")
    fazer.append("Manter a conversa curta de fechamento todo mês, com este painel.")
    fazer = fazer[:3]

    return {"versao": VERSAO, "kit": "painel", "hoje": hoje.isoformat(),
            "empresa": {k: emp.get(k) for k in ("nome", "regime", "atividade")},
            "numeros": N.itens, "projecao": proj, "receber": rec, "tem_receber": receber is not None,
            "tem_pagar": pagar is not None, "alertas": alertas, "fazer": fazer}


def painel_md(d):
    T = lambda k: d["numeros"][k]["texto"]
    e = d["empresa"]
    sobe = lambda k: ("subiu " + T(k + "_abs")) if d["numeros"][k]["valor"] >= 0 else ("caiu " + T(k + "_abs"))
    L = [f"# Painel do Empresário — {e.get('nome', 'Empresa')} — {T('mes')}", "",
         "O fechamento do mês em linguagem simples. Preparado pelo seu contador com o kit aberto do INEMA (não oficial).", "",
         "## 1. Como foi o mês",
         f"- Você vendeu {T('receita')} e sobrou {T('lucro')}: margem de {T('margem')}.",
         f"- A venda {sobe('var_rec_ant')} contra o mês anterior e {sobe('var_rec_med')} contra a média dos {T('meses_hist')} meses anteriores.",
         f"- O lucro {sobe('var_luc_ant')} contra o mês anterior. A margem média dos {T('meses_hist')} meses anteriores foi {T('margem_media')}.", "",
         "## 2. O resultado, linha por linha",
         f"- Vendas: {T('receita')}",
         f"- (−) Custo direto: {T('custo')}",
         f"- (=) Sobra depois do custo: {T('bruta')}",
         f"- (−) Despesas do dia a dia: {T('despesas')}",
         f"- (−) Impostos: {T('impostos')}",
         f"- (=) Lucro do mês: {T('lucro')} (antes das retiradas dos sócios e das parcelas de empréstimo)", "",
         "## 3. O caixa"]
    L.append(f"- Saldo no fim do mês: {T('saldo')}. Nos últimos {T('meses_var')} meses o saldo "
             + ("caiu" if d["numeros"]["var_saldo"]["valor"] < 0 else "subiu") + f" em média {T('var_saldo_abs')} por mês.")
    L.append("- Se o saldo continuar nesse ritmo: " + "; ".join(f"{p['mes']}: {T('proj_' + str(p['k']))}" for p in d["projecao"]) + ".")
    if d["tem_receber"]:
        L.append(f"- A receber nos próximos 30 dias: {T('receber_30')}. Já vencido: {T('receber_vencido')}.")
    if d["tem_pagar"]:
        L.append(f"- A pagar nos próximos 30 dias: {T('pagar_30')}.")
    if "folga_30" in d["numeros"]:
        L.append(f"- Folga dos próximos 30 dias (saldo + a receber − a pagar): {T('folga_30')}. É um teto: só existe se o que está a receber entrar em dia, só conta as contas lançadas e não conta os vencidos.")
    if "split_giro" in d["numeros"]:
        L.append(f"- Reforma: em 2027 isso ainda é preparação. Quando o split payment chegar (ele vai entrar aos poucos), no cenário de {T('split_aliq')} e sem descontar créditos, até {T('split_giro')} de imposto deixam de passar pelo caixa antes do vencimento. Vale guardar essa reserva.")
    L.append("")
    L.append("## 4. Alertas")
    L += [f"- {a}" for a in d["alertas"]] or ["- Nenhum alerta neste mês."]
    L.append("")
    L.append("## 5. O que fazer este mês")
    for i, f in enumerate(d["fazer"], 1):
        L.append(f"{i}. {f}")
    L.append("")
    L.append("Como ler: a projeção do caixa repete a variação média do saldo dos últimos meses e não conta com venda nova nem corte; serve para enxergar a tendência.")
    L.append("")
    L.append(f"---\nOrigem de cada número: `dados.json`. Kit Painel do Empresário v{d['versao']} (INEMA, não oficial).")
    return "\n".join(L) + "\n"


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else pasta / "saida" / "painel"  # não apaga o dados.json do Diagnóstico
    hoje = dt.date.fromisoformat(argv[argv.index("--hoje") + 1]) if "--hoje" in argv else dt.date.today()
    try:
        d = painel(*carregar(pasta), hoje)
    except ErroDados as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    gravar(saida, d, "painel.md", painel_md(d))
    print(f"ok: {saida/'painel.md'} e {saida/'dados.json'} ({len(d['alertas'])} alertas)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
