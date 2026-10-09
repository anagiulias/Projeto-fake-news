# 🚨 Verificador de Notícias 🚨

Projeto experimental com uma extensão Chrome e uma API Python local. 
A extensão captura uma notícia e o back-end combina:

1. **Classificador supervisionado local**, treinado com os TXT rotulados das
   pastas `datasets/fake/` e `datasets/true/`;
2. **Google Fact Check Tools API opcional**, para buscar checagens já publicadas
   por organizações de fact-checking;
3. **Resumo local opcional via Ollama**, que descreve a alegação sem decidir se
   é verdadeira ou falsa.

**Observação:** As saídas são pistas para estudo, não confirmação factual. A previsão local é
binária e pode ser inconclusiva e os ratings parciais do Google são apresentados
como publicados, sem serem convertidos em rótulos locais.

## Estrutura do projeto 🏗️

| Caminho | Papel |
| --- | --- |
| `Front-end/` | Extensão Chrome. `main.js` é executado; `main.ts` documenta contratos tipados; `manifest.json` configura o popup. |
| `Back-end/main.py` | API FastAPI, integração do classificador, Google Fact Check e Ollama. |
| `Back-end/classificador_veracidade.py` | TF-IDF, regressão logística, calibração e abstenção. |
| `Back-end/treinar_classificador.py` | Split 70/30, balanceamento do treino, métricas e geração do modelo. |
| `Back-end/fact_check_google.py` | Cliente da API Google Fact Check Tools. |
| `Back-end/test_fact_check_google.py` | Testes simulados da integração Google. |
| `Back-end/README.md` | Detalhes de bibliotecas, modelos, endpoints, ambiente e treinamento. |
| `Tratamento-dados/tratamento_datasets_rotulados.ipynb` | Lê/valida TXT e gera CSV de treino e auditoria. |
| `Tratamento-dados/tratamento_fakeNewsFinal.ipynb` | EDA textual dos mesmos TXT rotulados. |
| `Tratamento-dados/README.md` | Explica dados, limitações, limpeza, EDA e treinamento. |
| `datasets/fake/*.txt` | Exemplos rotulados como FALSA pela pasta de origem. |
| `datasets/true/*.txt` | Exemplos rotulados como VERDADEIRA pela pasta de origem. |
| `datasets/tratados/` | CSVs tratados, auditados e saídas de treino. |
| `requirements.txt` | Dependências Python do back-end. |

Não há mais dependência do `Historico_de_materias.csv`, dos CSVs originais
antigos nem de um acervo sem rótulos para busca local. A API Google é externa e
opcional; os TXT locais são fonte de treino/EDA, não evidências atuais.

## Dados, limpeza e rótulos 🧼🎲

As pastas atuais contêm aproximadamente 1.000 TXT em `fake/` e 821 em `true/`
(contagens do checkout documentado; confirme após atualizar os dados). O
pipeline é:

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

### O que acontece com o teste 70/30

`Back-end/treinar_classificador.py` cria a divisão estratificada e agrupada
antes de balancear os dados:

- Cerca de **70%** ficam no treino e **30%** no teste;
- Textos iguais após conversão para minúsculas permanecem na mesma partição;
- Apenas o treino passa por balanceamento temático;
- O teste não é reamostrado, então suas métricas refletem a distribuição
  existente;
- O modelo de produção é ajustado com todos os dados após a avaliação;
- O relatório de teste usado pela API é salvo em
  `Back-end/metricas_veracidade.json`.

Como os TXT não trazem URL nem identificador de alegação, paráfrases relacionadas
ainda podem aparecer em treino e teste. Para uma avaliação mais rigorosa, é preciso
recuperar identificadores de alegações/fontes e agrupe-los antes da divisão.
Avalie também notícias recentes rotuladas por revisão editorial independente.

## Classificador e estimativas 🔍

O classificador **não é um modelo generativo**. Ele usa:

- Vetorização TF-IDF de unigramas e bigramas;
- Regressão logística com pesos balanceados;
- Calibração Platt com previsões agrupadas fora da amostra;
- Abstenção quando confiança ou similaridade com os exemplos de treino ficam
  abaixo dos limites definidos.

