import os
import argparse
from time import sleep
from openpyxl.utils.exceptions import InvalidFileException
from db import Database
import ckan
from grading import calculate_grade
from offsite import fetch_file
from sheet import validate_csv, validate_excel, validate_xls
from text import is_this_utf8
from nicely_format import (
    detect_filetype,
    validate_json,
    validate_toml,
    validate_xml,
    validate_yaml,
)

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
        "xls": validate_xls,
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
        except Exception as e:
            print(e)
            return 0, None, "something is wrong"

    encoding = "unknown"
    if is_utf8:
        encoding = "utf-8"
    elif what is not None:
        encoding = what

    return good, encoding, note


def handle_file(fpath, **kwargs):
    max_filesize = os.getenv("MAX_FILESIZE_BYTES", 30*1024*1024)
    file_size = os.path.getsize(fpath)
    if file_size > max_filesize:
        print(f'[FILE] {fpath}')
        print(f'       is bigger than we can handle: {int(file_size/(1024*1024))} MB ({int(max_filesize/(1024*1024))} MB limit)')
        return

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

    print(f"""========== {link} ==========\n** ERR: """, status_code, flush=True)
    return 0, None, 404


def handle_ckan_api():
    FORMATS = ("CSV", "JSON", "XLS", "XLSX", "XML")
    packages = ckan.get_package_list()
    for id in packages:
        item = ckan.get_package_detail(id)
        sleep(3)  # so, this crawler doesn't hurt server much
        for res in item["resources"]:
            if res["format"] not in FORMATS:
                print("X", res["format"], res["url"], "\n\n")
                continue
            print("/", res["format"], res["url"])
            ckan.resource_grader(res)


def handle_ckan_db():
    CKAN_URL = os.getenv("CKAN_URL", "http://localhost:5000")
    db = Database()
    cursor = db.get_cursor()
    q = """SELECT format, grade, package_id, id, format, url, url_type
    FROM resource
    WHERE name != 'All resource data'
        AND grade IS null
    ORDER BY package_id
    """
    # AND format in ('CSV','JSON','XLS','XLSX','XML')
    cursor.execute(q)
    fields = ["format", "grade", "package_id", "id", "format", "url", "url_type"]
    skips = [
        "8a956917-436d-4afd-a2d4-59e4dd8e906e",
        "a03f8fb2-327e-4f22-887e-1b60212d4d9c",
        "d11d6cc2-74bf-4f2d-8839-2968c0ea925a",
    ]
    for row in cursor.fetchall():
        one = dict(zip(fields, row))
        if one["id"] in skips:
            # these are huge csv/excel files and will kill the process.
            # TODO: handle those huge files
            continue
        # http://localhost:5000/dataset/b4dd196a-3760-4314-aa27-6ccb763cb8c3/resource/fb48a9ad-01ac-4e3e-a2a7-fe938fb8810d/download/accident2019.xlsx
        fname = one["url"]
        # fname = f'target_file.{one["format"].lower()}'
        one["uri"] = one["url"]
        if one["url_type"] == "upload":
            one[
                "uri"
            ] = f'{CKAN_URL}/dataset/{one["package_id"]}/resource/{one["id"]}/download/{fname}'

        print(one["uri"], one["format"], flush=True)
        points, encoding, note = handle_url(one["uri"], one["format"])
        grade = calculate_grade(points)
        db.resource_grade_update(one["id"], grade)
        curr_grade = one["grade"]
        if grade != curr_grade:
            grade_delta = f"{curr_grade} --> {grade}"
        else:
            grade_delta = f"{grade} -- same old"

        print(
            f"""== {one['id']} ================\n"""
            f"""0. {fname}\n"""
            f"""1. grade:               {grade_delta}\n"""
            f"""2. filetype:            {one['format']}\n"""
            f"""3. encoding:            {encoding}\n"""
            f"""4. Machine readable:    {points if points else '0'} % {note}""",
            flush=True,
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
        if path.index('http') == 0:
            handle_url(path, 'CSV')
            return
        # whether it's file or directory
        if not os.path.exists(path):
            print(f"Error: {path} does not exist")
            return
        if os.path.isdir(path):
            handle_dir(path)
        else:
            handle_file(path)
    elif args.command == "ckan_db":
        # this will loop table resource in ckan database and see what's missing grade, then process it
        handle_ckan_db()
    elif args.command == "ckan":
        handle_ckan_api()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
