/* 
=========================================
  ANÁLISE DE NOTÍCIAS | VERSÃO TIPADA +
  Objetivo: Capturar o conteúdo de uma notícia e enviar para o back-end para análise de veracidade.
  Arqivo correspondente: main.js (JavaScript).
=========================================
*/

// Campos retornados pelo back-end após a análise da notícia.
interface ResultadoAnalise {
  veredicto: 'VERDADEIRO' | 'FALSO' | 'INCERTO' | 'INDETERMINADO';
  precisao: number;
  probabilidade_veracidade: number | null;
  confianca_veracidade: number | null;
  similaridade_treino: number | null;
  probabilidades_veracidade: {
    VERDADEIRA: number;
    FALSA: number;
    INCERTA: number | null;
  } | null;
  classificador_veracidade_ativo: boolean;
  modelo_classificador: string | null;
  modelo_busca_semantica: string | null;
  modelo_gerativo_ativo: boolean;
  modelo_gerativo: string;
  resposta_ia: string | null;
  erro_geracao_ia: string | null;
  aviso_modelo: string;
  resumo_modelo: string;
  resumo_sinais: string;
  detalhes: string;
  criterios: CriterioAnalise[];
  evidencias: EvidenciaAnalise[];
  checagens_fact_check_google?: ResultadoFactCheckGoogle;
}

// Estado e avaliações textuais devolvidos pelo Google Fact Check Tools API.
interface ResultadoFactCheckGoogle {
  status: 'nao_configurada' | 'consulta_vazia' | 'erro' | 'sem_resultados' | 'resultados' | 'nao_consultada';
  mensagem: string;
  consulta: string;
  resultados: RevisaoFactCheckGoogle[];
}

interface RevisaoFactCheckGoogle {
  alegacao: string;
  autor_alegacao: string;
  data_alegacao: string;
  publicador: string;
  site_publicador: string;
  titulo: string;
  url: string;
  data_revisao: string;
  avaliacao_textual: string;
}

// Avaliação opcional enviada pelo usuário sobre o resultado exibido.
interface FeedbackAnalise {
  texto: string;
  util: boolean;
  classificacao: 'VERDADEIRA' | 'FALSA' | 'INCERTA' | null;
  motivo: string;
  veredicto_predito: ResultadoAnalise['veredicto'];
}

// Critério de verificação apresentado junto ao veredicto.
interface CriterioAnalise {
  criterio: string;
  avaliacao: string;
  explicacao: string;
}

// Notícia relacionada usada como evidência para a análise.
interface EvidenciaAnalise {
  titulo: string;
  data: string;
  assunto: string;
  url: string;
  trecho: string;
  distancia_vetorial?: number;
  similaridade_lexical?: number;
}

// Métodos da resposta HTTP usados para validar e ler os dados do back-end.
interface RespostaApi {
  ok: boolean;
  json(): Promise<ResultadoAnalise>;
  text(): Promise<string>;
}

// Separa o conteúdo completo, a prévia do popup e a entrada do classificador.
interface CapturaNoticia {
  textoCompleto: string;
  textoPrevia: string;
  textoClassificacao: string;
}

