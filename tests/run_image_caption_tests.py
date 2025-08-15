import os
from pathlib import Path
from datetime import datetime

from pdf_preproc.image_caption import caption_images_from_extraction

REPORT = Path(__file__).resolve().parent / 'report_image_captions.md'

PDF_EXTRACTIONS = [
    # colocar paths dos extraction.json recém criados
    # serão detectados automaticamente se existir a subpasta ao lado do PDF
]

# varre as pastas de uploads e PDOT/comparacao para achar extraction.json
CANDIDATES = []
root = Path('/mnt/e/maquinaMP/normas_internas/pdf_preproc/uploads')
if root.exists():
    for p in root.glob('*/*'):
        if p.name == 'extraction.json':
            CANDIDATES.append(p)


def main():
    now = datetime.utcnow().isoformat()
    out = [f"# Relatório Descrição de Imagens ({now}Z)\n"]
    count = 0
    for ex in CANDIDATES:
        try:
            results = caption_images_from_extraction(ex)
            out.append(f"## {ex}")
            for r in results[:10]:
                out.append(f"- {r['hash']}: {r['description'][:200]}...")
            out.append("")
            count += len(results)
        except Exception as e:
            out.append(f"## {ex}\n- erro: {e}\n")
    REPORT.write_text("\n".join(out), encoding='utf-8')
    print(f"Relatório salvo em: {REPORT} (descrições geradas: {count})")

if __name__ == '__main__':
    main()

