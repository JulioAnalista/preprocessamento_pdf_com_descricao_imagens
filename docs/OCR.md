# OCR de Imagens (EasyOCR)

## Objetivo
Adicionar OCR às imagens únicas extraídas, para enriquecer o contexto textual além da descrição da Azure OpenAI.

## Como funciona
- Para cada imagem única (por hash), executamos EasyOCR (idiomas pt e en)
- O texto extraído (ocr_text) é:
  - Persistido em `image_descriptions.ocr_text`
  - Inserido também no `extraction.json` dentro de `pages[].images[].ocr_text`
- Continua a persistência de description e metadata geradas via Azure OpenAI

## Execução
- UI: Após “Extrair”, clique “Descrever imagens” (a mesma ação agora também realiza o OCR)
- CLI: `python pdf_preproc/tests/run_image_caption_tests.py`

## Requisitos
- easyocr instalado no virtualenv
- Performance: OCR é mais custoso; para grandes lotes, considerar paralelização e cache por hash (já deduplicamos por hash)

