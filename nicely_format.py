import logging
import json
from json.decoder import JSONDecodeError
import yaml
import toml
from lxml import etree

logging.basicConfig(filename="process.log", level=logging.ERROR)


def validate_json(fpath):
    with open(fpath, "rt") as f:
        try:
            json.loads(f.read())
            return True
        except JSONDecodeError as e:
            logging.error(f"json:{fpath}:{e}:")
            return False


def validate_yaml(fpath):
    with open(fpath, "rt") as f:
        try:
            yaml.load(f.read(), Loader=yaml.Loader)
            return True
        except Exception as e:
            logging.error(f"yaml:{fpath}:{e}:")
            return False


def validate_toml(fpath):
    with open(fpath, "rt") as f:
        try:
            toml.loads(f.read())
            return True
        except Exception as e:
            logging.error(f"toml:{fpath}:{e}:")
            return False


def validate_xml(fpath):
    with open(fpath, "rt") as f:
        try:
            etree.fromstring(f.read(), parser=etree.XMLParser())
            return True
        except Exception as e:
            logging.error(f"xml:{fpath}:{e}:")
            return False