// Referência tipada da captura usada pela extensão; o popup carrega main.js,
// portanto esta função não é executada nem compilada pelo projeto.
function capturarNoticiaCompleta(): CapturaNoticia {
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
  // Evita tratar como artigo um elemento genérico com pouco conteúdo.
  const tamanhoMinimoNoticia = 500;

  // Esses elementos normalmente são menus, anuncios, cabeçalhos ou rodapés.
  // Remove-los evita enviar simbolos da interface junto com a notícia enviada.
  const seletoresIgnorados: string[] = [
    'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside',
    'form', 'button', '[role="navigation"]', '[role="button"]',
    'video', 'iframe', '[class*="video" i]', '[class*="player" i]',
    '[id*="video" i]', '[id*="player" i]', '[class*="caption" i]',
    '[aria-label*="aumentar" i]', '[aria-label*="fonte" i]',
    '[class*="share" i]', '[class*="social" i]', '[class*="comment" i]',
    '[class*="related" i]', '[class*="recommend" i]', '[class*="advert" i]',
    '[class*="banner" i]'
  ];

  // Filtra chamadas de ação comuns para não misturá-las ao texto do artigo.
  const palavrasIgnoradas: string[] = [
    'assista', 'clique', 'leia mais', 'saiba mais', 'veja também',
    'siga-nos', 'compartilhe', 'inscreva-se', 'confira', 'ouça agora',
    'acesse', 'baixe o aplicativo'
  ];

  // Usa o título da página como alternativa quando não há um elemento H1.
  const titulo = document.querySelector('h1')?.textContent?.trim() || document.title.trim();

  const conteudo = seletoresNoticia
    .map((seletor) => document.querySelector<HTMLElement>(seletor))
    .find((elemento) => (elemento?.innerText.trim().length || 0) >= tamanhoMinimoNoticia);
  const seletorIgnorados = seletoresIgnorados.join(',');
  // Usa parágrafos do conteúdo principal e descarta os que pertencem a blocos ignorados.
  const paragrafosNoticia = conteudo
    ? Array.from(conteudo.querySelectorAll('p'))
      .filter((paragrafo) => {
        let elemento: Element | null = paragrafo;
        while (elemento && elemento !== conteudo) {
          if (elemento.matches(seletorIgnorados)) return false;
          elemento = elemento.parentElement;
        }
        return true;
      })
      .map((paragrafo) => paragrafo.innerText.trim())
      .filter((paragrafo) => paragrafo.length >= 30)
    : [];

  // Fallback para quando o texto da notícia não é encontrado.
  const textoBruto = conteudo
    ? paragrafosNoticia.length >= 2
      ? paragrafosNoticia.join('\n')
      : conteudo.innerText
    : document.body.innerText;

  // Mantém linhas com palavras ou números e elimina espaços e símbolos isolados.
  const textoCorpoCompleto = textoBruto
    .split('\n')
    .map((linha) => linha.replace(/\s+/g, ' ').trim())
    .filter((linha) => linha.length >= 3 && /[\p{L}\p{N}]{2}/u.test(linha))
    .filter((linha) => !/^(t[ií]tulo|subt[ií]tulo|autoclassifica[cç][aã]o et[aá]ria|agora|ao vivo|play|pausa|volume)\s*:/i.test(linha))
    .filter((linha) => linha.toLowerCase() !== titulo.toLowerCase())
    .filter((linha) => {
      const linhaNormalizada = linha.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      return !palavrasIgnoradas.some((palavra) => {
        const palavraNormalizada = palavra.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
        return linhaNormalizada === palavraNormalizada
          || linhaNormalizada.startsWith(`${palavraNormalizada} `)
          || linhaNormalizada.startsWith(`${palavraNormalizada}:`);
      });
    })
    .join('\n');

  // O texto integral alimenta o resumo; o campo curto é usado pelo classificador.
  // Se Ollama estiver disponível, o backend usa o resumo como consulta Google.
  const palavras = textoCorpoCompleto.split(/\s+/).filter(Boolean);
  const textoCorpoPrevia = palavras.slice(0, 100).join(' ')
    + (palavras.length > 100 ? ' ...' : '');
  // Limita a entrada do classificador ao título e ao início do artigo; o texto completo é preservado.
  const paragrafoPrincipal = paragrafosNoticia.find((paragrafo) => paragrafo.length >= 100)
    || document.querySelector('meta[name="description"]')?.getAttribute('content')?.trim()
    || paragrafosNoticia[0]
    || textoCorpoCompleto.slice(0, 600);
  const textoClassificacao = [titulo, paragrafoPrincipal]
    .filter(Boolean)
    .join('\n\n')
    .slice(0, 4000);

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

  const textoCompleto = [
    `Título: ${titulo}`,
    `Notícia: ${textoCorpoCompleto}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Fonte: ${fonte}`
  ].join('\n\n');
  const textoPrevia = [
    `Título: ${titulo}`,
    `Notícia (prévia): ${textoCorpoPrevia}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Fonte: ${fonte}`,
    `\nO classificador usa o título e o início do artigo; o resumo e a consulta Google usam o texto completo (${palavras.length} palavras) quando Ollama está disponível.`
  ].join('\n\n');

  return { textoCompleto, textoPrevia, textoClassificacao };
}

// Chamada tipada de referência; envia os mesmos campos que main.js.
async function analisarNoticia(captura: CapturaNoticia): Promise<ResultadoAnalise> {
  // ALTERE AQUI SE O BACKEND ESTIVER EM OUTRA URL, PORTA OU SERVIDOR.
  const resposta: RespostaApi = await fetch('http://localhost:8000/verificar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      texto: captura.textoCompleto,
      texto_classificacao: captura.textoClassificacao
    })
  });

  if (!resposta.ok) {
    throw new Error('Servidor indisponível');
  }

  return resposta.json();
}

// Exporta as funções de referência; a extensão não compila nem importa este arquivo.
export { analisarNoticia, capturarNoticiaCompleta };
