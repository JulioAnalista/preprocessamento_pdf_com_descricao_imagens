# Descrição de Imagens (Azure OpenAI)

## Objetivo
Gerar descrições e metadados estruturados para imagens únicas extraídas dos PDFs, persistindo no Postgres e enriquecendo o JSON de extração para consulta rápida e uso no grafo.

## Fluxo
1. Extração: imagens deduplicadas por hash e salvas em /public/images/<hash>.png
2. Descrição: endpoint /api/caption/{file_id} percorre extraction.json, chama Azure OpenAI multimodal com data URI base64 e retorna JSON com `descricao` e `metadados` (tipo_mapa, regiao, possui_legenda, itens_legenda, escala, cores_dominantes, texto_visivel)
3. Persistência: tabela `image_descriptions` (image_hash, model, description, metadata)
4. Enriquecimento: description e metadata são inseridos em pages[].images[] no próprio extraction.json
5. UI: botão “Descrever imagens” e aba “Descrições” exibem resultados

## Execução
- Backend rodando (uvicorn pdf_preproc.app:app --reload --port 8099)
- Abra a UI, faça upload e “Extrair”
- Clique “Descrever imagens”
- Veja a aba “Descrições” e o relatório de testes em `pdf_preproc/tests/report_image_captions.md`

## Variáveis Azure
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_VERSION (2025-01-01-preview)
- AZURE_OPENAI_CHAT_MODEL (gpt-4.1-nano ou equivalente disponível)

## Observações
- Não usamos OCR; apenas imagem -> descrição sem reconhecer texto explícito além do visível
- Modelo retorna JSON estrito; em casos de formatação inesperada, salvamos a string como descrição sem metadados
- Para grandes volumes, considere filas e controle de taxa

