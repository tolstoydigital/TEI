import os
import re

from tqdm import tqdm

from .lib.tei_document import TeiDocument
from .lib.tei_repository import TeiRepository
from .lib.utils import replace_square_brackets_with_cursive


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TOLSTOY_DIARY_REPOSITORY_PATH = os.path.join(ROOT_DIR, "../../../../texts/diaries")


def process_tolstoy_diary(document: TeiDocument, *, verbose: bool = False) -> None:
    notes = document.get_notes()

    for count, note in tqdm(
        enumerate(notes, 1),
        "Processing footnotes",
        len(notes),
        disable=not verbose,
    ):
        assert (
            note.has_numeric_link()
        ), f"Non-numeric link found at {document.get_path()}"

        note.set_link_text(str(count))
        replace_square_brackets_with_cursive(note)

    document.validate()
    document.save()


def process_tolstoy_diaries():
    repository = TeiRepository(TOLSTOY_DIARY_REPOSITORY_PATH)
    documents = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(documents, "Processing diaries", document_count):
        process_tolstoy_diary(document)


def main():
    process_tolstoy_diaries()


if __name__ == "__main__":
    main()
