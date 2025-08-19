import os
import base64
import json
from pathlib import Path
from typing import List, Dict, Tuple

from openai import AzureOpenAI

# Carregar variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv()

import db
from db import upsert_image_description, ensure_schema

AZ_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZ_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZ_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
AZ_CHAT_MODEL = os.getenv('AZURE_OPENAI_CHAT_MODEL', 'gpt-4.1-nano')


def _get_client():
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', AZ_ENDPOINT)
    key = os.getenv('AZURE_OPENAI_API_KEY', AZ_KEY)
    version = os.getenv('AZURE_OPENAI_API_VERSION', AZ_API_VERSION)
    return AzureOpenAI(api_key=key, api_version=version, azure_endpoint=endpoint)

PROMPT_DEV = {
    "role": "developer",
    "content": [{"type": "text", "text": (
        "Você é um assistente de IA que descreve imagens de documentos administrativos com objetividade, em português do Brasil. "
        "Retorne SEMPRE um JSON estrito com os campos: {"
        "\"descricao\": string curta e objetiva; "
        "\"metadados\": {\"tipo_mapa\": string|null, \"regiao\": string|null, \"possui_legenda\": bool, \"itens_legenda\": array de strings, \"escala\": string|null, \"cores_dominantes\": array de strings, \"texto_visivel\": array de strings}"
        "}. Não inclua texto fora do JSON."
    )}]
}


def _parse_response_to_json(text: str) -> Tuple[str, dict]:
    try:
        obj = json.loads(text)
        desc = obj.get('descricao') or ''
        meta = obj.get('metadados') or {}
        return desc, meta
    except Exception:
        return text.strip(), {}


def describe_image_b64(b64_png: str, model: str = AZ_CHAT_MODEL) -> Tuple[str, dict]:
    messages = [
        PROMPT_DEV,
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_png}"}},
                {"type": "text", "text": "Descreva e extraia metadados estruturados conforme instruções."},
            ],
        },
    ]
    client = _get_client()
    resp = client.chat.completions.create(model=model, messages=messages, max_completion_tokens=2048)
    txt = resp.choices[0].message.content or ""
    return _parse_response_to_json(txt)


def run_easyocr(img_path: Path) -> str:
    try:
        import easyocr
        reader = easyocr.Reader(['pt', 'en'], gpu=False)
        result = reader.readtext(str(img_path))
        # Concatenar os textos detectados na ordem
        texts = [seg[1] for seg in result if isinstance(seg, (list, tuple)) and len(seg) >= 2]
        return "\n".join([t.strip() for t in texts if (t or '').strip()])
    except Exception as e:
        return ""


def caption_images_from_extraction(extraction_json_path: Path) -> List[Dict]:
    ensure_schema()
    j = json.loads(extraction_json_path.read_text(encoding='utf-8'))
    results = []
    # Percorrer páginas e imagens únicas por hash e pular as já descritas salvas no DB
    import db as pdb
    seen = set()
    for page in j.get('pages', []):
        for img in page.get('images', []):
            h = img.get('hash')
            if not h or h in seen:
                continue
            seen.add(h)
            # Se já houver no DB, reaproveita
            cached = pdb.get_image_description(h)
            if cached and (cached.get('description') or cached.get('ocr_text')):
                # Atualiza JSON e segue
                img['description'] = cached.get('description')
                img['metadata'] = cached.get('metadata') or {}
                if cached.get('ocr_text'):
                    img['ocr_text'] = cached.get('ocr_text')
                continue
            # Ler a imagem canônica em /public/images/<hash>.png
            can_path = Path(__file__).resolve().parent / 'public' / 'images' / f'{h}.png'
            if not can_path.exists():
                local = Path(j['upload']['output_dir']) / 'images' / img.get('file_name','')
                if local.exists():
                    can_path = local
                else:
                    continue
            b64 = base64.b64encode(can_path.read_bytes()).decode('ascii')
            desc, meta = describe_image_b64(b64)
            ocr_text = run_easyocr(can_path)
            upsert_image_description(h, AZ_CHAT_MODEL, desc, meta, ocr_text)
            results.append({"hash": h, "description": desc, "metadata": meta, "ocr_text": ocr_text})
            # Atualizar no próprio JSON (para consulta rápida)
            img['description'] = desc
            img['metadata'] = meta
            if ocr_text:
                img['ocr_text'] = ocr_text
    # Persistir extraction.json atualizado
    extraction_json_path.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')
    return results

