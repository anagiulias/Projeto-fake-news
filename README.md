Comandos CMD:
1) & "E:\Python\python.exe" ".\Back-end\treinar_ia.py"
2) & "E:\Python\python.exe" ".\Back-end\main.py"

Notícias de teste:
Falsa: https://www.uol.com.br/esporte/ultimas-noticias/2023/06/06/suecia-sexo-esporte-verdade-mentira.htm
Verdadeira: https://ge.globo.com/futebol/times/flamengo/noticia/2026/09/19/escalacao-do-flamengo-jardim-fara-mudancas-na-equipe-para-enfrentar-o-bragantino.ghtml

Imagem:
<img width="781" height="545" alt="fakenews3" src="https://github.com/user-attachments/assets/adbcbc67-09ed-43cd-a181-6435ba86bf88" />

Adicione a imagem de capa com o tema do seu projeto:
![Thumbnail GitHub]( )
## Projeto - Identificador de Notícias Falsas

<details>
  <summary><b>Fluxo de funcionalidades:<b/></summary>
   Usuário abre notícia que deseja verificar > Abre a extensão instalada > Clica no botão "Analisar Notícia" > Sistema processa os elementos da notícia > Exibe na tela o resultado de notícia falsa ou verdadeira.  
</details>
  
## Descrição do Projeto

O sistema é uma extensão de navegador, ela é responsável por analisar a notícia que o usuário selecionar e após o processamento informa se a notícia é falsa ou verdadeira. 

## Funcionalidades do projeto
REFAZER
Após o usuário clicar no botão de "Analisar Notícia" o sistema irá capturar o HTML da notícia atual e exibir enquanto realiza a analise..

Se possível, apresente um exemplo visual do projeto, seja gif, imagens ou vídeo, abaixo segue um exemplo:

![]( )

## Tecnologias Utilizadas

- `HTML`: O HTML (Linguagem de Marcação de HiperTexto) define a estrutura do conteúdo por meio de elementos que delimitam ou agrupam diferentes partes do conteúdo para que ele apareça ou atue de determinada maneira. 
- `CSS`: O CSS (Folha de Estilo em Cascata) é uma linguagem de folhas de estilos que usa o código desenvolvido para dar estilo à página Web.
- `JavaScript`: O JavaScript é uma linguagem de script orientada a objetos e plataforma cruzada usada para tornar as páginas da Web interativas. Usando do lado cliente o JavaScript fornece objetos para controlar um navegador web e seu Document Object Model (DOM). 
  - `TypeScript`: É responsável por verificar se um programa contém erros antes da execução, com base nos tipos de valores, o que o torna um verificador de tipo estático. 
- `JavaScript Object Notation (JSON)`: É um formato baseado em texto padrão para representar dados estruturados com base na sintaxe do objeto JavaScript. 

## Abrir e rodar o projeto

**Passo 1 - Comandos no terminal**
* Rode os seguintes comandos no terminal substituindo o caminho do projeto:
  * Comando para rodar o treinamento do banco vetorial:
  ```bash
  & "C:\Python\python.exe" ".\Back-end\treinar_ia.py"
  ```

  * Comando para rodar o arquivo back-end em python:
  ```bash
  "C:\Python\python.exe" ".\Back-end\main.py"
  ```

- Comandos alternativos:
Caso esses comando não funcione, utilize esses outros comandos.

**Passo 2 - Abrindo a extensão no navegador**
1. Acesse o site `chrome://extensions/` e ative o modo desenvolvedor.  
  1.1 Clique em "Carregar sem compactação" e selecione a pasta **Front-end**.

## Comentários extras
		const textoCorpoCompleto = textoBruto
      .split(`\n`) // Divide o texto em linhas para processar cada uma separadamente.
		  .map(linha) => linha.replace(/\s+/g, ``).trim()) // Usa o "trim()"para remover espaços em branco e o "replace" substitui múltiplos espaços por um único.
      .filter((linha) => linha.length >= 3 && /[\p{L}\p{N}]{2}/u.test(linha)) // Filtra linhas com pelo menos 3 caracteres e que contenham letras ou números, ignorando símbolos isolados.
      .join(`\n`); // Junta as linhas filtradas de volta em um único texto.

    // Obtém a aba ativa e se não houver aba ativa exibe uma mensagem de erro.
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    // tab: é um objeto JavaScript fornecido pela API do Google Chrome. Contém todas as informações sobre a página web visualizada pelo usuário.

## MAP x FIND
- map: **Transforma um array em outro array**, retornando assim um novo array. 
Exemplo: 
- find: É **usado para filtrar** os dados e retornar um novo array com as informações selecionadas.
