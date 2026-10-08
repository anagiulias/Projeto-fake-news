# RELATÓRIO TÉCNICO

# Análise Exploratória de Dados do Fake.br Corpus

**Distribuição de classes, extensão textual, vocabulário discriminante e auditoria do balanceamento temático com MiniBatchKMeans**

**Projeto:** Verificador Inteligente de Notícias  
**Base:** `size_normalized_texts`  
**Data de elaboração:** 08/10/2026

---

## Resumo executivo

A análise exploratória incluiu **1.821 notícias (1.000 falsas e 821 verdadeiras)**. Os textos das duas classes exibiram comprimentos médios próximos.

A inspeção lexical identificou termos associados às classes e indícios de dependência temática.

Uma auditoria separada reproduziu a lógica de divisão e balanceamento do script de treino:

- **1.274 registros** no treino inicial;
- **1.148 registros** após subamostragem;
- **547 registros** no teste preservado.

As análises exploratórias de oito clusters e a auditoria de 30 clusters são procedimentos distintos e não devem ser confundidos.

---

## 1. Objetivos e escopo

Os objetivos da análise são:

- Quantificar as classes.
- Descrever palavras e caracteres por classe.
- Caracterizar termos e n-gramas.
- Investigar a associação entre agrupamentos lexicais e rótulos.
- Documentar a amostragem temática do treinamento.

Este relatório integra resultados de duas execuções já realizadas, com seus artefatos de saída, e a leitura dos scripts do classificador e treinamento.

---

## 2. Dados e procedimentos

### 2.1. Fonte dos dados

**Fonte:** arquivos TXT do subconjunto `size_normalized_texts` do Fake.br Corpus, consolidados para a EDA.

**Rótulos do projeto:**

| Rótulo | Classificação |
|---|---|
| 0 | VERDADEIRA |
| 1 | FALSA |

A auditoria do treino foi executada com um CSV reconstruído dos TXT, e não com o CSV original exportado pelo notebook de tratamento.

Portanto, equivalência byte a byte com o treinamento histórico não foi demonstrada.

### 2.2. Configuração do classificador

O classificador final emprega:

| Componente | Configuração |
|---|---|
| Vetorização | TF-IDF |
| N-gramas | Unigramas e bigramas |
| `min_df` | 2 |
| `max_features` | 150.000 |
| Modelo | Regressão logística |
| `class_weight` | `balanced` |
| Calibração | Platt |
| Validação | Agrupada |

### 2.3. Configuração do agrupamento temático

O agrupamento temático utiliza outra representação TF-IDF, com uma lista própria de stopwords.

| Parâmetro | Valor |
|---|---|
| Algoritmo | MiniBatchKMeans |
| `min_df` | 3 |
| `max_features` | 50.000 |
| Quantidade de clusters | 30 |
| `batch_size` | 1024 |
| `n_init` | 3 |
| `max_iter` | 100 |
| Semente aleatória | 42 |

---

## 3. Distribuição de classes

| Classe | Quantidade | Percentual |
|---|---:|---:|
| Falsas | 1.000 | 54,91% |
| Verdadeiras | 821 | 45,09% |
| **Total** | **1.821** | **100,00%** |

Há diferença de **179 notícias** entre as classes.

O desequilíbrio global é moderado, mas não informa se cada assunto está representado de maneira equivalente.

### Figura 1. Frequência e proporção de notícias por classe

O gráfico apresenta a distribuição absoluta e percentual das duas classes:

- Falsas: 1.000 notícias (54,91%).
- Verdadeiras: 821 notícias (45,09%).

---

## 4. Comprimento dos textos

| Indicador | Falsas | Verdadeiras |
|---|---:|---:|
| Palavras — média | 177,49 | 178,13 |
| Palavras — mediana | 154 | 156 |
| Palavras — desvio-padrão | 100,04 | 96,58 |
| Caracteres — média | 1.072,64 | 1.078,63 |
| Caracteres — mediana | 942,5 | 952 |
| Caracteres — desvio-padrão | 602,43 | 584,99 |
| Textos vazios | 0 | 0 |

A diferença média foi de **0,64 palavra e 5,99 caracteres**, compatível com a normalização por tamanho.

As amplitudes e dispersões mostram, porém, que ainda existem textos de comprimentos variados; a semelhança entre médias não equivale à identidade das distribuições.

### Figura 2. Distribuições de palavras e caracteres por classe (boxplots)

Os boxplots apresentam as distribuições de comprimento das notícias falsas e verdadeiras, considerando:

- Número de palavras.
- Número de caracteres.

A visualização foi produzida sem exibir outliers.

### Figura 3. Histogramas da extensão dos textos

Os histogramas representam a densidade das distribuições de:

- Palavras por texto.
- Caracteres por texto.

