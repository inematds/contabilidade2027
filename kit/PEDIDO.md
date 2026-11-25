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
2. Me ajude a montar na pasta do meu cliente o itens.csv (lista de produtos e serviços com NCM ou NBS, CST,
   cClassTrib, redução e vendas do ano) e, se eu tiver, fornecedores.csv e prontidao.json, no formato de kit/modelo/.
   Pergunte o que faltar. Não invente código nem número.
3. Rode kit/reforma_pronta.py na pasta do cliente.
4. Me explique o plano.md em linguagem simples, sem mudar nenhum número, e me mostre o pendencias.csv.
5. Se você reescrever o plano, rode kit/conferir.py no texto novo com o saida/dados.json e corrija o que ele acusar.
6. Não envie nada a ninguém: eu reviso e sou eu quem fala com o cliente.
```
