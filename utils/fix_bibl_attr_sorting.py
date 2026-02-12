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

bibllist_bio_path = BASE_DIR.parent / "reference" / "bibllist_bio.xml"
bibllist_bio_path = bibllist_bio_path.resolve()
bibllist_bio_short_path = bibllist_bio_path.relative_to(TOP_DIR)


logger = setup_logger(__name__, logfile=Path(f"{SCRIPT_NAME}.log"))


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


def fix_in_bibllist_bio_sort_attr_in_relations():
    bib_tree = etree.parse(bibllist_bio_path)
    bib_root = bib_tree.getroot()

    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    xpath = f'.//tei:relation[@source and @type]'


    rel_it_nodes = bib_root.xpath(xpath, namespaces=ns)
    logger.info(f"======= CASE_1")

    if rel_it_nodes:
        for _rel in rel_it_nodes:
            sort_attributes(_rel)
    else:
        logger.info(f"      NO relatedItem")

    # logger.info(f">>>> source_list errors: {sl_count}, slovo_tolstogo errors: {slovo_count}, biblist_bio errors: {bio_count}")
    bib_tree.write(bibllist_bio_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return


def main():
    start = time.perf_counter()

    fix_in_bibllist_bio_sort_attr_in_relations()

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
