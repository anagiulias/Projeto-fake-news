"""Pipeline TF-IDF calibrado com política de abstenção para textos curtos."""

# Importações de bibliotecas externas sem dependências de back ou front.
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

# Fixa para reprodutibilidade e garante que o ajuste seja determinístico.
SEMENTE = 42
# A abstenção exige simultaneamente os dois limites abaixo.
LIMIAR_CONFIANCA_MINIMA = 0.70
LIMIAR_SIMILARIDADE_MINIMA = 0.16

# Monta o pipeline lexical que transforma texto e prevê classes binárias usado em fit() e predict().
def criar_pipeline():
    # TF-IDF representa unigramas/bigramas; a regressão aprende os pesos das classes.
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    # Unigramas capturam termos, bigramas também capturam pares frequentes como "não funciona".
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=150_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classificador",
                LogisticRegression(
                    # Compensa desequilíbrio residual e limita ciclos de ajuste.
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=SEMENTE,
                    solver="liblinear",
                ),
            ),
        ]
    )

# Classificador binário com calibração e abstinência por confiança ou similaridade.
class ClassificadorTextoCalibrado:

    def __init__(self):
        """Inicializa os limites e os atributos preenchidos durante o ajuste."""
        # Esses campos são preenchidos em fit(). None indica um objeto ainda não treinado ou um artefato incompatível/incompleto.
        self.estimador = None
        self.calibrador = None
        self.classes_ = None
        self.limiar_falsa = 0.5
        self.limiar_confianca_minima = LIMIAR_CONFIANCA_MINIMA
        self.limiar_similaridade_minima = LIMIAR_SIMILARIDADE_MINIMA
        self.matriz_referencia = None

    def fit(self, textos, rotulos, groups):
        # Ajusta pipeline e calibrador usando previsões fora da amostra agrupadas.
        textos = pd.Series(textos).reset_index(drop=True)
        rotulos = np.asarray(rotulos)
        groups = np.asarray(groups)
        if len(textos) != len(rotulos) or len(textos) != len(groups):
            raise ValueError("Textos, rótulos e grupos precisam ter o mesmo tamanho.")

        # Guarda um score por exemplo para calibrar sem reutilizar previsões do treino.
        scores_oof = np.empty(len(textos), dtype=np.float64)
        # Cada texto recebe um score de um modelo que não foi ajustado com ele, assim a calibração e o limiar não dependem de previsões in-sample.
        divisao = StratifiedGroupKFold(
            n_splits=3,
            shuffle=True,
            random_state=SEMENTE,
        )
        # Validação agrupada evita que duplicatas definidas por `groups` apareçam simultaneamente no ajuste e na previsão usada para calibrar.
        for indices_treino, indices_validacao in divisao.split(
            textos,
            rotulos,
            groups=groups,
        ):
            estimador = clone(criar_pipeline())
            estimador.fit(textos.iloc[indices_treino], rotulos[indices_treino])
            scores_oof[indices_validacao] = estimador.decision_function(
                textos.iloc[indices_validacao]
            )

        # A regressão logística sobre os scores aprende a calibração Platt.
        self.calibrador = LogisticRegression(solver="lbfgs")
        self.calibrador.fit(scores_oof.reshape(-1, 1), rotulos)
        # Localiza a coluna da classe 1 sem assumir que a ordem das classes retornadas pela biblioteca permanecerá fixa.
        indice_falsa = list(self.calibrador.classes_).index(1)
        probabilidades_falsas_oof = self.calibrador.predict_proba(
            scores_oof.reshape(-1, 1)
        )[:, indice_falsa]

        falsos_positivos, verdadeiros_positivos, limiares = roc_curve(
            rotulos,
            probabilidades_falsas_oof,
            pos_label=1,
        )
        # roc_curve pode incluir um limiar infinito para representar o ponto inicial. Não sendo uma escolha operacional para classificação.
        indices_validos = np.flatnonzero(np.isfinite(limiares))
        indice_melhor = indices_validos[
            np.argmax(
                verdadeiros_positivos[indices_validos]
                - falsos_positivos[indices_validos]
            )
        ]
        # Escolhe o limiar que maximiza TPR - FPR (índice de Youden) no OOF.
        self.limiar_falsa = float(limiares[indice_melhor])
        # Reajusta o estimador completo para uso em produção depois da calibração.
        self.estimador = criar_pipeline()
        self.estimador.fit(textos, rotulos)
        self.classes_ = self.estimador.named_steps["classificador"].classes_
        # Mantém os vetores do treino para a política de abstenção por similaridade.
        self.matriz_referencia = self.estimador.named_steps["tfidf"].transform(
            textos
        )
        return self

    def predict_proba(self, textos):
        """Retorna probabilidades calibradas na ordem definida por classes_."""
        # O calibrador foi treinado com decision_function, então recebe o mesmo tipo de score durante a inferência.
        scores = self.estimador.decision_function(textos)
        return self.calibrador.predict_proba(np.asarray(scores).reshape(-1, 1))

    def similaridade_maxima(self, textos):
        # Mede a similaridade TF-IDF máxima com os textos vistos no ajuste.
        if self.matriz_referencia is None:
            raise RuntimeError(
                "O modelo não contém referências de treino. "
                "Execute treinar_classificador.py novamente."
            )

        # Vetores TF-IDF normalizados permitem comparar documentos por produto escalar.
        vetorizador = self.estimador.named_steps["tfidf"]
        vetores_consulta = vetorizador.transform(textos)
        # O produto entre linhas TF-IDF normalizadas equivale à similaridade cosseno. Reduzimos a cada texto sua maior correspondência no treino.
        similaridades = vetores_consulta @ self.matriz_referencia.T
        similaridades_maximas = similaridades.max(axis=1)
        if hasattr(similaridades_maximas, "toarray"):
            similaridades_maximas = similaridades_maximas.toarray()
        return np.asarray(similaridades_maximas).ravel()

    def predict_with_abstention(self, textos):
        #Prevê uma classe ou -1 quando confiança ou similaridade são insuficientes.
        probabilidades = self.predict_proba(textos)
        similaridades = self.similaridade_maxima(textos)
        confiancas = probabilidades.max(axis=1)
        # -1 representa abstenção e só substituímos quando os dois limites são atendidos.
        previsoes = np.full(len(probabilidades), -1, dtype=np.int64)
        # Não basta o modelo ter probabilidade alta se o texto estiver distante dos exemplos rotulados que sustentam essa estimativa.
        decisivos = (
            (similaridades >= self.limiar_similaridade_minima)
            & (confiancas >= self.limiar_confianca_minima)
        )
        previsoes[decisivos] = self.classes_[
            np.argmax(probabilidades[decisivos], axis=1)
        ]
        return previsoes, probabilidades, similaridades
