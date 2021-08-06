import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("command", help="The command to run this program, e.g. check")
parser.add_argument("path", type=str, help="File or directory path to work on")


def handle_file(fpath):
    print(f"File: {fpath}")


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
        handle_dir(path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
