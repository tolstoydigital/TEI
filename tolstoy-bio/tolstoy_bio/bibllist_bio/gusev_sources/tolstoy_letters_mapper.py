from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import StrEnum
import json
import os

from tqdm import tqdm
from tolstoy_bio.utilities.io import IoUtils

from .gusev_tei_repository import GusevTeiRepository
from .gusev_tei_document import GusevTeiDocument
from .tolstoy_diary_tei_document import TolstoyDiaryTeiDocument
from .tolstoy_letter_tei_document import TolstoyLetterTeiDocument


class LinkageCriterion(StrEnum):
    NUMBER = "number"
    PAGE = "page"


@dataclass(frozen=True)
class Source:
    linkage_criterion: str
    document_id: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def __hash__(self):
        return hash((self.linkage_criterion, self.document_id))

    def __eq__(self, other):
        if not isinstance(other, Source):
            return False

        return (
            self.document_id == other.document_id
            and self.linkage_criterion == other.linkage_criterion
        )


class TolstoyLettersMapper:
    _gusev_repository: GusevTeiRepository

    def __init__(self, gusev_repository: GusevTeiRepository) -> None:
        self._gusev_repository = gusev_repository

    def map(self) -> None:
        bibl_segment_to_locations = self._get_bibl_segment_to_locations_table()

        gusev_documents_by_bibl_segment = self._get_gusev_documents_by_bibl_segment(
            set(bibl_segment_to_locations.keys())
        )

        potential_source_paths = IoUtils.get_folder_contents_paths(
            os.path.join(
                os.path.dirname(__file__),
                "../../../../texts/letters",
            )
        )

        potential_source_filenames = [
            os.path.basename(path) for path in potential_source_paths
        ]

        volume_number_to_source_filenames: dict[tuple[int, int], set[str]] = (
            defaultdict(set)
        )

        volume_page_to_source_filenames: dict[tuple[int, int], set[str]] = defaultdict(
            set
        )

        for source_path, source_filename in zip(
            potential_source_paths, potential_source_filenames
        ):
            source_document = TolstoyLetterTeiDocument(source_path)
            source_metadata = source_document.get_metadata()

            volume_number_to_source_filenames[
                source_metadata.volume, source_metadata.number
            ].add(source_filename)

            for page in source_metadata.pages:
                volume_page_to_source_filenames[source_metadata.volume, page].add(
                    source_filename
                )

        gusev_id_to_sources: dict[str, str] = defaultdict(set)

        for segment, documents in tqdm(list(gusev_documents_by_bibl_segment.items())):
            for document in documents:
                locations = bibl_segment_to_locations[segment]

                matching_sources: set[Source] = set()

                for location in locations:
                    location_volume = location["volume"]

                    if location_volume is None:
                        continue

                    location_numbers = [
                        str(number) for number in (location.get("numbers") or [])
                    ]
                    
                    location_pages = location.get("pages") or []

                    for location_number in location_numbers:
                        matching_sources.update(
                            [
                                Source(
                                    linkage_criterion=LinkageCriterion.NUMBER,
                                    document_id=filename.replace(".xml", ""),
                                )
                                for filename in volume_number_to_source_filenames[
                                    location_volume, location_number
                                ]
                            ]
                        )

                    for location_page in location_pages:
                        matching_sources.update(
                            [
                                Source(
                                    linkage_criterion=LinkageCriterion.PAGE,
                                    document_id=filename.replace(".xml", ""),
                                )
                                for filename in volume_page_to_source_filenames[
                                    location_volume, location_page
                                ]
                            ]
                        )

                gusev_id_to_sources[document.get_id()].update(matching_sources)

        IoUtils.save_as_json(
            {
                gusev_id: [
                    source.to_dict()
                    for source in sorted(sources, key=lambda source: source.document_id)
                ]
                for gusev_id, sources in gusev_id_to_sources.items()
            },
            os.path.join(os.path.dirname(__file__), "gusev-to-tolstoy-letters.json"),
            indent=2,
        )

    def _get_gusev_documents_by_bibl_segment(
        self, bibl_segments_to_consider: set[str]
    ) -> dict[str, list[GusevTeiDocument]]:
        gusev_documents = self._gusev_repository.get_documents()

        documents_by_segment = defaultdict(list)

        for document in tqdm(gusev_documents, "_get_gusev_documents_by_bibl_segment"):
            bibl_elements = document.get_bibl_elements()

            for bibl_element in bibl_elements:
                bibl_text = bibl_element.get_text()
                bibl_text_segments = bibl_text.get_segments()

                for segment in bibl_text_segments:
                    segment_text = segment.get_text()

                    if segment_text in bibl_segments_to_consider:
                        documents_by_segment[segment_text].append(document)

        return documents_by_segment

    def _get_bibl_segment_to_locations_table(self) -> dict[str, list[dict]]:
        segments_by_type_as_json = IoUtils.read_as_text(
            os.path.join(
                os.path.dirname(__file__), "tolstoy-letter-segments-to-locations.json"
            )
        )

        return json.loads(segments_by_type_as_json)
