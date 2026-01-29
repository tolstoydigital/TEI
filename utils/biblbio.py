import logging
from pathlib import Path
from typing import Optional, Dict

from lxml import etree


# Абсолютный путь к текущему файлу
BASE_DIR = Path(__file__).resolve().parent
TOP_DIR = BASE_DIR.parent.parent


def set_biblist_title(
    filename: Path,
    title: str,
    xml_id: str,
    logger: Optional[logging.Logger] = None,
    dry_run: bool = True,
) -> Optional[Dict[str, str]]:

    if xml_id is None:
        logger.info(f"#### no new xml_id for {filename} skipping ####")
        return

    if logger is None:
        logger = logging.getLogger(__name__)

    target_fl = (TOP_DIR / filename).resolve()
    # print(f"target_fl: {target_fl}")

    tree = etree.parse(target_fl)
    root = tree.getroot()

    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }
    xpath_top = f".//tei:relatedItem[tei:ref[@xml:id=\"{xml_id}\"]]"
    xpath_inner = f".//tei:title[@type='bibl']"
    related_items = root.xpath(xpath_top, namespaces=ns)

    changed = False
    if not related_items:
        logger.error(f"#### NO relatedItem with ref {xml_id} in {filename} ####")
        return
    else:
        for rel in related_items:
            titles = rel.xpath(xpath_inner, namespaces=ns)
            if not titles:
                logger.info(f"#### NO title in {filename} try to create ####")
                title_node = etree.SubElement(rel, "title", attrib={"type": "bibl"})
                title_node.text = title
                xml_str = etree.tostring(
                    title_node,
                    pretty_print=True,
                    encoding="unicode",
                )
                logger.info(f"TITLE >>> {xml_str}")
            else:
                for t in titles:
                    logger.info(f"---")
                    if t.text == title:
                        logger.info(f"TITLE was not changed, skipping")
                    else:
                        logger.info(f"TITLE <<< {t.text}")
                        logger.info(f"TITLE >>> {title}")
                        t.text = title
                        changed = True

    if changed and not dry_run:
        tree.write(target_fl, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def set_tei_title_and_page(
    filename: Path,
    title: str,
    page: str,
    logger: Optional[logging.Logger] = None,
    dry_run: bool = True,
) -> Optional[Dict[str, str]]:

    if logger is None:
        logger = logging.getLogger(__name__)

    if filename is None:
        logger.info(f"#### no filename ####")
        return

    target_fl = (TOP_DIR / filename).resolve()
    # print(f"target_fl: {target_fl}")

    tree = etree.parse(target_fl)
    root = tree.getroot()

    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }
    xpath = f".//tei:title[@type='bibl']"
    xpath2 = ".//tei:biblScope[@unit='page']"
    titles = root.xpath(xpath, namespaces=ns)
    changed = False
    if not titles:
        logger.error(f"#### NO TITLE in {filename} ####")

    for t in titles:
        logger.info(f"---")
        if t.text == title:
            logger.info(f"TITLE was not changed, skipping")
        else:
            logger.info(f"TITLE <<< {t.text}")
            logger.info(f"TITLE >>> {title}")
            t.text = title
            changed = True

    pages = root.xpath(xpath2, namespaces=ns)
    if not pages:
        logger.error(f"#### NO PAGE in {filename} ####")
    for p in pages:
        logger.info(f"---")
        if p.text == page:
            logger.info(f"PAGE was not changed, skipping")
        else:
            logger.info(f"PAGE <<< {p.text}")
            logger.info(f"PAGE >>> {page}")
            p.text = page
            changed = True

    if changed and not dry_run:
        tree.write(target_fl, encoding="UTF-8", xml_declaration=True, pretty_print=True)
