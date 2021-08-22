import pandas as pd
import csv
import warnings

warnings.filterwarnings("error")

""" CSV grader
1. file encoding
2. check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
3. data consistency
"""


def has_good_header(fpath, *args, **kwargs):
    """Check if the file has a good header (1-row header)

    Args:
        fpath (string): path to file

    Returns:
        bool:   True as good
        string: what makes this file bad
    """
    enc = kwargs.get("encoding", "utf-8")
    good = fast_check_header(fpath, encoding=enc)
    if not good:
        return False, "header not alpha"

    good = header_checker_2(fpath, encoding=enc)
    if not good:
        return False, "headers might contain data"

    return True, ""


def fast_check_header(filename, **kwargs):
    enc = kwargs.get("encoding", "utf-8")
    with open(filename, encoding=enc) as f:
        first = f.read(1)
    return first not in ".-0123456789"


def header_checker_2(filename, **kwargs):
    enc = kwargs.get("encoding", "utf-8")
    with open(filename, encoding=enc) as f:
        cf = csv.reader(f.read(100))
        headers = next(cf)
        for h in headers:
            if h[0] in ".-0123456789":
                return False
    return True


def is_shape_consistency(fpath, **kwargs):
    """check dimension and especially column consistency

    return when found inconsistensy as fast as possible
        True        consistency
        False       inconsistency
    """
    enc = kwargs.get("encoding", "utf-8")

    dictreader_shape = [0, 0]
    with open(fpath, "rt", encoding=enc) as f:
        cols = set()
        tot = 0
        cf = csv.DictReader(f)
        for r in cf:
            cols.add(len(r))
            tot += 1
            if len(cols) > 1:
                return False, "#col mismatch"

        dictreader_shape = [tot, cols.pop()]

    reader_shape = [0, 0]
    with open(fpath, "rt", encoding=enc) as f:
        cols = set()
        tot = 0
        cf = csv.reader(f)
        # This skips the first row of the CSV file (fair with DictReader)
        next(cf)

        for r in cf:
            cols.add(len(r))
            tot += 1
            if len(cols) > 1:
                return False, "#col mismatch"

        reader_shape = [tot, cols.pop()]

    if dictreader_shape != reader_shape:
        return False, "dict != reader"

    try:
        df = pd.read_csv(fpath, encoding=enc)
    except pd.errors.DtypeWarning:
        return False, "df: mixed types"
    good = reader_shape == list(df.shape)
    return good, "" if good else "csv != dataframe"
