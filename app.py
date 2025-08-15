from pathlib import Path
import json
import uuid
import io
import os
import shutil
import zipfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slugify import slugify
import fitz

from .utils.pdf_extractor import PDFExtractor, TableExtractionUnavailable
from . import db as pdb

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
EXTRACTED_DIR = BASE_DIR / "extracted"
STATIC_DIR = BASE_DIR / "static"
PUBLIC_DIR = BASE_DIR / "public"

for d in (UPLOADS_DIR, EXTRACTED_DIR, STATIC_DIR, PUBLIC_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PDF Pré-processamento para GraphRAG")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,allow_headers=["*"]
)

# Serve static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h3>Interface não encontrada. Verifique /pdf_preproc/static/</h3>", status_code=200)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF")

    file_id = str(uuid.uuid4())
    ext = ".pdf"
    dest_path = UPLOADS_DIR / f"{file_id}{ext}"

    content = await file.read()
    dest_path.write_bytes(content)

    # sidecar metadata
    sidecar = {
        "file_id": file_id,
        "original_filename": file.filename,
        "stored_path": str(dest_path),
    }
    (UPLOADS_DIR / f"{file_id}.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"file_id": file_id, "filename": file.filename}


@app.get("/api/pdf/{file_id}")
def get_pdf(file_id: str):
    meta_path = UPLOADS_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pdf_path = Path(meta["stored_path"])  # should be a .pdf
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    # for better viewer behavior, prefer inline disposition
    headers = {"Content-Disposition": f"inline; filename=\"{meta.get('original_filename', f'{file_id}.pdf')}\""}
    return FileResponse(str(pdf_path), media_type="application/pdf", headers=headers)


@app.post("/api/extract/{file_id}")
def extract_all(file_id: str):
    meta_path = UPLOADS_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pdf_path = Path(meta["stored_path"])  # should be a .pdf
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    # Criar subpasta sanitizada na mesma pasta de entrada do PDF
    pdf_parent = pdf_path.parent
    sanitized = slugify(Path(meta.get("original_filename", pdf_path.name)).stem)
    out_dir = pdf_parent / sanitized
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)

    # Se já existir extraction.json, usar como cache e evitar retrabalho
    cached_extraction = out_dir / "extraction.json"
    if cached_extraction.exists():
        try:
            result = json.loads(cached_extraction.read_text(encoding="utf-8"))
        except Exception:
            result = None
    else:
        result = None

    if result is None:
        extractor = PDFExtractor()
        result = extractor.extract(pdf_path=pdf_path, output_dir=out_dir)

    # Persist and deduplicate using Postgres for images and tables
    # 1) pdf hash
    try:
        pdb.upsert_pdf(result.get("pdf_hash"), pdf_path.stat().st_size, result.get("pages_count", 0))
        pdb.upsert_pdf_file(file_id, result.get("pdf_hash"), meta.get("original_filename"), meta.get("stored_path"))
    except Exception as e:
        # falha no DB não deve impedir visualização, mas reportaremos no JSON
        result.setdefault("db_status", {})["pdf"] = f"erro: {e}"

    # 2) images: move para storage canônico e registrar
    unique_hashes = set()
    images_dir = out_dir / 'images'
    CAN_IMG = PUBLIC_DIR / 'images'
    CAN_IMG.mkdir(parents=True, exist_ok=True)

    for page in result.get("pages", []):
        for idx, img in enumerate(page.get("images", [])):
            h = img.get("hash")
            if not h:
                continue
            unique_hashes.add(h)
            can_path = CAN_IMG / f"{h}.png"
            # mover/copy se ainda não existe
            try:
                if not can_path.exists():
                    # origem é a pasta local do out_dir
                    src = images_dir / img.get("file_name", "")
                    if src.exists():
                        shutil.copyfile(src, can_path)
                # registrar no DB (idempotente)
                try:
                    size_bytes = can_path.stat().st_size if can_path.exists() else 0
                    pdb.upsert_image(h, img.get("width",0), img.get("height",0), "image/png", size_bytes, str(can_path))
                    pdb.insert_pdf_image_ref(file_id, page.get("page",0), idx+1, h)
                except Exception as e:
                    result.setdefault("db_status", {})[f"image_{h}"] = f"erro: {e}"
            except Exception as e:
                result.setdefault("storage_status", {})[f"image_{h}"] = f"erro: {e}"
            # rewrite URL canônica
            img["url"] = f"/public/images/{h}.png"

    # 3) tables: salvar JSON canônico individual e registrar
    CAN_TBL = PUBLIC_DIR / 'tables'
    CAN_TBL.mkdir(parents=True, exist_ok=True)
    import hashlib as _h
    for page in result.get("pages", []):
        for t_idx, tbl in enumerate(page.get("tables", [])):
            rows = tbl.get("rows") or []
            # serialização canônica
            tbl_json = json.dumps(rows, ensure_ascii=False, separators=(',',':'))
            t_hash = _h.sha256(tbl_json.encode('utf-8')).hexdigest()
            # Se já existir no DB, apenas preenche hash e url, sem reescrever arquivo
            tbl["hash"] = t_hash
            tbl_path = CAN_TBL / f"{t_hash}.json"
            if not tbl_path.exists():
                tbl_path.write_text(tbl_json, encoding='utf-8')
            try:
                pdb.upsert_table(t_hash, len(rows), max((len(r) for r in rows), default=0), str(tbl_path))
                pdb.insert_pdf_table_ref(file_id, page.get("page",0), t_idx+1, t_hash)
            except Exception as e:
                result.setdefault("db_status", {})[f"table_{t_hash}"] = f"erro: {e}"
            tbl["url"] = f"/public/tables/{t_hash}.json"

    # Rewrite image paths to API URLs for backward compatibility already handled above

    # add upload metadata for traceability
    result["upload"] = {
        "file_id": file_id,
        "original_filename": meta.get("original_filename"),
        "stored_path": meta.get("stored_path"),
        "output_dir": str(out_dir),
    }

    # Persistir JSON de extração no mesmo diretório (com upload incluso)
    extraction_json = out_dir / "extraction.json"
    extraction_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Persistir registro de extração
    public_zip_name = f"{sanitized}-{file_id}.zip"
    public_zip_path = PUBLIC_DIR / public_zip_name

    try:
        pdb.insert_extraction(file_id, str(out_dir), str(extraction_json), f"/public/{public_zip_name}")
    except Exception as e:
        result.setdefault("db_status", {})["extraction"] = f"erro: {e}"

    # Gerar .zip público dos artefatos únicos
    with zipfile.ZipFile(public_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
      z.write(extraction_json, arcname=f"{sanitized}/extraction.json")
      # apenas imagens únicas por hash
      for h in sorted(unique_hashes):
          can_path = PUBLIC_DIR / 'images' / f"{h}.png"
          if can_path.exists():
              z.write(can_path, arcname=f"{sanitized}/images/{h}.png")

    result["download"] = {
        "zip_url": f"/public/{public_zip_name}",
        "zip_path": str(public_zip_path),
    }

    return JSONResponse(result)


@app.get("/api/image/{file_id}/{image_name}")
def serve_image(file_id: str, image_name: str):
    # compat: servir imagem gerada por extração local (não canônica)
    meta_path = UPLOADS_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pdf_path = Path(meta["stored_path"]).resolve()
    sanitized = slugify(Path(meta.get("original_filename", pdf_path.name)).stem)
    img_path = pdf_path.parent / sanitized / "images" / image_name

    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    ext = img_path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")
    return FileResponse(str(img_path), media_type=mime)



@app.post("/api/caption/{file_id}")
def caption_images(file_id: str):
    meta_path = UPLOADS_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pdf_path = Path(meta["stored_path"]).resolve()
    sanitized = slugify(Path(meta.get("original_filename", pdf_path.name)).stem)
    extraction_json = pdf_path.parent / sanitized / "extraction.json"
    if not extraction_json.exists():
        raise HTTPException(status_code=400, detail="Extração não encontrada para este arquivo")
    from .image_caption import caption_images_from_extraction
    items = caption_images_from_extraction(extraction_json)
    return JSONResponse({"count": len(items), "items": items})


@app.get("/api/files")
def list_persisted_files(group_by: Optional[str] = Query(default=None, description="Use 'pdf' para agrupar por pdf_hash")):
    from . import db as pdb
    if group_by == 'pdf':
        items = pdb.list_files_grouped_by_pdf()
    else:
        items = pdb.list_files()
    return JSONResponse({"items": items})

@app.get("/api/file/{file_id}")
def load_file_payload(file_id: str):
    from . import db as pdb
    data = pdb.load_extraction_from_db(file_id)
    if not data:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no banco")
    return JSONResponse(data)





# Convenience: run with `uvicorn pdf_preproc.app:app --reload`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pdf_preproc.app:app", host="0.0.0.0", port=8099, reload=True)
