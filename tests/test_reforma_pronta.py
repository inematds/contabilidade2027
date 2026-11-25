"""Testes do kit Reforma Tributária Pronta.  Rodar:  python3 -m unittest discover -s tests"""
import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))
import reforma_pronta as R  # noqa: E402
import conferir as C  # noqa: E402

EX = RAIZ / "kit" / "exemplos"
HOJE = dt.date(2026, 11, 25)


def roda(pasta, hoje=HOJE):
    return R.planejar(*R.carregar(pasta), hoje)


class Agencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = roda(EX / "agencia")
        cls.n = cls.d["numeros"]

    def test_contagem_de_pendencias(self):
        # campanha: NBS com 7 dígitos + sem cClassTrib; consultoria: par CST/cClassTrib; curso: sem cClassTrib + redução sem cClassTrib
        self.assertEqual(self.n["itens_pend"]["valor"], 3)
        self.assertEqual(self.n["pendencias"]["valor"], 5)
        self.assertAlmostEqual(self.n["vendas_pend"]["valor"], 240000 + 96000 + 1000)

    def test_itens_que_somam_80_por_cento(self):
        # 504k + 240k + 144k = 888k de 985k = 90,2%; com 2 itens seriam 75,5% (< 80%)
        self.assertEqual(self.d["itens_80"], ["Gestão de redes sociais (mensal)", "Campanha de anúncios (mensal)", "Site institucional"])
        self.assertAlmostEqual(self.n["itens_80_pct"]["valor"], 888000 / 985000 * 100, places=3)

    def test_fornecedores_do_simples(self):
        self.assertAlmostEqual(self.n["compras_simples"]["valor"], 168000.0)
        self.assertAlmostEqual(self.n["compras_simples_pct"]["valor"], 168000 / 276000 * 100, places=3)

    def test_prioridade_1_e_o_item_de_maior_venda_com_pendencia(self):
        self.assertIn("Campanha de anúncios", self.d["prioridades"][0]["texto"])
        self.assertEqual(len(self.d["prioridades"]), 3)

    def test_plano_sem_numero_inventado(self):
        self.assertEqual(C.conferir(R.plano_md(self.d), self.d), [])


class Regras(unittest.TestCase):
    def item(self, **k):
        base = {"item": "x", "tipo": "produto", "codigo": "8544.49.00", "cst": "000", "cclasstrib": "000001", "reducao_pct": 0}
        base.update(k)
        return [p[0] for p in R.conferir_item(base)]

    def test_item_certo_nao_tem_pendencia(self):
        self.assertEqual(self.item(), [])
        self.assertEqual(self.item(tipo="servico", codigo="1.1506.10.00"), [])

    def test_formatos(self):
        self.assertEqual(self.item(codigo="8544.49"), ["codigo"])          # NCM com 6 dígitos
        self.assertEqual(self.item(cst="00"), ["cst"])
        self.assertEqual(self.item(cclasstrib="200001"), ["cclasstrib"])  # não começa pelo CST 000
        self.assertEqual(self.item(reducao_pct=45), ["reducao_pct"])      # fora de 30/60/100
        self.assertEqual(self.item(reducao_pct=60, cclasstrib=""), ["cclasstrib", "reducao_pct"])

    def test_janela_do_simples(self):
        self.assertEqual(R.proxima_janela_simples(dt.date(2026, 11, 25)), (dt.date(2027, 3, 1), dt.date(2027, 7, 1)))
        self.assertEqual(R.proxima_janela_simples(dt.date(2027, 2, 10)), (dt.date(2027, 3, 1), dt.date(2027, 7, 1)))
        self.assertEqual(R.proxima_janela_simples(dt.date(2027, 4, 1)), (dt.date(2027, 9, 1), dt.date(2028, 1, 1)))


class Simples(unittest.TestCase):
    def test_simples_tem_janela_e_pendencia_fora_dos_maiores(self):
        d = roda(EX / "loja-simples")
        self.assertEqual(d["simples"]["janela"], "março de 2027")
        self.assertTrue(any("pendências de cadastro" in p["texto"] or "Corrigir" in p["texto"] for p in d["prioridades"]))
        self.assertEqual(C.conferir(R.plano_md(d), d), [])


class Entradas(unittest.TestCase):
    def test_erros_claros(self):
        with tempfile.TemporaryDirectory() as t:
            Path(t, "empresa.json").write_text(json.dumps({"regime": "presumido"}))
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/reforma_pronta.py"), t], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("itens.csv", r.stderr)
            Path(t, "itens.csv").write_text("item;tipo;codigo;cst;cclasstrib;reducao_pct;vendas_ano\nx;mercadoria;1;000;000001;0;10\n")
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/reforma_pronta.py"), t], capture_output=True, text=True)
            self.assertIn("tipo deve ser produto ou servico", r.stderr)

    def test_cli_grava_os_tres_arquivos(self):
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/reforma_pronta.py"), str(EX / "agencia"), "--saida", t, "--hoje", "2026-11-25"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("plano.md", "pendencias.csv", "dados.json"):
                self.assertTrue(Path(t, f).exists(), f)


if __name__ == "__main__":
    unittest.main()