O dataset contém apenas `VERDADEIRA` e `FALSA`. A interface pode descrever
tendências moderadas ou fortes a partir das probabilidades, mas não declara
“parcialmente verdadeira/falsa”. `INCERTO` indica que o sistema se absteve, não
é uma terceira classe aprendida. A avaliação textual da API Google é exibida
separadamente.

<kbd><b>PARTE 1</b></kbd>

## Passo a passo para executar no Windows 💻

### 1. Pré-requisitos

- **Python 3.10 ou superior** instalado e disponível no terminal. O comando
  `py -3 --version` deve exibir a versão instalada.
- **Google Chrome** para carregar a extensão.
- **Ollama (opcional)** somente se quiser gerar o resumo local da notícia.
- **Chave Google Fact Check Tools (opcional)** somente se quiser consultar
  checagens publicadas por organizações de fact-checking.

Os dois serviços opcionais não são necessários para iniciar a API ou usar o
classificador local. <br> Sem Ollama, o resumo não será gerado e sem a chave Google,
a busca externa ficará desativada.

### 2. Preparar o ambiente Python

Abra o PowerShell na pasta raiz do repositório e crie o ambiente virtual:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, permita scripts apenas nesta
janela e tente ativá-lo novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**Importante:** Mantenha o ambiente virtual ativado nos terminais em que executar o back-end ou
o treinamento. Caso o arquivo `.venv` já existir, não é preciso criá-lo novamente; basta
ativá-lo e instalar eventuais dependências novas.

### 3. Configurar os serviços externos (Opcional)

