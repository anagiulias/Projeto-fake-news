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
LIMITE_CONSULTA = 300
TEMPO_LIMITE_SEGUNDOS = 10

def extrair_consulta(texto):
    # Captura o título da notícia e limita o texto enviado ao Google.
    titulo = re.search(
        r"^Título:\s*(.+)$",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not titulo:
        return ""
    # O título reduz ruído e o limite mantém a requisição pequena.
    consulta = titulo.group(1)
    return re.sub(r"\s+", " ", consulta).strip()[:LIMITE_CONSULTA]


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

    # A API agrupa as revisões por alegação. Achatamos claimReview para facilitar o consumo na extensão sem descartar os dados básicos da alegação.
    alegacoes = resposta.get("claims", [])
    if not isinstance(alegacoes, list):
        raise ValueError("O campo claims da resposta não é uma lista.")

    # A API pode devolver claims sem revisões, ignore entradas com  malformação.
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
            # Alguns registros podem não incluir publisher; nesse caso os campos ficam vazios, preservando ainda assim a revisão disponível.
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
    """Consulta checagens relacionadas ao título NUNCA classifica a notícia."""
    # A chave é lida do ambiente por padrão e nunca precisa ser persistida no código.
    # 'api_key' facilita testes e configuração explícita em ambientes de produção, usa-se a variável de ambiente se nenhum valor foi passado à função.
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
    # Sem uma frase pesquisável não há motivo para chamar o endpoint externo.
    if not consulta:
        return _resultado(
            "consulta_vazia",
            "Não foi possível extrair um título para pesquisar checagens.",
        )

    # urlencode protege caracteres especiais do título e da chave na URL.
    parametros = urllib.parse.urlencode(
        {
            "key": chave,
            "query": consulta,
            "languageCode": "pt-BR",
            "pageSize": LIMITE_RESULTADOS,
        }
    )
    # Solicita JSON explicitamente. A chave e a consulta seguem como query params.
    requisicao = urllib.request.Request(
        f"{URL_API}?{parametros}",
        headers={"Accept": "application/json"},
    )

    # A integração é best-effort: erros viram status explícito, sem ocultar a causa.
    try:
        with urllib.request.urlopen(
            requisicao,
            timeout=TEMPO_LIMITE_SEGUNDOS,
        ) as resposta_http:
            resposta = json.loads(resposta_http.read().decode("utf-8"))
        resultados = _normalizar_revisoes(resposta)
    except urllib.error.HTTPError as erro:
        # A mensagem da API costuma vir em JSON; caso contrário, mantém-se uma amostra limitada do corpo para que o erro continue compreensível.
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
        # Erros de DNS ou conexão são diferentes de uma resposta HTTP da API.
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

    # Resposta vazia não significa que a notícia seja verdadeira: significa somente que nenhuma revisão correspondente foi retornada pela busca.
    if not resultados:
        # Ratings textuais são mantidos como publicados; não viram classe do modelo.
        # Exibe as revisões como referências relacionadas, sem agregá-las em verdictos.
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
