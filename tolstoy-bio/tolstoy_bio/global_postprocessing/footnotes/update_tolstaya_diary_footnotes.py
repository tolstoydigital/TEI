import os
import re

from tqdm import tqdm

from .lib.tei_document import TeiDocument
from .lib.tei_note import TeiNote
from .lib.tei_repository import TeiRepository
from .lib.utils import replace_square_brackets_with_cursive


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TOLSTAYA_DIARY_ENTRY_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_diaries/data/xml/by_entry"
)


def transform_note_to_popup(note: TeiNote, index: int) -> None:
    note.set_id(f"a{index}")
    note.set_link_text("*")
    note.remove_footnote_type()
    replace_square_brackets_with_cursive(note)


def transform_note_with_wordy_link_to_footnote(note: TeiNote, index: int) -> None:
    link_soup = note.get_link_soup()
    link_soup.insert_before(*link_soup.contents)
    note.get_parent().smooth()

    string_before_link = note.get_string_before_link()

    if str(string_before_link):
        string_before_link.replace_with(re.sub("\s+", " ", str(string_before_link)))

    note.set_link_text(str(index))
    note.add_footnote_type()


def process_tolstaya_diary(document: TeiDocument, *, verbose: bool = False) -> None:
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


def process_tolstaya_diaries():
    repository = TeiRepository(TOLSTAYA_DIARY_ENTRY_REPOSITORY_PATH)
    documents = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(documents, "Processing entries", document_count):
        process_tolstaya_diary(document)


def main():
    process_tolstaya_diaries()


if __name__ == "__main__":
    main()