**Resumo local com Ollama:** Instale o Ollama pelo
[site oficial](https://ollama.com/download/windows).

<br> 

Abra um novo terminal e baixe o modelo padrão:

```powershell
ollama pull llama3.2:1b
```

O Ollama usa `http://127.0.0.1:11434` e o modelo `llama3.2:1b` por padrão. Se
necessário, configure `OLLAMA_URL` ou `OLLAMA_MODEL` no ambiente antes de
iniciar a API. O resumo gerado pelo Ollama descreve a alegação e não determina 
se ela é verdadeira.

**Google Fact Check Tools:** Essa integração consulta checagens já
publicadas na internet e não é uma biblioteca para instalar. 

<br>

Para configurá-la:

I. Acesse o [Google Cloud Console](https://console.cloud.google.com/) e entre
   com sua conta Google.
II. Crie um projeto ou selecione um projeto existente pelo seletor de projetos,
   na barra superior.
III. Abra **APIs e serviços > Biblioteca**, procure por **Fact Check Tools API**
   e clique em **Ativar**. Também é possível abrir diretamente a
   [página da API](https://console.cloud.google.com/marketplace/product/google/factchecktools.googleapis.com).
IV. Depois de ativar a API, abra **APIs e serviços > Credenciais** e clique em
   **Criar credenciais > Chave de API** copie a chave gerada.
V. Nas configurações dessa chave, restrinja o uso à **Fact Check Tools API**
   em **Restrições de API**. Restrições de aplicativo podem impedir chamadas feitas
   pelo back-end local, então apenas configure se souber
   qual restrição é compatível com o ambiente em que executará a API. Além disso, o Google
   Cloud pode solicitar configurações adicionais para o projeto antes de
   habilitar a API.
VI. No PowerShell em que iniciará o back-end, defina a variável de ambiente,
   substituindo o texto de exemplo pela chave copiada:

```powershell
$env:GOOGLE_FACT_CHECK_API_KEY = "SUA_CHAVE_AQUI"
```

Essa variável vale apenas para a sessão atual do PowerShell. Inicie ou reinicie
o back-end nesse mesmo terminal para que ele receba a chave:

```powershell
python .\Back-end\main.py
```

Não publique a chave, não a coloque no código nem no manifesto da extensão. 
Se ela for exposta, revogue-a no Google Cloud Console e gere outra. 
Sem chave, a aplicação continua funcionando, mas a busca externa
fica desativada. Os resultados são checagens previamente publicadas e não
alimentam automaticamente o treinamento.

### 4. Iniciar o back-end

Com o ambiente virtual ativado, execute a partir da raiz do repositório:

```powershell
python .\Back-end\main.py
```

Deixe esse terminal aberto enquanto usar a extensão. A API local estará
disponível em `http://127.0.0.1:8000` abra
[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs) para conferir se
iniciou e explorar os endpoints. A extensão usa `POST /verificar` para analisar
uma notícia e `POST /feedback` para registrar uma avaliação e o feedback não
retreina o classificador.

O repositório inclui o modelo treinado em
`Back-end/modelo_veracidade.joblib`, portanto não é necessário retreinar para
uma primeira execução. Se esse arquivo estiver ausente, a API ainda pode
iniciar, mas não fará a previsão local.

### 5. Carregar a extensão no Chrome

1°. Abra `chrome://extensions/` no Chrome.
2°. Ative **Modo do desenvolvedor**.
3°. Clique em **Carregar sem compactação**.
4°. Selecione a pasta `Front-end/` dentro do repositório.
5°. Fixe a extensão na barra de ferramentas pelo menu de extensões (Opcional).

Abra uma página de notícia, clique no ícone **Verificador de Fake News** e
selecione **Analisar Notícia**. A captura depende do conteúdo disponível na
página. Se não funcionar, confira se o back-end continua ativo e tente outra
página. Depois de alterar arquivos da extensão, volte a `chrome://extensions/`
e atualize a extensão antes de testar novamente.

O popup executa `Front-end/main.js`; `main.ts` é uma referência tipada e não é
compilado. Consulte `Front-end/README.md` para detalhes do fluxo da extensão.

### 6. Gerar novamente o modelo (Opcional)

Só é necessário treinar novamente quando os dados ou o código do classificador
forem alterados ou criados pela primeira vez. Execute todas as células de
`Tratamento-dados/tratamento_datasets_rotulados.ipynb`, confira
`datasets/tratados/auditoria_tratamento.csv` e, na raiz do projeto, rode:

```powershell
python .\Back-end\treinar_classificador.py
```

O treinamento atualiza `Back-end/modelo_veracidade.joblib` e
`Back-end/metricas_veracidade.json`. A divisão de teste e as limitações dos
dados estão descritas acima e detalhes para preparar os notebooks estão em
`Tratamento-dados/README.md`.

## JSON e arquivos que podem ser regenerados

JSON não aceita comentários `//` ou `/* ... */`. Portanto, as explicações de
`Front-end/manifest.json` e dos relatórios ficam neste README. Os arquivos
`metricas_veracidade.json` e `feedback_noticias.jsonl` também são dados da
aplicação, não locais apropriados para comentários.

Preserve os TXT de origem e `feedback_noticias.jsonl`. O CSV tratado e a
auditoria podem ser recriados pelo notebook. Os resultados de balanceamento,
`modelo_veracidade.joblib` e `metricas_veracidade.json` podem ser regenerados
executando o treinamento.

**Mudanças e arquivos apagados:** Artefatos do fluxo removido de busca semântica (`Back-end/treinar_ia.py`,
`Back-end/avaliar_dataset_historico.py`, `base_noticias.json`,
`embeddings_noticias.npy` e `datasets/tratados/metricas_teste_historico.json`)
não fazem parte do pipeline atual. O CSV `Historico_de_materias.csv` não é
necessário. Se cópias desses artefatos existirem em outra máquina, não são lidas
pela API atual e podem ser arquivadas/removidas após confirmar que não há
processos externos usando-as.

## Testes e verificações

```powershell
python -m unittest discover -s .\Back-end -p "test_*.py"
python -m py_compile .\Back-end\main.py .\Back-end\fact_check_google.py .\Back-end\classificador_veracidade.py .\Back-end\treinar_classificador.py
node --check .\Front-end\main.js
```

Consulte `Back-end/README.md` para detalhes dos endpoints, modelos, variáveis de
ambiente e treinamento, consulte `Tratamento-dados/README.md` para executar e
interpretar os notebooks.
