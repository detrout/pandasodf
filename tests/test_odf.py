from datetime import datetime, timedelta
from unittest import TestCase
import pandas
from pandas import Timestamp, Timedelta
import numpy
from pkg_resources import resource_filename
import pandasodf
import pandasodf.odfreader

class TestODF(TestCase):
    def test_read_types(self):
        """Make sure we read ODF data types correctly
        """
        filename = resource_filename(__name__, 'datatypes.ods')
        book = pandasodf.ODFReader(filename)
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
        filename = resource_filename(__name__, 'lowerdiagonal.ods')
        book = pandasodf.ODFReader(filename)
        sheet = book.parse('Sheet1', index_col=None, header=None)

        self.assertEqual(sheet.shape, (4,4))

    def test_read_headers(self):
        """Do we read headers correctly?
        """
        filename = resource_filename(__name__, 'headers.ods')
        book = pandasodf.ODFReader(filename)
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
        filename = resource_filename(__name__, 'writertable.odt')
        doc = pandasodf.ODFReader(filename)
        table = doc.parse('Table1', index_col=0)

        self.assertEqual(table.shape, (3,3))
        self.assertEqual(table['Column 1'][0], 1.0)
        self.assertEqual(table['Column 1'][1], 2.0)
        self.assertEqual(table['Column 1'][2], 3.0)
        self.assertEqual(table['Column 3'][0], 7.0)
        self.assertEqual(table['Column 3'][1], 8.0)
        self.assertEqual(table['Column 3'][2], 9.0)

        # make sure pandas gives a name to the unnamed column
        self.assertTrue(pandas.isnull(table['Unnamed: 2'][0]))

    def test_parse_isoduration(self):
        # FIXME: Implement parsing years
        # pandasodf.parse.isoduration('P1347Y')
        self.assertEqual(
            pandasodf.odfreader.parse_isoduration('-P120D'),
            timedelta(days=-120))

        self.assertEqual(
            pandasodf.odfreader.parse_isoduration('P0Y0M3D'),
            timedelta(days=3))

        self.assertEqual(
            pandasodf.odfreader.parse_isoduration('PT1H30M55S'),
            timedelta(hours=1, minutes=30, seconds=55))

    def test_runlengthencoding(self):
        """Calc will use repeat when adjacent columns have the same value.
        """
        filename = resource_filename(__name__, 'runlengthencoding.ods')
        book = pandasodf.ODFReader(filename)
        self.assertEquals(book.sheet_names, ['Sheet1'])
        sheet = book.parse('Sheet1', header=None)
        self.assertEqual(sheet.shape, (5, 3))
        # check by column, not by row.
        self.assertEqual(list(sheet[0]), [1.0, 1.0, 2.0, 2.0, 2.0])
        self.assertEqual(list(sheet[1]), [1.0, 2.0, 2.0, 2.0, 2.0])
        self.assertEqual(list(sheet[2]), [1.0, 2.0, 2.0, 2.0, 2.0])

