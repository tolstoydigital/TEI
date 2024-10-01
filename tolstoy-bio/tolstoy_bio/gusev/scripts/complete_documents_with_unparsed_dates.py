from collections import defaultdict
from functools import cached_property
import os
import re
import shutil
import sys

import pandas as pd
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


class DocumentFetcher:
    @cached_property
    def _repository_path(self):
        module_folder_relative_path = os.path.dirname(__file__)
        module_folder_absolute_path = os.path.abspath(module_folder_relative_path)
        return os.path.join(module_folder_absolute_path, "../data/tei")

    def get_path_by_filename(self, filename: str) -> str:
        return os.path.join(self._repository_path, filename)


def preprocess_date(date: str) -> str:
    if type(date) is not str:
        return None

    stripped = date.replace("(?)", "").strip()

    try:
        day, month, year = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", stripped).groups()
        return "-".join([year, month, day])
    except re.error as error:
        print(f"Wrong format: {stripped}")
        raise error


def preprocess(value) -> str | None:
    if type(value) is not str:
        return None

    return value.strip()


def main():
    excel_table_path = sys.argv[1]

    print(f"Parsing excel table from path {excel_table_path}...")

    df = pd.read_excel(excel_table_path, "ДАННЫЕ", dtype=str)

    document_fetcher = DocumentFetcher()

    filename_to_start_dates = defaultdict(list)
    filename_to_end_dates = defaultdict(list)

    for _, row in tqdm(df.iterrows(), desc="Generating", total=df.shape[0]):
        document_id = preprocess(row["ID документа"])
        editor_date_label = preprocess(row["Текст редакторской даты"])

        technical_date_start_date = preprocess_date(row["@from"])
        technical_date_end_date = (
            preprocess_date(row["@to"]) or technical_date_start_date
        )

        technical_date_calendar_label = preprocess(row["@calendar"])
        technical_date_period_label = preprocess(row["@period"])
        technical_date_certainty_label = preprocess(row["cert"])

        document_filename = f"{document_id}.xml"
        document_path = document_fetcher.get_path_by_filename(document_filename)
        document_soup = BeautifulSoupUtils.create_soup_from_file(document_path, "xml")

        editor_date_element = document_soup.find("date", {"type": "editor"})

        if editor_date_element.text.strip() == "":
            editor_date_element.append(document_soup.new_string(editor_date_label))

        technical_date_elements = document_soup.find_all(
            "date", attrs={"calendar": True}
        )

        new_technical_date_element_attributes = {
            k: v
            for k, v in {
                "calendar": (
                    technical_date_calendar_label.upper()
                    if technical_date_calendar_label
                    else None
                ),
                "period": technical_date_period_label,
                "from": technical_date_start_date,
                "to": technical_date_end_date,
                "cert": technical_date_certainty_label,
            }.items()
            if v is not None
        }

        new_technical_date_element = document_soup.new_tag(
            "date",
            attrs=new_technical_date_element_attributes,
        )

        if technical_date_elements:
            last_technical_date_element = technical_date_elements[-1]
            last_technical_date_element.insert_after(new_technical_date_element)
        else:
            editor_date_element.insert_after(new_technical_date_element)

        filename_to_start_dates[document_filename].append(technical_date_start_date)
        filename_to_end_dates[document_filename].append(technical_date_end_date)

        IoUtils.save_textual_data(document_soup.prettify(), document_path)

    new_paths = set()

    for filename in tqdm(
        filename_to_start_dates.keys(),
        desc="Changing filenames and updating IDs",
        total=len(filename_to_start_dates),
    ):
        start_dates = filename_to_start_dates[filename]
        end_dates = filename_to_end_dates[filename]

        earliest_date = sorted(start_dates)[0]
        latest_date = sorted(end_dates)[-1]

        filename_parts = filename.replace(".xml", "").split("_")
        filename_stem = filename_parts[:4]
        filename_postfix = filename_parts[-1] if len(filename_parts) == 11 else None

        new_filename_parts = [
            *filename_stem,
            earliest_date.replace("-", "_"),
            latest_date.replace("-", "_"),
        ]

        if filename_postfix:
            new_filename_parts.append(filename_postfix)

        new_id = "_".join(new_filename_parts)
        new_filename = f"{new_id}.xml"

        original_path = document_fetcher.get_path_by_filename(filename)
        new_path = os.path.join(os.path.dirname(original_path), new_filename)

        if new_path in new_paths:
            print(original_path)
            print(new_path)
            print()

        new_paths.add(new_path)

        document_soup = BeautifulSoupUtils.create_soup_from_file(original_path, "xml")
        id_title_elements = document_soup.find_all("title", {"xml:id": True})
        assert (n := len(id_title_elements)) == 1, f"Unexpected number of <title @xml:id> elements: {n}"
        id_title_element = id_title_elements[0]
        id_title_element.attrs["xml:id"] = new_id
        IoUtils.save_textual_data(document_soup.prettify(), original_path)

        shutil.copy(original_path, new_path)
        os.remove(original_path)


if __name__ == "__main__":
    main()
