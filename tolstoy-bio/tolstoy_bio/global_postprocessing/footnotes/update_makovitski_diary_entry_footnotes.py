from collections import Counter
import os
import re

from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils

from .lib.tei_document import TeiDocument
from .lib.tei_note import TeiNote
from .lib.tei_repository import TeiRepository
from .lib.utils import replace_square_brackets_with_cursive


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

MAKOVITSKI_DIARY_VOLUME_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../makovitski/data/xml/by_volume"
)

MAKOVITSKI_DIARY_ENTRY_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../makovitski/data/xml/by_entry"
)


def process_makovitski_entry(document: TeiDocument, *, verbose: bool = False) -> None:
    notes = document.get_notes()

    numeric_note_count = 1
    asterisk_note_count = 1

    for note in tqdm(notes, "Processing footnotes", disable=not verbose):
        if re.match(r"\d", note.get_link_text()):
            assert note.get_id().startswith("note")

            note.set_id(f"footnote{numeric_note_count}")
            note.set_link_text(str(numeric_note_count))
            note.add_footnote_type()
            numeric_note_count += 1
        else:
            assert note.get_id().startswith("footnote")

            note.set_id(f"a{asterisk_note_count}")
            note.remove_footnote_type()
            asterisk_note_count += 1

    document.validate()
    document.save()


def process_makovitski_entries():
    repository = TeiRepository(MAKOVITSKI_DIARY_ENTRY_REPOSITORY_PATH)
    documents = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(documents, "Processing entries", document_count):
        process_makovitski_entry(document)


def main():
    process_makovitski_entries()


if __name__ == "__main__":
    main()
