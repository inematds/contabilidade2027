# contabilidade2027 — Diagnóstico Reforma + Caixa y 3 kits más para contadores

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Diagnóstico Reforma + Caixa](guia/assets/banner-es.jpg)](https://inematds.github.io/contabilidade2027/guia/es/)

## Qué es

Su cliente le va a preguntar cuánto pesa la Reforma Tributaria en su caja en 2027. Este kit gratuito ayuda al contador a responder con los números del propio cliente. Usted coloca en una carpeta lo que ya tiene (el resumen mensual de ingresos, costos, impuestos y saldo y, si quiere, gastos y precios) y su IA arma un informe de 2 páginas para el dueño de la empresa: cuánto sobra, cómo está la caja, cuánto pagaría de CBS/IBS en 2027 en dos escenarios de alícuota, el efecto del split payment, qué llamó la atención y 3 prioridades. Un verificador garantiza que todo número del informe salió de los datos. En la misma carpeta del cliente funcionan otros 3 kits: **Reforma Tributária Pronta** (lo que falta en el registro, en el sistema y en los contratos), **Preço certo na Reforma** (precio mínimo y precio objetivo por producto) y **Painel do Empresário** (el cierre del mes en texto simple). Es un kit de INEMA, no oficial, y no sustituye el análisis técnico del contador.

## Los 4 kits (la misma carpeta del cliente sirve para todos)

| Kit | Qué entrega | Programa | Guía |
|---|---|---|---|
| 1. Diagnóstico Reforma + Caixa | Informe de 2 páginas: caja, margen, CBS/IBS de 2027, split payment, 3 prioridades | `kit/diagnostico.py` | [guía](https://inematds.github.io/contabilidade2027/guia/es/) |
| 2. Reforma Tributária Pronta | Plan por CNPJ: pendientes del registro (NCM/NBS, CST, cClassTrib), proveedores y crédito, checklist y plazos | `kit/reforma_pronta.py` | [guía](https://inematds.github.io/contabilidade2027/guia/es/reforma-pronta/) |
| 3. Preço certo na Reforma | Por ítem: margen de hoy y en 2027, precio mínimo, precio objetivo y descuento máximo | `kit/preco_certo.py` | [guía](https://inematds.github.io/contabilidade2027/guia/es/preco-certo/) |
| 4. Painel do Empresário | Cierre del mes en texto simple: resultado, comparaciones, caja de 3 meses, cuentas, alertas y qué hacer | `kit/painel.py` | [guía](https://inematds.github.io/contabilidade2027/guia/es/painel/) |

## 📖 Guía de uso

Guía completa: **https://inematds.github.io/contabilidade2027/guia/es/**

<!-- VIDEO: entra o explicavideo do projeto quando publicado -->

## Pídaselo a su IA

Abra Claude Code o Codex en una carpeta de su computadora y pegue el pedido del kit que quiere, en [`kit/PEDIDO.md`](kit/PEDIDO.md) (uno por kit). Le indica a la IA que ejecute el ejemplo, arme la carpeta de su cliente, genere el informe, lo reescriba en lenguaje simple sin tocar los números y lo verifique. No se envía nada a nadie: usted lo revisa y habla con el cliente.

## Qué trae el informe

1. **Cuánto sobra:** ingresos, ganancia y margen del período, y el margen de los 3 últimos meses comparado con el de los anteriores.
2. **Su caja:** saldo, salidas promedio, cuántos meses de salidas cubre la caja y los meses de aprieto.
3. **Reforma en 2027 (SIMULADO):** PIS/Cofins de hoy × CBS/IBS en dos escenarios (8,8% del ejemplo oficial de la Receita y 11,3% de la recomendación del TCU), la nota para quien vende a empresas y cuánto impuesto deja de pasar por la caja con el split payment. En el Simples, el aviso sobre crédito para clientes empresas.
4. **Qué llamó la atención:** gasto por encima del promedio e ítem con margen por debajo de la meta, con el precio mínimo.
5. **3 prioridades**, ordenadas por el valor en R$, cada una vinculada a un servicio que el contador puede ofrecer, más una agenda de reunión de 30 minutos.

Ejemplos listos: [`kit/exemplos/agencia/saida-exemplo/relatorio-base.md`](kit/exemplos/agencia/saida-exemplo/relatorio-base.md) (Lucro Presumido) y [`kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md`](kit/exemplos/loja-simples/saida-exemplo/relatorio-base.md) (Simples). Todos los datos son ficticios.

---

## Instalación técnica

Solo necesita **Python 3.9+**, sin bibliotecas adicionales. No usa internet ni modelo de IA: el script solo lee y calcula.

```bash
git clone https://github.com/inematds/contabilidade2027 && cd contabilidade2027
# ou baixe o ZIP: https://github.com/inematds/contabilidade2027/archive/refs/heads/main.zip

python3 kit/diagnostico.py kit/exemplos/agencia            # gera kit/exemplos/agencia/saida/
python3 kit/conferir.py kit/exemplos/agencia/saida/relatorio-base.md kit/exemplos/agencia/saida/dados.json
python3 -m unittest discover -s tests                        # 49 testes
```

### La carpeta del cliente

Copie `kit/modelo/` y complete. CSV con separador `;` y coma decimal, como Excel lo guarda en portugués.

| Archivo | Obligatorio | Columnas |
|---|---|---|
| `empresa.json` | sí | `nome`, `regime` (`simples`, `presumido` o `real`), `atividade`, `reducao_aliquota_pct` (0, 30 o 60), `cenarios_cbs_pct`, `ibs_2027_pct`, `prazo_medio_recebimento_dias`, `dia_vencimento_impostos`, `vendas_para_empresas_pct`, `margem_alvo_pct`; opcionales: `aliquota_simples_pct` (Simples, kit 3), `outros_impostos_pct` y `rateio_fixas_pct` (kits 1 y 3) |
| `mensal.csv` | sí (3+ meses) | `mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim` |
| `despesas.csv` | no | `mes;categoria;valor` (el último mes se compara con el promedio de los anteriores) |
| `produtos.csv` | no | `item;preco;custo_direto;qtd_mes` |

`compras_com_credito` es la parte de las compras que va a generar crédito de CBS/IBS (insumos y servicios de proveedores del régimen regular). La nómina no entra.

### Cómo se hace el cálculo (premisas)

- **CBS/IBS de 2027 (régimen regular):** `(receita − compras_com_credito) × alíquota de referência × (1 − redução)`, anualizado, comparado con el PIS/Cofins pagado. En 2027 la CBS es la referencia menos 0,1 punto (LC 214, art. 347) y el IBS es 0,05% estatal + 0,05% municipal (art. 344), por lo que los dos suman la propia referencia. Es una simplificación: la base es el ingreso informado, sin ajuste de otros tributos (la LC 214, art. 12, saca de la base la propia CBS/IBS y el IPI).
- **Crédito:** solo sobre lo que usted informe en `compras_com_credito`. La compra a un proveedor del Simples genera crédito limitado a lo que él paga en el Simples. Ajuste la columna.
- **Producto:** usa la misma cuenta del kit 3 (markup con impuestos y prorrateo de los gastos fijos, en `kit/comum.py`) y la misma regla de crédito de la empresa. La parte del costo que genera crédito es `compras_com_credito ÷ custo_direto` del período. El precio objetivo devuelve el `margem_alvo_pct` en el peor escenario (el mismo precio objetivo del kit 3).
- **Split payment:** `receita média × alíquota do pior cenário × dias ÷ 30`, con venta a mitad de mes, cobro en `prazo_medio_recebimento_dias` y vencimiento el día `dia_vencimento_impostos` del mes siguiente. Es una estimación máxima, sin descontar créditos. La implantación es gradual y depende de un acto conjunto del Comité Gestor y de la Receita (LC 214, art. 35).
- **Simples:** no simula cambio en el DAS. Avisa cuando la mayor parte de las ventas es a empresas. La opción de recaudar CBS/IBS fuera del DAS es semestral, hecha en septiembre y en marzo (LC 123, art. 13, §§ 9–10, con la redacción de la LC 227/2026).
- **Todo lo de 2027 sale marcado como SIMULADO.** La alícuota de referencia de la CBS la fija el Senado (plazo 15/12/2026). Rehaga cuando salga.

### Kit 2 — Reforma Tributária Pronta

```bash
python3 kit/reforma_pronta.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/reforma-pronta/plano.md, pendencias.csv e dados.json
```

Archivos adicionales en la carpeta del cliente (modelos en `kit/modelo/`):

| Archivo | Obligatorio | Columnas |
|---|---|---|
| `itens.csv` | sí | `item;tipo;codigo;cst;cclasstrib;reducao_pct;vendas_ano`. El `tipo` es `produto` (código NCM, 8 dígitos) o `servico` (código NBS, 9 dígitos) |
| `fornecedores.csv` | no | `fornecedor;regime;compras_ano`. El `regime` es `regular`, `simples` o `mei` |
| `prontidao.json` | no | `erp_atualizado`, `nota_teste`, `cadastro_revisado`, `contratos_revisados`, `precos_revisados`, `equipe_treinada`: `true`, `false` o `null` (no sé) |

Qué verifica:
- Formato de los códigos: NCM con 8 dígitos, NBS con 9, CST con 3, cClassTrib con 6.
- Si el cClassTrib empieza con el CST. En los ejemplos oficiales de la calculadora abierta de la Receita, 000 viene con 000001 y 200 con 200xxx; aquí es solo "verificar", no error.
- Reducción contra el CST: reducción con CST 000 (tributación integral), CST 200 (alícuota reducida) sin reducción, reducción sin cClassTrib. Una reducción fuera de 30/60/100% pasa a "verificar".
- Los ítems que suman el 80% de las ventas.
- La porción de las compras a proveedores del Simples o MEI, que generan crédito limitado a lo que el proveedor paga en el Simples (LC 214, art. 47).
- En el Simples, la próxima ventana de la opción de recaudar la CBS/IBS fuera del DAS (septiembre y marzo; LC 123, art. 13, § 10).

**No** dice si el código es el correcto para el ítem: eso le corresponde al contador, en la tabla oficial o en el [motor de la Receita](https://github.com/inematds/calculadora-da-reforma).

### Kit 3 — Preço certo na Reforma

```bash
python3 kit/preco_certo.py kit/exemplos/agencia        # gera saida/preco-certo/precos.md, precos.csv e dados.json
```

Usa `empresa.json`, `mensal.csv` y `produtos.csv`. El `produtos.csv` acepta estas columnas opcionales:
- `custo_com_credito`: R$ del costo del ítem que genera crédito. Sin ella, el kit usa la misma proporción de la empresa, `compras_com_credito ÷ custo_direto`.
- `comissao_pct` y `taxa_pct`: tarjeta, marketplace y gateway.

En el Simples, el `empresa.json` necesita `aliquota_simples_pct` (la alícuota efectiva del DAS, del PGDAS-D).

Cómo calcula (método del markup, la misma cuenta del Diagnóstico, en `kit/comum.py`):
- El precio cubre el costo, la comisión y la tasa, los otros impuestos sobre la venta y el prorrateo de los gastos fijos.
  - Los otros impuestos (ISS/ICMS, IR/CSLL del Presumido) son `outros_impostos ÷ receita` del `mensal.csv`, o `outros_impostos_pct` en el `empresa.json`. En el Simples son cero, porque el DAS ya los reúne.
  - El prorrateo de los gastos fijos es `despesas_operacionais ÷ receita`, o `rateio_fixas_pct`.
- El impuesto sobre el consumo es el PIS/Cofins efectivo hoy y, en 2027, `(preço − custo com crédito) × alíquota de referência × (1 − redução)`. En el Simples, es la alícuota del DAS.
- Margen = ganancia por venta ÷ precio. Precio mínimo = equilibrio (ganancia cero). Precio objetivo = `margem_alvo_pct`. Descuento máximo = cuánto puede bajar el precio de hoy sin salir del margen objetivo.
- Simplificaciones:
  - el impuesto se trata como parte del precio informado (conservador, porque la CBS/IBS es "por fuera");
  - en el Lucro Real, el IR/CSLL entra como fracción del ingreso;
  - el prorrateo por ingreso pesa más en los ítems de costo alto.
- El escenario principal es el mayor (11,3%). El precio objetivo coincide con el del Diagnóstico, y una prueba lo garantiza.

### Kit 4 — Painel do Empresário

```bash
python3 kit/painel.py kit/exemplos/agencia --hoje 2026-11-25   # gera saida/painel/painel.md e dados.json
```

El mes del panel es el último del `mensal.csv` (necesita al menos 3 meses; con 12 los promedios quedan mejores). Archivos opcionales (modelos en `kit/modelo/`):
- `despesas.csv`: `mes;categoria;valor`. Actualícelo junto con el `mensal.csv`: si el último mes de este es otro, el panel no da la alerta de gasto y lo avisa.
- `contas_receber.csv`: `cliente;valor;vencimento`
- `contas_pagar.csv`: `fornecedor;valor;vencimento`

El vencimiento puede ser AAAA-MM-DD o DD/MM/AAAA.

Qué trae el panel:
- **Resultado:** DRE gerencial del mes, con variación frente al mes anterior y frente al promedio.
- **Proyección:** 3 meses, por la variación promedio real del `saldo_caixa_fim` (la ganancia no es caja: retiros, cuotas e inversiones quedan fuera del DRE). Hay una alerta cuando la ganancia promedio es positiva y el saldo cae.
- **Cuentas:** por cobrar y por pagar en los próximos 30 días, las vencidas y los días de atraso.
- **Alertas:**
  - margen 3 puntos por debajo del promedio;
  - gasto fuera del patrón;
  - vencidas;
  - caja que cubre menos de medio mes;
  - proyección negativa;
  - holgura negativa.
- **Reserva del split payment:** siempre aparece, en el Presumido y en el Real. Es la misma cuenta del Diagnóstico.

### El verificador

`kit/conferir.py relatorio.md dados.json` sale con código 1 si el texto tiene:
- un valor en R$, % o número con coma que no esté en el `dados.json`;
- redondeo por extenso ("62 mil");
- una cantidad de días o meses inventada.

Sirve para el paso en que la IA reescribe el informe en lenguaje simple.

### Las pruebas

`tests/test_kit.py` (15, kit 1) cubre:
- la cuenta verificada a mano en el ejemplo de la agencia (CBS, PIS/Cofins, split, gasto, precio mínimo);
- el Simples;
- el Lucro Real con crédito;
- la reducción del 60%;
- el verificador detectando número inventado, redondeado y premisa usada como número;
- los errores de entrada y la línea de comandos.

`tests/test_reforma_pronta.py` (12, kit 2) cubre:
- el conteo de pendientes de la agencia y las ventas en riesgo;
- los ítems que suman el 80% de las ventas;
- los proveedores del Simples;
- la prioridad 1;
- cada regla de formato;
- la ventana del Simples en 3 fechas;
- los errores de entrada y la línea de comandos.

`tests/test_reforma_pronta.py` (12, kit 2), `tests/test_preco_certo.py` (10, kit 3) y `tests/test_painel.py` (12, kit 4) verifican las cuentas a mano en los dos ejemplos, la coherencia con el Diagnóstico y los errores de entrada. Total: 49 pruebas.

## El proceso, de principio a fin

1. 🧠 El contador abre Claude Code o Codex y pega el pedido de `kit/PEDIDO.md`.
2. ⚙️ `python3 kit/diagnostico.py kit/exemplos/agencia`: el ejemplo, para ver el formato.
3. 🧠 Arma la carpeta del cliente a partir de `kit/modelo/`, con los datos que ya tiene.
4. ⚙️ `python3 kit/diagnostico.py <pasta-do-cliente>` → `saida/relatorio-base.md` + `saida/dados.json`.
5. 🧠 La IA reescribe en `relatorio.md`, en lenguaje simple, sin tocar los números.
6. ⚙️ `python3 kit/conferir.py relatorio.md saida/dados.json`: debe salir `ok`.
7. 🧠 El contador revisa las premisas y lleva el informe a la reunión con el cliente.
8. ⚙️ Kit 2: `python3 kit/reforma_pronta.py <pasta-do-cliente>` → `saida/reforma-pronta/` (plano.md, pendencias.csv). La carpeta debe tener el `itens.csv`.
9. ⚙️ Kit 3: `python3 kit/preco_certo.py <pasta-do-cliente>` → `saida/preco-certo/` (precos.md, precos.csv).
10. ⚙️ Kit 4, todos los meses: agregar el mes en el `mensal.csv` (y las cuentas, si las hay) → `python3 kit/painel.py <pasta-do-cliente>` → `saida/painel/painel.md`.
11. ⚙️ `python3 -m unittest discover -s tests`: antes de cambiar el código.

## Base

- Alícuotas de escenario: [kit calculadora-da-reforma](https://github.com/inematds/calculadora-da-reforma) (ejemplo oficial de la Receita con CBS de 8,8%) y [TCU, 28/10/2026](https://portal.tcu.gov.br/imprensa/noticias/tcu-calcula-aliquota-de-referencia-de-113-para-novo-tributo-sobre-consumo) (alícuota de referencia de 11,3%; el Senado la fija hasta el 15/12).
- Reglas de 2027: [LC 214/2025, texto en el Senado](https://legis.senado.leg.br/norma/40180341/publicacao/40181429) (arts. 12, 35, 47, 344 y 347) y [LC 227/2026, texto actualizado en la Cámara](https://www2.camara.leg.br/legin/fed/leicom/2026/leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html) (opción del Simples). Verificado el 24/11/2026.
- Para verificar el cálculo ítem por ítem en el motor oficial de la Receita, use la prueba del motor de la calculadora-da-reforma.

Licencia MIT. Kit de INEMA, no oficial. No sustituye el análisis técnico del contador. Gratis en inema.club, directo en internet.
