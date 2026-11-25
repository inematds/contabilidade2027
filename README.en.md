# Tax Reform + Cash Flow Diagnosis

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Tax Reform + Cash Flow Diagnosis](guia/assets/banner-en.jpg)](https://inematds.github.io/contabilidade2027/guia/en/)

## What it is

Your client will ask how much the Tax Reform will affect their cash flow in 2027. This free kit helps accountants answer with the client’s own numbers. Put what you already have in a folder (the monthly summary of revenue, costs, taxes, and balance and, if you want, expenses and prices), and your AI will create a 2-page report for the business owner: how much is left over, the state of their cash flow, how much they would pay in CBS/IBS in 2027 under two tax rate scenarios, the effect of split payment, what stood out, and 3 priorities. A checker ensures every number in the report came from the data. This is an INEMA kit, not an official resource, and it does not replace the accountant’s technical analysis.

## 📖 User guide

Full guide: **https://inematds.github.io/contabilidade2027/guia/en/**

<!-- VIDEO: entra o explicavideo do projeto quando publicado -->

## Ask your AI

Open Claude Code or Codex in a folder on your computer and paste the request from [`kit/PEDIDO.md`](kit/PEDIDO.md). It tells the AI to run the example, create your client’s folder, generate the report, rewrite it in plain language without changing the numbers, and check it. Nothing is sent to anyone: you review it and talk with the client.

## What the report includes

1. **How much is left over:** revenue, profit, and margin for the period, and the margin for the last 3 months compared with the previous months.
2. **Your cash flow:** balance, average outflows, how many months of outflows the cash balance covers, and the tight months.
3. **Tax Reform in 2027 (SIMULATED):** today’s PIS/Cofins × CBS/IBS under two scenarios (8,8% from the official Receita example and 11,3% from the TCU recommendation), a note for those who sell to businesses, and how much tax no longer passes through cash flow with split payment. For Simples, a notice about tax credits for business customers.
4. **What stood out:** an expense above average and an item with a margin below target, with the minimum price.
5. **3 priorities**, ordered by value in R$, each tied to a service the accountant can offer, plus a 30-minute meeting agenda.

Ready-made examples: [`kit/exemplos/agencia/saida-exemplo/relatorio-base.md`](kit/exemplos/agencia/saida-exemplo/relatorio-base.md) (Lucro Presumido) and [`kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md`](kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md) (Simples). All data is fictional.

---

## Technical installation

Requires only **Python 3.9+**, with no extra libraries. It does not use the internet or an AI model: the script only reads and calculates.

```bash
git clone https://github.com/inematds/contabilidade2027 && cd contabilidade2027
# or download the ZIP: https://github.com/inematds/contabilidade2027/archive/refs/heads/main.zip

python3 kit/diagnostico.py kit/exemplos/agencia            # generates kit/exemplos/agencia/saida/
python3 kit/conferir.py kit/exemplos/agencia/saida/relatorio-base.md kit/exemplos/agencia/saida/dados.json
python3 -m unittest discover -s tests                        # 15 tests
```

### The client’s folder

Copy `kit/modelo/` and fill it in. CSV files use `;` as the separator and a comma as the decimal mark, as Excel saves them in Portuguese.

| File | Required | Columns |
|---|---|---|
| `empresa.json` | yes | `nome`, `regime` (`simples`, `presumido` or `real`), `atividade`, `reducao_aliquota_pct` (0, 30 or 60), `cenarios_cbs_pct`, `ibs_2027_pct`, `prazo_medio_recebimento_dias`, `dia_vencimento_impostos`, `vendas_para_empresas_pct`, `margem_alvo_pct` |
| `mensal.csv` | yes (3+ months) | `mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim` |
| `despesas.csv` | no | `mes;categoria;valor` (the last month is compared with the average of the previous months) |
| `produtos.csv` | no | `item;preco;custo_direto;qtd_mes` |

`compras_com_credito` is the portion of purchases that will generate CBS/IBS credits (inputs and services from suppliers under the regular regime). Payroll is not included.

### How the calculation works (assumptions)

- **2027 CBS/IBS (regular regime):** `(revenue − compras_com_credito) × reference tax rate × (1 − reduction)`, annualized and compared with the PIS/Cofins paid. In 2027, CBS is the reference minus 0,1 percentage point (LC 214, art. 347) and IBS is 0,05% state + 0,05% municipal (art. 344), so the two add up to the reference itself. This is a simplification: the tax base is the reported revenue, with no adjustment for other taxes (LC 214, art. 12, excludes CBS/IBS and IPI from the base).
- **Credit:** only on what you report in `compras_com_credito`. Purchases from a Simples supplier generate credits limited to what that supplier pays under Simples. Adjust the column.
- **Product:** uses the same credit rule as the company. The portion of the cost that generates credit is `compras_com_credito ÷ custo_direto` for the period. The minimum price achieves `margem_alvo_pct` in the worst-case scenario.
- **Split payment:** `average revenue × worst-case tax rate × days ÷ 30`, with the sale in the middle of the month, payment received within `prazo_medio_recebimento_dias`, and taxes due on `dia_vencimento_impostos` of the following month. This is a maximum estimate, with no credits deducted. Implementation is gradual and depends on a joint act by the Comitê Gestor and Receita (LC 214, art. 35).
- **Simples:** does not simulate a change in DAS. It gives a notice when most sales are to businesses. The option to pay CBS/IBS outside DAS is semiannual, exercised in September and March (LC 123, art. 13, §§ 9–10, as worded in LC 227/2026).
- **Everything for 2027 is marked SIMULATED.** The reference CBS rate is set by the Senate (deadline: 15/12/2026). Recalculate when it is announced.

### The checker

`kit/conferir.py relatorio.md dados.json` exits with code 1 if the text contains:
- a value in R$, %, or a number with a comma that is not in `dados.json`;
- a number rounded in words (“62 thousand”);
- an invented number of days or months.

It is intended for the step where the AI rewrites the report in plain language.

### The tests

`tests/test_kit.py` (15) covers:
- the calculation checked by hand in the agency example (CBS, PIS/Cofins, split, expense, minimum price);
- Simples;
- Lucro Real with credit;
- the 60% reduction;
- the checker catching an invented number, a rounded number, and an assumption used as a number;
- input errors and the command line.

## The process, from start to finish

1. 🧠 Accountant opens Claude Code or Codex and pastes the request from `kit/PEDIDO.md`.
2. ⚙️ `python3 kit/diagnostico.py kit/exemplos/agencia`: the example, to see the format.
3. 🧠 Creates the client’s folder from `kit/modelo/`, using the data already available.
4. ⚙️ `python3 kit/diagnostico.py <pasta-do-cliente>` → `saida/relatorio-base.md` + `saida/dados.json`.
5. 🧠 The AI rewrites it in `relatorio.md` in plain language without changing the numbers.
6. ⚙️ `python3 kit/conferir.py relatorio.md saida/dados.json`: it must return `ok`.
7. 🧠 The accountant reviews the assumptions and brings the report to the client meeting.
8. ⚙️ `python3 -m unittest discover -s tests`: before changing the code.

## Sources

- Scenario tax rates: [kit calculadora-da-reforma](https://github.com/inematds/calculadora-da-reforma) (official Receita example with CBS at 8,8%) and [TCU, 28/10/2026](https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo) (reference tax rate of 11,3%; the Senate sets it by 15/12).
- 2027 rules: [LC 214/2025, text at the Senate](https://legis.senado.leg.br/norma/40180341/publicacao/40181429) (arts. 12, 35, 47, 344 and 347) and [LC 227/2026, updated text at the Chamber of Deputies](https://www2.camara.leg.br/legin/fed/leicom/2026/leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html) (Simples option). Checked on 24/11/2026.
- To check the calculation item by item in Receita’s official engine, use the calculadora-da-reforma calculator engine test.

MIT License. An unofficial INEMA kit. It does not replace the accountant’s technical analysis. Free at inema.club, directly on the internet.
