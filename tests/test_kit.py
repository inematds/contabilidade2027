"""Testes do kit Diagnóstico Reforma + Caixa.  Rodar:  python3 -m unittest discover -s tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))
import diagnostico as D  # noqa: E402
import conferir as C  # noqa: E402

EX = RAIZ / "kit" / "exemplos"


def roda(pasta):
    return D.diagnosticar(*D.carregar(pasta))


class Agencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = roda(EX / "agencia")
        cls.n = cls.d["numeros"]

    def test_soma_receita(self):
        self.assertAlmostEqual(self.n["receita_periodo"]["valor"], 985000.0)

    def test_cbs_conferida_a_mao(self):
        # (985000 − 119200) × 11,3% (CBS 11,2% + IBS 0,1%) = 97.835,40 ; PIS/Cofins pagos = 35.952,50
        self.assertAlmostEqual(self.n["cbs_11_3_imposto_ano"]["valor"], 97835.4, places=2)
        self.assertAlmostEqual(self.n["pis_cofins_ano"]["valor"], 35952.5, places=2)
        self.assertAlmostEqual(self.n["cbs_11_3_diferenca_ano"]["valor"], 61882.9, places=2)
        self.assertAlmostEqual(self.n["cbs_8_8_imposto_ano"]["valor"], 76190.4, places=2)

    def test_split(self):
        # venda média 82.083,33 × 11,3% = 9.275,42/mês ; 15 + 25 − 20 = 20 dias → 6.183,61
        self.assertEqual(self.n["split_dias"]["valor"], 20)
        self.assertAlmostEqual(self.n["split_giro"]["valor"], 6183.61, places=2)

    def test_despesa_fora_do_padrao(self):
        cats = [f["categoria"] for f in self.d["despesas_fora"]]
        self.assertEqual(cats, ["Softwares e assinaturas"])  # energia subiu pouco (R$ 60) e não entra
        self.assertAlmostEqual(self.d["despesas_fora"][0]["acima"], 1980.0)

    def test_item_com_margem_baixa_e_preco_minimo(self):
        itens = [b["item"] for b in self.d["itens_margem_baixa"]]
        self.assertEqual(itens, ["Campanha de anúncios (mensal)"])
        b = self.d["itens_margem_baixa"][0]
        # markup: custo 1.400, outros impostos 98.500/985.000, rateio das fixas 356.500/985.000, CBS+IBS 11,3% com crédito
        out, fix, t, fc = 98500 / 985000, 356500 / 985000, 0.113, 119200 / 299000
        p = b["preco_min"]
        self.assertAlmostEqual((p - 1400 - p * (out + fix) - (p - 1400 * fc) * t) / p, 0.15, places=6)
        self.assertLess(b["m_2027"], b["m_hoje"])

    def test_tres_prioridades_e_maior_primeiro(self):
        pr = self.d["prioridades"]
        self.assertEqual(len(pr), 3)
        self.assertEqual(pr[0]["servico"], "Preço certo na Reforma")  # campanha: R$ por ano maior que o aumento de imposto
        self.assertTrue(any(x["servico"] == "Reforma Tributária Pronta" for x in pr))

    def test_todo_numero_do_relatorio_tem_origem(self):
        txt = D.relatorio(self.d)
        self.assertEqual(C.conferir(txt, self.d), [])
        for k, v in self.n.items():
            self.assertTrue(v["origem"], k)


class Simples(unittest.TestCase):
    def test_simples_nao_simula_cbs_e_avisa_b2b(self):
        d = roda(EX / "loja-simples")
        self.assertFalse(any(k.startswith("cbs_") for k in d["numeros"]))
        self.assertTrue(any("fora do DAS" in x["texto"] for x in d["prioridades"]))
        self.assertEqual(len(d["prioridades"]), 3)  # sempre 3, mesmo com poucos dados
        self.assertEqual(C.conferir(D.relatorio(d), d), [])


def pasta_temp(t, empresa, linhas):
    Path(t, "empresa.json").write_text(json.dumps(empresa), encoding="utf-8")
    cab = "mes;receita;compras_com_credito;custo_direto;despesas_operacionais;pis_cofins_pago;outros_impostos;saldo_caixa_fim\n"
    Path(t, "mensal.csv").write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")


class Regimes(unittest.TestCase):
    def test_lucro_real_com_credito(self):
        with tempfile.TemporaryDirectory() as t:
            # 3 meses: receita 100 mil, compras com crédito 60 mil, PIS/Cofins não cumulativo pago 3.700/mês
            pasta_temp(t, {"nome": "Indústria", "regime": "real"},
                       [f"0{m}/2026;100000;60000;60000;20000;3700;5000;50000" for m in (9, 8, 7)])
            d = roda(t)
            # (300000 − 180000) × 11,3% = 13.560 no trimestre → 54.240/ano ; PIS/Cofins 44.400/ano
            self.assertAlmostEqual(d["numeros"]["cbs_11_3_imposto_ano"]["valor"], 54240.0, places=2)
            self.assertAlmostEqual(d["numeros"]["pis_cofins_ano"]["valor"], 44400.0, places=2)
            self.assertEqual(C.conferir(D.relatorio(d), d), [])

    def test_reducao_de_60(self):
        with tempfile.TemporaryDirectory() as t:
            pasta_temp(t, {"nome": "Clínica", "regime": "presumido", "reducao_aliquota_pct": 60},
                       [f"0{m}/2026;50000;5000;10000;20000;1825;4000;30000" for m in (9, 8, 7)])
            d = roda(t)
            # (150000 − 15000) × 11,3% × 40% = 6.102 no trimestre → 24.408/ano
            self.assertAlmostEqual(d["numeros"]["cbs_11_3_imposto_ano"]["valor"], 24408.0, places=2)


class Conferidor(unittest.TestCase):
    def test_pega_numero_inventado(self):
        d = roda(EX / "agencia")
        txt = D.relatorio(d) + "\nA economia será de R$ 12.345,67 e 37,5% de margem.\n"
        sem = C.conferir(txt, d)
        self.assertIn("R$ 12.345,67", sem)
        self.assertIn("37,5%", sem)

    def test_pega_numero_arredondado(self):
        d = roda(EX / "agencia")
        self.assertEqual(C.conferir("O imposto sobe R$ 62.749 por ano.", d), ["R$ 62.749"])
        self.assertEqual(C.conferir("Cerca de 62 mil reais a mais.", d), ["62 mil"])

    def test_pega_quantidade_inventada(self):
        d = roda(EX / "agencia")
        self.assertEqual(C.conferir("O imposto fica 20 dias no caixa.", d), [])  # split_dias = 20
        self.assertEqual(C.conferir("O imposto fica 45 dias no caixa.", d), ["45 dias"])
        self.assertEqual(C.conferir("Margem de 25% no ano.", d), ["25%"])  # premissa não vira número livre


class Entradas(unittest.TestCase):
    def test_erros_claros(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/diagnostico.py"), t], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("falta", r.stderr)
            Path(t, "empresa.json").write_text(json.dumps({"regime": "mei"}))
            Path(t, "mensal.csv").write_text("mes;receita\n01/2026;10\n")
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/diagnostico.py"), t], capture_output=True, text=True)
            self.assertIn("regime", r.stderr)

    def test_cli_grava_saida(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/diagnostico.py"), str(EX / "agencia"), "--saida", t],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(Path(t, "relatorio-base.md").exists())
            r2 = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/conferir.py"), str(Path(t, "relatorio-base.md")), str(Path(t, "dados.json"))],
                                capture_output=True, text=True)
            self.assertEqual(r2.returncode, 0, r2.stdout)


if __name__ == "__main__":
    unittest.main()
