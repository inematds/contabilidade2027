# Diagnóstico Reforma + Caixa

[![Diagnóstico Reforma + Caixa](guia/assets/banner.jpg)](https://inematds.github.io/contabilidade2027/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O seu cliente vai perguntar quanto a Reforma Tributária pesa no caixa dele em 2027. Este kit gratuito ajuda o contador a responder com os números do próprio cliente. Você coloca numa pasta o que já tem (o resumo mensal de receitas, custos, impostos e saldo e, se quiser, despesas e preços) e a sua IA monta um relatório de 2 páginas para o dono da empresa: quanto sobra, como está o caixa, quanto ele recolheria de CBS/IBS em 2027 em dois cenários de alíquota, o efeito do split payment, o que chamou a atenção e 3 prioridades. Um conferidor garante que todo número do relatório veio dos dados. É um kit do INEMA, não oficial, e não substitui a análise técnica do contador.

## 📖 Guia de uso

Guia completo: **https://inematds.github.io/contabilidade2027/guia/**

<!-- VIDEO: entra o explicavideo do projeto quando publicado -->

## Peça para a sua IA

Abra o Claude Code ou o Codex numa pasta do seu computador e cole o pedido de [`kit/PEDIDO.md`](kit/PEDIDO.md). Ele manda a IA rodar o exemplo, montar a pasta do seu cliente, gerar o relatório, reescrever em linguagem simples sem mexer nos números e conferir. Nada é enviado a ninguém: você revisa e fala com o cliente.

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
python3 -m unittest discover -s tests                        # 15 testes
```

### A pasta do cliente

Copie `kit/modelo/` e preencha. CSV com separador `;` e vírgula decimal, como o Excel salva em português.

| Arquivo | Obrigatório | Colunas |
|---|---|---|
| `empresa.json` | sim | `nome`, `regime` (`simples`, `presumido` ou `real`), `atividade`, `reducao_aliquota_pct` (0, 30 ou 60), `cenarios_cbs_pct`, `ibs_2027_pct`, `prazo_medio_recebimento_dias`, `dia_vencimento_impostos`, `vendas_para_empresas_pct`, `margem_alvo_pct` |
| `mensal.csv` | sim (3+ meses) | `mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim` |
| `despesas.csv` | não | `mes;categoria;valor` (o último mês é comparado com a média dos anteriores) |
| `produtos.csv` | não | `item;preco;custo_direto;qtd_mes` |

`compras_com_credito` é a parte das compras que vai gerar crédito de CBS/IBS (insumos e serviços de fornecedores do regime regular). Folha não entra.

### Como o cálculo é feito (premissas)

- **CBS/IBS de 2027 (regime regular):** `(receita − compras_com_credito) × alíquota de referência × (1 − redução)`, anualizado, comparado com o PIS/Cofins pago. Em 2027 a CBS é a referência menos 0,1 ponto (LC 214, art. 347) e o IBS é 0,05% estadual + 0,05% municipal (art. 344), então os dois somam a própria referência. É uma simplificação: a base é a receita informada, sem ajuste de outros tributos (a LC 214, art. 12, tira da base a própria CBS/IBS e o IPI).
- **Crédito:** só sobre o que você informar em `compras_com_credito`. Compra de fornecedor do Simples gera crédito limitado ao que ele paga no Simples. Ajuste a coluna.
- **Produto:** usa a mesma regra de crédito da empresa. A parte do custo que gera crédito é `compras_com_credito ÷ custo_direto` do período. O preço mínimo devolve a `margem_alvo_pct` no pior cenário.
- **Split payment:** `receita média × alíquota do pior cenário × dias ÷ 30`, com venda no meio do mês, recebimento em `prazo_medio_recebimento_dias` e vencimento no dia `dia_vencimento_impostos` do mês seguinte. É uma estimativa máxima, sem descontar créditos. A implantação é gradual e depende de ato conjunto do Comitê Gestor e da Receita (LC 214, art. 35).
- **Simples:** não simula mudança no DAS. Avisa quando a maior parte das vendas é para empresas. A opção de recolher CBS/IBS fora do DAS é semestral, feita em setembro e em março (LC 123, art. 13, §§ 9–10, com a redação da LC 227/2026).
- **Tudo de 2027 sai marcado como SIMULADO.** A alíquota de referência da CBS é fixada pelo Senado (prazo 15/12/2026). Refaça quando sair.

### O conferidor

`kit/conferir.py relatorio.md dados.json` sai com código 1 se o texto tiver:
- valor em R$, % ou número com vírgula que não esteja no `dados.json`;
- arredondamento por extenso ("62 mil");
- quantidade de dias ou meses inventada.

Serve para o passo em que a IA reescreve o relatório em linguagem simples.

### Os testes

`tests/test_kit.py` (15) cobre:
- a conta conferida à mão no exemplo da agência (CBS, PIS/Cofins, split, despesa, preço mínimo);
- o Simples;
- o Lucro Real com crédito;
- a redução de 60%;
- o conferidor pegando número inventado, arredondado e premissa usada como número;
- os erros de entrada e a linha de comando.

## O processo, do início ao fim

1. 🧠 Contador abre o Claude Code ou o Codex e cola o pedido de `kit/PEDIDO.md`.
2. ⚙️ `python3 kit/diagnostico.py kit/exemplos/agencia`: o exemplo, para ver o formato.
3. 🧠 Monta a pasta do cliente a partir de `kit/modelo/`, com os dados que já tem.
4. ⚙️ `python3 kit/diagnostico.py <pasta-do-cliente>` → `saida/relatorio-base.md` + `saida/dados.json`.
5. 🧠 A IA reescreve em `relatorio.md`, em linguagem simples, sem mexer nos números.
6. ⚙️ `python3 kit/conferir.py relatorio.md saida/dados.json`: tem de sair `ok`.
7. 🧠 O contador revisa as premissas e leva o relatório para a reunião com o cliente.
8. ⚙️ `python3 -m unittest discover -s tests`: antes de mudar o código.

## Base

- Alíquotas de cenário: [kit calculadora-da-reforma](https://github.com/inematds/calculadora-da-reforma) (exemplo oficial da Receita com CBS de 8,8%) e [TCU, 28/10/2026](https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo) (alíquota de referência de 11,3%; o Senado fixa até 15/12).
- Regras de 2027: [LC 214/2025, texto no Senado](https://legis.senado.leg.br/norma/40180341/publicacao/40181429) (arts. 12, 35, 47, 344 e 347) e [LC 227/2026, texto atualizado na Câmara](https://www2.camara.leg.br/legin/fed/leicom/2026/leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html) (opção do Simples). Conferido em 24/11/2026.
- Para conferir o cálculo item por item no motor oficial da Receita, use o teste do motor da calculadora-da-reforma.

Licença MIT. Kit do INEMA, não oficial. Não substitui a análise técnica do contador. Grátis no inema.club, direto na internet.
