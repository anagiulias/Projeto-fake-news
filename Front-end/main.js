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
  const tamanhoMinimoNoticia = 500;

  // Elementos abaixo geralmente são propagandas, rodapés, cabeçalhos e etc.
  // Retira-los evita mandar simbolos e textos desnecessários para a IA.
  const seletoresIgnorados = [
    'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside',
    'form', 'button', '[role="navigation"]', '[role="button"]',
    'video', 'iframe', '[class*="video" i]', '[class*="player" i]',
    '[id*="video" i]', '[id*="player" i]', '[class*="caption" i]',
    '[aria-label*="aumentar" i]', '[aria-label*="fonte" i]',
    '[class*="share" i]', '[class*="social" i]', '[class*="comment" i]',
    '[class*="related" i]', '[class*="recommend" i]', '[class*="advert" i]',
    '[class*="banner" i]'
  ];

  // Linhas com chamadas de ação da página, que não fazem parte da notícia.
  const palavrasIgnoradas = [
    'assista', 'clique', 'leia mais', 'saiba mais', 'veja também',
    'siga-nos', 'compartilhe', 'inscreva-se', 'confira', 'ouça agora',
    'acesse', 'baixe o aplicativo'
  ];

  // Tenta capturar o título da notícia "H1", mas se não encontrar, usa o título da aba "document.title".
  const titulo = document.querySelector('h1')?.innerText.trim() || document.title.trim();

  const conteudo = seletoresNoticia
    .map((seletor) => document.querySelector(seletor)) // Tenta encontrar o elemento de notícia usando os seletores conhecidos.
    .find((elemento) => elemento && elemento.innerText.trim().length >= tamanhoMinimoNoticia);
  const seletorIgnorados = seletoresIgnorados.join(',');
  // Usa parágrafos do conteúdo principal e descarta os que pertencem a blocos ignorados.
  const paragrafosNoticia = conteudo
    ? Array.from(conteudo.querySelectorAll('p'))
      .filter((paragrafo) => {
        let elemento = paragrafo;
        while (elemento && elemento !== conteudo) {
          if (elemento.matches(seletorIgnorados)) return false;
          elemento = elemento.parentElement;
        }
        return true;
      })
      .map((paragrafo) => paragrafo.innerText.trim())
      .filter((paragrafo) => paragrafo.length >= 30)
    : [];

  // Se nenhum seletor conhecido funcionar, usa body como último recurso.
  const textoBruto = conteudo
    ? paragrafosNoticia.length >= 2
      ? paragrafosNoticia.join('\n')
      : conteudo.innerText
    : document.body.innerText; // "innerText" lê apenas o texto visível

  // Limpa espaços repetidos, linhas vazias e símbolos isolados de interface.
  const textoCorpoCompleto = textoBruto
    .split('\n')
    .map((linha) => linha.replace(/\s+/g, ' ').trim())
    .filter((linha) => linha.length >= 3 && /[\p{L}\p{N}]{2}/u.test(linha))
    .filter((linha) => !/^(t[ií]tulo|subt[ií]tulo|autoclassifica[cç][aã]o et[aá]ria|agora|ao vivo|play|pausa|volume)\s*:/i.test(linha))
    .filter((linha) => linha.toLowerCase() !== titulo.toLowerCase())
    .filter((linha) => {
      const linhaNormalizada = linha
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
      return !palavrasIgnoradas.some((palavra) => {
        const palavraNormalizada = palavra
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase();
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
    + (palavras.length > 100 ? '...' : ''); // Se o texto for maior adiciona reticências "..."
  // Limita a entrada do classificador ao título e ao início do artigo; o texto completo é preservado.
  const paragrafoPrincipal = paragrafosNoticia.find((paragrafo) => paragrafo.length >= 100)
    || document.querySelector('meta[name="description"]')?.getAttribute('content')?.trim()
    || paragrafosNoticia[0]
    || textoCorpoCompleto.slice(0, 600);
  const textoClassificacao = [titulo, paragrafoPrincipal]
    .filter(Boolean)
    .join('\n\n')
    .slice(0, 4000);

  // Tenta encontrar o autor "meta" e seletores comuns de noticias.
  const autor = (
    document.querySelector('meta[name="author"]')?.getAttribute('content')?.trim()
    || document.querySelector('[itemprop="author"]')?.textContent?.trim()
    || document.querySelector('[rel="author"], .author, [class*="author" i]')?.textContent?.trim()
    || 'Não identificado.'
  ).replace(/\d{2}\/\d{2}\/\d{4}.*$/, '').trim(); // Remove a datas que ficam junto com o nome do autor.

  // Prioriza a data estruturada, pois ela costuma ser mais confiável.
  // 1. Captura a string original da data
  const dataBruta = document.querySelector('meta[property="article:published_time"]')?.getAttribute('content')?.trim()
    || document.querySelector('meta[name="date"], meta[name="pubdate"]')?.getAttribute('content')?.trim()
    || document.querySelector('time[datetime]')?.getAttribute('datetime')?.trim()
    || document.querySelector('time')?.textContent?.trim();

  // 2. Valida e formata apenas para o dia/mês/ano no padrão PT-BR
  const dataPublicacao = (dataBruta && !isNaN(Date.parse(dataBruta)))
    ? new Date(dataBruta).toLocaleDateString('pt-BR', { timeZone: 'UTC' })
    : 'Não identificada.';

  // Usa o hostname (URL da página) como fonte ou marca como "Não identificada".
  const fonte = window.location.hostname || 'Não identificada.';

  // Prepara o texto completo e o texto de prévia para envio ao back-end.
  const textoCompleto = [
    `Título: ${titulo}`,
    `Notícia: ${textoCorpoCompleto}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Site: ${fonte}`
  ].join('\n\n');

  // Prepara o texto de prévia para exibição no popup da extensão
  const textoPrevia = [
    `Título: ${titulo}`,
    `Notícia base: ${textoCorpoPrevia}`,
    `Autor: ${autor}`,
    `Data de publicação: ${dataPublicacao}`,
    `Site: ${fonte}`,
    `Contador de palavras: ${palavras.length}.`
  ].join('\n\n');

  return { textoCompleto, textoPrevia, textoClassificacao };
}

// Converte as probabilidades binárias em uma leitura de tendência, sem criar
// rótulos de "verdade parcial" que não existem nos dados de treinamento.
const CONFIANCA_TENDENCIA_FORTE = 85;
const CONFIANCA_TENDENCIA_MODERADA = 70;

function interpretarEstimativa(probabilidades, veredicto) {
  const valorVerdadeira = probabilidades?.VERDADEIRA;
  const valorFalsa = probabilidades?.FALSA;
  if (valorVerdadeira == null || valorFalsa == null) return null;

  const probabilidadeVerdadeira = Number(valorVerdadeira);
  const probabilidadeFalsa = Number(valorFalsa);
  if (!Number.isFinite(probabilidadeVerdadeira) || !Number.isFinite(probabilidadeFalsa)) {
    return null;
  }

  const classe = probabilidadeVerdadeira >= probabilidadeFalsa
    ? { nome: 'VERDADEIRA', confianca: probabilidadeVerdadeira }
    : { nome: 'FALSA', confianca: probabilidadeFalsa };
  const tendencia = classe.confianca >= CONFIANCA_TENDENCIA_FORTE
    ? `Tendência forte do modelo para ${classe.nome}.`
    : classe.confianca >= CONFIANCA_TENDENCIA_MODERADA
      ? `Tendência moderada do modelo para ${classe.nome}.`
      : `Sem tendência suficientemente forte: maior estimativa para ${classe.nome} (${classe.confianca}%).`;
  const situacao = veredicto === 'INCERTO'
    ? ' A decisão continua inconclusiva: o modelo se absteve.'
    : veredicto === 'INDETERMINADO'
      ? ' O classificador treinado não está disponível.'
      : '';

  return `${tendencia}${situacao} Essa estimativa descreve padrões textuais, não confirma os fatos.`;
}

// Apresenta veredicto, explicação, evidências e controles de feedback no popup.
function renderizarResultado(resultadoDiv, dados, textoAnalisado) {
  // Usa a classe retornada pelo back-end para escolher o estilo do cartão.
  // INCERTO representa uma abstenção do modelo, não uma confirmação de que a notícia é falsa.
  const veredicto = dados.veredicto || 'INDETERMINADO';
  resultadoDiv.style.display = 'block';
  resultadoDiv.className = veredicto === 'FALSO'
    ? 'falso'
    : veredicto === 'VERDADEIRO' ? 'verdadeiro' : 'inconclusivo';
  resultadoDiv.replaceChildren();

  // Traduz os rótulos técnicos da API em um título que a pessoa consiga entender.
  const titulo = document.createElement('h4');
  titulo.textContent = veredicto === 'FALSO'
    ? 'Classificador textual: DESINFORMAÇÃO'
    : veredicto === 'VERDADEIRO'
      ? 'Classificador textual: CONFIÁVEL'
      : veredicto === 'INCERTO'
        ? 'Classificador textual: INCONCLUSIVO'
        : 'Não foi possível classificar';
  resultadoDiv.append(titulo);

  // Mostra a explicação gerada ou, se houver falha, a mensagem retornada pelo servidor.
  const respostaIA = document.createElement('section');
  respostaIA.className = 'resposta-ia';
  const tituloIA = document.createElement('h5');
  tituloIA.textContent = 'Resumo gerado pela IA';
  respostaIA.append(tituloIA);
  const textoIA = document.createElement('p');
  textoIA.textContent = dados.resposta_ia
    || dados.erro_geracao_ia
    || 'Não foi possível gerar uma explicação para este texto.';
  respostaIA.append(textoIA);
  resultadoDiv.append(respostaIA);

  // Mostra probabilidades por classe; respostas antigas da API podem trazer só uma estimativa.
  if (dados.probabilidades_veracidade) {
    const probabilidades = document.createElement('p');
    const estimativas = [
      ['Verdadeira', dados.probabilidades_veracidade.VERDADEIRA],
      ['Falsa', dados.probabilidades_veracidade.FALSA]
    ].filter(([, valor]) => valor != null)
      .map(([rotulo, valor]) => `${rotulo}: ${valor}%`);
    probabilidades.className = 'probabilidades-modelo';
    probabilidades.textContent = `Estimativa do modelo:\n${estimativas.join(' | ')}`;
    resultadoDiv.append(probabilidades);
    const interpretacao = interpretarEstimativa(
      dados.probabilidades_veracidade,
      veredicto
    );
    if (interpretacao) {
      const leitura = document.createElement('p');
      leitura.className = 'interpretacao-modelo';
      leitura.textContent = interpretacao;
      resultadoDiv.append(leitura);
    }
  } else if (dados.confianca_veracidade != null) {
    const confianca = document.createElement('p');
    confianca.className = 'probabilidades-modelo';
    confianca.textContent = `Estimativa do modelo:\n${dados.confianca_veracidade}%`;
    resultadoDiv.append(confianca);
  } else if (dados.probabilidade_veracidade != null) {
    const probabilidade = document.createElement('p');
    probabilidade.className = 'probabilidades-modelo';
    probabilidade.textContent = `Estimativa do modelo:\n${dados.probabilidade_veracidade}%`;
    resultadoDiv.append(probabilidade);
  }

  // Resultados externos são revisões publicadas; o texto do avaliador não vira rótulo local.
  const checagensGoogle = dados.checagens_fact_check_google;
  if (checagensGoogle) {
    const secaoGoogle = document.createElement('section');
    secaoGoogle.className = 'checagens-google';
    const tituloGoogle = document.createElement('h5');
    tituloGoogle.textContent = 'Checagens de fatos';
    secaoGoogle.append(tituloGoogle);

    const mensagemGoogle = document.createElement('p');
    mensagemGoogle.textContent = checagensGoogle.mensagem
      || 'Não foi possível obter o estado da busca Google Fact Check.';
    if (checagensGoogle.status === 'erro') {
      mensagemGoogle.classList.add('erro-checagem-google');
    }
    secaoGoogle.append(mensagemGoogle);

    const listaChecagens = document.createElement('ul');
    (checagensGoogle.resultados || []).forEach((checagem) => {
      const item = document.createElement('li');
      const link = document.createElement(checagem.url ? 'a' : 'span');
      link.textContent = checagem.titulo || checagem.alegacao || 'Checagem sem título';
      if (checagem.url) {
        try {
          const url = new URL(checagem.url);
          if (url.protocol === 'http:' || url.protocol === 'https:') {
            link.href = url.href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
          }
        } catch {
          // Mantém o título como texto se o endereço devolvido não for uma URL válida.
        }
      }
      item.append(link);

      const detalhes = [
        checagem.publicador,
        checagem.avaliacao_textual,
        checagem.data_revisao
      ].filter(Boolean).join(' | ');
      if (detalhes) {
        const metadados = document.createElement('span');
        metadados.textContent = ` (${detalhes})`;
        item.append(metadados);
      }
      listaChecagens.append(item);
    });
    if (listaChecagens.childElementCount) {
      secaoGoogle.append(listaChecagens);

      const avisoGoogle = document.createElement('p');
      avisoGoogle.className = 'aviso-modelo';
      avisoGoogle.textContent = 'Checagem feita pelo Google Fact Check. Confira a alegação e a matéria original, pois essa avaliação pode divergir.';
      secaoGoogle.append(avisoGoogle);
    }
    resultadoDiv.append(secaoGoogle);
  }

  // =========================================================================
  // CRITÉRIOS AVALIADOS (RESILIÊNCIA VISUAL ATIVA)
  // Oculta dinamicamente campos não identificados do DOM em vez de exibir 'Não identificado'.
  // =========================================================================
  const criteriosDeIdentificacao = {
    Autor: 'Autor',
    'Data de publicação': 'Data de publicação',
    'Fonte/site': 'Fonte'
  };

  const listaCriterios = document.createElement('ul');
  let totalCriteriosExibidos = 0;

  // Helper para validar se o valor retornado não é um texto nulo ou vazio
  const temValorValido = (val) => {
    if (!val) return false;
    const limpo = String(val).trim().toLowerCase();
    return (
      limpo !== '' &&
      !limpo.startsWith('não ') &&
      !limpo.startsWith('nao ') &&
      limpo !== 'undefined' &&
      limpo !== 'null'
    );
  };

  (dados.criterios || [])
    .filter((criterio) => Object.hasOwn(criteriosDeIdentificacao, criterio.criterio))
    .forEach((criterio) => {
      const valor = criterio.explicacao || criterio.avaliacao;
      // Só renderiza o <li> se a informação foi de fato identificada na página
      if (temValorValido(valor)) {
        const item = document.createElement('li');
        const rotulo = criteriosDeIdentificacao[criterio.criterio];
        item.textContent = `${rotulo}: ${valor}`;
        listaCriterios.append(item);
        totalCriteriosExibidos++;
      }
    });

  // Se ao menos um critério foi identificado, adiciona a seção ao DOM; caso contrário, não renderiza nada
  if (totalCriteriosExibidos > 0) {
    const criterios = document.createElement('section');
    const tituloCriterios = document.createElement('h5');
    tituloCriterios.textContent = 'Critérios avaliados';
    criterios.append(tituloCriterios);
    criterios.append(listaCriterios);
    resultadoDiv.append(criterios);
  }

  // Só apresenta matérias relacionadas se o backend realmente devolver fontes locais.
  const evidencias = dados.evidencias || [];
  if (evidencias.length) {
    const secaoEvidencias = document.createElement('section');
    secaoEvidencias.className = 'materias-relacionadas';
    const tituloEvidencias = document.createElement('h5');
    tituloEvidencias.textContent = 'Matérias relacionadas';
    secaoEvidencias.append(tituloEvidencias);
    const listaEvidencias = document.createElement('ul');

    // Links externos são aceitos somente para endereços HTTP(S) válidos.
    evidencias.forEach((evidencia) => {
      const item = document.createElement('li');
      const nome = document.createElement(evidencia.url ? 'a' : 'span');
      nome.textContent = evidencia.titulo || 'Notícia sem título';
      if (evidencia.url) {
        try {
          const url = new URL(evidencia.url);
          if (url.protocol === 'http:' || url.protocol === 'https:') {
            nome.href = url.href;
            nome.target = '_blank';
            nome.rel = 'noopener noreferrer';
          }
        } catch {
          nome.textContent = evidencia.titulo || 'Notícia sem título';
        }
      }
      item.append(nome);

      const metadados = [evidencia.data, evidencia.assunto].filter(Boolean).join(' | ');
      if (metadados) {
        const detalhe = document.createElement('span');
        detalhe.textContent = ` (${metadados})`;
        item.append(detalhe);
      }

      listaEvidencias.append(item);
    });
    secaoEvidencias.append(listaEvidencias);
    resultadoDiv.append(secaoEvidencias);
  }

  // Permite avaliar a utilidade do resultado e corrigir a classificação quando necessário.
  const feedback = document.createElement('section');
  feedback.className = 'feedback';
  const tituloFeedback = document.createElement('h5');
  tituloFeedback.textContent = 'Essa classificação está correta?';
  feedback.append(tituloFeedback);

  const botoesFeedback = document.createElement('div');
  botoesFeedback.className = 'botoes-feedback';
  const botaoUtil = document.createElement('button');
  botaoUtil.type = 'button';
  botaoUtil.textContent = 'Sim';
  const botaoImpreciso = document.createElement('button');
  botaoImpreciso.type = 'button';
  botaoImpreciso.textContent = 'Não';
  botoesFeedback.append(botaoUtil, botaoImpreciso);
  feedback.append(botoesFeedback);

  const mensagemFeedback = document.createElement('p');
  mensagemFeedback.className = 'mensagem-feedback';
  mensagemFeedback.setAttribute('role', 'status');
  mensagemFeedback.setAttribute('aria-live', 'polite');
  feedback.append(mensagemFeedback);

  const formulario = document.createElement('form');
  formulario.className = 'formulario-feedback';
  formulario.hidden = true;

  // A pessoa pode corrigir o rótulo previsto e explicar o motivo antes de enviar.
  const rotuloClassificacao = document.createElement('p');
  rotuloClassificacao.className = 'rotulo-classificacao';
  rotuloClassificacao.textContent = 'Qual é a classificação correta?';
  const botoesClassificacao = document.createElement('div');
  botoesClassificacao.className = 'botoes-classificacao';
  let classificacaoSelecionada = null;
  const botoesRotulo = [
    ['VERDADEIRA', 'Verdadeira'],
    ['FALSA', 'Falsa']
  ].map(([valor, texto]) => {
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.textContent = texto;
    botao.setAttribute('aria-pressed', 'false');
    botao.addEventListener('click', () => {
      // Guarda o rótulo escolhido e o comunica também aos leitores de tela.
      classificacaoSelecionada = valor;
      botoesRotulo.forEach(([outroValor, outroBotao]) => {
        outroBotao.setAttribute('aria-pressed', String(outroValor === valor));
      });
      mensagemFeedback.textContent = '';
    });
    botoesClassificacao.append(botao);
    return [valor, botao];
  });

  const rotuloMotivo = document.createElement('label');
  rotuloMotivo.textContent = 'Por que você escolheu essa catégoria?';
  rotuloMotivo.htmlFor = 'motivoFeedback';
  const motivo = document.createElement('textarea');
  motivo.id = 'motivoFeedback';
  motivo.required = true;
  motivo.maxLength = 2000;
  motivo.rows = 3;
  motivo.placeholder = 'Informe fontes ou evidências que apoiem sua classificação.';
  rotuloMotivo.append(motivo);

  const enviar = document.createElement('button');
  enviar.type = 'submit';
  enviar.textContent = 'Enviar análise';
  formulario.append(rotuloClassificacao, botoesClassificacao, rotuloMotivo, enviar);
  feedback.append(formulario);
  resultadoDiv.append(feedback);

  // Envia a avaliação ao back-end, mostrando o estado de envio e permitindo nova tentativa em caso de falha.
  async function enviarFeedback(util, classificacaoUsuario = null, motivoUsuario = '') {
    mensagemFeedback.replaceChildren();
    const indicador = document.createElement('span');
    indicador.className = 'indicador-feedback';
    indicador.setAttribute('aria-hidden', 'true');
    const textoEnvio = document.createElement('span');
    textoEnvio.textContent = 'Enviando sua avaliação...';
    mensagemFeedback.append(indicador, textoEnvio);
    botaoUtil.disabled = true;
    botaoImpreciso.disabled = true;
    enviar.disabled = true;
    botoesRotulo.forEach(([, botao]) => { botao.disabled = true; });
    try {
      const response = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          texto: textoAnalisado,
          util,
          classificacao: classificacaoUsuario,
          motivo: motivoUsuario,
          veredicto_predito: veredicto
        })
      });
      if (!response.ok) {
        throw new Error(`Servidor respondeu com HTTP ${response.status}`);
      }
      // Confirma o recebimento e oculta os controles para evitar envios duplicados.
      mensagemFeedback.replaceChildren();
      mensagemFeedback.classList.add('feedback-concluido');
      mensagemFeedback.textContent = 'Obrigado pela sua avaliação!';
      botoesFeedback.hidden = true;
      formulario.hidden = true;
      botaoUtil.disabled = true;
      botaoImpreciso.disabled = true;
      enviar.disabled = true;
    } catch (error) {
      // Restaura os controles para que a pessoa possa tentar novamente.
      mensagemFeedback.replaceChildren();
      mensagemFeedback.textContent = 'Não foi possível registrar sua avaliação. Verifique com a equipe técnica e tente novamente mais tarde.';
      botaoUtil.disabled = false;
      botaoImpreciso.disabled = false;
      enviar.disabled = false;
      botoesRotulo.forEach(([, botao]) => { botao.disabled = false; });
    }
  }

  botaoUtil.addEventListener('click', () => enviarFeedback(true));
  botaoImpreciso.addEventListener('click', () => {
    // Só abre o formulário detalhado quando a pessoa indica que o resultado não foi útil.
    formulario.hidden = false;
    motivo.focus();
  });
  formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    // Exige uma classe e uma justificativa antes de registrar uma correção.
    if (!classificacaoSelecionada) {
      mensagemFeedback.textContent = 'Selecione se a notícia é verdadeira ou falsa.';
      return;
    }
    motivo.value = motivo.value.trim();
    if (!formulario.reportValidity()) return;
    await enviarFeedback(false, classificacaoSelecionada, motivo.value.trim());
  });
}

