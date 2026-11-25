# contabilidade2027 — Reform + Cash Diagnostic and 3 more kits for accountants

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Diagnóstico Reforma + Caixa](guia/assets/banner-en.jpg)](https://inematds.github.io/contabilidade2027/guia/en/)

## What it is

Your client is going to ask how much the Tax Reform will weigh on their cash flow in 2027. This free kit helps the accountant answer with the client's own numbers. You put what you already have in a folder (the monthly summary of revenue, costs, taxes, and balance and, if you want, expenses and prices) and your AI builds a 2-page report for the business owner: how much is left over, how the cash flow looks, how much they would pay in CBS/IBS in 2027 under two rate scenarios, the effect of split payment, what stood out, and 3 priorities. A checker makes sure every number in the report came from the data. In the same client folder, 3 more kits run: **Reforma Tributária Pronta** (what's missing in the registry, the system, and the contracts), **Preço certo na Reforma** (minimum price and target price per product), and **Painel do Empresário** (the month-end close in plain text). It is an INEMA kit, unofficial, and does not replace the accountant's technical analysis.

## The 4 kits (the same client folder works for all of them)

| Kit | What it delivers | Program | Guide |
|---|---|---|---|
| 1. Diagnóstico Reforma + Caixa | 2-page report: cash, margin, 2027 CBS/IBS, split payment, 3 priorities | `kit/diagnostico.py` | [guide](https://inematds.github.io/contabilidade2027/guia/en/) |
| 2. Reforma Tributária Pronta | Plan per CNPJ: registry issues (NCM/NBS, CST, cClassTrib), suppliers and credit, checklist and deadlines | `kit/reforma_pronta.py` | [guide](https://inematds.github.io/contabilidade2027/guia/en/reforma-pronta/) |
| 3. Preço certo na Reforma | Per item: margin today and in 2027, minimum price, target price, and maximum discount | `kit/preco_certo.py` | [guide](https://inematds.github.io/contabilidade2027/guia/en/preco-certo/) |
| 4. Painel do Empresário | Month-end close in plain text: result, comparisons, 3-month cash flow, accounts, alerts, and what to do | `kit/painel.py` | [guide](https://inematds.github.io/contabilidade2027/guia/en/painel/) |

## 📖 User guide

Full guide: **https://inematds.github.io/contabilidade2027/guia/en/**

<!-- VIDEO: entra o explicavideo do projeto quando publicado -->

## Ask your AI

Open Claude Code or Codex in a folder on your computer and paste the request for the kit you want, from [`kit/PEDIDO.md`](kit/PEDIDO.md) (one per kit). It tells the AI to run the example, set up your client's folder, generate the report, rewrite it in plain language without touching the numbers, and check it. Nothing is sent to anyone: you review it and talk to the client.

## What the report includes

1. **How much is left over:** revenue, profit, and margin for the period, and the margin of the last 3 months compared with the previous ones.
2. **Your cash flow:** balance, average outflows, how many months of outflows the cash covers, and the tight months.
3. **Reform in 2027 (SIMULATED):** today's PIS/Cofins × CBS/IBS in two scenarios (8.8% from the Receita's official example and 11.3% from the TCU's recommendation), the note for those who sell to businesses, and how much tax no longer passes through the cash flow with split payment. Under Simples, the warning about credit for business customers.
4. **What stood out:** expense above average and an item with a margin below target, with the minimum price.
5. **3 priorities**, ordered by value in R$, each tied to a service the accountant can offer, plus a 30-minute meeting agenda.

Ready-made examples: [`kit/exemplos/agencia/saida-exemplo/relatorio-base.md`](kit/exemplos/agencia/saida-exemplo/relatorio-base.md) (Lucro Presumido) and [`kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md`](kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md) (Simples). All data is fictitious.

---

## Technical installation

All you need is **Python 3.9+**, with no extra libraries. It uses no internet and no AI model: the script only reads and calculates.

```bash
git clone https://github.com/inematds/contabilidade2027 && cd contabilidade2027
# ou baixe o ZIP: https://github.com/inematds/contabilidade2027/archive/refs/heads/main.zip

python3 kit/diagnostico.py kit/exemplos/agencia            # gera kit/exemplos/agencia/saida/
python3 kit/conferir.py kit/exemplos/agencia/saida/relatorio-base.md kit/exemplos/agencia/saida/dados.json
python3 -m unittest discover -s tests                        # 15 testes
```

### The client folder

Copy `kit/modelo/` and fill it in. CSV with `;` separator and decimal comma, as Excel saves it in Portuguese.

| File | Required | Columns |
|---|---|---|
| `empresa.json` | yes | `nome`, `regime` (`simples`, `presumido` or `real`), `atividade`, `reducao_aliquota_pct` (0, 30 or 60), `cenarios_cbs_pct`, `ibs_2027_pct`, `prazo_medio_recebimento_dias`, `dia_vencimento_impostos`, `vendas_para_empresas_pct`, `margem_alvo_pct`; optional: `aliquota_simples_pct` (Simples, kit 3), `outros_impostos_pct` and `rateio_fixas_pct` (kits 1 and 3) |
| `mensal.csv` | yes (3+ months) | `mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim` |
| `despesas.csv` | no | `mes;categoria;valor` (the last month is compared with the average of the previous ones) |
| `produtos.csv` | no | `item;preco;custo_direto;qtd_mes` |

`compras_com_credito` is the portion of purchases that will generate CBS/IBS credit (inputs and services from suppliers in the regular regime). Payroll is not included.

### How the calculation is done (assumptions)

- **2027 CBS/IBS (regular regime):** `(receita − compras_com_credito) × reference rate × (1 − reduction)`, annualized, compared with the PIS/Cofins paid. In 2027, CBS is the reference minus 0.1 point (LC 214, art. 347) and IBS is 0.05% state plus 0.05% municipal (art. 344), so the two together add up to the reference itself. This is a simplification: the base is the revenue reported, with no adjustment for other taxes (LC 214, art. 12, removes CBS/IBS itself and IPI from the base).
- **Credit:** only on what you report in `compras_com_credito`. A purchase from a Simples supplier generates credit limited to what that supplier pays under Simples. Adjust the column.
- **Product:** uses the same credit rule as the company. The portion of the cost that generates credit is `compras_com_credito ÷ custo_direto` for the period. The minimum price returns the `margem_alvo_pct` in the worst scenario.
- **Split payment:** `average revenue × worst-scenario rate × days ÷ 30`, with the sale in the middle of the month, receipt at `prazo_medio_recebimento_dias`, and due date on day `dia_vencimento_impostos` of the following month. It is a maximum estimate, with no credits deducted. Implementation is gradual and depends on a joint act of the Management Committee and the Receita (LC 214, art. 35).
- **Simples:** does not simulate a change in the DAS. It warns when most sales are to businesses. The option to pay CBS/IBS outside the DAS is semiannual, made in September and March (LC 123, art. 13, §§ 9–10, as worded by LC 227/2026).
- **Everything for 2027 is marked SIMULATED.** The CBS reference rate is set by the Senate (deadline 12/15/2026). Redo it when it is published.

### Kit 2 — Reforma Tributária Pronta

```bash
python3 kit/reforma_pronta.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/reforma-pronta/plano.md, pendencias.csv e dados.json
```

Additional files in the client folder (templates in `kit/modelo/`):

| File | Required | Columns |
|---|---|---|
| `itens.csv` | yes | `item;tipo;codigo;cst;cclasstrib;reducao_pct;vendas_ano`. The `tipo` is `produto` (NCM code, 8 digits) or `servico` (NBS code, 9 digits) |
| `fornecedores.csv` | no | `fornecedor;regime;compras_ano`. The `regime` is `regular`, `simples` or `mei` |
| `prontidao.json` | no | `erp_atualizado`, `nota_teste`, `cadastro_revisado`, `contratos_revisados`, `precos_revisados`, `equipe_treinada`: `true`, `false` or `null` (don't know) |

What it checks:
- Code format: NCM with 8 digits, NBS with 9, CST with 3, cClassTrib with 6.
- Whether the cClassTrib starts with the CST. In the official examples from the Receita's open calculator, 000 comes with 000001 and 200 with 200xxx; here it is only "check", not an error.
- Reduction against the CST: reduction with CST 000 (full taxation), CST 200 (reduced rate) with no reduction, reduction with no cClassTrib. A reduction other than 30/60/100% becomes "check".
- The items that add up to 80% of sales.
- The share of purchases from Simples or MEI suppliers, which generate credit limited to what the supplier pays under Simples (LC 214, art. 47).
- Under Simples, the next window for the option to pay CBS/IBS outside the DAS (September and March; LC 123, art. 13, § 10).

It does **not** say whether the code is the right one for the item: that is up to the accountant, using the official table or the [Receita's engine](https://github.com/inematds/calculadora-da-reforma).

### Kit 3 — Preço certo na Reforma

```bash
python3 kit/preco_certo.py kit/exemplos/agencia        # gera saida/preco-certo/precos.md, precos.csv e dados.json
```

Uses `empresa.json`, `mensal.csv`, and `produtos.csv`. The `produtos.csv` accepts these optional columns:
- `custo_com_credito`: R$ of the item's cost that generates credit. Without it, the kit uses the same ratio as the company, `compras_com_credito ÷ custo_direto`.
- `comissao_pct` and `taxa_pct`: card, marketplace, and gateway.

Under Simples, `empresa.json` needs `aliquota_simples_pct` (the effective DAS rate, from the PGDAS-D).

How it calculates (markup method, the same calculation as the Diagnóstico, in `kit/comum.py`):
- The price covers the cost, the commission and fee, the other taxes on the sale, and the allocation of fixed expenses.
  - The other taxes (ISS/ICMS, IR/CSLL under Presumido) are `outros_impostos ÷ receita` from `mensal.csv`, or `outros_impostos_pct` in `empresa.json`. Under Simples they are zero, because the DAS already combines them.
  - The allocation of fixed expenses is `despesas_operacionais ÷ receita`, or `rateio_fixas_pct`.
- The consumption tax is the effective PIS/Cofins today and, in 2027, `(price − cost with credit) × reference rate × (1 − reduction)`. Under Simples, it is the DAS rate.
- Margin = profit per sale ÷ price. Minimum price = break-even (zero profit). Target price = `margem_alvo_pct`. Maximum discount = how much today's price can drop without leaving the target margin.
- Simplifications:
  - the tax is treated as part of the reported price (conservative, because CBS/IBS is "on top");
  - under Lucro Real, IR/CSLL enters as a fraction of revenue;
  - allocation by revenue weighs more on high-cost items.
- The main scenario is the higher one (11.3%). The target price matches the Diagnóstico's, and a test guarantees it.

### Kit 4 — Painel do Empresário

```bash
python3 kit/painel.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/painel/painel.md e dados.json
```

The panel's month is the last one in `mensal.csv`. Optional files (templates in `kit/modelo/`):
- `contas_receber.csv`: `cliente;valor;vencimento`
- `contas_pagar.csv`: `fornecedor;valor;vencimento`

The due date can be AAAA-MM-DD or DD/MM/AAAA.

What the panel includes:
- **Result:** managerial income statement for the month, with variation against the previous month and against the average.
- **Projection:** 3 months, based on the actual average change in `saldo_caixa_fim` (profit is not cash: withdrawals, installments, and investments are left out of the income statement). There is an alert when average profit is positive and the balance falls.
- **Accounts:** receivable and payable in the next 30 days, overdue ones, and days late.
- **Alerts:**
  - margin 3 points below average;
  - out-of-pattern expense;
  - overdue items;
  - cash covering less than half a month;
  - negative projection;
  - negative slack.
- **Split payment reserve:** always shown, under Presumido and Real. It is the same calculation as the Diagnóstico.

### The checker

`kit/conferir.py relatorio.md dados.json` exits with code 1 if the text has:
- an R$ value, %, or number with a decimal comma that is not in `dados.json`;
- rounding in words ("62 mil");
- an invented number of days or months.

It serves the step where the AI rewrites the report in plain language.

### The tests

`tests/test_kit.py` (15, kit 1) covers:
- the hand-checked calculation in the agency example (CBS, PIS/Cofins, split, expense, minimum price);
- Simples;
- Lucro Real with credit;
- the 60% reduction;
- the checker catching an invented number, a rounded number, and an assumption used as a number;
- input errors and the command line.

`tests/test_reforma_pronta.py` (11, kit 2) covers:
- the count of the agency's issues and the sales at risk;
- the items that add up to 80% of sales;
- the Simples suppliers;
- priority 1;
- each format rule;
- the Simples window on 3 dates;
- input errors and the command line.

`tests/test_reforma_pronta.py` (12, kit 2), `tests/test_preco_certo.py` (10, kit 3), and `tests/test_painel.py` (11, kit 4) check the calculations by hand on the two examples, consistency with the Diagnóstico, and input errors. Total: 48 tests.

## The process, from start to finish

1. 🧠 The accountant opens Claude Code or Codex and pastes the request from `kit/PEDIDO.md`.
2. ⚙️ `python3 kit/diagnostico.py kit/exemplos/agencia`: the example, to see the format.
3. 🧠 Sets up the client folder from `kit/modelo/`, with the data they already have.
4. ⚙️ `python3 kit/diagnostico.py <pasta-do-cliente>` → `saida/relatorio-base.md` + `saida/dados.json`.
5. 🧠 The AI rewrites it in `relatorio.md`, in plain language, without touching the numbers.
6. ⚙️ `python3 kit/conferir.py relatorio.md saida/dados.json`: it must output `ok`.
7. 🧠 The accountant reviews the assumptions and takes the report to the meeting with the client.
8. ⚙️ Kit 2: `python3 kit/reforma_pronta.py <pasta-do-cliente>` → `saida/reforma-pronta/` (plano.md, pendencias.csv). The folder must have `itens.csv`.
9. ⚙️ Kit 3: `python3 kit/preco_certo.py <pasta-do-cliente>` → `saida/preco-certo/` (precos.md, precos.csv).
10. ⚙️ Kit 4, every month: add the month to `mensal.csv` (and the accounts, if any) → `python3 kit/painel.py <pasta-do-cliente>` → `saida/painel/painel.md`.
11. ⚙️ `python3 -m unittest discover -s tests`: before changing the code.

## Basis

- Scenario rates: [kit calculadora-da-reforma](https://github.com/inematds/calculadora-da-reforma) (official Receita example with CBS at 8.8%) and [TCU, 10/28/2026](https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo) (reference rate of 11.3%; the Senate sets it by 12/15).
- 2027 rules: [LC 214/2025, text at the Senate](https://legis.senado.leg.br/norma/40180341/publicacao/40181429) (arts. 12, 35, 47, 344 and 347) and [LC 227/2026, updated text at the Chamber](https://www2.camara.leg.br/legin/fed/leicom/2026/leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html) (Simples option). Checked on 11/24/2026.
- To check the calculation item by item in the Receita's official engine, use the calculadora-da-reforma engine test.

MIT License. INEMA kit, unofficial. Does not replace the accountant's technical analysis. Free at inema.club, straight on the internet.
