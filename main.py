import argparse
from openpyxl.utils.exceptions import InvalidFileException
from db import Database
from grading import calculate_grade
from offsite import fetch_file
from sheet import validate_csv, validate_excel
from text import is_this_utf8
from nicely_format import (
    detect_filetype,
    validate_json,
    validate_toml,
    validate_xml,
    validate_yaml,
)
import os

parser = argparse.ArgumentParser()
parser.add_argument("command", help="The command to run this program, e.g. check")
parser.add_argument("--path", type=str, help="File or directory path to work on")

BEST_FORMATS = ["json", "toml", "yml", "yaml", "xml", "html"]


def validate_this(fpath, format):
    validator = {
        "json": validate_json,
        "html": validate_xml,
        "xml": validate_xml,
        "yaml": validate_yaml,
        "yml": validate_yaml,
        "toml": validate_toml,
        "xlsx": validate_excel,
        "xls": validate_excel,  ## TODO: fix this
        "csv": validate_csv,
        "tsv": validate_csv,
    }
    format = format.lower()
    if format not in validator.keys():
        return 0, None, "unsupported filetype"

    good = False
    is_utf8, what = None, None
    note = ""
    if format in BEST_FORMATS:
        is_utf8 = is_this_utf8(fpath)
        good = validator[format](fpath)
        good = 100 if good else 0
    else:
        try:
            good, what, note = validator[format](fpath)
        except InvalidFileException:
            return 0, None, "unsupported xls"

    encoding = "unknown"
    if is_utf8:
        encoding = "utf-8"
    elif what is not None:
        encoding = what

    return good, encoding, note


def handle_file(fpath, **kwargs):
    expected = kwargs.get("filetype", None)
    fType = detect_filetype(fpath)
    good, encoding, note = validate_this(fpath, fType)
    print(
        f"""========== {fpath} ==========\n"""
        f"""1. filetype:            {expected or fType}\n"""
        f"""2. encoding:            {encoding}\n"""
        f"""3. Machine readable:    {good if good else '0'} % {note}"""
    )


def handle_dir(fpath):
    IGNORE_FILES = [".gitignore", ".DS_Store"]
    for root, _, fs in os.walk(fpath):
        for f in fs:
            fp = os.path.join(root, f)
            if f in IGNORE_FILES:
                continue
            handle_file(fp)


def handle_url(link, file_format):
    """This is for checking off-site CKAN which need to download the file to
    investigate if it's machine readable or not.
    """
    status_code, fp, format = fetch_file(link, file_format)
    if status_code == 200:
        good, encoding, note = validate_this(fp, format)
        if os.path.isfile(fp):
            os.remove(fp)
        return good, encoding, note

    # print(f"""========== {link} ==========\n** ERR: """, status_code)
    return 0, None, 404


def handle_ckan_db():
    CKAN_URL = os.getenv("CKAN_URL", "http://localhost:5000")
    db = Database()
    cursor = db.get_cursor()
    q = """SELECT format, grade, package_id, id, format, url
    FROM resource
    WHERE format in ('CSV','JSON','XLS','XLSX','XML')
    """
    cursor.execute(q)
    fields = ["format", "grade", "package_id", "id", "format", "url"]
    for row in cursor.fetchall():
        one = dict(zip(fields, row))
        # http://localhost:5000/dataset/b4dd196a-3760-4314-aa27-6ccb763cb8c3/resource/fb48a9ad-01ac-4e3e-a2a7-fe938fb8810d/download/accident2019.xlsx
        fname = one["url"]
        # fname = f'target_file.{one["format"].lower()}'
        one[
            "uri"
        ] = f'{CKAN_URL}/dataset/{one["package_id"]}/resource/{one["id"]}/download/{fname}'
        points, encoding, note = handle_url(one["uri"], one["format"])

        grade = calculate_grade(points)
        if grade != one["grade"]:
            db.resource_grade_update(one["id"], grade)

        grade_delta = f"{grade} -- same old"
        if one["grade"] != grade:
            grade_delta = f"{one['grade']} --> {grade}"

        print(
            f"""========== {fname} ==========\n"""
            f"""1. grade:               {grade_delta}\n"""
            f"""2. filetype:            {one['format']}\n"""
            f"""3. encoding:            {encoding}\n"""
            f"""4. Machine readable:    {points if points else '0'} % {note}"""
        )


def main():
    args = parser.parse_args()
    # print(args)
    if args.command == "check":
        path = args.path
        if not path:
            print(f"Error: path is missing")
            parser.print_help()
            return
        # whether it's file or directory
        if not os.path.exists(path):
            print(f"Error: {path} does not exist")
            return
        if os.path.isdir(path):
            handle_dir(path)
        else:
            handle_file(path)
    elif args.command == "ckan":
        # this will loop table resource in ckan database and see what's missing grade, then process it
        handle_ckan_db()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
