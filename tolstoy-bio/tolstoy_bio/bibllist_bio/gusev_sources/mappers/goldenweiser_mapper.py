from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import StrEnum
import json
import os

from tqdm import tqdm
from tolstoy_bio.utilities.io import IoUtils

from ..document.gusev_tei_repository import GusevTeiRepository
from ..document.gusev_tei_document import GusevTeiDocument


class LinkageCriterion(StrEnum):
    BIBL_DATE = "bibl-date"
    TECHNICAL_DATE = "technical-date"


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


def sort_sources(sources: list[Source]) -> list[Source]:
    def _sort_key(source: Source):
        if source.linkage_criterion == LinkageCriterion.BIBL_DATE:
            return (0, source.document_id)
        elif source.linkage_criterion == LinkageCriterion.TECHNICAL_DATE:
            return (1, source.document_id)
        else:
            raise ValueError(f"Unknown linkage criterion: {source.linkage_criterion}")

    return sorted(sources, key=_sort_key)


class GoldenweiserMapper:
    _gusev_repository: GusevTeiRepository

    def __init__(self, gusev_repository: GusevTeiRepository) -> None:
        self._gusev_repository = gusev_repository

    def map_to_sources(self) -> dict[str, set[Source]]:
        bibl_segment_to_possibly_dates = (
            self._get_bibl_segment_to_possible_dates_table()
        )

        gusev_documents_by_bibl_segment = self._get_gusev_documents_by_bibl_segment(
            set(bibl_segment_to_possibly_dates.keys())
        )

        source_document_filenames = IoUtils.get_folder_contents_names(
            os.path.join(
                os.path.dirname(__file__),
                "../../../goldenweiser/data/xml/by_entry",
            )
        )

        gusev_id_to_sources: dict[str, set[Source]] = defaultdict(set)

        for segment, documents in tqdm(list(gusev_documents_by_bibl_segment.items())):
            for document in documents:
                metadata = document.get_metadata()
                possibly_dates = bibl_segment_to_possibly_dates[segment]

                dates = None
                linkage_criterion = None

                if possibly_dates is None:
                    dates = sorted(document.get_technical_dates_as_iso_set())
                    linkage_criterion = LinkageCriterion.TECHNICAL_DATE
                else:
                    incomplete_dates = possibly_dates
                    year = metadata.start_date.year
                    dates = []

                    for date in incomplete_dates:
                        if "0000" in date:
                            assert (
                                metadata.start_date.year == metadata.end_date.year
                            ), document.get_path()

                            dates.append(date.replace("0000", year))
                        else:
                            dates.append(date)

                    linkage_criterion = LinkageCriterion.BIBL_DATE

                matching_sources: set[Source] = set()

                for date in dates:
                    matching_sources.update(
                        [
                            Source(
                                linkage_criterion=linkage_criterion,
                                document_id=name.replace(".xml", ""),
                            )
                            for name in source_document_filenames
                            if date in name
                        ]
                    )

                gusev_id_to_sources[document.get_id()].update(matching_sources)

        return gusev_id_to_sources

    def map_to_source_ids(self) -> dict[str, list[str]]:
        gusev_id_to_sources = self.map_to_sources()
        gusev_id_to_source_ids: dict[str, list[str]] = {}

        for gusev_id, sources in gusev_id_to_sources.items():
            ids: list[str] = []
            sorted_sources = sort_sources(sources)

            for source in sorted_sources:
                if source.document_id not in ids:
                    ids.append(source.document_id)
            
            gusev_id_to_source_ids[gusev_id] = ids

        return gusev_id_to_source_ids

    def map_to_sources_and_save(self) -> None:
        gusev_id_to_sources = self.map_to_sources()

        IoUtils.save_as_json(
            {
                gusev_id: [
                    source.to_dict()
                    for source in sorted(sources, key=lambda source: source.document_id)
                ]
                for gusev_id, sources in gusev_id_to_sources.items()
            },
            os.path.join(
                os.path.dirname(__file__),
                "../data/linking_results/gusev-to-goldenweiser.json",
            ),
            indent=2,
        )

    def _get_gusev_documents_by_bibl_segment(
        self, bibl_segments_to_consider: set[str]
    ) -> dict[str, list[GusevTeiDocument]]:
        gusev_documents = self._gusev_repository.get_documents()

        documents_by_segment = defaultdict(list)

        for document in tqdm(gusev_documents, "[Goldenweiser] Hashing Gusev's documents by <bibl> segment"):
            bibl_elements = document.get_bibl_elements()

            for bibl_element in bibl_elements:
                bibl_text = bibl_element.get_text()
                bibl_text_segments = bibl_text.get_segments()

                for segment in bibl_text_segments:
                    segment_text = segment.get_text()

                    if segment_text in bibl_segments_to_consider:
                        documents_by_segment[segment_text].append(document)

        return documents_by_segment

    def _get_bibl_segment_to_possible_dates_table(self) -> dict[str, list[str] | None]:
        segments_by_type_as_json = IoUtils.read_as_text(
            os.path.join(
                os.path.dirname(__file__),
                "../data/parsed_bibl_segments/goldenweiser-segments-to-dates.json",
            )
        )

        return json.loads(segments_by_type_as_json)
