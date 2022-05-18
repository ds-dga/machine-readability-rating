from sheet_common import has_na_in_number_cols
from text import is_this_utf8
from sheet_csv import (
    has_good_header as csv_has_good_header,
    is_shape_consistency as csv_shape_consistency,
    are_num_cols_consistency as csv_cols_consistency,
)
from sheet_excel import (
    has_good_header as excel_has_good_header,
    is_shape_consistency as excel_shape_consistency,
    has_merged_cells as excel_merged_cells,
    are_num_cols_consistency as excel_cols_consistency,
)
from sheet_xls import (
    has_good_header as xls_has_good_header,
    is_shape_consistency as xls_shape_consistency,
    has_merged_cells as xls_merged_cells,
    are_num_cols_consistency as xls_cols_consistency,
)


"""

* check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
* data consistency

"""


def validate_csv(fpath):
    note = []
    good = 100
    is_utf8, encoding_guess = is_this_utf8(fpath)
    if not is_utf8:
        good -= 10
    encoding = "utf-8" if is_utf8 else "iso-8859-11"
    _check, msg = csv_has_good_header(fpath, encoding=encoding)
    if not _check:
        good -= 20
        note.append(f"bad header: {msg}")
    # consistency includes both shape & each col inspection
    _consistency, msg = csv_shape_consistency(fpath)
    if not _consistency:
        # check again with cols_consistency
        _consistency = csv_cols_consistency(fpath)
    if not _consistency:
        good -= 15
        note.append(f"inconsistency: {msg}")
    return good, encoding_guess, ' / '.join(note)


def validate_excel(fpath):
    note = []
    good = 100
    _check, msg = excel_has_good_header(fpath)
    if not _check:
        good -= 20
        note.append(f"bad header: {msg}")
    # consistency includes both shape & each col inspection
    _consistency, msg = excel_shape_consistency(fpath)
    if not _consistency:
        # check again with cols_consistency
        _consistency = excel_cols_consistency(fpath)
    if not _consistency:
        good -= 15
        note.append(f"inconsistency: {msg}")
    _has_merged, msg = excel_merged_cells(fpath)
    if _has_merged:
        good -= 5
        note.append(f"merged cells: {msg}")
    # Microsoft always use utf-8 with BOM
    return good, "utf-8 with BOM", ' / '.join(note)


def validate_xls(fpath):
    note = []
    good = 100
    _check, msg = xls_has_good_header(fpath)
    if not _check:
        good -= 20
        note.append(f"bad header: {msg}")
    # consistency includes both shape & each col inspection
    _consistency, msg = xls_shape_consistency(fpath)
    if not _consistency:
        # check again with cols_consistency
        _consistency = xls_cols_consistency(fpath)
    if not _consistency:
        good -= 15
        note.append(f"inconsistency: {msg}")
    _has_merged, msg = xls_merged_cells(fpath)
    if _has_merged:
        good -= 5
        note.append(f"merged cells: {msg}")
    # Microsoft always use utf-8 with BOM
    return good, "utf-8 with BOM", ' / '.join(note)