// O clique no botão "analisarBtn" inicia o fluxo de captura e análise da notícia.
document.getElementById('analisarBtn').addEventListener('click', async () => { 
  // Guarda os elementos do popup que serão atualizados durante o fluxo.
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

    // A captura mantém separados o texto integral e as versões usadas na interface/modelo.
    const captura = results[0].result;
    if (!captura?.textoCompleto || !captura?.textoPrevia || !captura?.textoClassificacao) {
      resultadoDiv.innerText = 'Não foi possível capturar o texto completo da notícia.';
      return;
    }
    const textoNoticia = captura.textoCompleto;

    // A prévia é apenas para leitura no popup; o back-end recebe o artigo integral
    // e usa o campo curto separado para a classificação textual.
    textoDiv.value = captura.textoPrevia;

    try {
      // O back-end espera o JSON.
      // O título e o início do artigo são enviados separadamente para o classificador.
      // ALTERE AQUI SE O BACK-END ESTIVER EM OUTRA URL, PORTA OU SERVIDOR.
      const response = await fetch('http://localhost:8000/verificar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          texto: textoNoticia,
          texto_classificacao: captura.textoClassificacao
        })
      });

      // Se a resposta do back-end não for 200 OK, lança um erro para ser capturado no "catch".
      if (!response.ok) {
        const detalhe = await response.text();
        throw new Error(
          `Servidor respondeu com HTTP ${response.status}${detalhe ? `: ${detalhe}` : ''}`
        );
      }

      // Converte o JSON da API e delega toda a montagem visual à função de renderização.
      const dados = await response.json();
      renderizarResultado(resultadoDiv, dados, textoNoticia);
    } catch (error) {
      // Captura falhas de rede, back-end desligado ou respostas inesperadas.
      resultadoDiv.innerText = error instanceof Error
        ? `Não foi possível analisar a notícia completa: ${error.message}`
        : 'Não foi possível analisar a notícia completa. Verifique se o back-end está executando em http://localhost:8000.';
    }
  });
});