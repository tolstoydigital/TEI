import os
import time
import logging
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

# === Настройка логгера ===
def setup_logger(name: str = None, level=logging.INFO, logfile: Path | None = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if logfile:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


BASE_DIR = Path(__file__).resolve().parent
TOP_DIR = BASE_DIR.parent
bibllist_bio_path = BASE_DIR.parent / "reference" / "bibllist_bio.xml"

LD = "—"
logger = setup_logger(__name__, logfile=Path("mylog_makovitski_bs4.log"))

TITLE_MAP = {
    "Маковицкий Д. П. [Дневник] 1904 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 1: 1904—1905. — 1979 . — С. 93—120.": "Маковицкий Д. П. [Дневник] 1904 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 1: 1904—1905. М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1905 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 1: 1904—1905. — 1979 . — С. 121—482.": "Маковицкий Д. П. [Дневник] 1905 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 1: 1904—1905. М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1906 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 2: 1906—1907. — 1979 . — С. 7—345.": "Маковицкий Д. П. [Дневник] 1906 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 2: 1906—1907. М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1907 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 2: 1906—1907. — 1979 . — С. 346—606.": "Маковицкий Д. П. [Дневник] 1907 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 2: 1906—1907. М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1908 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 3: 1908—1909 (январь — июнь). — 1979 . — С. 7—291.": "Маковицкий Д. П. [Дневник] 1908 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 3: 1908—1909 (январь—июнь). М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1909 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 3: 1908—1909 (январь — июнь). — 1979 . — С. 292—456.": "Маковицкий Д. П. [Дневник] 1909 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 3: 1908—1909 (январь—июнь). М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1909 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 4: 1909 (июль — декабрь) — 1910. — 1979 . — С. 7—146.": "Маковицкий Д. П. [Дневник] 1909 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 4: 1909 (июль—декабрь) — 1910. М.: Наука, 1979. С.",
    "Маковицкий Д. П. [Дневник] 1910 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 4: 1909 (июль — декабрь) — 1910. — 1979 . — С. 147—432.": "Маковицкий Д. П. [Дневник] 1910 // Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. Кн. 4: 1909 (июль—декабрь) — 1910. М.: Наука, 1979. С.",
}



def replace_title(title: str) -> str:
    return TITLE_MAP.get(title.strip(), title.strip())


def iter_xml_files(root_dir: Path):
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(".xml"):
                yield Path(dirpath) / fn


def fix_title(xml_path: Path, save_to: Optional[Path] = None, dry_run: bool = False) -> Optional[str]:
    short_path = xml_path.relative_to(TOP_DIR)

    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "xml")

    titles = soup.find_all("title", {"type": "bibl"})
    if not titles:
        return None

    for title_el in titles:
        if not title_el.string:
            continue

        old_title_text = replace_title(title_el.string)
        nums = []

        for pb in soup.find_all("pb", n=True):
            try:
                nums.append(int(pb.get("n")))
            except (TypeError, ValueError):
                continue
            if pb.has_attr("xml:id"):
                old_val = pb["xml:id"]
                del pb["xml:id"]
                logger.info(f"Removed xml:id='{old_val}' in {short_path}")

        if not nums:
            continue

        _min, _max = min(nums), max(nums)
        new_title = f"{old_title_text} {_min}{LD + str(_max) if _min != _max else ''}."

        logger.info(f"************** {short_path}")
        logger.info(f"<<< {title_el.string}")
        logger.info(f">>> {new_title}")

        title_el.string.replace_with(new_title)

        if not dry_run:
            output_path = save_to or xml_path
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

        return new_title
    return None


def fix_in_bibllist_bio(filename: Path, new_title: Optional[str], dry_run: bool = False):
    if not new_title or not filename:
        return
    xml_id = filename.stem

    with open(bibllist_bio_path, "r", encoding="utf-8") as f:
        bib_soup = BeautifulSoup(f.read(), "xml")

    ref_tag = bib_soup.find("ref", {"xml:id": xml_id})
    if ref_tag:
        title_tag = ref_tag.find_parent("relatedItem").find("title", {"type": "bibl"})
        if title_tag:
            logger.info(f"====================================== {xml_id}")
            logger.info(f"BIBLIO <<< {title_tag.string}")
            logger.info(f"BIBLIO >>> {new_title}")
            title_tag.string.replace_with(new_title)
            if not dry_run:
                with open(bibllist_bio_path, "w", encoding="utf-8") as f:
                    f.write(str(bib_soup))


def main(dry_run: bool = False):
    start = time.perf_counter()

    makovitski_path = (
        BASE_DIR.parent / "tolstoy-bio" / "tolstoy_bio" / "makovitski" / "data" / "xml"
    ).resolve()
    makovitski_front_path = (
        BASE_DIR.parent / "tolstoy_bio_front" / "tolstoy_bio" / "makovitski" / "data" / "xml"
    ).resolve()

    for i, xml_file in enumerate(iter_xml_files(makovitski_path), 1):
        new_title = fix_title(xml_file, dry_run=dry_run)
        fix_in_bibllist_bio(xml_file, new_title, dry_run=dry_run)
    logger.info(f"Processed {i} files in {makovitski_path}")

    for i, xml_file in enumerate(iter_xml_files(makovitski_front_path), 1):
        _ = fix_title(xml_file, dry_run=dry_run)
    logger.info(f"Processed {i} files in {makovitski_front_path}")

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")
    if dry_run:
        logger.info("Dry run: no files were modified.")


if __name__ == "__main__":
    main(dry_run=False)
