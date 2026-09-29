/* 
=========================================
  + FUNÇÕES E LINHA DE TEMPO +
  Objetivo: Este arquivo controla o popup da extensão e se comunica com o back-end em Python.
  Linha do tempo: Clique no botão "Analisar Notícia" -> identificação da aba ativa -> captura do texto -> método POST -> exibe resultado visual.
=========================================
*/

// Esta função roda dentro da aba ativa e retorna o texto da notícia.
function capturarNoticiaCompleta() {
  // O Chrome copia somente essa função para a página da notícia.
  const seletoresNoticia = [
    '[itemprop="articleBody"]',
    '[data-testid="article-body"]',
    '.article-body',
    '.article-content',
    '.post-content',
    'article',
    'main'
  ];

  // Elementos abaixo geralmente são propagandas, rodapés, cabeçalhos e etc.
  // Retira-los evita mandar simbolos e textos desnecessários para a IA.
  const seletoresIgnorados = [
    'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside',
    'form', 'button', '[role="navigation"]', '[role="button"]',
    '[aria-label*="aumentar" i]', '[aria-label*="fonte" i]',
    '[class*="share" i]', '[class*="social" i]', '[class*="comment" i]',
    '[class*="related" i]', '[class*="recommend" i]', '[class*="advert" i]',
    '[class*="banner" i]'
  ];

  // Tenta capturar o título da notícia "H1", mas se não encontrar, usa o título da aba "document.title".
  const titulo = document.querySelector('h1')?.innerText.trim() || document.title.trim();

  // Cria uma cópia do conteúdo. Assim a extensão não altera a página original e apenas remove elementos que não são parte da notícia.
  const conteudo = seletoresNoticia
    .map((seletor) => document.querySelector(seletor)) // Tenta encontrar o elemento de notícia usando os seletores conhecidos.
    .find((elemento) => elemento && elemento.innerText.trim().length >= 120); // A notícia precisa ter pelo menos 120 caracteres para ser considerada válida.
  const copiaConteudo = conteudo?.cloneNode(true); // Cria uma cópia do elemento de notícia "cloneNode".

  // Remove elementos que não são parte da cópia da notícia "seletoresIgnorados".
  if (copiaConteudo instanceof HTMLElement) {
    copiaConteudo.querySelectorAll(seletoresIgnorados.join(',')).forEach((elemento) => {
      elemento.remove();
    });
  }

  // Se nenhum seletor conhecido funcionar, usa body como último recurso.
  const textoBruto = copiaConteudo instanceof HTMLElement
    ? copiaConteudo.innerText
    : document.body.innerText; // "innerText" lê apenas o texto visível

  // Limpa espaços repetidos, linhas vazias e símbolos isolados de interface.
  const textoCorpoCompleto = textoBruto
    .split('\n')
    .map((linha) => linha.replace(/\s+/g, ' ').trim())
    .filter((linha) => linha.length >= 3 && /[\p{L}\p{N}]{2}/u.test(linha)) 
    .join('\n');

  // Captura as primeiras 100 palavras para reduzir ruido e acelerar a análise.
  const palavras = textoCorpoCompleto.split(/\s+/).filter(Boolean);
  const textoCorpo = palavras.slice(0, 100).join(' ')
    + (palavras.length > 100 ? '...' : ''); // Se o texto for maior adiciona reticências "..."

  // Tenta encontrar o autor "meta" e seletores comuns de noticias.
  const autor = document.querySelector('meta[name="author"]')?.getAttribute('content')?.trim()
    || document.querySelector('[itemprop="author"]')?.textContent?.trim()
    || document.querySelector('[rel="author"], .author, [class*="author" i]')?.textContent?.trim()
    || 'Não identificado.';

  // Prioriza a data estruturada, pois ela costuma ser mais confiável.
  const dataPublicacao = document.querySelector('meta[property="article:published_time"]')?.getAttribute('content')?.trim()
    || document.querySelector('meta[name="date"], meta[name="pubdate"]')?.getAttribute('content')?.trim()
    || document.querySelector('time[datetime]')?.getAttribute('datetime')?.trim()
    || document.querySelector('time')?.textContent?.trim()
    || 'Não identificada.';

  // Usa o hostname (URL da página) como fonte ou marca como "Não identificada".
  const fonte = window.location.hostname || 'Não identificada.';

  // Retorna o resultado como uma string formatada, que será enviada para o back-end.
  return [
    `Título: ${titulo}`,
    `Notícia: ${textoCorpo}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Site: ${fonte}`
  ].join('\n\n');
}

