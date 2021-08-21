import argparse
from sheet import csv_shape_consistency, fast_check_header, has_good_header
from text import is_this_utf8
from nicely_format import validate_json, validate_toml, validate_xml, validate_yaml
import os
import filetype

parser = argparse.ArgumentParser()
parser.add_argument("command", help="The command to run this program, e.g. check")
parser.add_argument("path", type=str, help="File or directory path to work on")


def detect_filetype(fpath):
    # can only detect binary file
    kind = filetype.guess(fpath)
    # print(kind, fpath)
    # xlsx returns as ZIP!
    if kind is not None and kind.extension != "zip":
        return kind.extension
    fs = fpath.split(".")
    if len(fs) > 1:
        return fs[len(fs) - 1]
    return "unknown"


def handle_file(fpath, **kwargs):
    expected = kwargs.get("filetype", None)
    fType = detect_filetype(fpath)
    best_formats = ["json", "toml", "yml", "yaml", "xml", "html"]

    good = False
    is_utf8, what = None, None
    note = ""
    if fType in best_formats:
        is_utf8, what = is_this_utf8(fpath)
        if fType == "json":
            good = validate_json(fpath)
        elif fType in ["html", "xml"]:
            good = validate_xml(fpath)
        elif fType in ["yaml", "yml"]:
            good = validate_yaml(fpath)
        elif fType == "toml":
            good = validate_toml(fpath)
        good = 100 if good else 0
    else:
        if fType == "xlsx":
            good = False
        elif fType == "xls":
            good = False
        elif fType in ["csv", "tsv"]:
            good = 100
            is_utf8, what = is_this_utf8(fpath)
            if not is_utf8:
                good -= 10
            encoding = "utf-8" if is_utf8 else "iso-8859-11"
            _check, msg = has_good_header(fpath, encoding=encoding)
            if not _check:
                good -= 20
                note += f" / bad header: {msg}"
            _shape, msg = csv_shape_consistency(fpath, encoding=encoding)
            if not _shape:
                good -= 15
                note += f" / inconsistency: {msg}"

    encoding = "unknown"
    if is_utf8:
        encoding = "utf-8"
    elif what is not None:
        encoding = what

    print(
        f"""========== {fpath} ==========\n"""
        f"""1. filetype:            {expected or fType}\n"""
        f"""2. encoding:            {encoding}\n"""
        f"""3. Machine readable:    {good} % {note}"""
    )


def handle_dir(fpath):

    for root, _, fs in os.walk(fpath):
        for f in fs:
            fp = os.path.join(root, f)
            handle_file(fp)
        # dir is repetitive
        # for d in ds:
        #     handle_dir(os.path.join(root, d))


def main():
    args = parser.parse_args()
    if args.command == "check":
        path = args.path
        # whether it's file or directory
        if not os.path.exists(path):
            print(f"Error: {path} does not exist")
            return
        if os.path.isdir(path):
            handle_dir(path)
        else:
            handle_file(path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
