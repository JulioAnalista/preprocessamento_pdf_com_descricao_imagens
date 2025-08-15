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

REPORT_PATH = Path(__file__).resolve().parent / "report_verificacao_descricoes.md"


def stats_for_file(file_id: str):
    items = pdb.get_image_descriptions_for_file(file_id)
    com_ocr = sum(1 for it in items if (it.get('ocr_text') or '').strip())
    sem_ocr = sum(1 for it in items if not (it.get('ocr_text') or '').strip())
    total = len(items)
    return total, com_ocr, sem_ocr


def run_for_pdf(client: TestClient, pdf_path: str):
    p = Path(pdf_path)
    if not p.exists():
        return {"pdf": pdf_path, "status": "missing"}
    # Upload
    with open(p, 'rb') as f:
        r = client.post('/api/upload', files={'file': (p.name, f, 'application/pdf')})
    assert r.status_code == 200, r.text
    fid = r.json()['file_id']
    # Extrair (usa cache se existir)
    e = client.post(f"/api/extract/{fid}")
    assert e.status_code == 200, e.text
    # Descrever (gera apenas o que falta)
    d = client.post(f"/api/caption/{fid}")
    assert d.status_code == 200, d.text
    # Estatísticas
    total, com_ocr, sem_ocr = stats_for_file(fid)
    return {"pdf": pdf_path, "file_id": fid, "total": total, "com_ocr": com_ocr, "sem_ocr": sem_ocr}


def main():
    pdb.ensure_schema()
    client = TestClient(app)

    rows = []
    for path in PDFS:
        rows.append(run_for_pdf(client, path))

    # Detecção de reutilização do DB: reexecuta e compara
    reuse_rows = []
    for path in PDFS:
        reuse_rows.append(run_for_pdf(client, path))

    now = datetime.utcnow().isoformat()
    out = []
    out.append(f"# Verificação descrições (OCR + reutilização) ({now}Z)\n")
    for first, second in zip(rows, reuse_rows):
        out.append(f"## PDF: {first['pdf']}")
        if first.get('status') == 'missing':
            out.append("- Status: arquivo não encontrado\n"); continue
        out.append(f"- file_id: {first['file_id']}")
        out.append(f"- total: {first['total']} (2ª passada: {second['total']})")
        out.append(f"- com OCR: {first['com_ocr']} (2ª passada: {second['com_ocr']})")
        out.append(f"- sem OCR: {first['sem_ocr']} (2ª passada: {second['sem_ocr']})\n")

    REPORT_PATH.write_text("\n".join(out), encoding='utf-8')
    print(f"Relatório salvo em: {REPORT_PATH}")

if __name__ == '__main__':
    main()

