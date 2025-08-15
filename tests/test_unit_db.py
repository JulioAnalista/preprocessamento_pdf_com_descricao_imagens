import unittest
from pdf_preproc import db as pdb

class TestDBHelpers(unittest.TestCase):
    def test_schema_and_upserts(self):
        pdb.ensure_schema()
        # sanity call helpers shouldn't raise
        pdb.get_conn()
        # ensure image exists to satisfy FK
        pdb.upsert_image('0'*64, 0, 0, 'image/png', 0, '/tmp/zero.png')
        # upsert image description minimal
        pdb.upsert_image_description('0'*64, 'test-model', 'desc', {"k":"v"}, 'ocr')
        got = pdb.get_image_description('0'*64)
        self.assertIsNotNone(got)
        self.assertEqual(got['description'], 'desc')
        self.assertEqual(got['ocr_text'], 'ocr')

if __name__ == '__main__':
    unittest.main()

