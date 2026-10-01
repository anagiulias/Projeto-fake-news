# Relatório de Análise e Tratamento de Notícias

**Notebook:** [`tratamento_fakeNews.ipynb`](tratamento_fakeNews.ipynb)  
**Ambiente utilizado:** Google Colab
**Banco de dados:** `Historico_de_materias.csv`  

## 1. Objetivo

Documentar o pré-processamento e a análise exploratória de notícias em português. O notebook transforma o texto em medidas e representações que permitem examinar distribuição, vocabulário, entidades, similaridade e tópicos.

**Observação:**
Esta análise não classifica notícias como verdadeiras ou falsas. Os gráficos e modelos apresentados são exploratórios e não substituem checagem de fatos nem avaliação com dados rotulados.

## 2. Dados e preparação

O notebook espera acessar o arquivo `Historico_de_materias.csv` no Google Drive montado pelo Colab. A coluna `conteudo_noticia` fornece o texto; `assunto` é usada para comparar categorias.

O pré-processamento cria a coluna `texto_limpo`: converte o conteúdo para minúsculas, substitui pontuação por espaços preservando acentos, normaliza espaços e remove stopwords em português. O DataFrame `final_df` reúne o texto preparado e as características derivadas.

### Estrutura e exemplos

![Imagem da base de dados original](img/Tabela1.png)

*Banco de Dados - Estrutura inicial dos dados.*

![Imagem da base de dados tratados](img/Tabela2.1.png)

*Tabela 2.1. Representação após o tratamento textual.*

![Imagem de novas colunas geradas](img/Tabela2.2.png)

*Tabela 2.2. Características derivadas.*

## 3. Procedimentos

1. **Limpeza textual:** normalização de caixa e espaços, remoção de pontuação e stopwords. A limpeza preserva letras acentuadas.
2. **Características:** comprimento do texto limpo, quantidade de palavras, comprimento médio das palavras e comprimento médio das frases. A última medida usa o texto original, pois depende da pontuação.
3. **Distribuição e valores atípicos:** estatísticas descritivas, gráficos por assunto e identificação exploratória pelo critério `|z-score| >= 3`.
4. **Vocabulário:** frequências de palavras, bigramas e trigramas, além de nuvens de palavras.
5. **Análise linguística:** reconhecimento de entidades nomeadas (NER) e contagem de adjetivos, substantivos e verbos com spaCy.
6. **Representação semântica:** embeddings, projeções t-SNE em 2D e 3D e modelagem de tópicos com BERTopic.

## 4. Resultados visuais disponíveis

As imagens abaixo são as saídas encontradas na pasta `img`. Elas documentam as etapas do notebook; como os dados numéricos não foram transcritos aqui, a interpretação deve ser feita diretamente nos gráficos e nas saídas reproduzidas ao executar o notebook.

### Perfil da base e características textuais

![Quantidade de notícias por assunto](img/Gráfico1.png)

*Gráfico 1. Contagem de registros por assunto.*

![Comprimento dos textos](img/Gráfico2.1.png)

*Gráfico 2. Distribuição do comprimento dos textos.*

![Contagem de palavras](img/Gráfico2.2.png)

*Gráfico 2.1. Distribuição da contagem de palavras.*

![Comprimento médio das palavras](img/Gráfico2.3.png)

*Gráfico 2.2. Distribuição do comprimento médio das palavras.*

![Distribuição geral das características textuais](img/Gráfico2.4.png)

*Gráfico 2.3. Distribuição do comprimento médio das frases.*

### Distribuição e observações estatísticas

![Distribuição dos valores atípicos por assunto](img/Gráfico3.png)

*Gráfico 3. Distribuição dos textos sinalizados como atípicos.*

![Relação entre comprimento e comprimento médio das palavras](img/Gráfico4.png)

*Gráfico 4. Relação entre comprimento do texto e comprimento médio das palavras; a visualização limita os textos mais longos para facilitar a leitura.*

