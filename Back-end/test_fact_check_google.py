"""Testes locais do adaptador da Google Fact Check Tools API."""

import json
import unittest
from unittest.mock import patch

from fact_check_google import buscar_checagens_google, extrair_consulta


class FactCheckGoogleTests(unittest.TestCase):
    """Comentário: Verifica normalização e falhas usando respostas simuladas, sem rede real."""

    def test_extrai_titulo_sem_enviar_o_corpo_completo(self):
        # Um corpo longo não deve substituir nem ampliar a consulta baseada no título.
        texto = "Título: Alegação testada\n\nNotícia: " + ("detalhe " * 1000)
        self.assertEqual(extrair_consulta(texto), "Alegação testada")

    def test_nao_envia_corpo_quando_nao_ha_titulo(self):
        # A integração só pesquisa texto explicitamente marcado como título.
        self.assertEqual(extrair_consulta("Notícia: texto sem título"), "")

    def test_chave_ausente_nao_faz_requisicao(self):
        # Sem credencial, o adaptador deve informar o estado sem tentar acessar a rede.
        with patch("fact_check_google.urllib.request.urlopen") as abrir_url:
            resposta = buscar_checagens_google("Título: Alegação")
        abrir_url.assert_not_called()
        self.assertEqual(resposta["status"], "nao_configurada")

    def test_normaliza_resultado_preservando_avaliacao_do_publicador(self):
        # Simula a estrutura aninhada da API para validar os campos apresentados.
        conteudo = {
            "claims": [
                {
                    "text": "Alegação correspondente",
                    "claimant": "Pessoa",
                    "claimReview": [
                        {
                            "publisher": {"name": "Agência", "site": "exemplo.test"},
                            "title": "Checagem publicada",
                            "url": "https://exemplo.test/checagem",
                            "reviewDate": "2026-01-01",
                            "textualRating": "Parcialmente falso",
                        }
                    ],
                }
            ]
        }

        class Resposta:
            """Comentário: Resposta mínima compatível com o context manager de urlopen."""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(conteudo).encode("utf-8")

        # O 'mock' impede tráfego externo e fornece o corpo JSON controlado acima.
        with patch(
            "fact_check_google.urllib.request.urlopen",
            return_value=Resposta(),
        ) as abrir_url:
            resposta = buscar_checagens_google(
                "Título: Alegação correspondente",
                api_key="teste",
            )

        requisicao = abrir_url.call_args.args[0]
        self.assertIn("factchecktools.googleapis.com", requisicao.full_url)
        self.assertEqual(resposta["status"], "resultados")
        self.assertEqual(
            resposta["resultados"][0]["avaliacao_textual"],
            "Parcialmente falso",
        )

    def test_resposta_sem_revisoes_e_reportada_explicitamente(self):
        class Resposta:
            """Comentário: Resposta HTTP simulada contendo lista de alegações vazia."""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"claims": []}'

        # Uma busca sem correspondências tem status próprio, não um rótulo factual.
        with patch(
            "fact_check_google.urllib.request.urlopen",
            return_value=Resposta(),
        ):
            resposta = buscar_checagens_google(
                "Título: Alegação não checada",
                api_key="teste",
            )
        self.assertEqual(resposta["status"], "sem_resultados")
        self.assertIn("não determina", resposta["mensagem"])


if __name__ == "__main__":
    unittest.main()
