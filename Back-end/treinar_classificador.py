"""Treina, avalia e salva o classificador binário de notícias."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedGroupKFold
from classificador_veracidade import (
    LIMIAR_CONFIANCA_MINIMA,
    LIMIAR_SIMILARIDADE_MINIMA,
    ClassificadorTextoCalibrado,
)

PASTA_BASE = Path(__file__).resolve().parent.parent
# Caminhos absolutos ancorados no repositório tornam a execução independente do diretório atual do terminal.
CAMINHO_DATASET = (
    PASTA_BASE / "datasets" / "tratados" / "noticias_rotuladas_tratadas.csv"
)
CAMINHO_MODELO = Path(__file__).resolve().parent / "modelo_veracidade.joblib"
CAMINHO_METRICAS = Path(__file__).resolve().parent / "metricas_veracidade.json"
CAMINHO_DATASET_BALANCEADO = (
    PASTA_BASE / "datasets" / "tratados" / "noticias_rotuladas_balanceadas.csv"
)
CAMINHO_FALSAS_NAO_AMOSTRADAS = (
    PASTA_BASE / "datasets" / "tratados" / "noticias_falsas_nao_amostradas.csv"
)
SEMENTE = 42
ROTULOS = {0: "VERDADEIRA", 1: "FALSA"}
# Dez partições agrupadas permitem reservar (30%) para teste e sete (70%) para treino, mantendo textos iguais na mesma partição.
QUANTIDADE_TEMAS = 30
PARTICOES_DIVISAO = 10
PARTICOES_TESTE = 3
STOPWORDS_TEMAS = [
    "a", "à", "ao", "aos", "as", "às", "até", "com", "como", "da", "das",
    "de", "dela", "delas", "dele", "deles", "do", "dos", "e", "ela", "elas",
    "ele", "eles", "em", "entre", "era", "essa", "esse", "esta", "este",
    "eu", "foi", "foram", "há", "isso", "isto", "já", "lhe", "lhes", "mais",
    "mas", "me", "mesmo", "meu", "meus", "minha", "minhas", "muito", "na",
    "nas", "nem", "no", "nos", "nossa", "nossas", "nosso", "nossos", "num",
    "numa", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos",
    "por", "porque", "qual", "quando", "que", "quem", "se", "sem", "ser",
    "seu", "seus", "sua", "suas", "também", "tem", "tendo", "ter", "toda",
    "todas", "todo", "todos", "um", "uma", "umas", "uns", "você", "vocês",
    "não", "sim", "sobre", "após", "antes", "ainda", "já", "onde", "hoje",
    "ontem", "segundo", "disse", "afirma", "afirmou", "diz", "seria",
]


def carregar_dataset():
    """Carrega e valida a tabela rotulada produzida pelo notebook de tratamento."""
    if not CAMINHO_DATASET.is_file():
        raise FileNotFoundError(
            f"Dataset tratado não encontrado: {CAMINHO_DATASET}. "
            "Execute primeiro Tratamento-dados/tratamento_datasets_rotulados.ipynb."
        )

    # utf-8-sig também remove o BOM que pode ser escrito pelo exportador do notebook.
    dados = pd.read_csv(CAMINHO_DATASET, encoding="utf-8-sig")
    colunas_obrigatorias = {"texto_modelo", "label", "arquivo_origem"}
    colunas_ausentes = colunas_obrigatorias.difference(dados.columns)
    if colunas_ausentes:
        raise ValueError(
            "O dataset tratado não tem as colunas obrigatórias: "
            f"{sorted(colunas_ausentes)}. Gere-o novamente pelo notebook de tratamento."
        )

    # Descarta linhas sem os campos essenciais e normaliza os tipos que serão usados nas verificações, no agrupamento e no ajuste do modelo.
    dados = dados.dropna(subset=["texto_modelo", "label", "arquivo_origem"]).copy()
    dados["texto_modelo"] = dados["texto_modelo"].astype(str).str.strip()
    dados["arquivo_origem"] = dados["arquivo_origem"].astype(str).str.strip()
    dados = dados.loc[
        dados["texto_modelo"].ne("") & dados["arquivo_origem"].ne("")
    ].reset_index(drop=True)
    dados["label"] = pd.to_numeric(dados["label"], errors="raise").astype(int)

    classes = set(dados["label"].unique())
    if classes != set(ROTULOS):
        raise ValueError(
            "O classificador binário requer os rótulos 0 e 1 "
            f"(VERDADEIRA/FALSA); encontrados: {sorted(classes)}."
        )
    dados["_chave_texto"] = dados["texto_modelo"].str.lower()
    # O split agrupa textos iguais sem diferenciar maiúsculas e minúsculas.
    rotulos_por_texto = dados.groupby("_chave_texto")["label"].nunique()
    if rotulos_por_texto.gt(1).any():
        raise ValueError(
            "Há textos iguais após conversão para minúsculas associados a rótulos diferentes. "
            "Revise os conflitos no relatório de auditoria antes de treinar."
        )

    # StratifiedGroupKFold precisa de grupos independentes suficientes em cada classe para criar o número de partições configurado.
    grupos_por_rotulo = dados.groupby("label")["_chave_texto"].nunique()
    if (grupos_por_rotulo < PARTICOES_DIVISAO).any():
        raise ValueError(
            "Cada classe precisa ter ao menos "
            f"{PARTICOES_DIVISAO} textos independentes para a divisão agrupada."
        )

    return dados.drop(columns="_chave_texto")


def construir_grupos_sem_vazamento(dados):
    """Comentário: Mantém textos iguais após a normalização de caixa na mesma partição."""
    # Union-find aproxima registros equivalentes sem comparar cada par de textos.
    pais = list(range(len(dados)))

    # Union-find associa a mesma chave normalizada ao índice do primeiro registro.
    def encontrar(indice):
        # Compressão de caminho acelera futuras buscas do representante do grupo.
        while pais[indice] != indice:
            pais[indice] = pais[pais[indice]]
            indice = pais[indice]
        return indice

    def unir(primeiro, segundo):
        # Liga os representantes para que os dois registros compartilhem o grupo.
        raiz_primeiro = encontrar(primeiro)
        raiz_segundo = encontrar(segundo)
        if raiz_primeiro != raiz_segundo:
            pais[raiz_segundo] = raiz_primeiro

    primeiro_indice_por_valor = {}
    for indice, valor in enumerate(dados["texto_modelo"].str.lower()):
        anterior = primeiro_indice_por_valor.setdefault(valor, indice)
        unir(indice, anterior)

    return np.asarray([encontrar(indice) for indice in range(len(dados))])


def distribuir_quota_uniformemente(contagens, total):
    """Comentário: Divide o alvo igualmente entre temas, respeitando a capacidade de cada um."""
    # Redistribui sobras para temas que ainda tenham exemplos disponíveis.
    quotas = {tema: 0 for tema in contagens}
    restantes = total
    ativos = [tema for tema, capacidade in contagens.items() if capacidade > 0]

    while restantes and ativos:
        # Reparte igualmente a quantidade pendente, a capacidade do tema pode limitar a cota e a próxima volta redistribui a diferença.
        cota, sobra = divmod(restantes, len(ativos))
        progresso = 0
        for indice, tema in enumerate(ativos):
            incremento = cota + int(indice < sobra)
            incremento = min(incremento, contagens[tema] - quotas[tema])
            quotas[tema] += incremento
            progresso += incremento
        restantes -= progresso
        ativos = [
            tema for tema in ativos if quotas[tema] < contagens[tema]
        ]
        if progresso == 0:
            raise RuntimeError("Não foi possível distribuir a amostra entre os temas.")

    if restantes:
        raise ValueError("A amostra solicitada excede os exemplos falsos disponíveis.")
    return quotas


def criar_dataset_balanceado(dados):
    """Comentário: Subamostra a classe FALSA por tema e preserva o restante para inspeção."""
    dados = dados.copy()
    vetorizador_temas = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=3,
        max_features=50_000,
        stop_words=STOPWORDS_TEMAS,
        sublinear_tf=True,
    )
    # Os clusters servem para distribuir a amostra, não são rótulos de veracidade.
    matriz_temas = vetorizador_temas.fit_transform(dados["texto_modelo"])
    # Evita pedir mais clusters do que os exemplos permitem.
    quantidade_temas = min(QUANTIDADE_TEMAS, len(dados) // 2)
    agrupador = MiniBatchKMeans(
        n_clusters=quantidade_temas,
        random_state=SEMENTE,
        batch_size=1024,
        n_init=3,
        max_iter=100,
    )
    dados["tema_cluster"] = agrupador.fit_predict(matriz_temas)

    # Os termos com maiores pesos no centróide dão nomes legíveis aos clusters.
    termos = np.asarray(vetorizador_temas.get_feature_names_out())
    termos_por_tema = {}
    for tema, centro in enumerate(agrupador.cluster_centers_):
        principais = np.argsort(centro)[-5:][::-1]
        termos_por_tema[tema] = ", ".join(termos[principais])
    dados["tema_termos"] = dados["tema_cluster"].map(termos_por_tema)

    # Mantém todas as VERDADEIRAS e seleciona a mesma quantidade de FALSAS, repartindo essa seleção entre os grupos temáticos encontrados pelo K-means.
    verdadeiras = dados.loc[dados["label"] == 0]
    falsas = dados.loc[dados["label"] == 1]
    alvo_por_classe = len(verdadeiras)
    contagens_falsas = falsas["tema_cluster"].value_counts().to_dict()
    quotas = distribuir_quota_uniformemente(contagens_falsas, alvo_por_classe)

    # Usa uma amostra reprodutível dentro de cada tema e conserva o excedente.
    partes_falsas_selecionadas = []
    partes_falsas_restantes = []
    for tema, grupo in falsas.groupby("tema_cluster", sort=True):
        quantidade_selecionada = quotas.get(tema, 0)
        ordenado = grupo.sample(frac=1, random_state=SEMENTE)
        partes_falsas_selecionadas.append(ordenado.iloc[:quantidade_selecionada])
        partes_falsas_restantes.append(ordenado.iloc[quantidade_selecionada:])

    falsas_selecionadas = pd.concat(partes_falsas_selecionadas)
    falsas_restantes = pd.concat(partes_falsas_restantes)
    balanceadas = pd.concat([verdadeiras, falsas_selecionadas], ignore_index=True)
    balanceadas = balanceadas.sample(frac=1, random_state=SEMENTE).reset_index(drop=True)
    falsas_restantes = falsas_restantes.sort_values(
        ["tema_cluster", "arquivo_origem"]
    ).reset_index(drop=True)

    # Tabela de conferência: mostra a composição das classes em cada cluster.
    contagens_balanceadas = (
        balanceadas.groupby(["tema_cluster", "tema_termos", "label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[0, 1], fill_value=0)
    )
    contagens_balanceadas.columns = ["VERDADEIRA", "FALSA"]
    contagens_balanceadas["diferenca_absoluta"] = (
        contagens_balanceadas["VERDADEIRA"] - contagens_balanceadas["FALSA"]
    ).abs()

    # Exporta também as falsas não selecionadas para que nada seja descartado sem rastro.
    CAMINHO_DATASET_BALANCEADO.parent.mkdir(parents=True, exist_ok=True)
    balanceadas.to_csv(CAMINHO_DATASET_BALANCEADO, index=False, encoding="utf-8-sig")
    falsas_restantes.to_csv(
        CAMINHO_FALSAS_NAO_AMOSTRADAS,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Amostra balanceada: {len(verdadeiras):,} VERDADEIRAS e "
        f"{len(falsas_selecionadas):,} FALSAS, distribuídas por "
        f"{quantidade_temas} grupos temáticos automáticos."
    )
    print(
        f"Falsas não amostradas preservadas para inspeção temática: "
        f"{len(falsas_restantes):,}."
    )
    print(contagens_balanceadas.to_string())
    print(f"Dataset balanceado salvo em: {CAMINHO_DATASET_BALANCEADO}")
    print(f"Falsas restantes salvas em: {CAMINHO_FALSAS_NAO_AMOSTRADAS}")

    return balanceadas, falsas_restantes, contagens_balanceadas


def dividir_treino_teste(dados, grupos):
    """Comentário: Separa cerca de 70% para treino e 30% para teste sem cruzar grupos."""
    divisao = StratifiedGroupKFold(
        n_splits=PARTICOES_DIVISAO,
        shuffle=True,
        random_state=SEMENTE,
    )
    # Cada fold retornado é mantido para poder combinar os três folds de teste.
    indices_teste_por_particao = [
        indices
        for _, indices in divisao.split(
            dados["texto_modelo"],
            dados["label"],
            groups=grupos,
        )
    ]
    # Três dos dez folds formam o teste, os sete restantes ficam para treino.
    # A estratificação busca preservar as classes, e o agrupamento evita vazamento entre textos iguais, mesmo que os grupos tenham tamanhos diferentes.
    indices_teste = np.concatenate(
        indices_teste_por_particao[:PARTICOES_TESTE]
    )
    indices_treino = np.concatenate(
        indices_teste_por_particao[PARTICOES_TESTE:]
    )
    treino = dados.iloc[indices_treino].copy()
    teste = dados.iloc[indices_teste].copy()
    grupos_treino = grupos[indices_treino]
    grupos_teste = grupos[indices_teste]

    if set(treino["label"].unique()) != set(ROTULOS):
        raise ValueError("A partição de treino não contém as duas classes.")
    if set(teste["label"].unique()) != set(ROTULOS):
        raise ValueError("A partição de teste não contém as duas classes.")

    # Verificação defensiva: garante que a partição final não contém textos iguais dos dois lados, ainda que o gerador de grupos seja alterado no futuro.
    textos_em_comum = set(treino["texto_modelo"].str.lower()) & set(
        teste["texto_modelo"].str.lower()
    )
    if textos_em_comum:
        raise RuntimeError(
            "A divisão agrupada colocou textos iguais após conversão para "
            "minúsculas em treino e teste."
        )
    return (
        treino.reset_index(drop=True),
        teste.reset_index(drop=True),
        grupos_treino,
        grupos_teste,
    )


def avaliar(modelo, teste):
    """Comentário: Calcula métricas convencionais e métricas considerando a abstinência."""
    probabilidades = modelo.predict_proba(teste["texto_modelo"])
    indice_classe_verdadeira = list(modelo.classes_).index(0)
    indice_classe_falsa = list(modelo.classes_).index(1)
    # Usa o limiar otimizado apenas no treino e não escolhe um novo valor com o teste.
    previsoes = np.where(
        probabilidades[:, indice_classe_falsa] >= modelo.limiar_falsa,
        1,
        0,
    )
    probabilidades_verdadeiras = probabilidades[:, indice_classe_verdadeira]
    # O limiar foi aprendido no treino. Brier mede a qualidade das probabilidades, enquanto as demais métricas comparam a classe prevista com o rótulo real.
    metricas = {
        "acuracia": accuracy_score(teste["label"], previsoes),
        "acuracia_balanceada": balanced_accuracy_score(teste["label"], previsoes),
        "brier_score": brier_score_loss(
            teste["label"],
            1 - probabilidades_verdadeiras,
            pos_label=1,
        ),
        "limiar_sugestao_falsa": modelo.limiar_falsa,
        "matriz_confusao_labels_0_1": confusion_matrix(
            teste["label"],
            previsoes,
            labels=[0, 1],
        ).tolist(),
        "relatorio_por_classe": classification_report(
            teste["label"],
            previsoes,
            labels=[0, 1],
            target_names=[ROTULOS[0], ROTULOS[1]],
            output_dict=True,
            zero_division=0,
        ),
    }

    # A cobertura é a fração das notícias para as quais os limites permitem decidir a taxa indeterminada é a fração em que o modelo se abstém.
    # Registra separadamente a qualidade nos casos decididos e a fração em abstinência.
    previsoes_abstencao, probabilidades_abstencao, similaridades = (
        modelo.predict_with_abstention(teste["texto_modelo"])
    )
    classificados = previsoes_abstencao != -1
    rotulos_classificados = teste.loc[classificados, "label"]
    previsoes_classificadas = previsoes_abstencao[classificados]
    # Remove abstenções antes de medir os erros entre as previsões efetivas.
    matriz_classificados = confusion_matrix(
        rotulos_classificados,
        previsoes_classificadas,
        labels=[0, 1],
    )
    verdadeiras_no_teste = int((teste["label"] == 0).sum())
    falsos_positivos = int(matriz_classificados[0, 1])
    # Cobertura e taxa de indeterminação contextualizam a acurácia entre exemplos decididos: abster-se reduz o conjunto de respostas conclusivas.
    metricas["avaliacao_com_abstencao"] = {
        "limiar_confianca_minima": LIMIAR_CONFIANCA_MINIMA,
        "limiar_similaridade_minima": LIMIAR_SIMILARIDADE_MINIMA,
        "cobertura": float(classificados.mean()),
        "taxa_indeterminada": float((~classificados).mean()),
        "acuracia_balanceada_nos_classificados": balanced_accuracy_score(
            rotulos_classificados,
            previsoes_classificadas,
        ),
        "falsas_previstas_em_verdadeiras": falsos_positivos,
        "taxa_falsas_previstas_em_verdadeiras": (
            falsos_positivos / verdadeiras_no_teste
        ),
        "matriz_confusao_labels_0_1": matriz_classificados.tolist(),
        "relatorio_por_classe": classification_report(
            rotulos_classificados,
            previsoes_classificadas,
            labels=[0, 1],
            target_names=[ROTULOS[0], ROTULOS[1]],
            output_dict=True,
            zero_division=0,
        ),
        "similaridade_media_maxima": float(similaridades.mean()),
        "confianca_media": float(probabilidades_abstencao.max(axis=1).mean()),
    }
    return metricas


def main():
    """Comentário: Divide antes de balancear, avalia e só então ajusta o artefato de produção."""
    # Primeiro divide o conjunto original, para manter o teste representativo e impedir que a amostragem de balanceamento influencie sua composição.
    dados_originais = carregar_dataset()
    grupos_originais = construir_grupos_sem_vazamento(dados_originais)
    treino_original, teste, grupos_treino_original, grupos_teste = dividir_treino_teste(
        dados_originais,
        grupos_originais,
    )
    # O balanceamento usa apenas o treino; os registros de teste ficam intocados.
    treino, falsas_restantes_treino, _ = criar_dataset_balanceado(treino_original)
    # Recalcula os identificadores após o balanceamento, pois as linhas mudaram.
    grupos_treino = construir_grupos_sem_vazamento(treino)
    print(
        f"Dataset original: {len(dados_originais):,} registros e "
        f"{len(np.unique(grupos_originais)):,} grupos sem textos iguais "
        "após normalização de caixa; "
        f"partição: {len(treino_original):,} para treino e {len(teste):,} para teste."
    )
    print(
        f"Treino balanceado: {len(treino):,} registros; "
        f"teste preservado sem reamostragem: {len(teste):,} registros."
    )
    print(
        "Treinando baseline TF-IDF + regressão logística com calibração "
        "Platt em previsões fora da amostra agrupadas..."
    )

    # A calibração Platt e a escolha do limiar usam apenas o treino balanceado, o teste ainda não foi consultado nesta etapa.
    modelo_avaliacao = ClassificadorTextoCalibrado()
    modelo_avaliacao.fit(
        treino["texto_modelo"],
        treino["label"],
        groups=grupos_treino,
    )
    # A avaliação é feita uma única vez no conjunto separado antes do modelo final.
    metricas = avaliar(modelo_avaliacao, teste)
    print(json.dumps(metricas, ensure_ascii=False, indent=2))

    print("Ajustando o modelo final com todos os dados após a avaliação...")
    # Depois de registrar as métricas isoladas, treina o artefato final com todos os dados rotulados disponíveis. 
    # Essa etapa não altera a avaliação já salva.
    dados, falsas_restantes, contagens_temas = criar_dataset_balanceado(
        dados_originais
    )
    grupos = construir_grupos_sem_vazamento(dados)
    modelo_final = ClassificadorTextoCalibrado()
    modelo_final.fit(
        dados["texto_modelo"],
        dados["label"],
        groups=grupos,
    )
    # Salva o estimador que será carregado pela API, treinado com todos os registros disponíveis depois de concluída a avaliação.
    joblib.dump(modelo_final, CAMINHO_MODELO)

    # Registra configuração, proveniência e métricas junto ao modelo para interpretar futuras previsões e reproduzir a avaliação.
    metricas_com_metadados = {
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "modelo": (
            "TF-IDF (unigramas e bigramas) + regressão logística; "
            "calibração Platt com validação agrupada"
        ),
        "versao_sklearn": sklearn.__version__,
        "semente": SEMENTE,
        "divisao": {
            "metodo": "StratifiedGroupKFold",
            "grupos": "texto_modelo convertido para minúsculas",
            "particoes": PARTICOES_DIVISAO,
            "particoes_teste": PARTICOES_TESTE,
            "proporcao_teste_planejada": PARTICOES_TESTE / PARTICOES_DIVISAO,
            "proporcao_teste_real": len(teste) / len(dados_originais),
            "registros_dataset_original": len(dados_originais),
            "registros_treino_original": len(treino_original),
            "registros_treino_balanceado": len(treino),
            "registros_teste": len(teste),
            "arquivos_treino": int(treino_original["arquivo_origem"].nunique()),
            "arquivos_teste": int(teste["arquivo_origem"].nunique()),
            "grupos_treino_original": int(
                np.unique(grupos_treino_original).size
            ),
            "grupos_treino_balanceado": int(np.unique(grupos_treino).size),
            "grupos_teste": int(np.unique(grupos_teste).size),
        },
        "contagem_classes_dataset": {
            ROTULOS[label]: int(quantidade)
            for label, quantidade in dados_originais["label"].value_counts().items()
        },
        # O hash identifica exatamente o CSV balanceado usado neste treinamento.
        "sha256_dataset_balanceado": hashlib.sha256(
            CAMINHO_DATASET_BALANCEADO.read_bytes()
        ).hexdigest(),
        "balanceamento_tematica": {
            "metodo": "MiniBatchKMeans em TF-IDF de unigramas e bigramas",
            "quantidade_grupos": QUANTIDADE_TEMAS,
            "amostragem_falsas": "quota aproximadamente uniforme por grupo temático",
            "verdadeiras_utilizadas": int((dados["label"] == 0).sum()),
            "falsas_selecionadas": int((dados["label"] == 1).sum()),
            "falsas_preservadas_para_eda": int(len(falsas_restantes)),
            "falsas_preservadas_para_eda_no_treino": int(
                len(falsas_restantes_treino)
            ),
            "distribuicao_por_tema": [
                {
                    "tema_cluster": int(tema),
                    "termos_representativos": termos,
                    "verdadeiras": int(linha["VERDADEIRA"]),
                    "falsas": int(linha["FALSA"]),
                }
                for (tema, termos), linha in contagens_temas.iterrows()
            ],
        },
        "metricas_teste": metricas,
        "observacao": (
            "A partição de teste é formada antes do balanceamento temático e "
            "permanece sem reamostragem. As métricas são agrupadas por "
            "texto igual após conversão para minúsculas; os TXT não fornecem "
            "URL ou fonte editorial para "
            "agrupamento adicional. "
            "O limiar foi selecionado apenas nos dados de treino para maximizar "
            "a acurácia balanceada. As probabilidades calibradas não comprovam "
            "veracidade. A avaliação com abstinência exige confiança mínima e "
            "similaridade mínima com o treino; textos fora desses limites são "
            "retornados como INCERTOS. O dataset não contém a classe INCERTA."
        ),
        "limiar_sugestao_falsa_modelo_final": modelo_final.limiar_falsa,
    }
    # Grava JSON legível por humanos e com caracteres acentuados preservados.
    CAMINHO_METRICAS.write_text(
        json.dumps(metricas_com_metadados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Modelo salvo em: {CAMINHO_MODELO}")
    print(f"Métricas salvas em: {CAMINHO_METRICAS}")


if __name__ == "__main__":
    main()
