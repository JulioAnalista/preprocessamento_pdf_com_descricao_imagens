async function describeImages() {
  if (!state.extract) { log('Não há extração carregada.'); return; }
  log('Descrições: iniciando...');

  try {
    const resp = await fetch(`/api/caption/${state.extract.upload.file_id}`, { method: 'POST' });
    if (!resp.ok) {
      const t = await resp.text();
      log('Falha ao descrever imagens: ' + t);
      return;
    }

    const data = await resp.json();
    log(`Descrições processadas: ${data.count} novas descrições geradas`);

    if (data.count === 0) {
      log('💡 Todas as imagens já foram descritas anteriormente (reutilizando cache)');
    } else {
      log(`✅ ${data.count} novas descrições foram geradas e salvas`);
    }

    await loadCaptions();
  } catch (error) {
    log('Erro ao processar descrições: ' + error.message);
  }
}

async function loadCaptions() {
  if (!state.extract) return;

  try {
    log('📖 Carregando descrições existentes...');
    const resp = await fetch(`/api/caption/${state.extract.upload.file_id}`);
    if (!resp.ok) {
      log('⚠️ Não foi possível carregar descrições: ' + resp.status);
      return;
    }

    const data = await resp.json();
    const items = data.items || [];
    log(`📊 Carregadas ${items.length} descrições de imagens`);

    if (items.length === 0) {
      log('💡 Nenhuma descrição encontrada. Clique em "Descrever imagens" para gerar.');
    }

    renderDescriptions(items);
  } catch (error) {
    log('Erro ao carregar descrições: ' + error.message);
  }
}

function renderDescriptions(items) {
  // Mostrar filtros
  const filterBox = document.getElementById('desc-filters');
  filterBox.classList.remove('hidden');

  // Aplicar filtros locais
  const q = (document.getElementById('desc-q').value || '').toLowerCase();
  const ocrSel = document.getElementById('desc-ocr').value;
  const filtered = items.filter(it => {
    const text = ((it.description||'') + ' ' + JSON.stringify(it.metadata||{}) + ' ' + (it.ocr_text||'')).toLowerCase();
    if (q && !text.includes(q)) return false;
    if (ocrSel === 'sim' && !(it.ocr_text||'').trim()) return false;
    if (ocrSel === 'nao' && (it.ocr_text||'').trim()) return false;
    return true;
  });

  const rows = [];
  rows.push('<table class="table"><thead><tr><th>Imagem</th><th>Hash</th><th>Descrição</th><th>Metadados</th><th>OCR</th><th>Página</th></tr></thead><tbody>');
  for (const it of filtered) {
    const meta = it.metadata ? JSON.stringify(it.metadata, null, 2) : '';
    const imgTag = `<img src="${it.url}" alt="${it.image_hash}" style="max-width:180px; max-height:180px; object-fit:contain;">`;
    rows.push(`<tr>
      <td>${imgTag}</td>
      <td><code>${it.image_hash}</code></td>
      <td><pre class="code">${escapeHtml(it.description||'')}</pre></td>
      <td><pre class="code">${escapeHtml(meta)}</pre></td>
      <td><pre class="code">${escapeHtml(it.ocr_text||'')}</pre></td>
      <td>${it.pagina ?? ''}</td>
    </tr>`);
  }
  rows.push('</tbody></table>');
  tabPanels.descricoes.innerHTML = rows.join('\n');

  // Ligar botão aplicar filtros
  const btn = document.getElementById('desc-aplicar');
  btn.onclick = () => renderDescriptions(items);
}

btnDescrever.addEventListener('click', describeImages);

// Quando carregarmos uma extração existente, busque as descrições já persistidas
document.addEventListener('DOMContentLoaded', () => {
  const origRenderTabs = window.renderTabs;
  window.renderTabs = function(...args) {
    const r = origRenderTabs.apply(this, args);
    if (state.extract?.upload?.file_id) {
      loadCaptions();
    }
    return r;
  }
});

