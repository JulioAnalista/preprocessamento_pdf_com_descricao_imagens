## pdf_preproc - Aplicação Web de Pré-processamento de PDFs para GraphRAG

Esta aplicação permite:
- Fazer upload de um PDF
- Visualizar o PDF (WYSIWYG) por página usando PDF.js (build local)
- Extrair e visualizar por abas: "Texto puro", "Imagens", "Tabelas" e "Metadados"
- Salvar os artefatos de extração na mesma pasta de entrada do PDF, criando uma subpasta com nome sanitizado do arquivo e um extraction.json
- Baixar os artefatos como um .zip público após a extração (botão "Baixar artefatos")

### Tecnologias
- Backend: FastAPI + Uvicorn
- Extração: PyMuPDF (texto, metadados, imagens) e pdfplumber (tabelas, se instalado)
- Frontend: HTML/CSS/JS + PDF.js (build local em `static/pdfjs`) com bridge ESM

### Endpoints
- POST /api/upload
  - Corpo: multipart/form-data com campo `file` (PDF real)
  - Resposta: `{ file_id, filename }`
- GET /api/pdf/{file_id}
  - Retorna o próprio PDF enviado (Content-Disposition: inline)
- POST /api/extract/{file_id}
  - Executa extração e grava artefatos em `<pasta_do_pdf>/<nome_sanitizado>/`
  - Cria `<pasta_do_pdf>/<nome_sanitizado>/extraction.json`
  - Cria um .zip com os artefatos em `/public/<nome-sanitizado>-<file_id>.zip`
  - Resposta JSON inclui `metadata`, `pages`, `tables`, `upload.output_dir` e `download.zip_url`
- GET /api/image/{file_id}/{image_name}
  - Servir imagens extraídas da subpasta `images`

### Estrutura de diretórios
- pdf_preproc/app.py (servidor)
- pdf_preproc/utils/pdf_extractor.py (extração)
- pdf_preproc/static/ (UI + pdf.js local em static/pdfjs)
- pdf_preproc/public/ (arquivos .zip públicos de artefatos)
- pdf_preproc/uploads/ (armazenamento padrão de PDFs enviados via UI)
  - Ao extrair, os artefatos ficam na MESMA pasta do PDF: se o PDF estiver em `pdf_preproc/uploads/XYZ.pdf`, a extração é salva em `pdf_preproc/uploads/<nome-sanitizado>/`

### Como executar
1. Ativar o ambiente Python do projeto
2. Instalar dependências (se necessário):
   - `pip install fastapi uvicorn python-multipart pdfplumber python-slugify`
3. Rodar o servidor:
   - `uvicorn pdf_preproc.app:app --reload --port 8099`
4. Acessar a UI:
   - http://127.0.0.1:8099/
5. Realizar upload de um PDF real e clicar "Extrair"; ao final, o botão "Baixar artefatos (.zip)" ficará disponível.

### Testes realizados
- Anteprojeto_LC_PDOT_Aprovada_Conplan.pdf: extração OK (páginas ~165, tabelas ~29), zip público gerado
- Minuta_submetida_a_audiencia_publica.pdf: extração OK (páginas ~156, tabelas ~33), zip público gerado

### Observações
- Sem função de fallback (OCR) automática, conforme diretriz do projeto.
- Use PDFs reais; a aplicação não cria dados fictícios.
- Se o PDF original já existir fora de `pdf_preproc/uploads`, ao fazer a extração, os artefatos serão salvos ao lado dele (é necessário que o backend tenha acesso ao caminho).
- Caso o botão de download não apareça, verifique se a resposta de `/api/extract/{file_id}` contém `download.zip_url` e faça hard refresh (Ctrl+F5) após atualizações do backend.

