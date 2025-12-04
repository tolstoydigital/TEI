import os
import re
import time
from pathlib import Path
from typing import Optional

from lxml import etree
import logging


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
TOP_DIR = BASE_DIR.parent

bibllist_bio_path = BASE_DIR.parent / "reference" / "bibllist_bio.xml"
bibllist_bio_path = bibllist_bio_path.resolve()

SD = "-"
LD = "—"
BIO_C = "С."
pattern = r"(?<=\b\d{4})\s*[-–—]\s*(?=\d{4}\b)"
pages_pattern = re.compile(r"С\.\s*(\d+)(?:[—\-](\d+))?\.")

TITLE_MAP = {}

logger = setup_logger(__name__, logfile=Path("mylog_tolstaya_journals.log"))

def replace_title(title: str) -> str:
    return TITLE_MAP.get(title, title)

def iter_xml_files(root_dir):
    root_dir = Path(root_dir)
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".xml"):
                yield Path(dirpath) / filename


def ensure_bibl_scope(tree, new_text: str, save_to: Optional[Path] = None):

    root = tree.getroot()

    # Определяем namespace TEI
    nsmap = root.nsmap
    # Обычно TEI namespace имеет ключ None
    tei_ns = nsmap.get(None, "")

    def q(name):
        """Помогает формировать XPath с namespace."""
        return f"{{{tei_ns}}}{name}" if tei_ns else name

    # Гарантируем наличие всех родительских узлов
    def get_or_create(parent, tag):
        el = parent.find(q(tag))
        if el is None:
            el = etree.SubElement(parent, q(tag))
        return el

    # teiHeader
    teiHeader = root.find(q("teiHeader"))
    if teiHeader is None:
        teiHeader = etree.SubElement(root, q("teiHeader"))

    fileDesc = get_or_create(teiHeader, "fileDesc")
    sourceDesc = get_or_create(fileDesc, "sourceDesc")
    biblStruct = get_or_create(sourceDesc, "biblStruct")
    analytic = get_or_create(biblStruct, "analytic")

    # Ищем biblScope unit="page"
    biblScope = analytic.find(f'{q("biblScope")}[@unit="page"]')

    if biblScope is None:
        biblScope = etree.SubElement(analytic, q("biblScope"))
        biblScope.set("unit", "page")

    # Обновляем текст
    biblScope.text = new_text

    # Сохраняем
    tree.write(save_to, pretty_print=True, encoding="utf-8", xml_declaration=True)

    print(f"[OK] Updated <biblScope unit='page'> in {save_to}")


def get_new_pages(match_tuple: tuple) -> Optional[str]:
    cleaned = [x for x in match_tuple if x]
    if len(cleaned) == 0:
        return None

    if len(cleaned) == 1:
        return cleaned[0]

    return f"{cleaned[0]}{LD}{cleaned[1]}"


def fix_bibl_scope(xml_path: Path, save_to: Optional[Path] = None) -> Optional[str]:
    short_path = xml_path.relative_to(TOP_DIR)

    tree = etree.parse(xml_path)
    root = tree.getroot()

    ns = root.nsmap.get(None)
    nsmap = {
        "tei": ns,
        "xml": "http://www.w3.org/XML/1998/namespace"
    } if ns else {"xml": "http://www.w3.org/XML/1998/namespace"}

    for title_el in root.findall(
        ".//tei:title[@type='bibl']" if ns else ".//title[@type='bibl']",
        namespaces=nsmap,
    ):
        if title_el.text is None:
            continue  # защита от пустых тегов

        m = pages_pattern.search(title_el.text)
        if m:
            print(title_el.text, "→", m.groups())
            new_pages = get_new_pages(m.groups())
            logger.info(f"************** {short_path}")
            ensure_bibl_scope(tree, new_text=new_pages, save_to=xml_path)



        # title_el.text = new_title

        # # сохраняем изменения в файл
        # output_path = save_to or xml_path
        # tree.write(
        #     output_path,
        #     encoding="UTF-8",
        #     xml_declaration=True,
        #     pretty_print=True
        # )
        #
        # return new_title

    return None



def main():
    start = time.perf_counter()

    _path = (
        BASE_DIR.parent / "tolstoy-bio" / "tolstoy_bio" / "gusev" / "data" / "tei"
    )
    _path = _path.resolve()

    _front_path = (
            BASE_DIR.parent / "tolstoy_bio_front" / "tolstoy_bio" / "gusev" / "data" / "tei"
    )
    _front_path = _front_path.resolve()

    for i, xml_file in enumerate(iter_xml_files(_path)):
        # fn = xml_file.stem

        _ = fix_bibl_scope(xml_file)
    logger.info(f"Processed {i} files in {_path}")

    for i, xml_file in enumerate(iter_xml_files(_front_path)):
        # fn = xml_file.stem
        _ = fix_bibl_scope(xml_file)
    logger.info(f"Processed {i} files in {_path}")

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
