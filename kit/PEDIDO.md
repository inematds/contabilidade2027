# Pedido para colar na sua IA (Claude Code ou Codex)

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
5. Rode kit/conferir.py relatorio.md dados.json. Se acusar número sem origem, corrija e rode de novo.
6. Me mostre o relatório e as premissas (alíquota, crédito, redução). Não envie nada a ninguém:
   eu reviso e sou eu quem fala com o cliente.
```

Os dados do cliente ficam no seu computador. O kit não manda nada para a internet. A sua IA (Claude ou Codex) lê os arquivos que você abrir para ela, como em qualquer uso dela.
