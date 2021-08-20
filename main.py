import argparse
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
    if kind is not None and kind.extension != 'zip':
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
    else:
        if fType == "xlsx":
            good = False
        elif fType == "xls":
            good = False
        elif fType in ["csv", "tsv"]:
            is_utf8, what = is_this_utf8(fpath)
            good = False

    encoding = 'unknown'
    if is_utf8:
        encoding = 'utf-8'
    elif what is not None:
        encoding = what

    print(
        f"{'/' if good else 'X'} [{encoding:>15s}] [expected:{expected}] [ftype:{fType}] path: {fpath}"
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
