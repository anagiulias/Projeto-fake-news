# Back-end: API e Classificador

O back-end fornece a API local usada pela extensão Chrome. O componente de
classificação é um modelo supervisionado binário treinado apenas com os TXT
rotulados nas pastas `datasets/fake/` e `datasets/true/`. A busca por checagens
publicadas é uma integração externa opcional, não existe mais acervo local sem
rótulos nem geração de embeddings de historico_materias.

## Componentes

| Arquivo | Função |
| --- | --- |
| `main.py` | API FastAPI: valida entradas, executa o classificador, solicita revisões ao Google, gera resumo local opcional e registra feedback. |
| `classificador_veracidade.py` | Pipeline TF-IDF/Regressão Logística, calibração e política de abstenção. |
| `treinar_classificador.py` | Lê o CSV tratado, divide, balanceia somente o treino, mede desempenho e grava o modelo e métricas. |
| `fact_check_google.py` | Cliente HTTP para Google Fact Check Tools API; usa a biblioteca padrão `urllib`. |
| `test_fact_check_google.py` | Testes do cliente externo com respostas simuladas, sem chave ou chamada real. |
| `feedback_noticias.jsonl` | Histórico append-only (formato de armazenamento de dados) das avaliações recebidas por `/feedback`. Esse arquivo deve ser preservado. |

## Roteiro de Estudo

Pontos importantes nos arquivos:

1. `main.py`: Vale conferir `NoticiaRequest` e `verificar_noticia` para entender a
   validação, a chamada do classificador e o formato da resposta. Depois ler
   `registrar_feedback` para ver como o feedback é validado e persistido.
2. `classificador_veracidade.py`: Acompanhe `criar_pipeline` e os métodos
   `fit`, `predict_proba` e `predict_with_abstention`. O último só decide quando
   confiança e similaridade com os exemplos de treino passam seus limites.
3. `treinar_classificador.py`: Confira `carregar_dataset`, `dividir_treino_teste`,
   `criar_dataset_balanceado` e `avaliar`, nessa ordem. A separação de teste
   acontece antes de balancear o treino para evitar que a avaliação seja feita
   sobre uma amostra alterada.
4. `fact_check_google.py`: Acompanhe `extrair_consulta`, `buscar_checagens_google` e
   `_normalizar_revisoes`. Essa integração apenas apresenta avaliações
   publicadas por terceiros; não converte ratings em rótulos do classificador.

Os comentários no código destacam decisões e limites importantes, as
string de documentação (docstrings) descrevem a responsabilidade de cada função. Para observar a API sem a extensão, inicie o servidor e use a documentação interativa em
`http://127.0.0.1:8000/docs`.

## Bibliotecas e Modelos

- **FastAPI** e **Uvicorn**: Endpoints HTTP locais e execução do servidor.
- **Pydantic**: Validação dos modelos de entrada.
- **pandas** e **NumPy**: Leitura e preparação tabular dos dados e cálculos.
- **scikit-learn**: TF-IDF (unigramas e bigramas), regressão logística,
  `StratifiedGroupKFold`, clusters temáticos e métricas.
- **joblib**: Serialização do classificador treinado.
- **Google Fact Check Tools API**: Consulta opcional de alegações que já foram
  avaliadas por organizações de checagem, não é um feed geral de notícias.
- **Ollama** (opcional, serviço externo ao Python): Geração de um resumo
  descritivo da alegação. O modelo padrão é `llama3.2:1b`, e o seu resumo não decide
  veracidade.

**O classificador não é um LLM**: ele aprende frequências/padrões lexicais em
TF-IDF e usa regressão logística. Uma calibração Platt ajustada com previsões
agrupadas fora da amostra estima probabilidades. O sistema pode responder
`INCERTO` quando a confiança calibrada ou a similaridade com textos de treino
ficam abaixo dos limites. A probabilidade é um sinal experimental, não uma
checagem factual.

## Dados e Treinamento

1. Em `Tratamento-dados/tratamento_datasets_rotulados.ipynb`, leia os TXT como
   UTF-8. A pasta determina os rótulos: `fake = 1`, `true = 0`. O notebook
   preserva os originais, remove cópias equivalentes após conversão para
   minúsculas dentro da mesma classe, sinaliza conflitos e grava:
   - `datasets/tratados/noticias_rotuladas_tratadas.csv`;
   - `datasets/tratados/auditoria_tratamento.csv`.
2. Revise a procedência dos rótulos e resolva conflitos antes do treino.
   `arquivo_origem` é apenas o caminho do TXT e essas fontes não contêm URL,
   data ou publicador.
3. Na raiz do repositório, execute:

   ```powershell
   python .\Back-end\treinar_classificador.py
   ```

4. O script cria uma divisão agrupada/estratificada com cerca de 70% para treino
   e 30% para teste. A divisão ocorre **antes** do balanceamento temático. Os
   textos de teste mantêm a distribuição original, somente o treino é
   balanceado. Textos iguais após conversão para minúsculas ficam na mesma
   partição. Sem URL ou identificador de alegação, paráfrases ainda podem
   atravessar as partições.
5. As métricas do teste são gravadas em `metricas_veracidade.json`. Após medir,
   o script treina o modelo de produção com o conjunto completo balanceado e
   grava `modelo_veracidade.joblib`.

## API Local

Inicie na raiz do projeto:

```powershell
python .\Back-end\main.py
```

O servidor escuta em `http://127.0.0.1:8000`.

- `POST /verificar`: recebe `texto` (20–100.000 caracteres) e, opcionalmente,
  `texto_classificacao` (20–4.000 caracteres). Devolve estimativa do
  classificador, sinais descritivos e estado/resultados da busca Google. A
  consulta externa usa o resumo do Ollama, se não for gerado, usa até 150
  caracteres de `texto_classificacao` (ou de `texto` quando esse campo não foi
  enviado). O cliente recebe essa consulta no campo `Título`.
- `POST /feedback`: registra se o resultado foi útil. Se o usuário indicar erro,
  exige classe corrigida e justificativa. Esse arquivo não é reaproveitado no
  treino automaticamente.

A busca semântica local foi removida porque dependia de uma base sem rótulos
fora do escopo escolhido. A API não usa os TXT como evidência: são dados de
treino e avaliação, não fontes atuais para comprovar notícias.

## Configurações opcionais

### Google Fact Check Tools API

Habilite a API no Google Cloud e configure a chave apenas no processo do
back-end:

```powershell
$env:GOOGLE_FACT_CHECK_API_KEY = "SUA-CHAVE"
python .\Back-end\main.py
```

Não grave a chave no `manifest.json` nem em `main.js`. Sem chave,
a resposta indica `nao_configurada`. Erros da consulta ficam no estado da seção
Fact Check e não substituem a análise local.

### Ollama

Para habilitar resumo local, instale Ollama e baixe o modelo padrão:

```powershell
ollama pull llama3.2:1b
```

Configure `OLLAMA_URL` e/ou `OLLAMA_MODEL` no ambiente quando necessário. A API
continua retornando os outros campos se Ollama estiver desligado e expõe a
falha do resumo em `erro_geracao_ia`.

## Ambiente e Validações

Na raiz do projeto, crie um ambiente Python e instale as dependências:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Execute os testes e verificações:

```powershell
python -m unittest discover -s .\Back-end -p "test_*.py"
python -m py_compile .\Back-end\main.py .\Back-end\fact_check_google.py .\Back-end\classificador_veracidade.py .\Back-end\treinar_classificador.py
```
