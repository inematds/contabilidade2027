"""Testes do kit Preço certo na Reforma.  Rodar:  python3 -m unittest discover -s tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))
import preco_certo as P  # noqa: E402
import diagnostico as D  # noqa: E402
import conferir as C  # noqa: E402

EX = RAIZ / "kit" / "exemplos"


def roda(pasta):
    return P.calcular(*P.carregar(pasta))


class Agencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = roda(EX / "agencia")
        cls.n = cls.d["numeros"]

    def test_mesmo_preco_alvo_do_diagnostico(self):
        # os dois kits usam a mesma regra de crédito: o preço-alvo da campanha tem de bater
        diag = D.diagnosticar(*D.carregar(EX / "agencia"))
        j = [b for b in diag["itens_margem_baixa"] if b["item"].startswith("Campanha")][0]["j"]
        self.assertAlmostEqual(self.n["p2_11_3_preco_alvo"]["valor"], diag["numeros"][f"prod_{j}_preco_min"]["valor"], places=2)

    def test_preco_alvo_devolve_a_margem(self):
        fc = 119200 / 299000
        t = 0.113
        pa = self.n["p2_11_3_preco_alvo"]["valor"]
        self.assertAlmostEqual((pa - 2150 - (pa - 2150 * fc) * t) / pa, 0.15, places=5)
        p0 = self.n["p2_11_3_preco_min"]["valor"]
        self.assertAlmostEqual((p0 - 2150 - (p0 - 2150 * fc) * t) / p0, 0.0, places=5)

    def test_cenario_principal_e_o_maior(self):
        self.assertEqual(self.d["cenarios"], [11.3, 8.8])

    def test_desconto_maximo(self):
        # consultoria: preço-alvo 155,49 sobre 400 → até 61,1% de desconto; campanha abaixo do alvo → 0
        self.assertAlmostEqual(self.n["p3_11_3_desc_max"]["valor"], (1 - self.n["p3_11_3_preco_alvo"]["valor"] / 400) * 100, places=3)
        self.assertEqual(self.n["p2_11_3_desc_max"]["valor"], 0.0)

    def test_prioridade_1_e_a_campanha(self):
        self.assertIn("Campanha de anúncios", self.d["prioridades"][0]["texto"])
        self.assertEqual(C.conferir(P.precos_md(self.d), self.d), [])


class Simples(unittest.TestCase):
    def test_simples_com_comissao_e_taxa(self):
        d = roda(EX / "loja-simples")
        n = d["numeros"]
        # lâmpada: (14,90 − 11,50 − 14,90 × (5% + 8%)) / 14,90
        self.assertAlmostEqual(n["p2_margem_hoje"]["valor"], (14.90 - 11.50 - 14.90 * 0.13) / 14.90 * 100, places=3)
        # preço-alvo 12%: 11,50 / (1 − 0,05 − 0,08 − 0,12)
        self.assertAlmostEqual(n["p2_preco_alvo"]["valor"], 11.50 / 0.75, places=2)
        self.assertEqual(len(d["prioridades"]), 3)
        self.assertEqual(C.conferir(P.precos_md(d), d), [])

    def test_simples_sem_aliquota_da_erro(self):
        with tempfile.TemporaryDirectory() as t:
            for f in ("mensal.csv", "produtos.csv"):
                Path(t, f).write_text((EX / "loja-simples" / f).read_text(encoding="utf-8"), encoding="utf-8")
            Path(t, "empresa.json").write_text(json.dumps({"regime": "simples"}))
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/preco_certo.py"), t], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("aliquota_simples_pct", r.stderr)


class Conferidor(unittest.TestCase):
    def test_numero_no_nome_do_item_nao_e_acusado(self):
        d = roda(EX / "loja-simples")
        self.assertEqual(C.conferir("O Fio elétrico 2,5 mm (rolo 100 m) está bem.", d), [])
        self.assertEqual(C.conferir("Um fio de 4,0 mm custaria mais.", d), ["4,0"])


class Cli(unittest.TestCase):
    def test_cli_grava_os_tres_arquivos(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/preco_certo.py"), str(EX / "agencia"), "--saida", t],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("precos.md", "precos.csv", "dados.json"):
                self.assertTrue(Path(t, f).exists(), f)
            self.assertIn("preco_alvo_11_3", Path(t, "precos.csv").read_text(encoding="utf-8").splitlines()[0])


if __name__ == "__main__":
    unittest.main()
