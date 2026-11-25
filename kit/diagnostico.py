#!/usr/bin/env python3
"""Diagnóstico Reforma + Caixa — kit aberto do INEMA (não oficial).

Lê uma pasta com os dados que o contador já tem do cliente e gera:
  saida/dados.json          todos os números, cada um com a origem
  saida/relatorio-base.md   relatório de 2 páginas em linguagem de empresário

Uso:  python3 kit/diagnostico.py <pasta-do-cliente> [--saida <pasta>]

Arquivos da pasta (CSV com separador ; e vírgula decimal, como o Excel salva):
  empresa.json   obrigatório  dados e premissas da empresa
  mensal.csv     obrigatório  mes;receita;compras_com_credito;custo_direto;
                              despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim
  despesas.csv   opcional     mes;categoria;valor
  produtos.csv   opcional     item;preco;custo_direto;qtd_mes

Só lê e calcula. Não envia nada, não chama internet, não chama modelo de IA.
Tudo o que é 2027 sai marcado como SIMULADO: a alíquota da CBS ainda não é a definitiva.
"""
import csv
import json
import sys
from pathlib import Path

VERSAO = "1.0.0"

PADROES = {
    "cenarios_cbs_pct": [8.8, 11.3],      # alíquota de referência: 8,8% exemplo oficial da Receita; 11,3% TCU (28/10/2026)
    "ibs_2027_pct": 0.1,                  # 0,05% estadual + 0,05% municipal (art. 344 LC 214); a CBS de 2027 é a
                                          # referência − 0,1 p.p. (art. 347), então CBS + IBS = a própria referência
    "reducao_aliquota_pct": 0,            # 0, 30 ou 60 conforme a atividade (o contador confere)
    "prazo_medio_recebimento_dias": 0,
    "dia_vencimento_impostos": 25,        # do mês seguinte
    "vendas_para_empresas_pct": 0,
    "despesa_alerta_fator": 1.3,
    "despesa_alerta_minimo": 300.0,
    "margem_alvo_pct": 15.0,
}

CAMPOS_MENSAL = ["mes", "receita", "compras_com_credito", "custo_direto",
                 "despesas_operacionais", "pis_cofins_pago", "outros_impostos", "saldo_caixa_fim"]


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


def carregar(pasta):
    pasta = Path(pasta)
    emp_f = pasta / "empresa.json"
    men_f = pasta / "mensal.csv"
    if not emp_f.exists():
        raise ErroDados(f"falta {emp_f}")
    if not men_f.exists():
        raise ErroDados(f"falta {men_f}")
    empresa = {**PADROES, **json.loads(emp_f.read_text(encoding="utf-8"))}
    if empresa.get("regime") not in ("simples", "presumido", "real"):
        raise ErroDados("empresa.json: 'regime' deve ser simples, presumido ou real")
    mensal = []
    for i, r in enumerate(ler_csv(men_f), start=2):
        faltam = [c for c in CAMPOS_MENSAL if c not in r]
        if faltam:
            raise ErroDados(f"mensal.csv: faltam colunas {faltam}")
        linha = {"mes": r["mes"].strip(), "_linha": i}
        for c in CAMPOS_MENSAL[1:]:
            linha[c] = num(r[c], "mensal.csv", i, c)
        mensal.append(linha)
    if len(mensal) < 3:
        raise ErroDados("mensal.csv: precisa de pelo menos 3 meses")
    despesas = []
    if (pasta / "despesas.csv").exists():
        for i, r in enumerate(ler_csv(pasta / "despesas.csv"), start=2):
            despesas.append({"mes": r["mes"].strip(), "categoria": r["categoria"].strip(),
                             "valor": num(r["valor"], "despesas.csv", i, "valor"), "_linha": i})
    produtos = []
    if (pasta / "produtos.csv").exists():
        for i, r in enumerate(ler_csv(pasta / "produtos.csv"), start=2):
            produtos.append({"item": r["item"].strip(),
                             "preco": num(r["preco"], "produtos.csv", i, "preco"),
                             "custo_direto": num(r["custo_direto"], "produtos.csv", i, "custo_direto"),
                             "qtd_mes": num(r.get("qtd_mes", "0"), "produtos.csv", i, "qtd_mes"),
                             "_linha": i})
    return empresa, mensal, despesas, produtos


