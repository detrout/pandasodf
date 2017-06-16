from argparse import ArgumentParser
import pandas
from pandas.io.parsers import TextParser
from odf.opendocument import load
from odf.namespaces import TABLENS, OFFICENS
from odf.table import (
    Table,
    TableCell,
    TableRows,
    TableRow,
    TableColumns,
    TableColumn,
)


class ODFReader:
    """Read tables out of ODF files
    """
    def __init__(self, filename=None):
        self.filename = None
        self.document = None
        self.tables = None
        if filename:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        self.document = load(filename)
        self.tables = self.document.getElementsByType(Table)

    @property
    def sheet_names(self):
        """Return table names is the document"""
        return [t.attributes[(TABLENS, 'name')] for t in self.tables]

    def __get_sheet(self, sheetname):
        """Given a sheet name or index, return the root ODF Table node
        """
        if isinstance(sheetname, int):
            return get_table(self.tables[sheetname])
        elif isinstance(sheetname, str):
            i = self.sheet_names.index(sheetname)
            if i != -1:
                return get_table(self.tables[i])
            else:
                raise KeyError(sheetname)

    def parse(self, sheetname=0, header=0, skiprows=None, skip_footer=0,
              names=None, index_col=None, parse_cols=None, parse_dates=False,
              date_parser=None, na_values=None, thousands=None,
              convert_float=True, has_index_names=None,
              converters=None, true_values=None, false_values=None,
              squeeze=False, **kwds):

        data = self.__get_sheet(sheetname)
        parser = TextParser(data, header=header, index_col=index_col,
                            has_index_names=has_index_names,
                            na_values=na_values,
                            thousands=thousands,
                            parse_dates=parse_dates,
                            date_parser=date_parser,
                            true_values=true_values,
                            false_values=false_values,
                            skiprows=skiprows,
                            skipfooter=skip_footer,
                            squeeze=squeeze,
                            **kwds)
        return parser.read()


def get_table(sheet):
    """Parse ODF Table into a list of lists
    """
    table = []
    sheet_rows = sheet.getElementsByType(TableRow)

    empty_rows = 0
    max_row_len = 0
    for i, sheet_row in enumerate(sheet_rows):
        sheet_cells = sheet_row.getElementsByType(TableCell)
        empty_cells = 0
        table_row = []
        for j, sheet_cell in enumerate(sheet_cells):
            value = get_cell_value(sheet_cell)
            column_repeat = get_cell_repeat(sheet_cell)

            if len(sheet_cell.childNodes) == 0:
                empty_cells += column_repeat
            else:
                if empty_cells > 0:
                    table_row.extend([None]*empty_cells)
                    empty_cells = 0
                assert column_repeat == 1
                table_row.append(value)

        if max_row_len < len(table_row):
            max_row_len = len(table_row)

        row_repeat = get_row_repeat(sheet_row)
        if is_empty_row(sheet_row):
            empty_rows += row_repeat
        else:
            if empty_rows > 0:
                table.extend([None]*empty_rows)
                empty_rows = 0
            assert row_repeat == 1, ("%d %d" % (row_repeat, len(sheet_row.childNodes)))
            table.append(table_row)

    # Make our table square
    for row in table:
        if len(row) < max_row_len:
            s = len(row)
            row.extend([None] * (max_row_len - len(row)))

    return table


def is_empty_row(row):
    """Helper function to find empty rows
    """
    if len(row.childNodes) == 1 and len(row.childNodes[0].childNodes) == 0:
        return True
    else:
        return False


def get_row_repeat(row):
    repeat = row.attributes.get((TABLENS, 'number-rows-repeated'))
    if repeat is None:
        return 1
    return int(repeat)


def get_cell_repeat(cell):
    repeat = cell.attributes.get((TABLENS, 'number-columns-repeated'))
    if repeat is None:
        return 1
    return int(repeat)


def get_cell_value(cell):
    cell_type = cell.attributes.get((OFFICENS, 'value-type'))
    if cell_type == 'boolean':
        cell_value = cell.attributes.get((OFFICENS, 'boolean'))
        return bool(cell_value)
    elif cell_type in ('float', 'percentage'):
        cell_value = cell.attributes.get((OFFICENS, 'value'))
        return float(cell_value)
    elif cell_type == 'string':
        # FIXME: how do I actually get the string value?
        return str(cell)
    elif cell_type == 'currency':
        cell_value = cell.attributes.get((OFFICENS, 'value'))
        return float(cell_value)
    elif cell_type == 'date':
        cell_value = cell.attributes.get((OFFICENS, 'date-value'))
        return pandas.Timestamp(cell_value)
    elif cell_type == 'time':
        cell_value = cell.attributes.get((OFFICENS, 'time-value'))
        return(parse_isoduration(cell_value))

    elif cell_type is None:
        return None
    else:
        raise ValueError('Unrecognized type %s', cell_type)


def parse_isoduration(duration):
    """Parse an ISO 8601 style duration

    The format used by OpenDocument is actually defined in xmlschema.
    https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#isoformats

    - optional negative sign indicating a negative duration
    P is used as to indicate the field is a duration
    Y follows the number of years
    M follows the number of months
    D follows the number of days
    T indicates the start of the time duration
    H follows the number of hours
    M follows the number of minutes
    S follows the number of seconds

    P and T are required, the other fields are optional.

    For example P1Y2M3DT12:00:00
    for 1 year, 2 months, 3 days and 12 hours.
    """
    years = 0
    months = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 0
    is_days = True
    is_negative = False
    start = 0

    for i, c in enumerate(duration):
        if c == '-':
            is_negative = True
            start = i + 1
        elif c == 'P':
            start = i + 1
        elif c == 'Y':
            years = int(duration[start:i])
            start = i + 1
        elif c == 'M' and is_days:
            months = int(duration[start:i])
            start = i + 1
        elif c == 'D':
            days = int(duration[start:i])
            start = i + 1
        elif c == 'T':
            # start of time
            start = i + 1
            is_days = False
        elif c == 'H':
            hours = int(duration[start:i])
            start = i + 1
        elif c == 'M' and is_days is False:
            minutes = int(duration[start:i])
            start = i + 1
        elif c == 'S':
            seconds = int(duration[start:i])
            start = i + 1
        elif c.isdigit():
            continue
        else:
            raise ValueError('Unrecognized character %s in timedelta %s' % (c, duration))

    # TODO support years & months
    if years != 0:
        raise ValueError("Year delta not supported")

    if months != 0:
        raise ValueError("Month delta not supported")

    delta = pandas.Timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    if is_negative:
        delta = -delta

    return delta


def get_attributes(element):
    """Yield element attribute key value pairs
    """
    for key in element.attributes:
        value = element.attributes[key]
        yield (key[1], value)
