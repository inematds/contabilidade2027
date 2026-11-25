"""Testes do kit Painel do Empresário.  Rodar:  python3 -m unittest discover -s tests"""
import datetime as dt
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))
import painel as PN  # noqa: E402
import diagnostico as D  # noqa: E402
import conferir as C  # noqa: E402

EX = RAIZ / "kit" / "exemplos"
HOJE = dt.date(2026, 11, 25)


def roda(pasta, hoje=HOJE):
    return PN.painel(*PN.carregar(pasta), hoje)


class Agencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = roda(EX / "agencia")
        cls.n = cls.d["numeros"]

    def test_dre_do_mes(self):
        # 11/2026: 92.000 − 28.000 − 34.500 − (3.358 + 9.200) = 16.942
        self.assertAlmostEqual(self.n["lucro"]["valor"], 16942.0)
        self.assertAlmostEqual(self.n["bruta"]["valor"], 64000.0)
        self.assertAlmostEqual(self.n["impostos"]["valor"], 12558.0)

    def test_comparacoes(self):
        self.assertAlmostEqual(self.n["var_rec_ant"]["valor"], (92000 - 87000) / 87000 * 100, places=3)
        self.assertLess(self.n["var_luc_ant"]["valor"], 0)
        self.assertEqual(self.n["var_luc_ant_abs"]["texto"], self.n["var_luc_ant"]["texto"].lstrip("-"))

    def test_projecao_pelo_saldo_real(self):
        # saldo de 08 a 11/2026: 41.000 → 39.000 → 37.000 → 34.000 (média −2.333,33 por mês)
        self.assertAlmostEqual(self.n["var_saldo"]["valor"], -7000 / 3, places=2)
        self.assertAlmostEqual(self.n["proj_1"]["valor"], 34000 - 7000 / 3, places=2)
        self.assertAlmostEqual(self.n["proj_3"]["valor"], 27000.0, places=2)
        self.assertEqual([p["mes"] for p in self.d["projecao"]], ["12/2026", "01/2027", "02/2027"])

    def test_alerta_quando_resultado_e_caixa_nao_batem(self):
        # lucro médio dos 3 últimos meses positivo e saldo caindo → dinheiro saindo fora do resultado
        self.assertTrue(any("não batem" in a for a in self.d["alertas"]))
        self.assertAlmostEqual(self.n["fora_dre"]["valor"], self.n["lucro_3m"]["valor"] + 7000 / 3, places=2)

    def test_reserva_do_split_sempre_aparece(self):
        self.assertIn("split payment", PN.painel_md(self.d))

    def test_contas_vencidas_e_30_dias(self):
        self.assertAlmostEqual(self.n["receber_vencido"]["valor"], 7500 + 6000 + 3500)
        self.assertEqual(self.n["venc_0_dias"]["valor"], 26)          # venceu em 30/10, hoje 25/11
        self.assertAlmostEqual(self.n["receber_30"]["valor"], 42000 + 6000 + 20000 + 8000)  # 10/01 fica fora
        self.assertAlmostEqual(self.n["folga_30"]["valor"], 34000 + 76000 - 59058)

    def test_split_igual_ao_do_diagnostico(self):
        diag = D.diagnosticar(*D.carregar(EX / "agencia"))
        self.assertEqual(self.n["split_giro"]["valor"], diag["numeros"]["split_giro"]["valor"])

    def test_cobranca_e_a_prioridade_1(self):
        self.assertIn("Cobrar Clínica Exemplo", self.d["fazer"][0])
        self.assertEqual(C.conferir(PN.painel_md(self.d), self.d), [])


class SemContas(unittest.TestCase):
    def test_simples_sem_contas_funciona(self):
        d = roda(EX / "loja-simples")
        self.assertNotIn("folga_30", d["numeros"])
        self.assertEqual(C.conferir(PN.painel_md(d), d), [])


class Entradas(unittest.TestCase):
    def test_vencimento_invalido(self):
        with tempfile.TemporaryDirectory() as t:
            for f in ("empresa.json", "mensal.csv"):
                Path(t, f).write_text((EX / "agencia" / f).read_text(encoding="utf-8"), encoding="utf-8")
            Path(t, "contas_receber.csv").write_text("cliente;valor;vencimento\nX;10;31-12\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/painel.py"), t], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("vencimento inválido", r.stderr)

    def test_data_em_formato_brasileiro(self):
        self.assertEqual(PN.data("05/12/2026", "x", 2), dt.date(2026, 12, 5))


if __name__ == "__main__":
    unittest.main()