def diagnosticar(empresa, mensal, despesas, produtos):
    N = Numeros()
    n = len(mensal)
    periodo = f"mensal.csv, {mensal[0]['mes']} a {mensal[-1]['mes']} ({n} meses)"
    soma = lambda c: sum(m[c] for m in mensal)
    fator_ano = 12 / n  # anualiza quando há menos (ou mais) de 12 meses

    receita = soma("receita")
    custo = soma("custo_direto")
    desp = soma("despesas_operacionais")
    pis_cof = soma("pis_cofins_pago")
    outros = soma("outros_impostos")
    lucro = receita - custo - desp - pis_cof - outros
    margem = lucro / receita * 100 if receita else 0.0
    N.add("receita_periodo", receita, "brl", f"soma de receita em {periodo}")
    N.add("lucro_periodo", lucro, "brl", "receita − custo_direto − despesas_operacionais − pis_cofins_pago − outros_impostos")
    N.add("margem_pct", margem, "pct", "lucro_periodo ÷ receita_periodo")
    N.add("meses", n, "int", periodo)

    # margem dos 3 últimos meses x anteriores
    ult = mensal[-3:]
    ant = mensal[:-3]
    def marg(ms):
        r = sum(m["receita"] for m in ms)
        l = sum(m["receita"] - m["custo_direto"] - m["despesas_operacionais"] - m["pis_cofins_pago"] - m["outros_impostos"] for m in ms)
        return l / r * 100 if r else 0.0
    N.add("margem_ult3_pct", marg(ult), "pct", "margem dos 3 últimos meses de mensal.csv")
    if ant:
        N.add("margem_antes_pct", marg(ant), "pct", "margem dos meses anteriores aos 3 últimos")

    # ---------- caixa ----------
    saldo_final = mensal[-1]["saldo_caixa_fim"]
    saidas_medias = (custo + desp + pis_cof + outros) / n
    meses_folego = saldo_final / saidas_medias if saidas_medias else 0.0
    N.add("saldo_final", saldo_final, "brl", f"saldo_caixa_fim de {mensal[-1]['mes']} (mensal.csv linha {mensal[-1]['_linha']})")
    N.add("saidas_medias_mes", saidas_medias, "brl", "média mensal de custo_direto + despesas_operacionais + impostos")
    N.add("meses_folego", round(meses_folego, 1), "int", "saldo_final ÷ saidas_medias_mes")
    N.itens["meses_folego"]["texto"] = f"{meses_folego:.1f}".replace(".", ",")
    meses_aperto = [m["mes"] for m in mensal if m["saldo_caixa_fim"] < saidas_medias * 0.5]

    # ---------- Reforma ----------
    reforma = {"regime": empresa["regime"], "simulado": True, "cenarios": []}
    pior = None
    red = empresa["reducao_aliquota_pct"] / 100
    ibs = empresa["ibs_2027_pct"]
    compras = soma("compras_com_credito")
    N.add("compras_credito_ano", compras * fator_ano, "brl", f"compras_com_credito de {periodo}, anualizado (× 12 ÷ {n})")
    N.add("pis_cofins_ano", pis_cof * fator_ano, "brl", f"pis_cofins_pago de {periodo}, anualizado (× 12 ÷ {n})")
    if empresa["regime"] in ("presumido", "real"):
        N.add("ibs_pct", ibs, "pct", "IBS de 2027 (art. 344 LC 214: 0,05% estadual + 0,05% municipal)")
        N.itens["ibs_pp"] = {"valor": ibs, "texto": f"{ibs:.1f}".replace(".", ","), "origem": "redução da CBS em 2027, em pontos percentuais (art. 347 LC 214)"}
        for aliq in empresa["cenarios_cbs_pct"]:
            total_pct = aliq * (1 - red)  # (referência − 0,1 de CBS) + 0,1 de IBS
            debito = receita * total_pct / 100
            credito = compras * total_pct / 100
            novo_ano = (debito - credito) * fator_ano
            dif = novo_ano - pis_cof * fator_ano
            k = str(aliq).replace(".", "_")
            N.add(f"cbs_{k}_aliq", aliq, "pct", "cenário de alíquota da CBS (empresa.json)")
            N.add(f"cbs_{k}_imposto_ano", novo_ano, "brl",
                  f"(receita − compras_com_credito) × ({pct(aliq - ibs, 2)} CBS + {pct(ibs)} IBS = {pct(aliq)}) × (1 − {pct(red*100,0)} de redução), anualizado")
            N.add(f"cbs_{k}_diferenca_ano", dif, "brl", f"cbs_{k}_imposto_ano − pis_cofins_ano")
            c = {"aliq": aliq, "imposto_ano": novo_ano, "diferenca_ano": dif, "chave": k}
            reforma["cenarios"].append(c)
            if pior is None or dif > pior["diferenca_ano"]:
                pior = c
        reforma["pior"] = pior
        # split payment: dinheiro do imposto que hoje passa pelo caixa
        venda_media = receita / n
        imposto_bruto_mes = venda_media * pior["aliq"] * (1 - red) / 100
        dias = max(0, 15 + empresa["dia_vencimento_impostos"] - empresa["prazo_medio_recebimento_dias"])
        giro = imposto_bruto_mes * dias / 30
        N.add("split_dias", dias, "int",
              f"venda no meio do mês, recebida em {empresa['prazo_medio_recebimento_dias']} dias, imposto vence dia {empresa['dia_vencimento_impostos']} do mês seguinte")
        N.add("split_imposto_bruto_mes", imposto_bruto_mes, "brl", f"receita média × {pct(pior['aliq'])} (CBS + IBS) × (1 − redução)")
        N.add("split_giro", giro, "brl", "split_imposto_bruto_mes × split_dias ÷ 30 (estimativa máxima, sem descontar créditos)")
        if saldo_final > 0:
            N.add("split_giro_pct_saldo", giro / saldo_final * 100, "pct", "split_giro ÷ saldo_final")
        reforma["split_giro"] = giro
    reforma["b2b"] = empresa["vendas_para_empresas_pct"]
    N.add("vendas_empresas_pct", float(empresa["vendas_para_empresas_pct"]), "pct", "empresa.json (vendas_para_empresas_pct)")

    # ---------- despesas fora do padrão ----------
    fora = []
    if despesas:
        meses_ord = []
        for d in despesas:
            if d["mes"] not in meses_ord:
                meses_ord.append(d["mes"])
        ultimo = meses_ord[-1]
        cats = sorted({d["categoria"] for d in despesas})
        for cat in cats:
            atual = sum(d["valor"] for d in despesas if d["categoria"] == cat and d["mes"] == ultimo)
            prev = [sum(d["valor"] for d in despesas if d["categoria"] == cat and d["mes"] == m) for m in meses_ord[:-1]]
            prev = [p for p in prev]
            if not prev:
                continue
            media = sum(prev) / len(prev)
            if media > 0 and atual > media * empresa["despesa_alerta_fator"] and atual - media >= empresa["despesa_alerta_minimo"]:
                i = len(fora)
                N.add(f"desp_{i}_atual", atual, "brl", f"despesas.csv, {cat} em {ultimo}")
                N.add(f"desp_{i}_media", media, "brl", f"despesas.csv, média de {cat} nos {len(prev)} meses anteriores")
                N.add(f"desp_{i}_acima", atual - media, "brl", f"desp_{i}_atual − desp_{i}_media")
                fora.append({"categoria": cat, "mes": ultimo, "atual": atual, "media": media, "acima": atual - media, "i": i})
        fora.sort(key=lambda x: -x["acima"])

    # ---------- produtos e preço ----------
    # Mesma regra de crédito da empresa: só a parte do custo que é compra com crédito
    # (compras_com_credito ÷ custo_direto do período). Folha e MEI/Simples não dão crédito cheio.
    itens_baixos = []
    fc = min(1.0, compras / custo) if custo else 0.0
    if produtos:
        alvo = empresa["margem_alvo_pct"]
        imp_hoje = pis_cof / receita if receita else 0.0  # PIS/Cofins efetivo sobre a receita
        regular = empresa["regime"] in ("presumido", "real") and pior
        t = pior["aliq"] * (1 - red) / 100 if regular else 0.0
        if regular:
            N.add("fator_credito_pct", fc * 100, "pct", "compras_com_credito ÷ custo_direto (parte do custo que gera crédito)")
        for j, p in enumerate(produtos):
            P, c = p["preco"], p["custo_direto"]
            if P <= 0:
                continue
            m_hoje = (P - c - P * imp_hoje) / P * 100
            m_2027 = (P - c - (P - c * fc) * t) / P * 100 if regular else m_hoje
            N.add(f"prod_{j}_margem_hoje", m_hoje, "pct", f"produtos.csv linha {p['_linha']}: (preço − custo − PIS/Cofins efetivo) ÷ preço")
            N.add(f"prod_{j}_margem_2027", m_2027, "pct",
                  f"produtos.csv linha {p['_linha']}: (preço − custo − (preço − custo × fator_credito) × alíquota do pior cenário) ÷ preço")
            if m_2027 < alvo:
                denom = (1 - t) - alvo / 100
                preco_min = c * (1 - fc * t) / denom if denom > 0 else 0.0
                N.add(f"prod_{j}_preco_min", preco_min, "brl", f"preço que devolve a margem-alvo de {pct(alvo,0)} no pior cenário")
                itens_baixos.append({"item": p["item"], "j": j, "m_hoje": m_hoje, "m_2027": m_2027,
                                     "preco": P, "preco_min": preco_min, "qtd": p["qtd_mes"]})
        N.add("margem_alvo", alvo, "pct", "empresa.json (margem_alvo_pct)")
        itens_baixos.sort(key=lambda x: x["m_2027"])

    # ---------- prioridades (ordenadas pelo valor em R$ por ano) ----------
    cand = []
    if empresa["regime"] in ("presumido", "real") and pior and pior["diferenca_ano"] > 0:
        cand.append({"valor": pior["diferenca_ano"], "chave": f"cbs_{pior['chave']}_diferenca_ano", "servico": "Reforma Tributária Pronta",
                     "texto": "Rever regime, créditos, cadastros e preços antes de 2027: no pior cenário, o que você recolhe de CBS/IBS fica {v} por ano acima do PIS/Cofins de hoje."})
    if empresa["regime"] in ("presumido", "real") and reforma.get("split_giro", 0) > 0:
        cand.append({"valor": reforma["split_giro"], "chave": "split_giro", "servico": "Painel do Empresário",
                     "texto": "Preparar o caixa para o split payment, que vai chegar aos poucos: até {v} de imposto deixam de passar pelo seu caixa antes do vencimento."})
    if fora:
        f0 = fora[0]
        cand.append({"valor": f0["acima"] * 12, "chave": f"desp_{f0['i']}_acima", "servico": "Painel do Empresário",
                     "texto": f"Olhar a despesa de {f0['categoria']}: em {f0['mes']} ficou {{v}} acima da média."})
    if itens_baixos:
        b = itens_baixos[0]
        perda = max(0.0, (b["preco_min"] - b["preco"]) * b["qtd"] * 12)
        cand.append({"valor": perda, "chave": f"prod_{b['j']}_preco_min", "servico": "Preço certo na Reforma",
                     "texto": f"Rever o preço de {b['item']}: para manter a margem-alvo, o preço mínimo é {{v}}."})
    if empresa["regime"] == "simples" and empresa["vendas_para_empresas_pct"] >= 50:
        cand.append({"valor": 0, "chave": "vendas_empresas_pct", "servico": "Reforma Tributária Pronta",
                     "texto": "Avaliar com o contador se vale recolher CBS/IBS fora do DAS (a opção é semestral, feita em setembro e março): {v} das vendas são para empresas, que vão querer crédito cheio."})
    if meses_aperto:
        cand.append({"valor": 0, "chave": "saidas_medias_mes", "servico": "Painel do Empresário",
                     "texto": "Montar a previsão de caixa: em " + ", ".join(meses_aperto) + " o saldo ficou abaixo de meio mês de saídas (saídas médias de {v} por mês)."})
    cand.sort(key=lambda c: -c["valor"])
    # sempre 3 prioridades: completa com as de acompanhamento, que valem para todo cliente
    extras = [{"valor": -1, "chave": "margem_pct", "servico": "Painel do Empresário",
               "texto": "Acompanhar a margem todo mês, numa conversa curta: no período ela foi {v}."},
              {"valor": -2, "chave": "saidas_medias_mes", "servico": "Painel do Empresário",
               "texto": "Montar a previsão de caixa dos próximos 3 meses, com as saídas médias de {v} por mês."},
              {"valor": -3, "chave": "meses", "servico": "Reforma Tributária Pronta",
               "texto": "Refazer este diagnóstico quando o Senado fixar a alíquota de referência da CBS (período analisado: {v} meses)."}]
    usadas = {c["chave"] for c in cand}
    for e in extras:
        if len(cand) >= 3:
            break
        if e["chave"] not in usadas:
            cand.append(e)
            usadas.add(e["chave"])
    prioridades = []
    for c in cand[:3]:
        prioridades.append({"texto": c["texto"].format(v=N.itens[c["chave"]]["texto"]), "servico": c["servico"], "chave": c["chave"]})

    return {"versao": VERSAO, "empresa": {k: empresa[k] for k in ("nome", "regime", "atividade") if k in empresa},
            "premissas": {k: empresa[k] for k in PADROES}, "numeros": N.itens, "reforma": reforma,
            "despesas_fora": fora, "itens_margem_baixa": itens_baixos, "meses_aperto": meses_aperto,
            "prioridades": prioridades}