![Saída estatística de assimetria e curtose](img/Saída1.png)

*Saída 1. Estatísticas de assimetria e curtose do comprimento.*

![Quantidade de valores atípicos](img/Saída2 - outliers.png)

*Saída 2. Quantidade de registros sinalizados pelo critério de z-score.*

### Vocabulário e estrutura gramatical

![Nuvem de palavras](img/Gráfico5.png)

*Gráfico 5. Visualização de termos recorrentes.*

![Nuvem de bigramas](img/Gráfico5.1.png)

*Gráfico 5.1. Nuvem de bigramas.*

![Frequências de palavras e n-gramas](img/Gráfico6.png)

*Gráfico 6. Visão geral das frequências de termos.*

![Unigramas mais frequentes](img/Gráfico6.1.png)

*Gráfico 6.1. Palavras isoladas mais frequentes.*

![Bigramas mais frequentes](img/Gráfico6.2.png)

*Gráfico 6.2. Sequências de duas palavras mais frequentes.*

![Classes gramaticais mais frequentes](img/Gráfico7.png)

*Gráfico 7. Visão geral das classes gramaticais analisadas.*

![Adjetivos mais frequentes](img/Gráfico7.1.png)

*Gráfico 7.1. Adjetivos mais frequentes na amostra processada.*

![Substantivos mais frequentes](img/Gráfico7.2.png)

*Gráfico 7.2. Substantivos mais frequentes na amostra processada.*

### Entidades, similaridade e tópicos

![Entidades reconhecidas no texto](img/Saída3.png)

*Saída 3. Trecho usado na demonstração de reconhecimento de entidades.*

![Visualização de entidades nomeadas](img/Saída3.1.png)

*Saída 3.1. Visualização das entidades detectadas pelo spaCy.*

![Projeção semântica](img/Gráfico8.png)

*Gráfico 8. Projeção dos embeddings para inspeção de similaridade.*

![Projeção t-SNE em duas dimensões](img/Gráfico8.1.png)

*Gráfico 8.1. Projeção t-SNE 2D dos textos amostrados.*

![Visualizações de tópicos](img/Gráfico9.png)

*Gráfico 9. Saída da etapa de modelagem de tópicos.*

![Detalhamento de tópicos](img/Gráfico9.1.png)

*Gráfico 9.1. Visualização complementar dos tópicos identificados.*

## 5. Limitações e cuidados

- O caminho do CSV está configurado para o Google Drive e precisa ser ajustado para outro ambiente.
- O modelo de embeddings `all-MiniLM-L6-v2` é voltado principalmente a textos em inglês; seu uso em português pode prejudicar a qualidade das similaridades e dos tópicos. Recomenda-se comparar com um modelo multilíngue ou treinado para português.
- A análise POS utiliza as primeiras 3.000 linhas, que podem não representar a base se os dados estiverem ordenados por assunto, data ou fonte.
- t-SNE é uma projeção visual: seus eixos não têm interpretação direta, e distâncias globais não devem ser tratadas como medidas exatas de similaridade.
- O critério de z-score é exploratório e pode ser inadequado para distribuições muito assimétricas. Um outlier pode ser uma notícia válida, não um erro.
- Contagens por assunto dependem do tamanho de cada grupo; para comparar categorias, examine também frequências relativas.
- As imagens são saídas previamente salvas. O notebook precisa ser executado novamente para confirmar que código, base e figuras estão sincronizados.

## 6. Conclusão

O notebook reúne etapas de preparação textual e análise exploratória úteis para estudar o vocabulário, as características dos textos e possíveis agrupamentos temáticos. Os resultados devem ser interpretados como pistas para investigação, não como evidência de veracidade ou falsidade. Para conclusões reproduzíveis, execute o fluxo completo com a base identificada, registre as versões dos modelos e valide as observações em uma amostra revisada.
