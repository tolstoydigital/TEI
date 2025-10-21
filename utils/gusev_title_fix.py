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

    formatter = logging.Formatter('%(levelname)s: %(message)s')  # Без даты

    # Вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Если указан файл — пишем ещё и туда
    if logfile:
        file_handler = logging.FileHandler(logfile, encoding='utf-8')
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

logger = setup_logger(__name__, logfile=Path("mylog_gusev.log"))

def iter_xml_files(root_dir):
    root_dir = Path(root_dir)
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".xml"):
                yield Path(dirpath) / filename


def fix_title(xml_path: Path, save_to: Optional[Path] = None) -> Optional[str]:
    short_path = xml_path.relative_to(TOP_DIR)

    tree = etree.parse(xml_path)
    root = tree.getroot()

    ns = root.nsmap.get(None)  # default namespace if present
    nsmap = {"tei": ns} if ns else {}

    num = ''
    for _num in root.findall(
            ".//tei:biblScope[@unit='page']" if ns else ".//biblScope[@unit='page']",
            namespaces=nsmap,
    ):
        if _num.text:
            num = _num.text
            num = num.strip()
            num = num.replace(SD, LD)
            _num.text = num
            logger.info(f"--- {short_path} {_num.getroottree().getroot().tag}")
            logger.info(f"<<< {_num.text}")
            logger.info(f">>> {num}")
            break

    assert num != ''

    for title_el in root.findall(
        ".//tei:title[@type='bibl']" if ns else ".//title[@type='bibl']",
        namespaces=nsmap,
    ):
        old_title_text = title_el.text.strip()

        new_title = re.sub(pattern, LD, old_title_text)

        logger.info(f"************** {short_path}")
        logger.info(f"<<< {old_title_text}")
        logger.info(f">>> {new_title}")

        title_el.text = new_title

        # сохраняем изменения в файл
        output_path = save_to or xml_path
        tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

        new_title_for_bio = f"{new_title} {BIO_C} {num}."

        return new_title_for_bio

    return None


def fix_in_bibllist_bio(filename: Path, new_title: Optional[str]):

    if not new_title or not filename:
        return

    xml_id = filename.stem
    bib_tree = etree.parse(bibllist_bio_path)
    bib_root = bib_tree.getroot()

    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }
    xpath = f".//tei:relatedItem[tei:ref[@xml:id=\"{xml_id}\"]]/tei:title[@type='bibl']"
    titles = bib_root.xpath(xpath, namespaces=ns)
    for t in titles:
        logger.info(f"====================================== {xml_id}")
        logger.info(f"BIBLIO <<< {t.text}")
        logger.info(f"BIBLIO >>> {new_title}")
        t.text = new_title
        bib_tree.write(bibllist_bio_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
        return

def main():
    start = time.perf_counter()

    gusev_path = BASE_DIR.parent / "tolstoy-bio" / "tolstoy_bio" / "gusev" / "data" / "tei"
    gusev_path = gusev_path.resolve()

    gusev_front_path = BASE_DIR.parent / "tolstoy_bio_front" / "tolstoy_bio" / "gusev" / "data" / "tei"
    gusev_front_path = gusev_front_path.resolve()

    for i, xml_file in enumerate(iter_xml_files(gusev_path)):
        new_title = fix_title(xml_file)
        fix_in_bibllist_bio(xml_file, new_title)
    logger.info(f"Processed {i} files in {gusev_path}")

    for i, xml_file in enumerate(iter_xml_files(gusev_front_path)):
        _ = fix_title(xml_file)
    logger.info(f"Processed {i} files in {gusev_front_path}")

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
