from os import getenv
import json
from requests import Session
from tempfile import NamedTemporaryFile
from nicely_format import detect_filetype
import subprocess


def get_git_revision_short_hash() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except:
        return "-"


sess = Session()
git_rev = get_git_revision_short_hash()


def fetch_api(url):
    resp = sess.get(url)
    if resp.status_code != 200:
        return []
    body = json.loads(resp.text)
    return body


def is_content_size_ok(url):
    max_filesize = getenv("MAX_FILESIZE_BYTES", 30 * 1024 * 1024)
    if url.find('http://192.168') == 0:
        return False, -1
    try:
        max_filesize = int(max_filesize)
        resp = sess.head(url)
        resp_in_bytes = resp.headers["content-length"]
        resp_in_bytes = int(resp_in_bytes)
        is_ok = resp_in_bytes < max_filesize
        if not is_ok:
            # TODO: we should save this somewhere to process on other node
            print(f"[URL] {url}")
            print(
                f"       is bigger than we can handle: {int(resp_in_bytes/(1024*1024))} MB ({int(max_filesize/(1024*1024))} MB limit)"
            )
        return is_ok, resp_in_bytes
    except:
        return False, -1


def fetch_file(url, file_format):
    if url.find('http://192.168') == 0:
        return 591, "", 'file_format', -1
    size_ok, fsize = is_content_size_ok(url)
    if not size_ok:
        return 590, "", file_format, fsize

    try:
        resp = sess.get(url, timeout=10)
    except:
        return 599, "", file_format, -1

    status_code = resp.status_code
    if status_code != 200:
        return status_code, "", file_format, -1

    _suffix = None
    # somehow openpyxl wants .xlsx, as a result we need to rename that
    # because NamedTemporaryFile does not have extension by default
    if file_format.lower() in ["xls", "xlsx"]:
        us = url.split(".")
        if us[-1].lower() == "xlsx":
            _suffix = ".xlsx"
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
    return 200, fp, ft, fsize


def machine_readable_hook(
    package_id, resource_id, uri, format, grade, points, note="", encoding=""
):
    """machine_readable_hook

    introduce another way of tracking grading and what not since it is pain in
    the butt to monitor what we should focus. This aims to fix that, especially
    590 error (big-ass-filesize)

    curl --header "Content-Type: application/json" \
    --request POST \
    --data '{"package_id":"xyz","resource_id":"xyz","uri":"https://data.go.th/xxx","inspected_by":"curl@10coffee","format":"html","grade":"d","points":42,"note":"unreadable","encoding":"utf-8"}' \
    https://ds.10z.dev/hook/machine-readable
    """
    inspector = f"github.com:ds-dga/machine-readability-rating:{git_rev}"
    body = {
        "package_id": package_id,
        "resource_id": resource_id,
        "uri": uri,
        "inspected_by": inspector,
        "format": format,
        "grade": grade,
        "points": points,
        "note": note,
        "encoding": encoding,
    }
    URL = "https://ds.10z.dev/hook/machine-readable"
    resp = sess.post(URL, json=body)
    if resp.status_code != 200:
        return []
    body = resp.json()
    return body
