// Logger visual
const logPanel = document.getElementById('logPanel');
function log(msg) {
  const t = new Date().toISOString();
  logPanel.textContent += `[${t}] ${msg}\n`;
  logPanel.scrollTop = logPanel.scrollHeight;
}

// Esperar o bridge carregar e expor pdfjsLib
if (!window['pdfjsLib']) {
  log('Aguardando pdfjsLib do bridge...');
}
const waitPdfjs = new Promise((resolve) => {
  let tries = 0;
  const h = setInterval(() => {
    if (window['pdfjsLib']) { clearInterval(h); resolve(); }
    if (++tries > 50) { clearInterval(h); resolve(); }
  }, 100);
});

waitPdfjs.then(() => {
  if (window['pdfjsLib']) {
    try { pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdfjs/pdf.worker.js'; }
    catch (e) { log('Erro ao configurar worker do PDF.js: ' + (e?.message||e)); }
  } else {
    log('pdfjsLib não carregado. Verifique se /static/pdfjs/bridge.js e pdf.js estão acessíveis.');
  }
});

const state = {
  fileId: null,
  totalPages: 0,
  currentPage: 1,
  extract: null
};

// Tabs
const tabs = document.querySelectorAll('.tab');
const tabPanels = {
  texto: document.getElementById('tab-texto'),
  imagens: document.getElementById('tab-imagens'),
  tabelas: document.getElementById('tab-tabelas'),
  metadados: document.getElementById('tab-metadados'),
  descricoes: document.getElementById('tab-descricoes')
}

tabs.forEach(btn => btn.addEventListener('click', () => {
  tabs.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const tab = btn.dataset.tab;
  for (const [key, el] of Object.entries(tabPanels)) {
    el.classList.toggle('hidden', key !== tab);
  }
}));

// Upload
const pdfInput = document.getElementById('pdfFile');
const btnUpload = document.getElementById('btnUpload');
const btnExtrair = document.getElementById('btnExtrair');
const btnDescrever = document.getElementById('btnDescrever');
const btnBaixar = document.getElementById('btnBaixar');
const prevPage = document.getElementById('prevPage');
const nextPage = document.getElementById('nextPage');
const pageInfo = document.getElementById('pageInfo');


// Carregar do Banco de Dados
const btnLoadDB = document.getElementById('btnLoadDB');
const dbLoader = document.getElementById('dbLoader');
const dbFiles = document.getElementById('dbFiles');
const btnLoadSelected = document.getElementById('btnLoadSelected');

btnLoadDB.addEventListener('click', async () => {
  dbLoader.classList.remove('hidden');
  // pedir lista agrupada por pdf_hash
  const res = await fetch('/api/files?group_by=pdf');
  if (!res.ok) { log('Falha ao listar arquivos do banco'); return; }
  const data = await res.json();
  dbFiles.innerHTML = '';
  for (const it of (data.items||[])) {
    const opt = document.createElement('option');
    opt.value = it.file_id;
    opt.textContent = `${it.original_filename} (imgs:${it.images} descr:${it.images_described} tabs:${it.tables})`;
    dbFiles.appendChild(opt);
  }
});

btnLoadSelected.addEventListener('click', async () => {
  const fid = dbFiles.value;
  if (!fid) { alert('Selecione um arquivo'); return; }
  log('Carregando do banco: ' + fid);
  const res = await fetch(`/api/file/${fid}`);
  if (!res.ok) { const t = await res.text(); log('Falha ao carregar: ' + t); return; }
  const data = await res.json();
  state.fileId = fid;
  state.extract = data;
  renderTabs();
  btnExtrair.disabled = false;
  btnDescrever.disabled = false;
  try { await loadPdf(); } catch (e) { log('Aviso: não foi possível carregar o PDF no viewer: ' + (e?.message||e)); }
  await loadCaptions?.();
});

btnUpload.addEventListener('click', async () => {
  const file = pdfInput.files?.[0];
  if (!file) { alert('Selecione um PDF'); log('Nenhum arquivo selecionado.'); return; }

  const form = new FormData();
  form.append('file', file);

  log('Enviando PDF...');
  btnBaixar.classList.add('hidden');
  const res = await fetch('/api/upload', { method: 'POST', body: form });
  if (!res.ok) { const t = await res.text(); log('Falha no upload: ' + t); alert('Falha no upload'); return; }
  const data = await res.json();
  state.fileId = data.file_id;
  log('Upload OK. file_id=' + state.fileId + ' filename=' + data.filename);
  try {
    await loadPdf();
    btnExtrair.disabled = false;
  } catch (e) {
    log('Erro ao carregar PDF no viewer: ' + (e?.message||e));
  }
});

async function loadPdf() {
  const url = `/api/pdf/${state.fileId}`;
  log('Carregando PDF no viewer a partir de ' + url);
  if (!window['pdfjsLib']) {
    throw new Error('pdfjsLib não está disponível - verifique /static/pdfjs/pdf.min.js');
  }
  const loadingTask = pdfjsLib.getDocument(url);
  const pdf = await loadingTask.promise;
  state.totalPages = pdf.numPages;
  state.currentPage = 1;
  updatePager();
  await renderPage(pdf, state.currentPage);
  log('PDF renderizado: ' + state.totalPages + ' página(s).');
}

function updatePager() {
  pageInfo.textContent = `Página ${state.currentPage}/${state.totalPages}`;
  prevPage.disabled = state.currentPage <= 1;
  nextPage.disabled = state.currentPage >= state.totalPages;
}

async function renderPage(pdf, pageNum) {
  const page = await pdf.getPage(pageNum);
  const viewport = page.getViewport({ scale: 1.3 });
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = viewport.width;
  canvas.height = viewport.height;
  const renderContext = { canvasContext: ctx, viewport };
  document.getElementById('pdfViewer').innerHTML = '';
  document.getElementById('pdfViewer').appendChild(canvas);
  await page.render(renderContext).promise;
}

prevPage.addEventListener('click', async () => {
  if (!state.fileId) return;
  const url = `/api/pdf/${state.fileId}`;
  const pdf = await pdfjsLib.getDocument(url).promise;
  if (state.currentPage > 1) { state.currentPage--; updatePager(); await renderPage(pdf, state.currentPage); }
});

nextPage.addEventListener('click', async () => {
  if (!state.fileId) return;
  const url = `/api/pdf/${state.fileId}`;
  const pdf = await pdfjsLib.getDocument(url).promise;
  if (state.currentPage < state.totalPages) { state.currentPage++; updatePager(); await renderPage(pdf, state.currentPage); }
});

btnExtrair.addEventListener('click', async () => {
  if (!state.fileId) { log('Sem fileId, faça upload primeiro.'); return; }
  log('Iniciando extração...');
  const res = await fetch(`/api/extract/${state.fileId}`, { method: 'POST' });
  if (!res.ok) { const t = await res.text(); log('Falha na extração: ' + t); alert('Falha na extração: ' + t); return; }
  const data = await res.json();
  log('Extração concluída. Páginas=' + (data.pages?.length||0) + ' Tabelas=' + (data.tables?.length||0));
  state.extract = data;
  renderTabs();
  btnDescrever.disabled = false;
  if (data.download?.zip_url) {
    btnBaixar.href = data.download.zip_url;
    btnBaixar.classList.remove('hidden');
    log('Artefatos prontos para download: ' + data.download.zip_url);
  } else {
    btnBaixar.classList.add('hidden');
  }
});

function renderTabs() {
  if (!state.extract) return;
  // Texto puro por página
  const texts = state.extract.pages.map(p => `--- PÁGINA ${p.page} ---\n${p.text || ''}`).join('\n\n');
  tabPanels.texto.innerHTML = `<pre class="code">${escapeHtml(texts)}</pre>`;

  // Imagens por página
  const imgs = [];
  for (const p of state.extract.pages) {
    if (p.images?.length) {
      imgs.push(`<div><div style='color:#9ca3af;margin:6px 0'>Página ${p.page}</div><div class='img-grid'>${p.images.map(img => `<a href='${img.url}' target='_blank'><img src='${img.url}' alt='img p${p.page}'/></a>`).join('')}</div></div>`)
    }
  }
  tabPanels.imagens.innerHTML = imgs.length ? imgs.join('') : '<div class="muted">Nenhuma imagem encontrada</div>';

  // Tabelas
  const tabHtml = [];
  if (state.extract.tables?.length) {
    for (const t of state.extract.tables) {
      const rows = (t.rows || []).map(r => `<tr>${r.map(c => `<td>${escapeHtml(c || '')}</td>`).join('')}</tr>`).join('');
      tabHtml.push(`<div style='margin-bottom:10px'><div style='color:#9ca3af;margin:6px 0'>Página ${t.page} - Tabela ${t.index}</div><table class='table'><tbody>${rows}</tbody></table></div>`);
    }
  }
  tabPanels.tabelas.innerHTML = tabHtml.length ? tabHtml.join('') : '<div class="muted">Nenhuma tabela detectada</div>';

  // Metadados
  tabPanels.metadados.innerHTML = `<pre class='code'>${escapeHtml(JSON.stringify(state.extract.metadata || {}, null, 2))}</pre>`;
}

function escapeHtml(s) {
  return s?.toString().replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;') ?? '';
}

