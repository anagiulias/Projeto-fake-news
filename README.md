# Verificador de Notícias

Projeto experimental com uma extensão Chrome e uma API Python local. A
extensão captura uma notícia e o backend combina:

1. **Classificador supervisionado local**, treinado com os arquivos TXT rotulados das
   pastas `datasets/fake/` e `datasets/true/`;
2. **Google Fact Check Tools API opcional**, para buscar checagens já publicadas
   por organizações de fact-checking;
3. **Resumo da notícia local opcional via Ollama**, que descreve a alegação sem decidir se
   é verdadeira ou falsa.

As saídas são pistas para estudo, não confirmação factual. A previsão local é
binária e pode ser inconclusiva; ratings parciais do Google são apresentados
como publicados, sem serem convertidos em rótulos locais.

## Estrutura do projeto

| Caminho | Papel |
| --- | --- |
| `Front-end/` | Extensão Chrome. `main.js` é executado; `main.ts` documenta contratos tipados; `manifest.json` configura o popup. |
| `Back-end/main.py` | API FastAPI, integração do classificador, Google Fact Check e Ollama. |
| `Back-end/classificador_veracidade.py` | TF-IDF, regressão logística, calibração e abstenção. |
| `Back-end/treinar_classificador.py` | Split 70/30, balanceamento do treino, métricas e geração do modelo. |
| `Back-end/fact_check_google.py` | Cliente da API Google Fact Check Tools. |
| `Back-end/test_fact_check_google.py` | Testes simulados da integração Google. |
| `Tratamento-dados/tratamento_datasets_rotulados.ipynb` | Lê e valida TXT e gera CSV de treino e auditoria. |
| `Tratamento-dados/tratamento_fakeNewsFinal.ipynb` | EDA textual dos mesmos TXT rotulados. |
| `datasets/fake/*.txt` | Exemplos rotulados como FALSA pela pasta de origem. |
| `datasets/true/*.txt` | Exemplos rotulados como VERDADEIRA pela pasta de origem. |
| `datasets/tratados/` | CSVs tratados, auditados e saídas de treino. |
| `requirements.txt` | Dependências Python do backend. |

**Observação**: Não há mais dependência do `Historico_de_materias.csv`, dos CSVs originais
antigos nem de um acervo sem rótulos para busca local. A API Google é externa e
opcional; os TXT locais são fonte de treino / EDA, não evidências atuais.

## Dados, limpeza e rótulos

As pastas atuais contêm aproximadamente 1.000 TXT em `fake/` e 821 em `true/`
(contagens do checkout documentado; confirme após atualizar os dados). <br><br>
O pipeline é:

1. `tratamento_datasets_rotulados.ipynb` lê os TXT em UTF-8. A pasta determina
   os rótulos (`fake = 1`, `true = 0`); nenhuma classe é deduzida do conteúdo.
2. O processamento mantém pontuação, caixa, negações e stopwords. Para
   `texto_modelo`, apenas espaços são normalizados. Textos curtos ou com erro de
   encoding são apontados explicitamente.
3. Textos iguais após conversão para minúsculas são tratados como duplicatas
   dentro da mesma classe. Se aparecerem nas duas classes, são sinalizados e
   impedem o treino até revisão. O CSV de auditoria registra as contagens.
4. O CSV tratado guarda também `arquivo_origem`, que é somente um caminho
   relativo para rastrear o TXT. As fontes não fornecem URL, data ou publicador.
5. `tratamento_fakeNewsFinal.ipynb` faz EDA das duas classes. Limpeza adicional
   para gráficos não substitui o texto preservado usado pelo classificador.

É importante revisar a procedência dos rótulos antes de treinar. A pasta é uma codificação
prática, não comprovação de que cada notícia foi rotulada corretamente.

### O que acontece com o teste 70/30

`Back-end/treinar_classificador.py` cria a divisão estratificada e agrupada
antes de balancear os dados:

- Cerca de **70%** ficam no treino e **30%** no teste;
- Textos iguais após conversão para minúsculas permanecem na mesma partição;
- Apenas o treino passa por balanceamento temático;
- O teste não é replicado, então suas métricas refletem a distribuição
  existente;
- O modelo de produção é ajustado com todos os dados após a avaliação;
- O relatório de teste usado pela API é salvo em
  `Back-end/metricas_veracidade.json`.

Como os TXT não trazem URL nem identificador de alegação, paráfrases relacionadas
ainda podem aparecer em treino e teste. Para uma avaliação mais rigorosa,
recupere identificadores de alegações/fontes e agrupe-os antes da divisão.
É recomendado também avaliar notícias recentes rotuladas por revisão editorial independente.

## Classificador e estimativas

O classificador **não é um modelo generativo**. Ele usa:

- Vetorização TF-IDF de unigramas e bigramas;
- Regressão logística com pesos balanceados;
- Calibração Platt com previsões agrupadas fora da amostra;
- Abstenção quando confiança ou similaridade com os exemplos de treino ficam
  abaixo dos limites definidos.

O dataset contém apenas `VERDADEIRA` e `FALSA`. A interface pode descrever
tendências moderadas ou fortes a partir das probabilidades, mas não declara resultados intermediários. `INCERTO` indica que o sistema se absteve; não
é uma terceira classe aprendida. A avaliação textual da API Google é exibida
separadamente.

## Instalação no Windows

Ops! Tópico ainda em fase de teste...

## Iniciar a API

```powershell
python .\Back-end\main.py
```

A API local fica em `http://127.0.0.1:8000`.

- `POST /verificar`: recebe o texto integral da notícia e, opcionalmente, o
  título/início do artigo para classificação;
- `POST /feedback`: recebe avaliação do resultado e grava uma linha em
  `Back-end/feedback_noticias.jsonl`. Feedback não retreina o classificador.

O backend não pesquisa um acervo local. As checagens externas são obtidas pelo
Google Fact Check Tools quando configurado, e são separadas da saída
probabilística local.

## Google Fact Check Tools API (opcional)

Configure um projeto Google Cloud com a API habilitada e defina a chave somente
no ambiente do processo:

```powershell
$env:GOOGLE_FACT_CHECK_API_KEY = "SUA-CHAVE"
python .\Back-end\main.py
```

Tenha atenção com a segurança da chave gerada. Em último caso, ela poderá ser adicionada 
em um arquivo `.env`. O backend envia ao Google um campo `Título` com o resumo do
Ollama, quando disponível; se a geração falhar, usa até 150 caracteres do texto
de classificação. As quebras de linha são removidas antes da consulta. Os
resultados são checagens previamente publicadas, podem não corresponder ao
contexto da matéria aberta e não alimentam automaticamente o treino.

## Resumo Ollama (opcional)

Instale Ollama e baixe o modelo padrão:

```powershell
ollama pull llama3.2:1b
```

O backend usa por padrão `http://127.0.0.1:11434` e `llama3.2:1b`. As variáveis
`OLLAMA_URL` e `OLLAMA_MODEL` permitem alterar essas configurações. Por sua vez, o resumo 
é uma descrição da alegação e não decide sua veracidade.

## Carregar a extensão

1. Inicie a API e deixe-a rodando.
2. No Chrome, abra `chrome://extensions/` e ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação** e escolha `Front-end/`.
4. Abra uma página de notícia e clique no ícone da extensão.

O popup carrega `Front-end/main.js`; `main.ts` é uma referência tipada e não é
compilado. `Front-end/README.md` documenta o fluxo JS/TS/JSON e como manter as
URLs e permissões alinhadas.

