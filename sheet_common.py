import numpy as np


def has_na_in_number_cols(df):
    """check columns with float64/int64 data type if there is null/na

    return <bool>, <float>
        <bool>      True  when found null
        <float>     percentage of null values in that column**

    **  found then return: which doesn't mean that represents the whole file,
        but we don't quantify this anyway. If there is any consistent, then
        we judge the file as "inconsistency" as of May 10, 2022
    """
    total = df.count()[0]
    for col in df.dtypes[(df.dtypes == np.float64) | (df.dtypes == np.int64)].keys():
        na = df[col].isna().sum()
        print(f"{col} [{total}] ==> na = {na} / {total}")
        perct = na * 100 / total
        if na > 0:
            return True, perct
    return False, 0