As duas classes apresentam distribuições visualmente próximas, embora com variações de extensão e dispersão.

---

## 5. Vocabulário e n-gramas discriminantes

A EDA calculou frequências de termos e associações por classe.

A tabela apresenta exemplos de termos com maior associação positiva à classe falsa na execução exploratória.

A frequência documental indica em quantos documentos o termo aparece, não o número bruto de ocorrências.

| Termo | Docs. falsas | Docs. verdadeiras |
|---|---:|---:|
| lava-jato | 100 | 1 |
| diario brasil | 40 | 0 |
| jon-un | 29 | 0 |
| kim jon-un | 26 | 0 |
| internautas | 25 | 0 |
| etc | 24 | 0 |
| resumindo | 21 | 0 |
| perder | 21 | 0 |

### Figura 4. Vocabulário frequente nas duas classes

O gráfico compara os termos mais frequentes nos textos classificados como falsos e verdadeiros.

A visualização apresenta contagens de ocorrências dos termos em cada classe.

### Figura 5. Termos associados diferencialmente às classes

O gráfico apresenta os termos com maior associação diferencial às notícias falsas e verdadeiras.

A associação é representada pelo log-odds de presença por documento.

### 5.1. Interpretação dos padrões lexicais

A documentação do projeto menciona expressões como:

**Notícias falsas:**

- "vídeo"
- "redes sociais"
- "urgente"
- "veja"

**Notícias verdadeiras:**

- "tribunal"
- "federal"
- "segundo"
- "ministro"
- "afirmou"

Essas observações devem ser entendidas como padrões do corpus, não como critérios universais de veracidade.

Termos referentes a pessoas e eventos específicos também podem refletir viés de assunto.

Marcadores cronológicos, como dias da semana, podem ser correlações espúrias.

---

## 6. Estrutura temática: análise exploratória

A exploração inicial utilizou **oito agrupamentos lexicais**.

A associação entre cluster e classe apresentou os seguintes resultados:

| Indicador estatístico | Resultado |
|---|---:|
| Número de clusters exploratórios | 8 |
| Estatística qui-quadrado (χ²) | 124,47 |
| Valor-p | 8,97 × 10⁻²⁴ |
| V de Cramér | 0,261 |

Esse resultado sustenta a existência de dependência estatística entre os grupos textuais e os rótulos, sem estabelecer causalidade nem comprovar melhoria preditiva.

### Figura 6. Distribuição absoluta das classes nos oito clusters exploratórios

O gráfico apresenta a composição absoluta dos oito agrupamentos lexicais, identificados de 0 a 7.

Para cada cluster, são apresentadas as quantidades de notícias falsas e verdadeiras.

### Figura 7. Distribuição percentual das classes nos oito clusters exploratórios

O gráfico apresenta a composição percentual das classes em cada agrupamento.

A comparação permite observar a variação da proporção de notícias falsas e verdadeiras entre os diferentes clusters.

### Figura 8. Projeção exploratória dos textos no espaço de atributos

A projeção bidimensional utiliza SVD sobre os atributos TF-IDF, com finalidade ilustrativa.

A projeção bidimensional é apenas uma visualização aproximada do espaço textual e não deve ser interpretada como prova de separação semântica perfeita.

---

## 7. Auditoria do balanceamento temático do treinamento

O script `treinar_classificador.py` separa treino e teste antes da amostragem.

No conjunto de treinamento, o procedimento:

1. Constrói clusters com MiniBatchKMeans.
2. Mantém todas as notícias verdadeiras.
3. Subamostra notícias falsas por cotas aproximadamente uniformes entre os clusters.
4. Respeita a disponibilidade de exemplos em cada grupo.

Não há imposição de paridade entre notícias falsas e verdadeiras dentro de cada cluster.

### 7.1. Resultados da auditoria

| Indicador | Resultado |
|---|---:|
| Dataset consolidado | 1.821 |
| Treino antes do balanceamento | 1.274 |
| Treino após o balanceamento | 1.148 |
| Verdadeiras no treino balanceado | 574 |
| Falsas no treino balanceado | 574 |
| Falsas do treino não amostradas | 126 |
| Teste preservado | 547 |
| Clusters no script | 30 |

### 7.2. Composição do treinamento após o balanceamento

O conjunto selecionado contém:

| Classe | Quantidade | Proporção |
|---|---:|---:|
| Verdadeiras | 574 | 50,00% |
| Falsas | 574 | 50,00% |
| **Total** | **1.148** | **100,00%** |

O procedimento produziu paridade global entre as classes no conjunto de treinamento selecionado.

### Figura 9. Contagens por cluster no treino antes e depois da amostragem temática

O gráfico compara as contagens de notícias falsas e verdadeiras nos 30 clusters temáticos.

