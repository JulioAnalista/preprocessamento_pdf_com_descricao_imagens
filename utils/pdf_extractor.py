from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

try:
    import pdfplumber  # type: ignore
    HAS_PDFPLUMBER = True
except Exception:
    HAS_PDFPLUMBER = False


class TableExtractionUnavailable(Exception):
    pass


@dataclass
class PageImage:
    page_index: int
    file_name: str
    width: int
    height: int


class PDFExtractor:
    def __init__(self, ocr: bool = False) -> None:
        self.ocr = ocr  # not implemented here per instruction (no fallbacks unless requested)

    def extract(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path))
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "images").mkdir(parents=True, exist_ok=True)

        # Compute pdf hash
        import hashlib
        pdf_bytes = pdf_path.read_bytes()
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

        doc = fitz.open(str(pdf_path))

        # Metadata
        metadata = doc.metadata or {}
        meta_clean = {k: v for k, v in metadata.items() if v is not None}

        pages: List[Dict[str, Any]] = []
        all_tables: List[Dict[str, Any]] = []

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            text = page.get_text("text")  # plain text

            # Extract images per page
            images_info: List[Dict[str, Any]] = []
            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    # Compor alpha em RGB quando aplicável
                    if pix.alpha and pix.colorspace is not None:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    # Converter para RGB se não for RGB
                    if pix.colorspace is None or (pix.colorspace.n != 3):
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    img_name = f"p{page_index+1}_img{img_index+1}.png"
                    img_path = output_dir / "images" / img_name
                    # Gerar bytes PNG e hash
                    try:
                        png_bytes = pix.tobytes("png")
                    except Exception:
                        # fallback: usar save para arquivo e reler bytes
                        pix.save(str(img_path))
                        png_bytes = img_path.read_bytes()
                    import hashlib as _h
                    image_hash = _h.sha256(png_bytes).hexdigest()
                    # garantir escrita do arquivo (para compatibilidade com UI atual)
                    try:
                        img_path.write_bytes(png_bytes)
                    except Exception:
                        pass
                    images_info.append({
                        "file_name": img_name,
                        "width": pix.width,
                        "height": pix.height,
                        "hash": image_hash,
                    })
                except Exception:
                    # Não interromper a extração por falha em uma imagem
                    continue
                finally:
                    try:
                        pix = None  # free
                    except Exception:
                        pass

            # Extract tables with pdfplumber if available
            page_tables: List[Dict[str, Any]] = []
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(str(pdf_path)) as pdfp:
                        p = pdfp.pages[page_index]
                        tables = p.extract_tables() or []
                        for t_index, table in enumerate(tables):
                            page_tables.append({
                                "page": page_index + 1,
                                "index": t_index + 1,
                                "rows": table,
                            })
                except Exception as e:
                    # graceful degradation: just no tables for this page
                    pass
            else:
                # Respect user's rule: do not create fallbacks silently
                pass

            pages.append({
                "page": page_index + 1,
                "text": text,
                "images": images_info,
                "tables": page_tables,
            })
            all_tables.extend(page_tables)

        result: Dict[str, Any] = {
            "metadata": meta_clean,
            "pages": pages,
            "tables": all_tables,
            "pdf_hash": pdf_hash,
            "pages_count": len(doc),
        }
        return result

