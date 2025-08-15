import os
import json
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient

from pdf_preproc.app import app
from pdf_preproc import db as pdb

PDFS = [
    "/mnt/e/PDOT/comparacao/Anteprojeto_LC_PDOT_Aprovada_Conplan.pdf",
    "/mnt/e/PDOT/comparacao/Minuta_submetida_a_audiencia_publica.pdf",
]

REPORT = Path(__file__).resolve().parent / 'report_final_fase_imagens.md'


def main():
    pdb.ensure_schema()
    client = TestClient(app)

    out = []
    now = datetime.utcnow().isoformat()
    out.append(f"# Relatório Final - Fase Imagens (descrições + OCR + metadados) ({now}Z)\n")

    for pdf in PDFS:
        p = Path(pdf)
        if not p.exists():
            out.append(f"## {pdf}\n- Status: arquivo não encontrado\n"); continue
        # upload
        with open(p, 'rb') as f:
            r = client.post('/api/upload', files={'file': (p.name, f, 'application/pdf')})
        if r.status_code != 200:
            out.append(f"## {pdf}\n- ERRO upload: {r.text}\n"); continue
        fid = r.json()['file_id']
        # extract
        e = client.post(f"/api/extract/{fid}")
        if e.status_code != 200:
            out.append(f"## {pdf}\n- ERRO extract: {e.text}\n"); continue
        J = e.json()
        pages = len(J.get('pages', []))
        imgs = sum(len(pg.get('images', [])) for pg in J.get('pages', []))
        tbls = len(J.get('tables', []))
        # caption
        c = client.post(f"/api/caption/{fid}")
        if c.status_code != 200:
            out.append(f"## {pdf}\n- ERRO caption: {c.text}\n"); continue
        items = pdb.get_image_descriptions_for_file(fid)
        tot = len(items)
        com_ocr = sum(1 for it in items if (it.get('ocr_text') or '').strip())
        sem_ocr = tot - com_ocr
        com_desc = sum(1 for it in items if (it.get('description') or '').strip())

        out.append(f"## {pdf}")
        out.append(f"- file_id: {fid}")
        out.append(f"- páginas: {pages} | imagens: {imgs} | tabelas: {tbls}")
        out.append(f"- descrições no DB: {com_desc}/{tot}")
        out.append(f"- imagens com OCR: {com_ocr}/{tot}")
        out.append("")

    REPORT.write_text("\n".join(out), encoding='utf-8')
    print(f"Relatório salvo em: {REPORT}")

if __name__ == '__main__':
    main()

