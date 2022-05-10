from xlrd import open_workbook
import pandas as pd
from itertools import chain

from sheet_common import has_na_in_number_cols

""" XLS, XLSX grader
1. check if it's excel file.
2. check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
3. data consistency
"""


def has_good_header(fpath):
    wb = open_workbook(fpath)
    sheets = wb.sheets()
    for sheet in sheets:
        A1 = sheets[0].col(0)[0]
        if not A1.value:
            return False, "empty A1"
        for col in sheet.row(0):
            if not col or col.value in ".-0123456789":
                return False, "header not alpha"
    return True, ""


def is_shape_consistency(fpath, **kwargs):
    """check dimension and especially column consistency

    return when found inconsistensy as fast as possible
        True        consistency
        False       inconsistency
    """
    wb = open_workbook(fpath)
    shapes = []
    sheets = wb.sheets()
    for sheet in sheets:
        shapes.append([sheet.nrows, sheet.ncols])

    df_shapes = []
    try:
        dfs = pd.read_excel(fpath, sheet_name=None)
        for sheet in dfs.keys():
            df_shapes.append(dfs[sheet].shape)
    except pd.errors.DtypeWarning:
        return False, "df: mixed types"

    good = list(chain(*shapes)) == list(chain(*df_shapes))
    # if not good:
    #     print(shapes, df_shapes)
    #     print(dfs[sheets[len(sheets) - 1]].iloc[0])
    return good, "" if good else "xlrd != dataframe"


def has_merged_cells(fpath, **kwargs):
    """check if there is any merged cell

    return when found inconsistensy as fast as possible
        True        found merged cells & sheet + cound
        False       not found, ''
    """
    wb = open_workbook(fpath, formatting_info=True)
    sheets = wb.sheets()
    for sheet in sheets:
        if not sheet.merged_cells:
            continue

        bd = [f"{i}" for i in sheet.merged_cells]
        return True, f"{sheet.name}/{','.join(bd)}"

    return False, ""


def are_num_cols_consistency(fpath):
    """Basically check if there is NA or null in numbered columns

    return <bool>
        True    all numbered columns are consistency
        False   Not all numbered columns are consistency
    """
    df = pd.read_excel(fpath)
    bad, _ = has_na_in_number_cols(df)
    return not bad
