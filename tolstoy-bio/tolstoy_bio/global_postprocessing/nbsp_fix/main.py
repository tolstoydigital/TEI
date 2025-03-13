import os
import re
import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.xml import XmlUtils


def traverse_documents():
    for folder_path, _, filenames in os.walk(
        os.path.abspath(os.path.join(__file__, "../../../"))
    ):
        if not filenames:
            continue

        for filename in filenames:
            if filename == "template.xml":
                continue

            if "__pycache__" in folder_path:
                continue

            if not filename.endswith(".xml"):
                continue

            if "gusev/data/source" in folder_path:
                continue

            yield os.path.join(folder_path, filename)


def main() -> None:
    total_nbsp_replacement_count = 0

    for document_path in tqdm(list(traverse_documents())):
        document_content = IoUtils.read_as_text(document_path)

        updated_document_content, nbsp_replacement_count = re.subn(
            r"(&amp;|&)?nbsp;?", "&#160;", document_content
        )

        total_nbsp_replacement_count += nbsp_replacement_count

        XmlUtils.validate_xml_or_fail(updated_document_content, ignore_xml_ids=True)
        IoUtils.save_textual_data(updated_document_content, document_path)

    print(f"{total_nbsp_replacement_count=}")


if __name__ == "__main__":
    main()
