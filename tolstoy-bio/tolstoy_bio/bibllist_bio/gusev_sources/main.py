from collections import defaultdict
from dataclasses import dataclass
import os
from typing import Generator

import pandas as pd
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils

from .document.gusev_tei_repository import GusevTeiRepository
from .document.gusev_tei_document import GusevTeiDocument
from .document.bibllist_bio import BibllistBio
from .mappers.makovitski_mapper import MakovitskiMapper
from .mappers.tolstaya_journals_mapper import TolstayaJournalsMapper
from .mappers.tolstaya_diaries_mapper import TolstayaDiariesMapper
from .mappers.tolstoy_diaries_mapper import TolstoyDiariesMapper
from .mappers.tolstoy_diaries_mapper_for_parenthesis_prefix import (
    TolstoyDiariesMapperForParenthesisPrefix,
)
from .mappers.goldenweiser_mapper import GoldenweiserMapper
from .mappers.tolstoy_letters_mapper import TolstoyLettersMapper


# class GusevTeiDocumentsAnalyzer:
#     _documents: list[GusevTeiDocument]

#     def __init__(self, documents: list[GusevTeiDocument]) -> None:
#         self._documents = documents

#     def _iterate_documents(
#         self, message: str
#     ) -> Generator[GusevTeiDocument, None, None]:
#         for document in tqdm(self._documents, message):
#             yield document

#     def assert_no_bibl_elements_in_bodies(self) -> None:
#         for document in self._iterate_documents(
#             "Asserting no <bibl> elements in Gusev's bodies"
#         ):
#             document.assert_no_bibl_elements_in_body()


def main():
    map_and_update_bibllist_bio()


def map_and_update_bibllist_bio():
    gusev_repository = GusevTeiRepository()

    mappers = [
        MakovitskiMapper,
        TolstayaJournalsMapper,
        TolstayaDiariesMapper,
        TolstoyDiariesMapper,
        GoldenweiserMapper,
        TolstoyLettersMapper,
        TolstoyDiariesMapperForParenthesisPrefix,
    ]

    maps: list[dict[str, list[str]]] = []

    for Mapper in mappers:
        mapper_instance = Mapper(gusev_repository)
        maps.append(mapper_instance.map_to_source_ids())

    bibllist_bio_path: str = os.path.join(
        os.path.dirname(__file__),
        "../../../../reference/bibllist_bio.xml",
    )

    print("Loading bibllist_bio.xml...")

    bibllist_bio = BibllistBio(bibllist_bio_path)
    gusev_item = bibllist_bio.get_gusev_item()
    gusev_related_items_by_id = gusev_item.get_related_items_hashed_by_id()

    gusev_sources_by_id: dict[str, list[str]] = defaultdict(list)

    for map_ in tqdm(maps, "Combining maps"):
        for gusev_id, source_ids in map_.items():
            gusev_sources_by_id[gusev_id].extend(source_ids)

    for gusev_id, source_ids in tqdm(
        list(gusev_sources_by_id.items()), "Updating related items"
    ):
        gusev_related_item = gusev_related_items_by_id[gusev_id]
        gusev_related_item.set_tolstoy_bio_sources(source_ids)

    print("Saving bibllist_bio.xml...")
    bibllist_bio.save()

    print("Done!")


def generate_json_with_counted_segments_by_item_type() -> None:
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
        output += f"{type} ({len(segments)})\n\n"
        output += "\n".join(segments)
        output += "\n\n"

    IoUtils.save_textual_data(
        output,
        os.path.join(
            os.path.dirname(__file__), "data/segments-by-type-with-counts.txt"
        ),
    )


if __name__ == "__main__":
    main()
