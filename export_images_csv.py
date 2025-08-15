import csv
from pathlib import Path
from pdf_preproc import db as pdb

def export_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with pdb.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.image_hash,
                   '/public/images/' || r.image_hash || '.png' as url,
                   i.width, i.height,
                   COALESCE(d.description, '') as description,
                   pf.pdf_hash,
                   r.file_id,
                   r.page as pagina
            FROM pdf_image_refs r
            JOIN images i ON i.hash = r.image_hash
            LEFT JOIN image_descriptions d ON d.image_hash = r.image_hash
            JOIN pdf_files pf ON pf.file_id = r.file_id
            ORDER BY pf.pdf_hash, r.page, r.image_hash
            """
        )
        rows = cur.fetchall()
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['image_hash','url','width','height','description','pdf_hash','file_id','pagina'])
        for row in rows:
            w.writerow(row)

if __name__ == '__main__':
    out = Path(__file__).resolve().parent / 'public' / 'exports' / 'imagens.csv'
    export_csv(out)
    print('CSV salvo em:', out)

