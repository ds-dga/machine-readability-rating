from os import getenv
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


def is_content_size_ok(url):
    max_filesize = getenv("MAX_FILESIZE_BYTES", 30*1024*1024)
    try:
        resp = sess.head(url)
        resp_in_bytes = resp.headers['content-length']
        is_ok = resp_in_bytes < max_filesize
        if not is_ok:
            print(f'[URL] {url}')
            print(f'       is bigger than we can handle: {int(resp_in_bytes/(1024*1024))} MB ({int(max_filesize/(1024*1024))} MB limit)')
        return is_ok
    except:
        return False


def fetch_file(url, file_format):
    if not is_content_size_ok(url):
        return 590, "", file_format

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
