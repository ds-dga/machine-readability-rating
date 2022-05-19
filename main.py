import os
import csv
import argparse
from time import sleep
from openpyxl.utils.exceptions import InvalidFileException
import arrow
from db import Database
import ckan
from grading import calculate_grade
from offsite import fetch_file, machine_readable_hook
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
csv_writer = None
CSV_FIELDNAMES = [
    "package_id",
    "resource_id",
    "timestamp",
    "url",
    "filesize",
    "point",
    "grade",
    "grade_prior",
    "error",
]

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

    points = False
    is_utf8, what = None, None
    note = ""
    if format not in BEST_FORMATS:
        try:
            points, what, note = validator[format](fpath)
        except InvalidFileException:
            return 0, None, "unsupported xls"
        except Exception as e:
            print(e)
            return 0, None, f"something is wrong: {e}"
    else:
        is_utf8 = is_this_utf8(fpath)
        points = validator[format](fpath)
        points = 100 if points else 0

    encoding = "unknown"
    if is_utf8:
        encoding = "utf-8"
    elif what is not None:
        encoding = what

    return points, encoding, note


def handle_file(fpath, **kwargs):
    max_filesize = os.getenv("MAX_FILESIZE_BYTES", 30 * 1024 * 1024)
    file_size = os.path.getsize(fpath)
    if file_size > int(max_filesize):
        # TODO: we should save this somewhere to process on other node
        print(f"[FILE] {fpath}")
        print(
            f"       is bigger than we can handle: {int(file_size/(1024*1024))} MB ({int(max_filesize/(1024*1024))} MB limit)"
        )
        return

    expected = kwargs.get("filetype", None)
    fType = detect_filetype(fpath)
    points, encoding, note = validate_this(fpath, fType)
    # print(fType, points, encoding, note)
    grade = calculate_grade(points)
    print(
        f"""========== {fpath} ==========\n"""
        f"""1. filetype:            {expected or fType}\n"""
        f"""2. encoding:            {encoding}\n"""
        f"""3. Machine readable:    {points if points else '0'}\n"""
        f"""4. Grade:               {grade}\n"""
        f"""5. Note:                {note}\n"""
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
    status_code, fp, format, file_size = fetch_file(link, file_format)
    if status_code == 200:
        points, encoding, note = validate_this(fp, format)
        if os.path.isfile(fp):
            os.remove(fp)
        print(
            f""">>>=================\n""",
            f"""  LINK:      {link}\n""",
            f"""  ERR:       {status_code}\n""",
            f"""  format:    {format}\n""",
            f"""  file size: {file_size}\n""",
            f"""  points:    {points}\n""",
            flush=True,
        )
        return points, encoding, note, file_size

    print(
        f""">>>=================\n""",
        f"""  LINK:      {link}\n""",
        f"""  ERR:       {status_code}\n""",
        f"""  format:    {format}\n""",
        f"""  file size: {file_size}\n""",
        flush=True,
    )
    return 0, None, status_code, file_size


def handle_ckan_api():
    FORMATS = ("CSV", "JSON", "XLS", "XLSX", "XML")
    packages = ckan.get_package_list()
    for id in packages:
        item = ckan.get_package_detail(id)
        sleep(3)  # so, this crawler doesn't hurt server much
        for res in item["resources"]:
            if res["format"] not in FORMATS:
                print("X", res["format"], res["url"])
                continue
            print("/", res["format"], res["url"])
            out = ckan.resource_grader(res)
            write_output(*out)


def handle_ckan_db():
    CKAN_URL = os.getenv("CKAN_URL", "http://localhost:5000")
    db = Database()
    cursor = db.get_cursor()
    q = """SELECT format, grade, package_id, id, format, url, url_type
    FROM resource
    WHERE name != 'All resource data'
        AND (grade IS null OR grade = 'f')
    ORDER BY package_id
    """
    # AND format in ('CSV','JSON','XLS','XLSX','XML')
    cursor.execute(q)
    fields = ["format", "grade", "package_id", "id", "format", "url", "url_type"]
    for row in cursor.fetchall():
        one = dict(zip(fields, row))
        # http://localhost:5000/dataset/b4dd196a-3760-4314-aa27-6ccb763cb8c3/resource/fb48a9ad-01ac-4e3e-a2a7-fe938fb8810d/download/accident2019.xlsx
        fname = one["url"]
        # fname = f'target_file.{one["format"].lower()}'
        one["uri"] = one["url"]
        if one["url_type"] == "upload":
            one[
                "uri"
            ] = f'{CKAN_URL}/dataset/{one["package_id"]}/resource/{one["id"]}/download/{fname}'

        print(one["uri"], one["format"], flush=True)
        points, encoding, note, file_size = handle_url(one["uri"], one["format"])
        grade = "f"
        if note == 590:
            print("    >>> FILE is TOO big to handle here", flush=True)

        if note not in (404, 590, 599):
            grade = calculate_grade(points)
        db.resource_grade_update(one["id"], grade)
        curr_grade = one["grade"]
        if grade != curr_grade:
            grade_delta = f"{curr_grade} --> {grade}"
        else:
            grade_delta = f"{grade} -- same old"

        write_output(
            one["package_id"],
            one["id"],
            arrow.get().isoformat(),
            one["uri"],
            file_size,
            points,
            grade,
            curr_grade,
            f"{encoding}|{note}",
        )
        # store some data in opendata_item/stats
        machine_readable_hook(
            one["package_id"],
            one["id"],
            one["uri"],
            one["format"],
            grade,
            points,
            f"{file_size}|{note}",
            encoding,
        )
        print(
            f"""== {one['id']} ================\n"""
            f"""0. {fname}\n"""
            f"""1. grade:               {grade_delta}\n"""
            f"""2. filetype:            {one['format']}\n"""
            f"""3. encoding:            {encoding}\n"""
            f"""4. Machine readable:    {points if points else '0'} % {note}\n"""
            f"""=================>>>""",
            flush=True,
        )


def write_output(
    package_id, resource_id, timestamp, url, filesize, point, grade, grade_prior, error
):
    global csv_writer
    csv_writer.writerow(
        {
            "package_id": package_id,
            "resource_id": resource_id,
            "timestamp": timestamp,
            "url": url,
            "filesize": filesize,
            "point": point,
            "grade": grade,
            "grade_prior": grade_prior,
            "error": error,
        }
    )


def main():
    args = parser.parse_args()
    # print(args)

    fn = f'output-{arrow.get().format("YYYY-MM-DD")}.csv'
    output_exists = os.path.isfile(fn)
    f = open(fn, "at")
    global csv_writer
    csv_writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
    if not output_exists:
        csv_writer.writeheader()

    if args.command == "check":
        path = args.path
        if not path:
            print(f"Error: path is missing")
            parser.print_help()
            return
        if path.find("http") == 0:
            handle_url(path, "CSV")
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

    if f:
        f.close()


if __name__ == "__main__":
    main()
