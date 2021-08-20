import pandas as pd
import csv


"""

* check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
* data consistency

"""


def fast_check_header(filename, **kwargs):
    enc = kwargs.get("encoding", "utf-8")
    with open(filename, encoding=enc) as f:
        first = f.read(1)
    return first not in ".-0123456789"


def csv_shape_consistency(fpath, **kwargs):
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

    df = pd.read_csv(fpath, encoding=enc, low_memory=False)
    return reader_shape == list(df.shape), "csv != dataframe"
