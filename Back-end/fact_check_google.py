"""Busca revisões de checagem de fatos na Google Fact Check Tools API."""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

# Constantes de configuração da integração com a API pública do Google Fact Check Tools.
URL_API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
LIMITE_RESULTADOS = 5
LIMITE_CONSULTA = 120
TEMPO_LIMITE_SEGUNDOS = 10


def extrair_consulta(texto):
    """Extrai uma consulta objetiva e limpa para pesquisar checagens no Google."""
    if not texto or not texto.strip():
        return ""

    # 1. Tenta capturar explicitamente 'Título: ...'
    correspondencia = re.search(
        r"^Título:\s*(.+)$",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if correspondencia:
        consulta = correspondencia.group(1).strip()
    else:
        # 2. Fallback: pega a primeira linha não vazia
        linhas = [linha.strip() for linha in texto.strip().splitlines() if linha.strip()]
        consulta = linhas[0] if linhas else ""

    # Remove qualquer menção remanescente a prefixos de título ou ruído
    consulta = re.sub(r"^Título:\s*", "", consulta, flags=re.IGNORECASE).strip()
    
    # Se a primeira linha for muito curta ou genérica, usa os primeiros 100 caracteres do texto
    if len(consulta) < 10:
        consulta = texto.strip()[:100]

    # Normaliza múltiplos espaços e quebras de linha em um único espaço
    consulta = re.sub(r"\s+", " ", consulta).strip()
    return consulta[:LIMITE_CONSULTA]


def _resultado(status, mensagem, consulta="", resultados=None):
    # Padroniza todas as respostas para que a API sempre exponha os mesmos campos.
    return {
        "status": status,
        "mensagem": mensagem,
        "consulta": consulta,
        "resultados": resultados or [],
    }


def _normalizar_revisoes(resposta):
    # Seleciona campos públicos relevantes sem inferir um rótulo binário.
    if not isinstance(resposta, dict):
        raise ValueError("A resposta da API precisa ser um objeto JSON.")

    alegacoes = resposta.get("claims", [])
    if not isinstance(alegacoes, list):
        raise ValueError("O campo claims da resposta não é uma lista.")

    revisoes_normalizadas = []
    for alegacao in alegacoes:
        if not isinstance(alegacao, dict):
            continue
        revisoes = alegacao.get("claimReview", [])
        if not isinstance(revisoes, list):
            continue

        for revisao in revisoes:
            if not isinstance(revisao, dict):
                continue
            publicador = revisao.get("publisher")
            if not isinstance(publicador, dict):
                publicador = {}
            revisoes_normalizadas.append(
                {
                    "alegacao": str(alegacao.get("text", "")),
                    "autor_alegacao": str(alegacao.get("claimant", "")),
                    "data_alegacao": str(alegacao.get("claimDate", "")),
                    "publicador": str(publicador.get("name", "")),
                    "site_publicador": str(publicador.get("site", "")),
                    "titulo": str(revisao.get("title", "")),
                    "url": str(revisao.get("url", "")),
                    "data_revisao": str(revisao.get("reviewDate", "")),
                    "avaliacao_textual": str(revisao.get("textualRating", "")),
                }
            )
            if len(revisoes_normalizadas) >= LIMITE_RESULTADOS:
                return revisoes_normalizadas
    return revisoes_normalizadas


def buscar_checagens_google(texto, api_key=None):
    """Consulta checagens relacionadas ao título. NUNCA classifica a notícia."""
    chave = (
        api_key
        if api_key is not None
        else os.environ.get("GOOGLE_FACT_CHECK_API_KEY", "")
    ).strip()
    
    consulta = extrair_consulta(texto)
    
    if not chave:
        return _resultado(
            "nao_configurada",
            "Busca Google Fact Check desativada: configure GOOGLE_FACT_CHECK_API_KEY.",
            consulta,
        )
        
    if not consulta:
        return _resultado(
            "consulta_vazia",
            "Não foi possível extrair um título para pesquisar checagens.",
        )

    parametros = urllib.parse.urlencode(
        {
            "key": chave,
            "query": consulta,
            "languageCode": "pt-BR",
            "pageSize": LIMITE_RESULTADOS,
        }
    )
    requisicao = urllib.request.Request(
        f"{URL_API}?{parametros}",
        headers={"Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(
            requisicao,
            timeout=TEMPO_LIMITE_SEGUNDOS,
        ) as resposta_http:
            resposta = json.loads(resposta_http.read().decode("utf-8"))
        resultados = _normalizar_revisoes(resposta)
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        try:
            detalhe_json = json.loads(detalhe)
            detalhe = detalhe_json.get("error", {}).get("message", detalhe)
        except json.JSONDecodeError:
            detalhe = detalhe[:300]
        return _resultado(
            "erro",
            f"Google Fact Check API respondeu HTTP {erro.code}: {detalhe}",
            consulta,
        )
    except urllib.error.URLError as erro:
        return _resultado(
            "erro",
            f"Não foi possível acessar a Google Fact Check API: {erro.reason}",
            consulta,
        )
    except TimeoutError:
        return _resultado(
            "erro",
            "A consulta à Google Fact Check API excedeu o tempo limite.",
            consulta,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as erro:
        return _resultado(
            "erro",
            f"Resposta inválida da Google Fact Check API: {erro}",
            consulta,
        )

    if not resultados:
        return _resultado(
            "sem_resultados",
            (
                "O Google Fact Check não encontrou uma revisão para o título "
                "pesquisado. Esse campo não determina o veredito da notícia analisada."
            ),
            consulta,
        )
        
    return _resultado(
        "resultados",
        "Revisões de checagem relacionadas; confira o contexto e a fonte original.",
        consulta,
        resultados,
    )