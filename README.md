Adicione a imagem de capa com o tema do seu projeto:
![Thumbnail GitHub]( )

## Projeto - Identificador de Notícias Falsas
Um sistema inteligente que auxilia na verificação de notícias online, detectando se um texto é falso ou verdadeiro por meio de processamento linguistico e análise semântica. O projeto combina uma extensão de navegador com uma API em Python e um banco vetorial para realizar a análise do conteúdo.

## Visão Geral
Este projeto foi desenvolvimento para analisar notícias acessadas pelo usuários diretamente no navegador. A extensão coleta o título e o corpo da notícia, envia os dados para o back-end, que compara o texto com uma base vetorial treinada e retorna um resultado com a classificação da informação.

A proposta central é oferecer uma ferramenta prática, simples e eficieinte para ajudar os usuários na identificação de conteúdos duvidosos antes de compartilharem informações falsas.

##Fluxo de Funcionamento
<details>
  <summary><b>Fluxo de aplicação:<b/></summary>
     1. O usuário abre uma notícia no navegador.
  	 2. Ativa a extensão instalada.
  	 3. O usuário clica no botão "Analisar Notícia".
  	 4. O sistema captura o texto da página e envia para a API.
     5. O back-end processa o conteúdo e compara com o banco vetorial.
     6. O sistema retorna se a notícia é considerada falsa ou verdadeira.
</details>

## Funcionalidades do projeto
- Análise automática de notícias diretamente na aba ativa do navegador;
- Extração do título e do conteúdo da página atual;
- Envio do texto para processamento no back-end;
- Comparação com base vetorial treinada;
- Classificação da notícia como falsa ou verdadeira;
- Exibição do resultado em uma interface simples e intuitiva;
- Suporte para uso em extensão do navegador Google Chrome.

## Demonstração
<img width="780" height="496" alt="fakenews3" src="https://github.com/user-attachments/assets/6451cde8-fb00-4b12-9184-c3e7781f0f6b" />
URL: https://ge.globo.com/futebol/times/flamengo/noticia/2026/09/19/escalacao-do-flamengo-jardim-fara-mudancas-na-equipe-para-enfrentar-o-bragantino.ghtml

## Arquitetura do Projeto
O sistema é dividido em três partes principais:
- Front-end: extensão do navegador responsável pela interface e captura do conteúdo.
- Back-end: API em Python que processa as informações do texto.
- Banco vetorial: estrutura de dados que armazena e compara embedding das notícias.

## Tecnologias Utilizadas

- `HTML`: Estrutura da interface da extensão.
- `CSS`: estilização visual da página e do popup.
- `JavaScript`: lógica do cliente e integração com o navegador.
  - `TypeScript`: tipagem estática para maior organização e segurança do código.
- `JavaScript Object Notation (JSON)`: armazenamento e transporte de dados estrutudados.

## Estrutura do repositório 
```text
Projeto-FakeNews/
├── Back-end/
│   ├── main.py
│   ├── treinar_ia.py
│   ├── base_noticias.json
│   └── meu_banco_vetorial/
├── Front-end/
│   ├── index.html
│   ├── main.js
│   ├── main.ts
│   ├── style.css
│   ├── manifest.json
│   └── tsconfig.json
├── datasets/
│   ├── fake.csv
│   ├── FakenewsBR_factchecked.csv
│   └── real.csv
├── readme.md
├── readme1.md
└── .gitignore
```

## Pré-requisitos
Antes de executar o projeto, certifique-se de ter:
- Python 3.10 ou superior
- Navegador Google Chrome
- Dependências Python do projeto instaladas

## Como rodar o projeto
**Passo 1 - Preparar o ambiente**
Abra o terminal do diretório do projeto e execute:
```bash
cd "C:\Códigos IA\Projeto-FakeNews"
```

**Passo 2 - Treinar a base vetorial**
Execute o comando abaixo:
```bash
& "C:\Python\python.exe" ".\Back-end\treinar_ia.py"
```
Esse passo recria a base de dados vetorial e prepara os embeddings para análise.

**Passo 3 - Iniciar o servidor back-end**
Abra outro terminal e execute:
  ```bash
  cd "C:\Códigos IA\Projeto-FakeNews"
  & "C:\Python\python.exe" ".\Back-end\main.py"
  ```
O servidor deve continuar em execução durante o uso da extensão.

**Passo 4 - Carregar a extensão no navegador**
1. Acesse o site `chrome://extensions/`
2. Ative o modo desenvolvedor
3. Clique em "Carregar sem compactação"
4. Selecione a pasta `Front-end`

## Benefícios do projeto
- Ajuda a combater a disseminação de notícias falsas
- Facilita a verificação rápida de conteúdo online
- Pode ser expandido para novos modelos e bases de dados
- Funciona como uma ferramenta prática de apoio à informação

## Futuras melhorias
- Adicionar suporte a mais navegadores
- Melhorar a interface visual da extensão
- Incorporar mais modelos de análise textual
- Testar em redes sociais

## Conclusão
O projeto representa uma aplicação útil e relevante ao contexto atual, onde a velocidade de divulgação de informações exige ferramentas de apoio para checar a veracidade dos conteúdos. A combinação de extensão, API e banco vetorial oferece uma solução prática, funcional e com grande potencial de evolução.
