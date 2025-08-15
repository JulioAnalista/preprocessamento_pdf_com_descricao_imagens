# Cleanup de duplicatas no banco (pdf_files)

Objetivo: Manter apenas uma instância de cada PDF por pdf_hash, consolidando referências e extrações para um file_id canônico e removendo entradas duplicadas.

Como funciona
- Agrupa registros de pdf_files por pdf_hash
- Escolhe um file_id canônico por grupo:
  - Preferência para o que possui extraction_json_path existente
  - Caso contrário, o mais antigo (created_at)
- Move referências:
  - pdf_image_refs (file_id, page, img_index, image_hash)
  - pdf_table_refs (file_id, page, table_index, table_hash)
  - Usa INSERT ... ON CONFLICT DO NOTHING para evitar duplicidades
- Move extractions se o canônico ainda não tiver
- Em modo APPLY, remove os file_id restantes (refs, extractions e pdf_files)

Comandos
- Dry-run (apenas relatório):
  - python -m pdf_preproc.tools.cleanup_duplicates
- Aplicar (executa remoções de fato):
  - python -m pdf_preproc.tools.cleanup_duplicates --apply

Relatório
- duplicates: grupos com mais de um file_id
- kept: quantos file_id canônicos mantidos
- removed: quantos file_id removidos (somente com --apply)
- moved_img_refs / moved_tbl_refs: total de refs movidas
- moved_extractions: quantas extractions transferidas para o canônico

Pré-requisitos
- As tabelas devem seguir o schema usado pelo app (pdf_files, pdf_image_refs, pdf_table_refs, extractions). O script chama ensure_schema() para criar se necessário.

Observações
- O script não toca nas tabelas de imagens e tabelas (images, tables) porque são deduplicadas por hash.
- Não mexe em arquivos do sistema (como imagens públicas ou zips); apenas consolida registros no DB.
- É idempotente e pode ser executado mais de uma vez.

