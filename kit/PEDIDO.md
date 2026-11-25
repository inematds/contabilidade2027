# Pedidos para colar na sua IA (Claude Code ou Codex)

## Kit 1 — Diagnóstico Reforma + Caixa

Abra o Claude Code ou o Codex numa pasta do seu computador e cole:

```text
Leia o kit "contabilidade2027" em https://github.com/inematds/contabilidade2027 (o README explica tudo).
Quero fazer o Diagnóstico Reforma + Caixa de um cliente meu. Neste computador:
1. Baixe o kit (ZIP ou git) e rode primeiro o exemplo da agência, para eu ver como fica o relatório.
2. Me ajude a montar a pasta do meu cliente no formato de kit/modelo/ (empresa.json, mensal.csv e,
   se eu tiver, despesas.csv e produtos.csv). Pergunte o que faltar. Não invente número.
3. Rode kit/diagnostico.py na pasta do cliente.
4. Reescreva o relatorio-base.md num relatorio.md em linguagem simples, para o dono da empresa,
   sem mudar nenhum número (copie os valores exatamente como estão).
5. Rode kit/conferir.py relatorio.md saida/dados.json (os dois dentro da pasta do cliente). Se acusar número sem origem, corrija e rode de novo.
6. Me mostre o relatório e as premissas (alíquota, crédito, redução). Não envie nada a ninguém:
   eu reviso e sou eu quem fala com o cliente.
```

Os dados do cliente ficam no seu computador. O kit não manda nada para a internet. A sua IA (Claude ou Codex) lê os arquivos que você abrir para ela, como em qualquer uso dela.

## Kit 2 — Reforma Tributária Pronta

```text
Leia o kit "contabilidade2027" em https://github.com/inematds/contabilidade2027 (o README explica tudo).
Quero montar o plano Reforma Tributária Pronta de um cliente meu. Neste computador:
1. Baixe o kit (ZIP ou git) e rode primeiro kit/reforma_pronta.py no exemplo da agência, para eu ver como fica o plano.
2. Me ajude a montar na pasta do meu cliente o empresa.json (se ainda não existir) e o itens.csv (lista de produtos e serviços
   com NCM ou NBS, CST, cClassTrib, redução e vendas do ano) e, se eu tiver, fornecedores.csv e prontidao.json, no formato de kit/modelo/.
   Pergunte o que faltar. Não invente código nem número.
3. Rode kit/reforma_pronta.py na pasta do cliente.
4. Me explique o saida/reforma-pronta/plano.md em linguagem simples, sem mudar nenhum número, e me mostre o pendencias.csv.
5. Se você reescrever o plano, rode kit/conferir.py no texto novo com o saida/reforma-pronta/dados.json e corrija o que ele acusar.
6. Não envie nada a ninguém: eu reviso e sou eu quem fala com o cliente.
```

## Kit 3 — Preço certo na Reforma

```text
Leia o kit "contabilidade2027" em https://github.com/inematds/contabilidade2027 (o README explica tudo).
Quero montar a tabela Preço certo na Reforma de um cliente meu. Neste computador:
1. Baixe o kit (ZIP ou git) e rode primeiro kit/preco_certo.py no exemplo da agência, para eu ver como fica a tabela.
2. Me ajude a montar na pasta do meu cliente o produtos.csv (item, preço, custo, quantidade por mês e, se eu tiver,
   comissão e taxa de cartão), além do empresa.json e do mensal.csv (com impostos pagos, despesas e compras com crédito),
   no formato de kit/modelo/. No Simples, pergunte a alíquota efetiva do DAS. Não invente número.
3. Rode kit/preco_certo.py na pasta do cliente.
4. Me explique o saida/preco-certo/precos.md em linguagem simples, sem mudar nenhum número, e me mostre o precos.csv.
5. Se você reescrever o texto, rode kit/conferir.py no texto novo com o saida/preco-certo/dados.json e corrija o que ele acusar.
6. Não envie nada a ninguém: eu reviso e sou eu quem fala com o cliente.
```

## Kit 4 — Painel do Empresário

```text
Leia o kit "contabilidade2027" em https://github.com/inematds/contabilidade2027 (o README explica tudo).
Quero montar o Painel do Empresário do mês de um cliente meu. Neste computador:
1. Baixe o kit (ZIP ou git) e rode primeiro kit/painel.py no exemplo da agência, para eu ver como fica o painel.
2. Me ajude a atualizar na pasta do meu cliente o mensal.csv com o mês que fechou e, se eu tiver,
   contas_receber.csv e contas_pagar.csv (com o vencimento), no formato de kit/modelo/. Não invente número.
3. Rode kit/painel.py na pasta do cliente.
4. Reescreva o saida/painel/painel.md num texto curto para mandar ao cliente pelo WhatsApp, sem mudar nenhum número.
5. Rode kit/conferir.py no texto novo com o saida/painel/dados.json e corrija o que ele acusar.
6. Não envie nada a ninguém: eu reviso e sou eu quem fala com o cliente.
```
