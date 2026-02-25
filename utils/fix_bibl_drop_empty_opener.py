import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, Set

from lxml import etree
import logging
from csv import DictWriter
from openpyxl import load_workbook, Workbook
import subprocess


def setup_logger(name: str = None, level=logging.INFO, logfile: Path | None = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter("%(levelname)s: %(message)s")  # Без даты

    # Вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Если указан файл — пишем ещё и туда
    if logfile:
        file_handler = logging.FileHandler(logfile, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Абсолютный путь к текущему файлу
BASE_DIR = Path(__file__).resolve().parent
TOP_DIR = BASE_DIR.parent.parent

SCRIPT_NAME = Path(__file__).stem
logger = setup_logger(__name__, logfile=Path(f"{SCRIPT_NAME}.log"))

bibllist_bio_path = BASE_DIR.parent / "reference" / "bibllist_bio.xml"
bibllist_bio_path = bibllist_bio_path.resolve()
bibllist_bio_short_path = bibllist_bio_path.relative_to(TOP_DIR)





def sort_attributes(element):
    # Получаем пары (имя, значение)
    attrs = sorted(element.attrib.items(), key=lambda x: x[0])

    # Очищаем атрибуты
    element.attrib.clear()

    # Добавляем обратно в нужном порядке
    for name, value in attrs:
        element.set(name, value)


def sort_attributes_alt(element):
    def sort_key(item):
        name, _ = item
        if name.startswith("{"):
            # namespaced
            uri, local = name[1:].split("}")
            return local
        return name

    attrs = sorted(element.attrib.items(), key=sort_key)
    element.attrib.clear()
    for name, value in attrs:
        element.set(name, value)


# xmlstarlet sel -N t="http://www.tei-c.org/ns/1.0"   -t -m './/t:relation[following-sibling::*[1][self::t:opener and not(node())]]'   -c . -n bibllist_bio.xml
# xmlstarlet sel -N t="http://www.tei-c.org/ns/1.0"   -t -m './/t:opener[preceding-sibling::*[1][self::t:relation] and not(node())]'   -c . -n bibllist_bio.xml
def fix_in_bibllist_bio_drop_empty_opener():
    bib_tree = etree.parse(bibllist_bio_path)
    bib_root = bib_tree.getroot()

    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    # пустой opener, который идёт сразу после relation
    xpath = (
        ".//tei:opener["
        "preceding-sibling::*[1][self::tei:relation]"
        " and not(normalize-space())"
        " and not(*)"
        "]"
    )

    opener_nodes = bib_root.xpath(xpath, namespaces=ns)

    logger.info("======= DROP EMPTY OPENERS: %d found", len(opener_nodes))

    removed = 0
    for o in opener_nodes:
        parent = o.getparent()
        if parent is not None:
            parent.remove(o)
            removed += 1

    if removed:
        logger.info("Removed %d empty <opener> nodes", removed)
        bib_tree.write(
            bibllist_bio_path,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
        )
    else:
        logger.info("No empty <opener> nodes to remove")

    return removed


def main():
    start = time.perf_counter()

    fix_in_bibllist_bio_drop_empty_opener()

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