// O clique no botão "analisarBtn" inicia o fluxo de captura e análise da notícia.
document.getElementById('analisarBtn').addEventListener('click', async () => { 
  const resultadoDiv = document.getElementById('resultado');
  const textoDiv = document.getElementById('textoSelecionado');

  // Mensagem de "Analisando notícia..." e ícone de carregando.
  resultadoDiv.style.display = 'flex';
  resultadoDiv.className = 'texto-analisando';
  resultadoDiv.innerHTML = '<div class="icone-carregando"></div><span>Analisando notícia...</span>';

  // Obtém a aba ativa e se não houver aba ativa exibe uma mensagem de erro.
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab?.id) {
    resultadoDiv.innerText = 'Não foi possível identificar a aba atual.';
    return;
  }

  // "executeScript" muda temporariamente o contexto do popup da extensão para a página ativa.
  // Direcionando o "document.body" e "document.querySelector" para o HTML da notícia e não para o popup da extensão.
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: capturarNoticiaCompleta
  }, async (results) => {
    // O resultado é uma lista porque o Chrome permite executar em várias abas.
    // Aqui analisamos apenas a primeira aba solicitada pelo usuário.
    if (!results || !results[0]) {
      resultadoDiv.innerText = 'Não foi possível capturar o texto da página. Por favor, insira manualmente no campo acima.';
      return;
    }

    // O texto da notícia capturado pelo "executeScript" é retornado no campo "result".
    const textoNoticia = results[0].result;

    // Exibe o texto capturado no "textarea" para que o usuário possa revisar o que foi analisado.
    textoDiv.value = textoNoticia;

    try {
      // O back-end espera o JSON.
      // O título junto do corpo ajuda a busca semântica a preservar o contexto.
      // ALTERE AQUI SE O BACK-END ESTIVER EM OUTRA URL, PORTA OU SERVIDOR.
      const response = await fetch('http://localhost:8000/verificar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: textoNoticia })
      });

      // Se a resposta do back-end não for 200 OK, lança um erro para ser capturado no "catch".
      if (!response.ok) {
        throw new Error(`Servidor respondeu com HTTP ${response.status}`);
      }

      // Converte a resposta JSON em um objeto JavaScript (JS).
      const dados = await response.json();

      // O "veredicto" controla a classe CSS e a mensagem exibida ao usuário.
      if (dados.veredicto === 'VERDADEIRO') {
        resultadoDiv.className = 'verdadeiro';
        resultadoDiv.innerText = `✅ ${"Notícia Verdadeira!".toUpperCase()} ✅ \nConfiança: ${dados.precisao}%`;
      } else {
        resultadoDiv.className = dados.veredicto === 'FALSO' ? 'falso' : '';
        resultadoDiv.innerText = dados.veredicto === 'FALSO'
          ? `🚨 ${"Notícia Falsa!".toUpperCase()} 🚨 \n ${dados.detalhes}`
          : `⚠️ ${"Resultado inconclusivo...".toUpperCase()} ⚠️\n ${dados.detalhes}`;
      }
    } catch (error) {
      // Captura falhas de rede, back-end desligado ou respostas inesperadas.
      resultadoDiv.innerText = 'Não foi possível analisar agora. Verifique se o back-end está executando em http://localhost:8000.';
    }
  });
});