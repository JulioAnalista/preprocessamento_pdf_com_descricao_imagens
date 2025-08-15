import argparse
from pathlib import Path
from typing import List, Dict, Tuple

from pdf_preproc import db as pdb


def choose_canonical(rows: List[Dict]) -> Dict:
    # Prefer one with extraction.json existing; else earliest created_at
    best = None
    for r in rows:
        # try check extraction path
        ex = r.get('extraction_json_path')
        if ex and Path(ex).exists():
            return r
    # fallback earliest created_at
    best = sorted(rows, key=lambda x: x.get('created_at'))[0]
    return best


def fetch_groups(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pf.file_id, pf.pdf_hash, pf.original_filename, pf.stored_path, pf.created_at,
               COALESCE(e.extraction_json_path, '') as extraction_json_path
        FROM pdf_files pf
        LEFT JOIN extractions e ON e.file_id = pf.file_id
        ORDER BY pf.pdf_hash, pf.created_at
        """
    )
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    groups: Dict[str, List[Dict]] = {}
    for r in rows:
        groups.setdefault(r['pdf_hash'], []).append(r)
    return groups


def merge_refs(conn, from_file_id: str, to_file_id: str) -> Tuple[int, int]:
    cur = conn.cursor()
    # images
    cur.execute(
        """
        INSERT INTO pdf_image_refs(file_id, page, img_index, image_hash)
        SELECT %s as file_id, page, img_index, image_hash
        FROM pdf_image_refs WHERE file_id = %s
        ON CONFLICT DO NOTHING
        """,
        (to_file_id, from_file_id)
    )
    imgs = cur.rowcount if cur.rowcount is not None else 0
    # tables
    cur.execute(
        """
        INSERT INTO pdf_table_refs(file_id, page, table_index, table_hash)
        SELECT %s as file_id, page, table_index, table_hash
        FROM pdf_table_refs WHERE file_id = %s
        ON CONFLICT DO NOTHING
        """,
        (to_file_id, from_file_id)
    )
    tbls = cur.rowcount if cur.rowcount is not None else 0
    return imgs, tbls


def maybe_move_extraction(conn, from_file_id: str, to_file_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT output_dir, extraction_json_path, zip_url FROM extractions WHERE file_id=%s", (to_file_id,))
    if cur.fetchone():
        return False
    cur.execute("SELECT output_dir, extraction_json_path, zip_url FROM extractions WHERE file_id=%s", (from_file_id,))
    row = cur.fetchone()
    if not row:
        return False
    cur.execute(
        """
        INSERT INTO extractions(file_id, output_dir, extraction_json_path, zip_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (file_id) DO UPDATE SET output_dir=EXCLUDED.output_dir, extraction_json_path=EXCLUDED.extraction_json_path, zip_url=EXCLUDED.zip_url
        """,
        (to_file_id, row[0], row[1], row[2])
    )
    return True


def cleanup(apply: bool = False) -> Dict:
    pdb.ensure_schema()
    report = {"duplicates": 0, "kept": 0, "removed": 0, "moved_img_refs": 0, "moved_tbl_refs": 0, "moved_extractions": 0}
    with pdb.get_conn() as conn:
        groups = fetch_groups(conn)
        for pdf_hash, rows in groups.items():
            if len(rows) <= 1:
                continue
            report["duplicates"] += 1
            canon = choose_canonical(rows)
            to_id = canon['file_id']
            report["kept"] += 1
            for r in rows:
                if r['file_id'] == to_id:
                    continue
                from_id = r['file_id']
                # merge refs to canonical
                imgs, tbls = merge_refs(conn, from_id, to_id)
                report["moved_img_refs"] += imgs
                report["moved_tbl_refs"] += tbls
                # move extraction if needed
                if maybe_move_extraction(conn, from_id, to_id):
                    report["moved_extractions"] += 1
                if apply:
                    # delete old refs and file entry (and extraction row)
                    cur = conn.cursor()
                    cur.execute("DELETE FROM pdf_image_refs WHERE file_id=%s", (from_id,))
                    cur.execute("DELETE FROM pdf_table_refs WHERE file_id=%s", (from_id,))
                    cur.execute("DELETE FROM extractions WHERE file_id=%s", (from_id,))
                    cur.execute("DELETE FROM pdf_files WHERE file_id=%s", (from_id,))
                    report["removed"] += 1
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Cleanup duplicate pdf_files by pdf_hash")
    ap.add_argument("--apply", action="store_true", help="Apply changes (otherwise dry-run)")
    args = ap.parse_args()
    rep = cleanup(apply=args.apply)
    mode = 'APPLY' if args.apply else 'DRY-RUN'
    print(f"[{mode}] duplicates={rep['duplicates']} kept={rep['kept']} removed={rep['removed']} moved_img_refs={rep['moved_img_refs']} moved_tbl_refs={rep['moved_tbl_refs']} moved_extractions={rep['moved_extractions']}")

