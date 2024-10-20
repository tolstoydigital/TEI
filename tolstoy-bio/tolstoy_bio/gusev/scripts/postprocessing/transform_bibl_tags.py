import os

import bs4
from lxml import etree
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils


GUSEV_TEI_REPOSITORY_PATH = os.path.join(os.path.dirname(__file__), "../../data/tei")


def main():
    record_paths = IoUtils.get_folder_contents_paths(
        GUSEV_TEI_REPOSITORY_PATH, ignore_hidden=True
    )

    for record_path in tqdm(record_paths, "Transforming <bibl> tags"):
        record_content = IoUtils.read_as_text(record_path)
        updated_record_content = transform_bibl_tags(record_content)

        validate_xml(updated_record_content, f"XML became invalid at {record_path}")
        validate_absence_of_milestones_in_title_stmt(
            updated_record_content,
            f"Milestone found inside the title of {record_path}",
        )

        IoUtils.save_textual_data(updated_record_content, record_path)


def transform_bibl_tags(content: str) -> str:
    content = content.replace("&lt;bibl&gt;", '<milestone type="bibl-tag-start"/>')
    content = content.replace("&lt;/bibl&gt;", '<milestone type="bibl-tag-end"/>')
    return content


def validate_xml(content: str, error_message: str | None = None) -> None:
    try:
        etree.fromstring(content.encode())
    except Exception as e:
        if error_message:
            print(error_message)

        raise e


def validate_absence_of_milestones_in_title_stmt(
    content: str, error_message: str = None
) -> None:
    soup = bs4.BeautifulSoup(content, "xml")
    title_stmt_element = soup.find("titleStmt")
    assert "milestone" not in title_stmt_element.prettify(), error_message


if __name__ == "__main__":
    main()
