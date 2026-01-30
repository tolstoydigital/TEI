import time
from pathlib import Path

import logging

from utils import setup_logger, iter_xlsx_rows_as_column_letter_dict
from biblbio import set_biblist_title, set_tei_title_and_page

# Абсолютный путь к текущему файлу
BASE_DIR = Path(__file__).resolve().parent
TOP_DIR = BASE_DIR.parent.parent

bibllist_bio_path = BASE_DIR.parent / "reference" / "bibllist_bio.xml"
bibllist_bio_path = bibllist_bio_path.resolve()
bibllist_bio_short_path = bibllist_bio_path.relative_to(TOP_DIR)

_fn = __file__.split("/")[-1].split(".")[0]

logger = setup_logger(
    __name__,
    level=logging.INFO,
    logfile=Path(f"{_fn}.log")
)


def main():
    start = time.perf_counter()

    reference_path = (
        BASE_DIR.parent / "utils" / "doc" / "! tolstaya-s-a-diaries_d831e869e1f.xlsx"
    )
    reference_path = reference_path.resolve()

    DRY_RUN = False

    # sheet = workbook.active
    sheet_name = "Лист1"
    # sheet = workbook[sheet_name]

    next_row = 3  # sheet.max_row + 1

    for i, row in enumerate(
        iter_xlsx_rows_as_column_letter_dict(
            file_path=str(reference_path),
            sheet_name=sheet_name,
            start_row=next_row,
        ),
        start=next_row,
    ):
        # print(i, row)
        bib_id = row["A"]

        tei_text_path = row["M"]

        title_type_bibl_text = row["N"]
        biblscope_page_text = str(row["O"])
        if '.' in biblscope_page_text:
            biblscope_page_text = biblscope_page_text.split('.')[0]

        front_tei_text_path = row["P"]
        front_title_type_bibl_text = row["Q"]
        front_biblscope_page_text = str(row["R"])
        if '.' in front_biblscope_page_text:
            front_biblscope_page_text = front_biblscope_page_text.split('.')[0]

        biblist_id = row["T"]
        biblist_title = row["U"]

        # main fails
        logger.info(f"============== {'DRY RUN' if DRY_RUN else ''} {tei_text_path} ==============")
        set_tei_title_and_page(
            filename=tei_text_path,
            title=title_type_bibl_text,
            page=biblscope_page_text,
            logger=logger,
            dry_run=DRY_RUN,
        )

        # front files
        logger.info(f"============== {'DRY RUN' if DRY_RUN else ''} {front_tei_text_path} ==============")
        set_tei_title_and_page(
            filename=front_tei_text_path,
            title=front_title_type_bibl_text,
            page=front_biblscope_page_text,
            logger=logger,
            dry_run=DRY_RUN,
        )

        # biblist
        logger.info(f"============== {'DRY RUN' if DRY_RUN else ''} biblist_bio {biblist_id} ==============")
        set_biblist_title(
            filename=bibllist_bio_path,
            title=biblist_title,
            xml_id=biblist_id,
            logger=logger,
            dry_run=DRY_RUN,
        )

    elapsed = time.perf_counter() - start
    logger.info(f"Total time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
