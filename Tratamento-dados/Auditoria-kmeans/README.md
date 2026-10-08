# Auditoria temática Fake.br — resultados executados

Fonte: `size_normalized_texts.zip` enviado na conversa. Os arquivos TXT foram convertidos em CSV com as colunas `texto_modelo`, `label` (0=verdadeira, 1=falsa) e `arquivo_origem`, sem a etapa de limpeza/deduplicação do notebook original. Assim, este é um **CSV reconstruído para a auditoria**, não uma verificação byte a byte do `noticias_rotuladas_tratadas.csv` do repositório.

## Resultados observados
- Total: 1.821 textos (821 verdadeiros e 1.000 falsos).
- Treino original: 1.274; teste separado: 547.
- Treino após seleção: 1.148 (574 verdadeiros e 574 falsos).
- Falsos não selecionados do treino: 126.
- MiniBatchKMeans: 30 clusters, com os parâmetros importados diretamente de `treinar_classificador.py`.

## Arquivos
- `scripts/05_auditoria_kmeans_treino.py`: reproduz o split e a seleção temática do script fornecido.
- `scripts/00_reconstruir_csv.py`: reconstrói o CSV a partir do ZIP de textos.
- `imagens/kmeans_antes_depois_contagens.png`: composição por cluster, antes e depois.
- `imagens/kmeans_antes_depois_percentuais.png`: percentuais por cluster, antes e depois.
- `relatorios/comparacao_clusters_antes_depois.csv`: tabela comparativa por cluster.
- `relatorios/auditoria_kmeans.json`: contagens e parâmetros resumidos.
- `relatorios/noticias_rotuladas_balanceadas_auditoria.csv`: treino selecionado.
- `relatorios/falsas_nao_amostradas_auditoria.csv`: falsas excedentes do treino.

## Limitação importante
A amostragem **equilibra o total das duas classes**, mas **não equilibra cada cluster internamente**: preserva todas as verdadeiras e distribui cotas das falsas. O efeito na generalização deve ser testado com uma comparação de modelos com/sem balanceamento no mesmo conjunto de teste. A rotulagem semântica dos clusters é aproximada (termos mais fortes dos centroides).

## Reprodução
`python scripts/05_auditoria_kmeans_treino.py --dataset /caminho/noticias_rotuladas_tratadas.csv --treino-script /caminho/treinar_classificador.py --saida Tratamento-dados`
