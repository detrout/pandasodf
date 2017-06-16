from datetime import datetime, timedelta
from unittest import TestCase

from pandas import Timestamp, Timedelta
import pandasodf


class TestODF(TestCase):
    def test_read_types(self):
        """Make sure we read ODF data types correctly
        """
        book = pandasodf.ODFReader('datatypes.ods')
        self.assertEquals(len(book.sheet_names), 1)
        self.assertEquals(book.sheet_names, ['Sheet1'])
        sheet = book.parse('Sheet1', header=None)

        self.assertEqual(sheet[0][0], 1.0)
        self.assertEqual(sheet[0][1], 1.25)
        self.assertEqual(sheet[0][2], 'a')
        self.assertEqual(sheet[0][3], Timestamp(2003, 1, 2))
        self.assertEqual(sheet[0][4], False)
        self.assertEqual(sheet[0][5], 0.35)
        self.assertEqual(sheet[0][6], Timedelta(hours=3, minutes=45))
        self.assertEqual(sheet[1][6], Timedelta(hours=17, minutes=53))
        self.assertEqual(sheet[2][6], Timedelta(hours=14, minutes=8))

        # though what should the value of a hyperlink be?
        self.assertEqual(sheet[0][7], 'UBERON:0002101')

    def test_read_lower_diagonal(self):
        """TextParser failed when given an irregular list of lists

        Make sure we can parse:
        1
        2 3
        4 5 6
        7 8 9 10
        """
        book = pandasodf.ODFReader('lowerdiagonal.ods')
        sheet = book.parse('Sheet1', index_col=None, header=None)

        self.assertEqual(sheet.shape, (4,4))

    def test_read_headers(self):
        """Do we read headers correctly?
        """
        book = pandasodf.ODFReader('headers.ods')
        self.assertEquals(len(book.sheet_names), 1)
        self.assertEquals(book.sheet_names, ['Sheet1'])
        sheet = book.parse('Sheet1', index_col=0)

        self.assertEqual(list(sheet.columns), ['Column 1', 'Column 2', None, 'Column 4'])
        self.assertEqual(list(sheet.index), ['Row 1', 'Row 2'])
        self.assertEqual(sheet['Column 1'][0], 1.0)
        self.assertEqual(sheet['Column 1'][1], 2.0)
        self.assertEqual(sheet['Column 2'][0], 3.0)
        self.assertEqual(sheet['Column 2'][1], 4.0)
        self.assertEqual(sheet['Column 4'][0], 7.0)
        self.assertEqual(sheet['Column 4'][1], 8.0)

    def test_read_writer_table(self):
        """ODF reuses the same table tags in Writer and Presentation files

        Test reading a table out of a text document
        """
        doc = pandasodf.ODFReader('writertable.odt')
        table = doc.parse('Table1', index_col=0)

        self.assertEqual(table.shape, (3,3))
        self.assertEqual(table['Column 1'][0], 1.0)
        self.assertEqual(table['Column 1'][1], 2.0)
        self.assertEqual(table['Column 1'][2], 3.0)
        self.assertEqual(table['Column 3'][0], 7.0)
        self.assertEqual(table['Column 3'][1], 8.0)
        self.assertEqual(table['Column 3'][2], 9.0)

        # FIXME: What should the column heading for an empty column be?
        #self.assertEqual(table[''][0], '')
        
    def test_parse_isoduration(self):
        #pandasodf.parse.isoduration('P1347Y')
        self.assertEqual(
            pandasodf.parse_isoduration('-P120D'),
            timedelta(days=-120))

        self.assertEqual(
            pandasodf.parse_isoduration('P0Y0M3D'),
            timedelta(days=3))

        self.assertEqual(
            pandasodf.parse_isoduration('PT1H30M55S'),
            timedelta(hours=1, minutes=30, seconds=55))

