from os import stat
import json
from requests import Session
from tempfile import NamedTemporaryFile
from nicely_format import detect_filetype

sess = Session()


def fetch_api(url):
    resp = sess.get(url)
    if resp.status_code != 200:
        return []
    body = json.loads(resp.text)
    return body


def fetch_file(url, file_format):
    try:
        resp = sess.get(url, timeout=10)
    except:
        return 599, "", file_format

    status_code = resp.status_code
    if status_code != 200:
        return status_code, "", file_format

    _suffix = None
    # somehow openpyxl wants .xlsx, as a result we need to rename that
    # because NamedTemporaryFile does not have extension by default
    if file_format.lower() in ["xls", "xlsx"]:
        us = url.split('.')
        if us[-1].lower() == 'xlsx':
            _suffix = '.xlsx'
        else:
            _suffix = f".{file_format.lower()}"

    f = NamedTemporaryFile("wb", delete=False, suffix=_suffix)
    for chunk in resp.iter_content(chunk_size=1024):
        if chunk:  # filter out keep-alive new chunks
            f.write(chunk)
    # f.write(resp.text)
    fp = f.name
    f.close()

    ft = detect_filetype(fp)
    if ft == "unknown":
        ft = file_format
    return 200, fp, ft
