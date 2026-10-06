# Extensão do Chrome

Esta pasta contém o popup que captura uma notícia na aba atual, solicita análise
à API local e apresenta a estimativa e as revisões externas encontradas. O
JavaScript executado pelo Chrome é `main.js`.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `manifest.json` | Configuração Manifest V3: popup, ícone, permissões e origem permitida para a API local. |
| `index.html` | Estrutura do popup, campos, botões e áreas onde os resultados são exibidos. |
| `style.css` | Layout, estados visuais, cores, mensagens e barra de rolagem do popup. |
| `main.js` | Implementação efetivamente carregada: captura do artigo, requisições HTTP, validação e renderização dos resultados. |
| `main.ts` | Referência tipada para os contratos e funções principais. Não é compilado nem carregado pela extensão; mantenha-o sincronizado manualmente com `main.js`. |
| `img/` | Ícones declarados no manifesto. |

## Fluxo do JavaScript

Ao clicar em **Analisar Notícia**, `main.js`:

1. Consulta a aba ativa e executa `capturarNoticiaCompleta` no contexto da
   página;
2. Tenta localizar o título e o artigo com seletores comuns, removendo menus,
   anúncios, controles e textos acessórios;
3. Mantém o texto completo para a API e cria uma prévia curta para o popup;
4. Cria `texto_classificacao` com o título e o início do artigo, limitado a
   4.000 caracteres. O backend recebe os dois campos em
   `POST http://localhost:8000/verificar`;
5. Trata erros de rede/HTTP e renderiza a resposta sem interpretar conteúdo
   recebido como HTML;
6. Mostra as probabilidades binárias do classificador e, quando houver, as
   revisões textuais do Google Fact Check Tools em seção separada. No backend,
   a consulta Google usa o resumo do Ollama quando disponível; se a geração
   falhar, usa até 150 caracteres do texto de classificação;
7. Envia avaliações voluntárias para `POST /feedback`. O feedback é salvo em
   JSON Lines no backend e não atualiza o modelo automaticamente.

Captura automática depende da estrutura de cada site. Se falhar, confira o texto
da página e a resposta do back-end; a extensão não consegue contornar páginas
restritas ou conteúdo que não esteja presente no DOM.

## JavaScript, TypeScript e JSON

- **JavaScript (`main.js`)**: Código fonte executado diretamente pelo popup.
  Nele estão as funções de captura, comunicação, apresentação e feedback.
- **TypeScript (`main.ts`)**: Documenta tipos como `ResultadoAnalise`,
  `RevisaoFactCheckGoogle` e `FeedbackAnalise`, mas não é uma segunda
  implementação executável. Se alterar o contrato, atualize os tipos e a
  implementação juntos.
- **JSON (`manifest.json`)**: É configuração lida pelo Chrome. Não coloque chaves 
da Google API no manifesto ou no front-end.

## Instalar para desenvolvimento

1. Inicie o back-end conforme `../Back-end/readme.md`.
2. Abra `chrome://extensions/` no Chrome e ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação** e selecione a pasta `Front-end/`.
4. Abra uma notícia, clique no ícone da extensão e use **Analisar Notícia**.

O manifesto permite requisições a `http://localhost:8000/*`. Se alterar host ou
porta, atualize `manifest.json` e as URLs do backend em `main.js` e
`main.ts`; confira também as regras CORS da API.

## Contrato esperado

`POST /verificar` recebe JSON com:

```json
{
  "texto": "Texto completo da notícia",
  "texto_classificacao": "Título e trecho inicial usados pelo classificador"
}
```

A resposta inclui veredicto, probabilidades calibradas, critérios, resumo e
`checagens_fact_check_google`. As estimativas do classificador são binárias
(`VERDADEIRA`/`FALSA`) ou inconclusivas; classificações parciais da checagem
externa são exibidas com a avaliação textual original, sem conversão em rótulos
locais.
