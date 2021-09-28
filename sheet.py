from text import is_this_utf8
from sheet_csv import (
    has_good_header as csv_has_good_header,
    is_shape_consistency as csv_shape_consistency,
)
from sheet_excel import (
    has_good_header as excel_has_good_header,
    is_shape_consistency as excel_shape_consistency,
    has_merged_cells as excel_merged_cells,
)


"""

* check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
* data consistency

"""


def validate_csv(fpath):
    note = ""
    good = 100
    is_utf8, encoding_guess = is_this_utf8(fpath)
    if not is_utf8:
        good -= 10
    encoding = "utf-8" if is_utf8 else "iso-8859-11"
    _check, msg = csv_has_good_header(fpath, encoding=encoding)
    if not _check:
        good -= 20
        note += f" / bad header: {msg}"
    _shape, msg = csv_shape_consistency(fpath, encoding=encoding)
    if not _shape:
        good -= 15
        note += f" / inconsistency: {msg}"
    return good, encoding_guess, note


def validate_excel(fpath):
    note = ""
    good = 100
    _check, msg = excel_has_good_header(fpath)
    if not _check:
        good -= 20
        note += f" / bad header: {msg}"
    _shape, msg = excel_shape_consistency(fpath)
    if not _shape:
        good -= 15
        note += f" / inconsistency: {msg}"
    _has_merged, msg = excel_merged_cells(fpath)
    if _has_merged:
        good -= 5
        note += f" / merged cells: {msg}"
    # Microsoft always use utf-8 with BOM
    return good, "utf-8 with BOM", note
