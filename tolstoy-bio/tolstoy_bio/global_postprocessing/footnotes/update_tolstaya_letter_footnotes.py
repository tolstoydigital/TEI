import os
import re

from tqdm import tqdm

from .lib.tei_document import TeiDocument
from .lib.tei_note import TeiNote
from .lib.tei_repository import TeiRepository
from .lib.utils import replace_square_brackets_with_cursive


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TOLSTAYA_LETTER_VOLUME_XML_DOCUMENT_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_letters/data/tolstaya-s-a-letters.xml"
)

TOLSTAYA_LETTER_ENTRY_XML_DOCUMENTS_FOLDER_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_letters/data/xml"
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


def process_tolstaya_letter(document: TeiDocument, *, verbose: bool = False) -> None:
    footnotes = document.get_footnotes()

    numeric_footnote_count = 1
    sentence_footnote_count = 1

    for footnote in tqdm(footnotes, "Processing footnotes", disable=not verbose):
        if footnote.has_numeric_link():
            transform_note_to_popup(footnote, numeric_footnote_count)
            numeric_footnote_count += 1
        else:
            transform_note_with_wordy_link_to_footnote(
                footnote, sentence_footnote_count
            )

            sentence_footnote_count += 1

    document.validate()
    document.save()


def process_tolstaya_letters():
    volume_document = TeiDocument(TOLSTAYA_LETTER_VOLUME_XML_DOCUMENT_PATH)
    process_tolstaya_letter(volume_document, verbose=True)

    entry_repository = TeiRepository(TOLSTAYA_LETTER_ENTRY_XML_DOCUMENTS_FOLDER_PATH)
    entry_documents = entry_repository.get_documents()

    for document in tqdm(entry_documents, "Processing entries"):
        process_tolstaya_letter(document)


def main():
    process_tolstaya_letters()


if __name__ == "__main__":
    main()
