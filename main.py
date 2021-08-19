import argparse
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
    if kind is not None:
        return kind
    fs = fpath.split(".")
    if len(fs) > 1:
        return fs[len(fs) - 1]
    return "unknown"


def handle_file(fpath, **kwargs):
    expected = kwargs.get("filetype", None)
    fType = detect_filetype(fpath)
    best_formats = ["json", "toml", "yml", "yaml", "xml", "html"]

    good = False
    if fType in best_formats:
        if fType == "json":
            good = validate_json(fpath)
        elif fType in ["html", "xml"]:
            good = validate_xml(fpath)
        elif fType in ["yaml", "yml"]:
            good = validate_yaml(fpath)
        elif fType == "toml":
            good = validate_toml(fpath)

    print(f"{'/' if good else 'X'} [expected:{expected}] [ftype:{fType}] path: {fpath}")


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
