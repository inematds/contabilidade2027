# contabilidade2027 — Diagnóstico Reforma + Caixa e mais 3 kits para contadores

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Diagnóstico Reforma + Caixa](guia/assets/banner.jpg)](https://inematds.github.io/contabilidade2027/guia/)

## O que é

O seu cliente vai perguntar quanto a Reforma Tributária pesa no caixa dele em 2027. Este kit gratuito ajuda o contador a responder com os números do próprio cliente. Você coloca numa pasta o que já tem (o resumo mensal de receitas, custos, impostos e saldo e, se quiser, despesas e preços) e a sua IA monta um relatório de 2 páginas para o dono da empresa: quanto sobra, como está o caixa, quanto ele recolheria de CBS/IBS em 2027 em dois cenários de alíquota, o efeito do split payment, o que chamou a atenção e 3 prioridades. Um conferidor garante que todo número do relatório veio dos dados. Na mesma pasta do cliente rodam mais 3 kits: o **Reforma Tributária Pronta** (o que falta no cadastro, no sistema e nos contratos), o **Preço certo na Reforma** (preço mínimo e preço-alvo por produto) e o **Painel do Empresário** (o fechamento do mês em texto simples). É um kit do INEMA, não oficial, e não substitui a análise técnica do contador.

## Os 4 kits (a mesma pasta do cliente serve para todos)

| Kit | O que entrega | Programa | Guia |
|---|---|---|---|
| 1. Diagnóstico Reforma + Caixa | Relatório de 2 páginas: caixa, margem, CBS/IBS de 2027, split payment, 3 prioridades | `kit/diagnostico.py` | [guia](https://inematds.github.io/contabilidade2027/guia/) |
| 2. Reforma Tributária Pronta | Plano por CNPJ: pendências do cadastro (NCM/NBS, CST, cClassTrib), fornecedores e crédito, checklist e prazos | `kit/reforma_pronta.py` | [guia](https://inematds.github.io/contabilidade2027/guia/reforma-pronta/) |
| 3. Preço certo na Reforma | Por item: margem de hoje e em 2027, preço mínimo, preço-alvo e desconto máximo | `kit/preco_certo.py` | [guia](https://inematds.github.io/contabilidade2027/guia/preco-certo/) |
| 4. Painel do Empresário | Fechamento do mês em texto simples: resultado, comparações, caixa de 3 meses, contas, alertas e o que fazer | `kit/painel.py` | [guia](https://inematds.github.io/contabilidade2027/guia/painel/) |

## 📖 Guia de uso

Guia completo: **https://inematds.github.io/contabilidade2027/guia/**

<!-- VIDEO: entra o explicavideo do projeto quando publicado -->

## Peça para a sua IA

Abra o Claude Code ou o Codex numa pasta do seu computador e cole o pedido do kit que você quer, em [`kit/PEDIDO.md`](kit/PEDIDO.md) (um por kit). Ele manda a IA rodar o exemplo, montar a pasta do seu cliente, gerar o relatório, reescrever em linguagem simples sem mexer nos números e conferir. Nada é enviado a ninguém: você revisa e fala com o cliente.

## O que o relatório traz

1. **Quanto sobra:** receita, lucro e margem do período, e a margem dos 3 últimos meses comparada com a dos anteriores.
2. **Seu caixa:** saldo, saídas médias, quantos meses de saídas o caixa cobre e os meses de aperto.
3. **Reforma em 2027 (SIMULADO):** PIS/Cofins de hoje × CBS/IBS em dois cenários (8,8% do exemplo oficial da Receita e 11,3% da recomendação do TCU), a nota para quem vende para empresas e quanto de imposto deixa de passar pelo caixa com o split payment. No Simples, o aviso sobre crédito para clientes empresas.
4. **O que chamou a atenção:** despesa acima da média e item com margem abaixo da meta, com o preço mínimo.
5. **3 prioridades**, ordenadas pelo valor em R$, cada uma ligada a um serviço que o contador pode oferecer, mais uma pauta de reunião de 30 minutos.

Exemplos prontos: [`kit/exemplos/agencia/saida-exemplo/relatorio-base.md`](kit/exemplos/agencia/saida-exemplo/relatorio-base.md) (Lucro Presumido) e [`kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md`](kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md) (Simples). Todos os dados são fictícios.

---

## Instalação técnica

Precisa só de **Python 3.9+**, sem bibliotecas extras. Não usa internet nem modelo de IA: o script só lê e calcula.

```bash
git clone https://github.com/inematds/contabilidade2027 && cd contabilidade2027
# ou baixe o ZIP: https://github.com/inematds/contabilidade2027/archive/refs/heads/main.zip

python3 kit/diagnostico.py kit/exemplos/agencia            # gera kit/exemplos/agencia/saida/
python3 kit/conferir.py kit/exemplos/agencia/saida/relatorio-base.md kit/exemplos/agencia/saida/dados.json
python3 -m unittest discover -s tests                        # 49 testes
```

### A pasta do cliente

Copie `kit/modelo/` e preencha. CSV com separador `;` e vírgula decimal, como o Excel salva em português.

| Arquivo | Obrigatório | Colunas |
|---|---|---|
| `empresa.json` | sim | `nome`, `regime` (`simples`, `presumido` ou `real`), `atividade`, `reducao_aliquota_pct` (0, 30 ou 60), `cenarios_cbs_pct`, `ibs_2027_pct`, `prazo_medio_recebimento_dias`, `dia_vencimento_impostos`, `vendas_para_empresas_pct`, `margem_alvo_pct`; opcionais: `aliquota_simples_pct` (Simples, kit 3), `outros_impostos_pct` e `rateio_fixas_pct` (kits 1 e 3) |
| `mensal.csv` | sim (3+ meses) | `mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim` |
| `despesas.csv` | não | `mes;categoria;valor` (o último mês é comparado com a média dos anteriores) |
| `produtos.csv` | não | `item;preco;custo_direto;qtd_mes` |

`compras_com_credito` é a parte das compras que vai gerar crédito de CBS/IBS (insumos e serviços de fornecedores do regime regular). Folha não entra.

### Como o cálculo é feito (premissas)

- **CBS/IBS de 2027 (regime regular):** `(receita − compras_com_credito) × alíquota de referência × (1 − redução)`, anualizado, comparado com o PIS/Cofins pago. Em 2027 a CBS é a referência menos 0,1 ponto (LC 214, art. 347) e o IBS é 0,05% estadual + 0,05% municipal (art. 344), então os dois somam a própria referência. É uma simplificação: a base é a receita informada, sem ajuste de outros tributos (a LC 214, art. 12, tira da base a própria CBS/IBS e o IPI).
- **Crédito:** só sobre o que você informar em `compras_com_credito`. Compra de fornecedor do Simples gera crédito limitado ao que ele paga no Simples. Ajuste a coluna.
- **Produto:** usa a mesma conta do kit 3 (markup com impostos e rateio das despesas fixas, em `kit/comum.py`) e a mesma regra de crédito da empresa. A parte do custo que gera crédito é `compras_com_credito ÷ custo_direto` do período. O preço-alvo devolve a `margem_alvo_pct` no pior cenário (o mesmo preço-alvo do kit 3).
- **Split payment:** `receita média × alíquota do pior cenário × dias ÷ 30`, com venda no meio do mês, recebimento em `prazo_medio_recebimento_dias` e vencimento no dia `dia_vencimento_impostos` do mês seguinte. É uma estimativa máxima, sem descontar créditos. A implantação é gradual e depende de ato conjunto do Comitê Gestor e da Receita (LC 214, art. 35).
- **Simples:** não simula mudança no DAS. Avisa quando a maior parte das vendas é para empresas. A opção de recolher CBS/IBS fora do DAS é semestral, feita em setembro e em março (LC 123, art. 13, §§ 9–10, com a redação da LC 227/2026).
- **Tudo de 2027 sai marcado como SIMULADO.** A alíquota de referência da CBS é fixada pelo Senado (prazo 15/12/2026). Refaça quando sair.

### Kit 2 — Reforma Tributária Pronta

```bash
python3 kit/reforma_pronta.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/reforma-pronta/plano.md, pendencias.csv e dados.json
```

Arquivos a mais na pasta do cliente (modelos em `kit/modelo/`):

| Arquivo | Obrigatório | Colunas |
|---|---|---|
| `itens.csv` | sim | `item;tipo;codigo;cst;cclasstrib;reducao_pct;vendas_ano`. O `tipo` é `produto` (código NCM, 8 dígitos) ou `servico` (código NBS, 9 dígitos) |
| `fornecedores.csv` | não | `fornecedor;regime;compras_ano`. O `regime` é `regular`, `simples` ou `mei` |
| `prontidao.json` | não | `erp_atualizado`, `nota_teste`, `cadastro_revisado`, `contratos_revisados`, `precos_revisados`, `equipe_treinada`: `true`, `false` ou `null` (não sei) |

O que ele confere:
- Formato dos códigos: NCM com 8 dígitos, NBS com 9, CST com 3, cClassTrib com 6.
- Se o cClassTrib começa pelo CST. Nos exemplos oficiais da calculadora aberta da Receita, 000 vem com 000001 e 200 com 200xxx; aqui é só "conferir", não erro.
- Redução contra o CST: redução com CST 000 (tributação integral), CST 200 (alíquota reduzida) sem redução, redução sem cClassTrib. Redução fora de 30/60/100% vira "conferir".
- Os itens que somam 80% das vendas.
- A fatia das compras de fornecedor do Simples ou MEI, que geram crédito limitado ao que o fornecedor paga no Simples (LC 214, art. 47).
- No Simples, a próxima janela da opção de recolher a CBS/IBS fora do DAS (setembro e março; LC 123, art. 13, § 10).

Ele **não** diz se o código é o certo para o item: isso é com o contador, na tabela oficial ou no [motor da Receita](https://github.com/inematds/calculadora-da-reforma).

### Kit 3 — Preço certo na Reforma

```bash
python3 kit/preco_certo.py kit/exemplos/agencia        # gera saida/preco-certo/precos.md, precos.csv e dados.json
```

Usa `empresa.json`, `mensal.csv` e `produtos.csv`. O `produtos.csv` aceita estas colunas opcionais:
- `custo_com_credito`: R$ do custo do item que gera crédito. Sem ela, o kit usa a mesma proporção da empresa, `compras_com_credito ÷ custo_direto`.
- `comissao_pct` e `taxa_pct`: cartão, marketplace e gateway.

No Simples, o `empresa.json` precisa de `aliquota_simples_pct` (a alíquota efetiva do DAS, do PGDAS-D).

Como calcula (método do markup, a mesma conta do Diagnóstico, em `kit/comum.py`):
- O preço cobre o custo, a comissão e a taxa, os outros impostos sobre a venda e o rateio das despesas fixas.
  - Os outros impostos (ISS/ICMS, IR/CSLL do Presumido) são `outros_impostos ÷ receita` do `mensal.csv`, ou `outros_impostos_pct` no `empresa.json`. No Simples são zero, porque o DAS já os reúne.
  - O rateio das despesas fixas é `despesas_operacionais ÷ receita`, ou `rateio_fixas_pct`.
- O imposto sobre o consumo é o PIS/Cofins efetivo hoje e, em 2027, `(preço − custo com crédito) × alíquota de referência × (1 − redução)`. No Simples, é a alíquota do DAS.
- Margem = lucro por venda ÷ preço. Preço mínimo = equilíbrio (lucro zero). Preço-alvo = `margem_alvo_pct`. Desconto máximo = quanto o preço de hoje pode cair sem sair da margem-alvo.
- Simplificações:
  - o imposto é tratado como parte do preço informado (conservador, porque a CBS/IBS é "por fora");
  - no Lucro Real, o IR/CSLL entra como fração da receita;
  - o rateio pela receita pesa mais nos itens de custo alto.
- O cenário principal é o maior (11,3%). O preço-alvo bate com o do Diagnóstico, e um teste garante isso.

### Kit 4 — Painel do Empresário

```bash
python3 kit/painel.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/painel/painel.md e dados.json
```

O mês do painel é o último do `mensal.csv` (precisa de pelo menos 3 meses; com 12 as médias ficam melhores). Arquivos opcionais (modelos em `kit/modelo/`):
- `despesas.csv`: `mes;categoria;valor`. Atualize junto com o `mensal.csv`: se o último mês dele for outro, o painel não dá o alerta de despesa e avisa.
- `contas_receber.csv`: `cliente;valor;vencimento`
- `contas_pagar.csv`: `fornecedor;valor;vencimento`

O vencimento pode ser AAAA-MM-DD ou DD/MM/AAAA.

O que o painel traz:
- **Resultado:** DRE gerencial do mês, com variação contra o mês anterior e contra a média.
- **Projeção:** 3 meses, pela variação média real do `saldo_caixa_fim` (o lucro não é caixa: retiradas, parcelas e investimentos ficam fora do DRE). Há um alerta quando o lucro médio é positivo e o saldo cai.
- **Contas:** a receber e a pagar nos próximos 30 dias, os vencidos e os dias de atraso.
- **Alertas:**
  - margem 3 pontos abaixo da média;
  - despesa fora do padrão;
  - vencidos;
  - caixa que cobre menos de meio mês;
  - projeção negativa;
  - folga negativa.
- **Reserva do split payment:** sempre aparece, no Presumido e no Real. É a mesma conta do Diagnóstico.

### O conferidor

`kit/conferir.py relatorio.md dados.json` sai com código 1 se o texto tiver:
- valor em R$, % ou número com vírgula que não esteja no `dados.json`;
- arredondamento por extenso ("62 mil");
- quantidade de dias ou meses inventada.

Serve para o passo em que a IA reescreve o relatório em linguagem simples.

### Os testes

`tests/test_kit.py` (15, kit 1) cobre:
- a conta conferida à mão no exemplo da agência (CBS, PIS/Cofins, split, despesa, preço mínimo);
- o Simples;
- o Lucro Real com crédito;
- a redução de 60%;
- o conferidor pegando número inventado, arredondado e premissa usada como número;
- os erros de entrada e a linha de comando.

`tests/test_reforma_pronta.py` (12, kit 2) cobre:
- a contagem de pendências da agência e as vendas em risco;
- os itens que somam 80% das vendas;
- os fornecedores do Simples;
- a prioridade 1;
- cada regra de formato;
- a janela do Simples em 3 datas;
- os erros de entrada e a linha de comando.

`tests/test_reforma_pronta.py` (12, kit 2), `tests/test_preco_certo.py` (10, kit 3) e `tests/test_painel.py` (12, kit 4) conferem as contas à mão nos dois exemplos, a coerência com o Diagnóstico e os erros de entrada. Total: 49 testes.

## O processo, do início ao fim

1. 🧠 Contador abre o Claude Code ou o Codex e cola o pedido de `kit/PEDIDO.md`.
2. ⚙️ `python3 kit/diagnostico.py kit/exemplos/agencia`: o exemplo, para ver o formato.
3. 🧠 Monta a pasta do cliente a partir de `kit/modelo/`, com os dados que já tem.
4. ⚙️ `python3 kit/diagnostico.py <pasta-do-cliente>` → `saida/relatorio-base.md` + `saida/dados.json`.
5. 🧠 A IA reescreve em `relatorio.md`, em linguagem simples, sem mexer nos números.
6. ⚙️ `python3 kit/conferir.py relatorio.md saida/dados.json`: tem de sair `ok`.
7. 🧠 O contador revisa as premissas e leva o relatório para a reunião com o cliente.
8. ⚙️ Kit 2: `python3 kit/reforma_pronta.py <pasta-do-cliente>` → `saida/reforma-pronta/` (plano.md, pendencias.csv). A pasta precisa ter o `itens.csv`.
9. ⚙️ Kit 3: `python3 kit/preco_certo.py <pasta-do-cliente>` → `saida/preco-certo/` (precos.md, precos.csv).
10. ⚙️ Kit 4, todo mês: acrescentar o mês no `mensal.csv` (e as contas, se tiver) → `python3 kit/painel.py <pasta-do-cliente>` → `saida/painel/painel.md`.
11. ⚙️ `python3 -m unittest discover -s tests`: antes de mudar o código.

## Base

- Alíquotas de cenário: [kit calculadora-da-reforma](https://github.com/inematds/calculadora-da-reforma) (exemplo oficial da Receita com CBS de 8,8%) e [TCU, 28/10/2026](https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo) (alíquota de referência de 11,3%; o Senado fixa até 15/12).
- Regras de 2027: [LC 214/2025, texto no Senado](https://legis.senado.leg.br/norma/40180341/publicacao/40181429) (arts. 12, 35, 47, 344 e 347) e [LC 227/2026, texto atualizado na Câmara](https://www2.camara.leg.br/legin/fed/leicom/2026/leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html) (opção do Simples). Conferido em 24/11/2026.
- Para conferir o cálculo item por item no motor oficial da Receita, use o teste do motor da calculadora-da-reforma.

Licença MIT. Kit do INEMA, não oficial. Não substitui a análise técnica do contador. Grátis no inema.club, direto na internet.
