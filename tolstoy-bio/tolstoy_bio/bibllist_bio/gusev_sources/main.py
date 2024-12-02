from collections import defaultdict
import os
from pprint import pprint
from typing import Generator

from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils

from .gusev_tei_repository import GusevTeiRepository
from .gusev_tei_document import GusevTeiDocument
from .makovitski_mapper import MakovitskiMapper


class GusevTeiDocumentsAnalyzer:
    _documents: list[GusevTeiDocument]

    def __init__(self, documents: list[GusevTeiDocument]) -> None:
        self._documents = documents

    def _iterate_documents(
        self, message: str
    ) -> Generator[GusevTeiDocument, None, None]:
        for document in tqdm(self._documents, message):
            yield document

    def assert_no_bibl_elements_in_bodies(self) -> None:
        for document in self._iterate_documents(
            "Asserting no <bibl> elements in Gusev's bodies"
        ):
            document.assert_no_bibl_elements_in_body()


def main():
    gusev_repository = GusevTeiRepository()
    makovitski_mapper = MakovitskiMapper(gusev_repository)
    makovitski_mapper.map()


def generate_json() -> None:
    gusev_repository = GusevTeiRepository()
    gusev_documents = gusev_repository.get_documents()

    segments_by_type = defaultdict(set)

    for document in tqdm(gusev_documents):
        bibl_elements = document.get_bibl_elements()

        for bibl_element in bibl_elements:
            bibl_text = bibl_element.get_text()
            bibl_text_segments = bibl_text.get_segments()

            for segment in bibl_text_segments:
                segment_types = segment.get_source_types()
                segment_text = segment.get_text()

                for segment_type in segment_types:
                    segments_by_type[segment_type].add(segment_text)
    
    output = ""

    for type, segments in segments_by_type.items():
        output += f"{type}\n\n"
        output += "\n".join(segments)
        output += "\n\n"
    
    IoUtils.save_textual_data(output, os.path.join(os.path.dirname(__file__), "segments-by-type.txt"))


if __name__ == "__main__":
    main()