São apresentadas duas situações:

- Treino original, antes do balanceamento.
- Treino selecionado, após a aplicação das cotas por cluster.

### Figura 10. Proporções de classes por cluster no treino antes e depois da amostragem

O gráfico compara as proporções percentuais de notícias falsas e verdadeiras em cada cluster.

A visualização apresenta:

- Composição percentual antes da amostragem.
- Composição percentual depois da amostragem.

### 7.3. Interpretação do balanceamento

O balanceamento produziu paridade global no treino selecionado, preservando os **547 exemplos de teste**.

Os gráficos documentam a alteração da composição por cluster.

Entretanto, o procedimento não garante uniformidade perfeita dos clusters, nem demonstra por si só redução do erro de generalização.

A hipótese de mitigação de *topic bias* requer comparação controlada de desempenho com e sem amostragem, idealmente em teste externo ou temporal.

---

## 8. Cuidados metodológicos e limitações

### 8.1. Diferença entre os agrupamentos exploratórios e os de treinamento

Oito clusters exploratórios e 30 clusters de treinamento foram produzidos em análises diferentes.

Seus identificadores não são intercambiáveis.

### 8.2. Reconstrução do CSV utilizado na auditoria

O CSV utilizado na auditoria foi reconstruído dos arquivos TXT.

Falta confronto direto com o arquivo original:

`noticias_rotuladas_tratadas.csv`

Portanto, não foi demonstrada equivalência byte a byte entre os dados reconstruídos e os dados históricos de treinamento.

### 8.3. Interpretação dos clusters

O agrupamento temático utiliza representação lexical TF-IDF.

Os clusters não são categorias jornalísticas validadas manualmente.

### 8.4. Ausência de comparação entre modelos

O teste é separado antes da subamostragem.

Entretanto, os resultados apresentados neste relatório não incluem métricas comparativas de modelos treinados com e sem balanceamento.

### 8.5. Limitações das associações lexicais

Frequências e n-gramas discriminantes são associações observacionais.

Esses resultados não demonstram que:

- Linguagem formal implica veracidade.
- Linguagem urgente implica falsidade.

As associações precisam ser interpretadas dentro do contexto do corpus analisado.

### 8.6. Possibilidade de vazamento textual

A deduplicação exata e o agrupamento por texto em minúsculas reduzem vazamento por identidade textual.

Entretanto, esses procedimentos não excluem a presença de:

- Paráfrases.
- Republicações muito semelhantes.

---

## 9. Conclusões

O conjunto analisado tem predomínio moderado de notícias falsas e comprimentos médios semelhantes entre as classes.

As diferenças lexicais e a associação entre clusters e rótulos indicam risco plausível de aprendizagem de atalhos temáticos.

A auditoria confirma que a implementação de MiniBatchKMeans e cotas de amostragem produziu treino globalmente equilibrado, com:

- **574 notícias verdadeiras.**
- **574 notícias falsas.**
- **547 registros de teste preservados fora da reamostragem.**

A evidência disponível justifica a decisão de investigar mitigação de viés temático, mas não permite afirmar que o balanceamento foi essencial ou superior sem estudo comparativo de desempenho.

---

## 10. Materiais e rastreabilidade

Os seguintes materiais estão associados às análises apresentadas.

### 10.1. Corpus original

- `size_normalized_texts.zip`
  - Corpus TXT fornecido.

### 10.2. Artefatos da EDA exploratória

Diretório: `eda_fakebr/`

Arquivos:

- `resultados.json`
- `estatisticas_comprimento.csv`
- `termos_discriminantes.csv`
- Figuras 01–08

### 10.3. Implementação do classificador

Arquivo: `classificador_veracidade.py`

Componentes documentados:

- Vetorização TF-IDF.
- Regressão logística.
- Calibração.
- Abstenção.

### 10.4. Script de treinamento

Arquivo: `treinar_classificador.py`

Procedimentos documentados:

- Divisão agrupada.
- MiniBatchKMeans.
- Amostragem temática.

### 10.5. Artefatos de auditoria

Diretório: `Tratamento-dados/relatorios/`

Arquivos:

- `auditoria_kmeans.json`
- `comparacao_clusters_antes_depois.csv`

### 10.6. Visualizações comparativas

Diretório: `Tratamento-dados/imagens/`

Arquivos:

- `kmeans_antes_depois_*.png`

### 10.7. Documentação complementar

**Documento:** Documentação Técnica e Conceitual: Verificador Inteligente de Notícias.

**Seções utilizadas:** 3 e 4.

**Finalidade:** Enquadramento do projeto.

---

**Fake.br Corpus | Relatório técnico de EDA**

**Projeto:** Verificador Inteligente de Notícias  
**Data:** 08/10/2026