def relatorio(d):
    T = lambda k: d["numeros"][k]["texto"]
    e = d["empresa"]
    L = []
    L.append(f"# Diagnóstico Reforma + Caixa — {e.get('nome', 'Empresa')}")
    L.append("")
    L.append(f"Período analisado: {T('meses')} meses. Regime: {e['regime']}. "
             "Números de 2027 = **SIMULADO** (a alíquota da CBS ainda não é a definitiva). "
             "Preparado pelo seu contador com o kit aberto do INEMA; não substitui a análise técnica dele.")
    L.append("")
    L.append("## 1. Quanto sobra")
    L.append(f"- Você vendeu {T('receita_periodo')} e sobrou {T('lucro_periodo')} depois de custos, despesas e impostos: margem de {T('margem_pct')}.")
    if "margem_antes_pct" in d["numeros"]:
        L.append(f"- Nos 3 últimos meses a margem foi {T('margem_ult3_pct')}; antes, {T('margem_antes_pct')}.")
    L.append("")
    L.append("## 2. Seu caixa")
    L.append(f"- Saldo no fim do período: {T('saldo_final')}. Suas saídas médias são {T('saidas_medias_mes')} por mês: o caixa cobre {T('meses_folego')} mês(es) de saídas.")
    if d["meses_aperto"]:
        L.append(f"- Meses de aperto (saldo abaixo de meio mês de saídas): {', '.join(d['meses_aperto'])}.")
    L.append("")
    L.append("## 3. Reforma Tributária em 2027 (SIMULADO)")
    r = d["reforma"]
    if r["regime"] in ("presumido", "real"):
        L.append(f"- Hoje você paga {T('pis_cofins_ano')} por ano de PIS/Cofins. Em 2027 a CBS substitui os dois.")
        for c in r["cenarios"]:
            k = c["chave"]
            sinal = "a mais" if c["diferenca_ano"] > 0 else "a menos"
            L.append(f"- Com alíquota de referência de {T(f'cbs_{k}_aliq')}: você recolheria {T(f'cbs_{k}_imposto_ano')} por ano de CBS + IBS, {d['numeros'][f'cbs_{k}_diferenca_ano']['texto'].replace('-', '')} {sinal} que hoje (valor máximo: base simplificada).")
        if r.get("b2b", 0) >= 50:
            L.append(f"- {T('vendas_empresas_pct')} das suas vendas são para empresas. Elas poderão usar a CBS/IBS que você destaca como crédito, então parte desse valor pode ir no preço sem pesar para elas. O contador avalia o repasse.")
        L.append(f"- Premissas: em 2027 a CBS é a alíquota de referência menos {T('ibs_pp')} ponto percentual e o IBS é {T('ibs_pct')}, então CBS + IBS somam a própria referência. Base = receita informada (simplificação). Crédito só sobre as compras com crédito informadas ({T('compras_credito_ano')} por ano); fornecedor do Simples gera crédito limitado ao que ele paga no Simples. Atividade com redução de alíquota: o contador informa em empresa.json.")
        L.append(f"- **Split payment:** a implantação é gradual e ainda depende de ato do Comitê Gestor e da Receita. Quando valer para você, o imposto sai na hora do pagamento. Hoje até {T('split_giro')} ficam no seu caixa até o vencimento"
                 + (f" ({T('split_giro_pct_saldo')} do saldo atual)." if "split_giro_pct_saldo" in d["numeros"] else "."))
    else:
        L.append("- No Simples Nacional, a CBS e o IBS ficam dentro do DAS; este diagnóstico não prevê mudança no valor do DAS em 2027.")
        L.append(f"- Ponto de atenção: {T('vendas_empresas_pct')} das suas vendas são para empresas. Quem compra de você só aproveita como crédito o imposto que você paga no DAS.")
    L.append("")
    L.append("## 4. O que chamou a atenção")
    if d["despesas_fora"]:
        for f in d["despesas_fora"][:3]:
            i = f["i"]
            L.append(f"- {f['categoria']}: {T(f'desp_{i}_atual')} em {f['mes']}, contra média de {T(f'desp_{i}_media')}.")
    if d["itens_margem_baixa"]:
        for b in d["itens_margem_baixa"][:3]:
            j = b["j"]
            L.append(f"- {b['item']}: margem depois do custo e do PIS/Cofins de {T(f'prod_{j}_margem_hoje')} hoje e {T(f'prod_{j}_margem_2027')} em 2027 no pior cenário; preço mínimo para margem de {T('margem_alvo')}: {T(f'prod_{j}_preco_min')}.")
    if not d["despesas_fora"] and not d["itens_margem_baixa"]:
        L.append("- Nenhuma despesa fora do padrão nem item com margem baixa nos dados enviados.")
    L.append("")
    L.append("## 5. Suas 3 prioridades")
    for i, p in enumerate(d["prioridades"], 1):
        L.append(f"{i}. {p['texto']} *(serviço: {p['servico']})*")
    if not d["prioridades"]:
        L.append("1. Nenhuma prioridade urgente nos dados enviados: manter o acompanhamento mensal.")
    L.append("")
    L.append("## Pauta da reunião (30 min)")
    L.append("1. Confirmar os números acima (5 min).")
    L.append("2. Decidir a prioridade 1 e quem faz (10 min).")
    L.append("3. Combinar o que o contador vai acompanhar todo mês (10 min).")
    L.append("4. Próxima conversa: depois que o Senado fixar a alíquota da CBS (5 min).")
    L.append("")
    L.append(f"---\nPremissas e origem de cada número: `dados.json`. Kit Diagnóstico Reforma + Caixa v{d['versao']} (INEMA, não oficial).")
    return "\n".join(L) + "\n"


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else pasta / "saida"
    try:
        d = diagnosticar(*carregar(pasta))
    except ErroDados as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "dados.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    (saida / "relatorio-base.md").write_text(relatorio(d), encoding="utf-8")
    print(f"ok: {saida/'relatorio-base.md'} e {saida/'dados.json'} ({len(d['numeros'])} números, {len(d['prioridades'])} prioridades)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
