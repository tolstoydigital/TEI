from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import StrEnum
import json
import os

from tqdm import tqdm
from tolstoy_bio.utilities.io import IoUtils

from .gusev_tei_repository import GusevTeiRepository
from .gusev_tei_document import GusevTeiDocument


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


class MakovitskiMapper:
    _gusev_repository: GusevTeiRepository

    def __init__(self, gusev_repository: GusevTeiRepository) -> None:
        self._gusev_repository = gusev_repository

    def map(self) -> None:
        bibl_segment_to_possibly_dates = (
            self._get_bibl_segment_to_possible_dates_table()
        )

        gusev_documents_by_bibl_segment = self._get_gusev_documents_by_bibl_segment(
            set(bibl_segment_to_possibly_dates.keys())
        )

        makovitski_document_filenames = IoUtils.get_folder_contents_names(
            os.path.join(
                os.path.dirname(__file__), "../../makovitski/data/xml/by_entry"
            )
        )

        gusev_id_to_makovitski_sources: dict[str, str] = defaultdict(set)

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
                    dates = [date.replace("0000", year) for date in incomplete_dates]
                    linkage_criterion = LinkageCriterion.BIBL_DATE

                matching_makovitski_sources: set[Source] = set()

                for date in dates:
                    matching_makovitski_sources.update(
                        [
                            Source(
                                linkage_criterion=linkage_criterion,
                                document_id=name.replace(".xml", ""),
                            )
                            for name in makovitski_document_filenames
                            if date in name
                        ]
                    )

                gusev_id_to_makovitski_sources[document.get_id()].update(
                    matching_makovitski_sources
                )

        IoUtils.save_as_json(
            {
                gusev_id: [
                    source.to_dict()
                    for source in sorted(sources, key=lambda source: source.document_id)
                ]
                for gusev_id, sources in gusev_id_to_makovitski_sources.items()
            },
            os.path.join(os.path.dirname(__file__), "gusev-to-makovitski.json"),
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

    def _get_bibl_segment_to_possible_dates_table(self) -> dict[str, list[str] | None]:
        segments_by_type_as_json = IoUtils.read_as_text(
            os.path.join(os.path.dirname(__file__), "segments-to-dates-makovitski.json")
        )

        return json.loads(segments_by_type_as_json)
