import os
import re

from tqdm import tqdm

from .lib.tei_document import TeiDocument
from .lib.tei_repository import TeiRepository


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

MAKOVITSKI_DIARY_VOLUME_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../makovitski/data/xml/by_volume"
)


def process_makovitski_volume(document: TeiDocument, *, verbose: bool = False) -> None:
    notes = document.get_notes()

    numeric_note_count = 1
    asterisk_note_count = 1

    for note in tqdm(notes, "Processing footnotes", disable=not verbose):
        if re.match(r"\d", note.get_link_text()):
            note.set_link_text(str(numeric_note_count))
            note.add_footnote_type()
            numeric_note_count += 1
        else:
            note.remove_footnote_type()
            asterisk_note_count += 1

    document.validate()
    document.save()


def process_makovitski_volumes():
    repository = TeiRepository(MAKOVITSKI_DIARY_VOLUME_REPOSITORY_PATH)
    documents = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(documents, "Processing volumes", document_count):
        process_makovitski_volume(document)


def main():
    process_makovitski_volumes()


if __name__ == "__main__":
    main()
