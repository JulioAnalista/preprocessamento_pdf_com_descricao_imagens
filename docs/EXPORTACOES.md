# Exportações

## CSV de imagens descritas
- Colunas: image_hash, url, width, height, description, pdf_hash, file_id, pagina
- Origem: join entre images, image_descriptions e pdf_image_refs, e pdf_files

Exemplo de query (conceitual):

SELECT r.image_hash, 
       CONCAT('/public/images/', r.image_hash, '.png') AS url,
       i.width, i.height,
       d.description,
       pf.pdf_hash,
       r.file_id,
       r.page as pagina
FROM pdf_image_refs r
JOIN images i ON i.hash = r.image_hash
LEFT JOIN image_descriptions d ON d.image_hash = r.image_hash
JOIN pdf_files pf ON pf.file_id = r.file_id;

Saída em arquivo CSV pode ser adicionada via comando Python/psycopg2 (pendente de aceite) para `/pdf_preproc/public/exports/imagens.csv`.

