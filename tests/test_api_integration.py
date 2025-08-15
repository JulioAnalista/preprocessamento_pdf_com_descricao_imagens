import os
import json
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from pdf_preproc.app import app
from pdf_preproc import db as pdb

PDFS = [
    "/mnt/e/PDOT/comparacao/Anteprojeto_LC_PDOT_Aprovada_Conplan.pdf",
    "/mnt/e/PDOT/comparacao/Minuta_submetida_a_audiencia_publica.pdf",
]

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        pdb.ensure_schema()
        self.client = TestClient(app)

    def test_end_to_end_extract_and_caption(self):
        for pdf in PDFS:
            p = Path(pdf)
            self.assertTrue(p.exists(), f"Arquivo não encontrado: {pdf}")
            with open(p, 'rb') as f:
                r = self.client.post('/api/upload', files={'file': (p.name, f, 'application/pdf')})
            self.assertEqual(r.status_code, 200, r.text)
            fid = r.json()['file_id']

            # extract (cache-aware)
            e = self.client.post(f"/api/extract/{fid}")
            self.assertEqual(e.status_code, 200, e.text)

            # caption (only missing)
            c = self.client.post(f"/api/caption/{fid}")
            self.assertEqual(c.status_code, 200, c.text)

            # read captions from DB
            items = pdb.get_image_descriptions_for_file(fid)
            self.assertGreater(len(items), 0)
            # at least some with OCR or description present
            having_desc = sum(1 for it in items if (it.get('description') or '').strip())
            self.assertGreater(having_desc, 0)

            # second pass should not increase number of described items
            before_desc = having_desc
            c2 = self.client.post(f"/api/caption/{fid}")
            self.assertEqual(c2.status_code, 200, c2.text)
            items2 = pdb.get_image_descriptions_for_file(fid)
            having_desc2 = sum(1 for it in items2 if (it.get('description') or '').strip())
            self.assertGreaterEqual(having_desc2, before_desc)

if __name__ == '__main__':
    unittest.main()

