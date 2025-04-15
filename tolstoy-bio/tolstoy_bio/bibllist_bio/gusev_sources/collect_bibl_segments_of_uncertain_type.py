import os

import pandas as pd
from tqdm import tqdm

from .document.gusev_tei_repository import GusevTeiRepository


DOCUMENT_ID_COLUMN_LABEL = "document_id"
BIBL_SEGMENT_COLUMN_LABEL = "segment"
BIBL_SEGMENT_ABSENCE_PLACEHOLDER = "check"


def main():
    collect_bibl_segments_of_uncertain_type()


def collect_bibl_segments_of_uncertain_type():
    gusev_repository = GusevTeiRepository()
    gusev_documents = gusev_repository.get_documents()

    table_entries = []

    for document in tqdm(gusev_documents, "Collecting table data"):
        bibl_elements = document.get_bibl_elements()

        for bibl_element in bibl_elements:
            bibl_text = bibl_element.get_text()
            bibl_text_segments = bibl_text.get_segments()

            for segment in bibl_text_segments:
                if (
                    segment.has_uncertain_type()
                    and segment.get_text() != BIBL_SEGMENT_ABSENCE_PLACEHOLDER
                ):
                    table_entries.append(
                        {
                            DOCUMENT_ID_COLUMN_LABEL: document.get_id(),
                            BIBL_SEGMENT_COLUMN_LABEL: segment.get_text(),
                        }
                    )

    sorted_table_entries = sorted(
        table_entries,
        key=lambda entry: (
            entry[DOCUMENT_ID_COLUMN_LABEL],
            entry[BIBL_SEGMENT_COLUMN_LABEL],
        ),
    )

    table = pd.DataFrame(
        sorted_table_entries,
        columns=[DOCUMENT_ID_COLUMN_LABEL, BIBL_SEGMENT_COLUMN_LABEL],
    )

    table.to_excel(
        os.path.join(
            os.path.dirname(__file__), "data/gusev_bibl_segments_of_uncertain_type.xlsx"
        ),
        index=False,
    )


if __name__ == "__main__":
    main()
