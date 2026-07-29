from pathlib import Path
import tempfile
import unittest

from app.db import Database
from app.generator import generate_docx, generate_pdf
from app.parser import parse_pdf


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PDF = ROOT / "detalheRelatorioLaudos - 2026-07-28T163315.138.pdf"


class WorkflowTest(unittest.TestCase):
    def test_parse_sample_pdf_and_rural_address_rule(self):
        labels = parse_pdf(SAMPLE_PDF)

        self.assertEqual(len(labels), 45)
        first = labels[0]
        self.assertEqual(first.exam_number, "7233")
        self.assertEqual(first.patient_name, "EDITH FERNANDES DA SILVA")
        self.assertEqual(first.city, "FERVEDOURO")
        self.assertEqual(first.district, "SAMAMBAIA")
        self.assertEqual(first.birth_date, "05/07/1964")
        self.assertEqual(first.exam_date, "26/06/2026")

    def test_database_blocks_duplicate_patient_birth_and_exam_date(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            labels = parse_pdf(SAMPLE_PDF)
            db = Database(Path(temp_dir) / "db.sqlite3")

            first_import = db.insert_labels(labels, "sample.pdf")
            second_import = db.insert_labels(labels, "sample.pdf")

            self.assertEqual(first_import, {"inserted": 45, "duplicated": 0, "parsed": 45})
            self.assertEqual(second_import, {"inserted": 0, "duplicated": 45, "parsed": 45})

    def test_generates_pdf_and_docx(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            labels = parse_pdf(SAMPLE_PDF)
            db = Database(temp_path / "db.sqlite3")
            db.insert_labels(labels, "sample.pdf")
            rows = db.list_labels()[:14]

            pdf = generate_pdf(rows, temp_path / "etiquetas.pdf")
            docx = generate_docx(rows, temp_path / "etiquetas.docx")

            self.assertTrue(pdf.exists())
            self.assertGreater(pdf.stat().st_size, 1000)
            self.assertTrue(docx.exists())
            self.assertGreater(docx.stat().st_size, 10000)


if __name__ == "__main__":
    unittest.main()
