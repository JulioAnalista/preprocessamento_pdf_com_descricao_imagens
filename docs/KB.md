# Bases de Conhecimento de Grafos

## Escopo
Construção de uma base por PDF (graph_id=pdf_hash) com nós de chunks textuais, tabelas e descrições de imagens (opcional), embutidos com Azure OpenAI (text-embedding-3-large).

## Processo
1. Agregação de conteúdo (texto por página + tabelas como JSON canônico)
2. Chunking (~4k chars)
3. Embedding Azure OpenAI
4. Inserção em graph_nodes; edges NEXT entre chunks
5. (Opcional) Inserir nós de descrições de imagens com embeddings

## Consultas futuras
- Similaridade: vetor em embedding (armazenado em JSON); integração posterior com Weaviate/Arango
- Filtros por graph_id (pdf_hash)

## Execução de testes
- Script: `pdf_preproc/tests/run_graph_kb_tests.py`
- Relatório: `pdf_preproc/tests/report_graph_kb.md`

