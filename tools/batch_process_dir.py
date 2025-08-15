import argparse
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

DEFAULT_HOST = os.getenv("PREPROC_HOST", "http://127.0.0.1:8099")


def process_pdf(client: requests.Session, pdf_path: Path):
    files = {"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
    r = client.post(f"{DEFAULT_HOST}/api/upload", files=files, timeout=300)
    r.raise_for_status()
    j = r.json()
    fid = j["file_id"]
    # extract
    r2 = client.post(f"{DEFAULT_HOST}/api/extract/{fid}", timeout=600)
    r2.raise_for_status()
    # caption
    r3 = client.post(f"{DEFAULT_HOST}/api/caption/{fid}", timeout=600)
    if r3.status_code not in (200, 204):
        print(f"warn: caption status={r3.status_code} {pdf_path}")
    return fid


def list_pdfs(folder: Path):
    return sorted([p for p in folder.glob("*.pdf") if p.is_file()])


def main(folder: str, workers: int):
    sess = requests.Session()
    paths = list_pdfs(Path(folder))
    if not paths:
        print("Nenhum PDF encontrado na pasta")
        return 1
    print(f"Processando {len(paths)} PDFs com {workers} workers em {folder}")
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process_pdf, sess, p): p for p in paths}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                fid = fut.result()
                done += 1
                print(f"OK [{done}/{len(paths)}]: {p.name} -> {fid}")
            except Exception as e:
                print(f"ERRO: {p.name}: {e}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Processa PDFs de uma pasta com upload/extract/caption em paralelo")
    ap.add_argument("folder", help="Pasta com PDFs")
    ap.add_argument("--workers", type=int, default=4, help="Número de workers")
    args = ap.parse_args()
    raise SystemExit(main(args.folder, args.workers))

