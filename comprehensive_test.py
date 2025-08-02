import unittest
import os
import shutil
from converter.document_converter import DocumentConverter
from utils.config_manager import ConfigManager

class TestAllConversions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.config = ConfigManager()
        cls.converter = DocumentConverter(cls.config)
        cls.test_dir = 'test_conversion_temp'
        cls.output_dir = os.path.join(cls.test_dir, 'output')
        os.makedirs(cls.output_dir, exist_ok=True)

        # Create dummy files
        cls.create_dummy_files()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    @classmethod
    def create_dummy_files(cls):
        """Create dummy files for testing."""
        # Word
        cls.word_path = os.path.join(cls.test_dir, 'test.docx')
        # Simple docx creation is complex, so we'll assume a file exists
        # For a real scenario, you'd use python-docx or have a template file
        if not os.path.exists(cls.word_path):
            from docx import Document
            doc = Document()
            doc.add_paragraph('This is a test document for Word to Markdown conversion.')
            doc.save(cls.word_path)

        # Excel
        cls.excel_path = os.path.join(cls.test_dir, 'test.xlsx')
        if not os.path.exists(cls.excel_path):
            import pandas as pd
            df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            df.to_excel(cls.excel_path, index=False)

        # PDF
        cls.pdf_path = os.path.join(cls.test_dir, 'test.pdf')
        if not os.path.exists(cls.pdf_path):
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(40, 10, 'Hello World!')
            pdf.output(cls.pdf_path)

    def test_word_to_markdown(self):
        """Test converting Word to Markdown."""
        output_path = self.converter.convert_file(self.word_path, '.md', self.output_dir)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('This is a test document', content)

    def test_excel_to_markdown(self):
        """Test converting Excel to Markdown."""
        output_path = self.converter.convert_file(self.excel_path, '.md', self.output_dir)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('| col1 | col2 |', content)
            self.assertIn('| 1 | 3 |', content)
            self.assertIn('| 2 | 4 |', content)

    def test_pdf_to_markdown(self):
        """Test converting PDF to Markdown."""
        output_path = self.converter.convert_file(self.pdf_path, '.md', self.output_dir)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Hello World!', content)

if __name__ == '__main__':
    unittest.main()