/* 
=========================================
  ANÁLISE DE NOTÍCIAS | VERSÃO TIPADA +
  Objetivo: Capturar o conteúdo de uma notícia e enviar para o back-end para análise de veracidade.
  Arqivo correspondente: main.js (JavaScript).
=========================================
*/

interface ResultadoAnalise {
  veredicto: 'VERDADEIRO' | 'FALSO' | 'INDETERMINADO';
  precisao: number;
  detalhes: string;
}

// O fetch/busca do navegador retorna um objeto com status HTTP e método json().
interface RespostaApi {
  ok: boolean;
  json(): Promise<ResultadoAnalise>;
}

// Captura um resumo padronizado da notícia, sem depender da seleção do usuário.
// Esta função é equivalente à função de mesmo nome em main.js.
function capturarNoticiaCompleta(): string {
  // A função pode ser executada dentro da página ativa.
  const seletoresNoticia: string[] = [
    '[itemprop="articleBody"]',
    '[data-testid="article-body"]',
    '.article-body',
    '.article-content',
    '.post-content',
    'article',
    'main'
  ];

  // Esses elementos normalmente são menus, anuncios, cabeçalhos ou rodapés.
  // Remove-los evita enviar simbolos da interface junto com a notícia enviada.
  const seletoresIgnorados: string[] = [
    'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside',
    'form', 'button', '[role="navigation"]', '[role="button"]',
    '[aria-label*="aumentar" i]', '[aria-label*="fonte" i]',
    '[class*="share" i]', '[class*="social" i]', '[class*="comment" i]',
    '[class*="related" i]', '[class*="recommend" i]', '[class*="advert" i]',
    '[class*="banner" i]'
  ];

  // O título principal é importante; "document.title" é o erros para sites sem H1.
  const titulo = document.querySelector('h1')?.textContent?.trim() || document.title.trim();

  const conteudo = seletoresNoticia
    .map((seletor) => document.querySelector<HTMLElement>(seletor))
    .find((elemento) => (elemento?.innerText.trim().length || 0) >= 120);
  const copiaConteudo = conteudo?.cloneNode(true);

  // Trabalha em uma cópia para não modificar a página original do usuário.
  if (copiaConteudo instanceof HTMLElement) {
    copiaConteudo.querySelectorAll(seletoresIgnorados.join(',')).forEach((elemento) => {
      elemento.remove();
    });
  }

  // Fallback para quando o texto da notícia não é encontrado.
  const textoBruto = copiaConteudo instanceof HTMLElement
    ? copiaConteudo.innerText
    : document.body.innerText;

  // Mantém linhas com palavras ou números e elimina espaços e símbolos isolados.
  const textoCorpoCompleto = textoBruto
    .split('\n')
    .map((linha) => linha.replace(/\s+/g, ' ').trim())
    .filter((linha) => linha.length >= 3 && /[\p{L}\p{N}]{2}/u.test(linha))
    .join('\n');

  // Limita o corpo a 100 palavras e sinaliza a continuação com reticencias.
  const palavras = textoCorpoCompleto.split(/\s+/).filter(Boolean);
  const textoCorpo = palavras.slice(0, 100).join(' ')
    + (palavras.length > 100 ? ' ...' : '');

  // Tenta encontrar o autor em metadados e seletores comuns de noticias.
  const autor = document.querySelector('meta[name="author"]')?.getAttribute('content')?.trim()
    || document.querySelector('[itemprop="author"]')?.textContent?.trim()
    || document.querySelector('[rel="author"], .author, [class*="author" i]')?.textContent?.trim()
    || 'Não identificado';

  // Prioriza a data estruturada (metadados)
  const dataPublicacao = document.querySelector('meta[property="article:published_time"]')?.getAttribute('content')?.trim()
    || document.querySelector('meta[name="date"], meta[name="pubdate"]')?.getAttribute('content')?.trim()
    || document.querySelector('time[datetime]')?.getAttribute('datetime')?.trim()
    || document.querySelector('time')?.textContent?.trim()
    || 'Não identificada';

  const fonte = window.location.hostname || 'Não identificada';

  return [
    `Título: ${titulo}`,
    `Notícia: ${textoCorpo}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Fonte: ${fonte}`
  ].join('\n\n');
}

// Mantém o que é enviado ao back-end explícito e reutilizável no JavaScript gerado.
async function analisarNoticia(texto: string): Promise<ResultadoAnalise> {
  // ALTERE AQUI SE O BACKEND ESTIVER EM OUTRA URL, PORTA OU SERVIDOR.
  const resposta: RespostaApi = await fetch('http://localhost:8000/verificar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto })
  });

  if (!resposta.ok) {
    throw new Error('Servidor indisponível');
  }

  return resposta.json();
}

// Permite reutilizar essas funções caso o projeto passe a importar o módulo TS.
export { analisarNoticia, capturarNoticiaCompleta };