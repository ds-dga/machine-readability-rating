import pandas as pd
import csv


"""

* check if it has one header row. This is a bit triggy how to find that out.
    - has header or not
    - has one-row header or multiple row
* data consistency

"""


def fast_check_header(filename):
    with open(filename) as f:
        first = f.read(1)
    return first not in ".-0123456789"


def csv_shape_consistency(fpath):
    """check dimension and especially column consistency

    return when found inconsistensy as fast as possible
        True        consistency
        False       inconsistency
    """
    dictreader_shape = [0, 0]
    with open(fpath, "rt") as f:
        cols = set()
        tot = 0
        cf = csv.DictReader(f)
        for r in cf:
            cols.add(len(r))
            tot += 1
            if len(cols) > 1:
                return False

        dictreader_shape = [tot, cols.pop()]

    reader_shape = [0, 0]
    with open(fpath, "rt") as f:
        cols = set()
        tot = 0
        cf = csv.reader(f)
        for r in cf:
            cols.add(len(r))
            tot += 1
            if len(cols) > 1:
                return False

        reader_shape = [tot, cols.pop()]

    if dictreader_shape != reader_shape:
        return False

    df = pd.read_csv(fpath)
    return reader_shape == list(df.shape)
