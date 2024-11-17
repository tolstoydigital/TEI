import os

from tqdm import tqdm

from .lib.tei_document import TeiDocument
from .lib.tei_repository import TeiRepository
from .lib.utils import replace_square_brackets_with_cursive


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TOLSTOY_LETTER_REPOSITORY_PATH = os.path.join(ROOT_DIR, "../../../../texts/letters")


def process_tolstoy_letter(document: TeiDocument) -> None:
    footnotes = document.get_footnotes()

    for footnote in footnotes:
        replace_square_brackets_with_cursive(footnote)

    document.validate()
    document.save()


def prettify_tolstoy_letters():
    repository = TeiRepository(TOLSTOY_LETTER_REPOSITORY_PATH)

    document_iterator = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(
        document_iterator, "Prettifying Tolstoy's letters", document_count
    ):
        document.save()


def process_tolstoy_letters():
    repository = TeiRepository(TOLSTOY_LETTER_REPOSITORY_PATH)

    document_iterator = repository.get_document_iterator()
    document_count = repository.count_documents()

    for document in tqdm(
        document_iterator, "Processing Tolstoy's letters", document_count
    ):
        process_tolstoy_letter(document)


def main():
    process_tolstoy_letters()


if __name__ == "__main__":
    main()
