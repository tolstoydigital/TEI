import os
import re
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

from tolstoy_bio.utilities.io import IoUtils
from .entities.gusev_tei_repository import GusevTeiRepository
from .entities.source_list import SourceList
from .entities.bibllist_bio import (
    BibllistBio,
    BibllistBioSourceListRelationConfiguration,
)

MATCHING_THRESHOLD = 0.5
LINKING_APPROACH_COMMENT = f"Default scikit-learn TF-IDF vectorization with cosine similarity matrix and matching threshold of {MATCHING_THRESHOLD}. Preprocessing includes converting full month labels to abbreviations."


def main():
    print("Getting segment ID to segment text map...")
    segment_id_to_segment_text = get_segment_id_to_segment_text_map()

    print("Getting source ID to source title map...")
    source_id_to_source_title = get_source_id_to_source_title_map()

    print("Linking segments to sources...")
    segment_id_to_source_match = get_segment_id_to_matching_source_match(
        segment_id_to_segment_text=segment_id_to_segment_text,
        source_id_to_source_title=source_id_to_source_title,
    )

    print("Evaluating results...")
    evaluation_table = evaluate_matches(segment_id_to_source_match)

    print(
        "Adding relation tags to bibllist_bio.xml",
        "and generating post-evaluation table...",
    )
    add_relation_tags_to_bibllist_bio(evaluation_table)

    print("Done!")


def _build_data_repository_path(path: str):
    return os.path.join(
        os.path.dirname(__file__),
        f"data/{path}",
    )


def _build_linking_results_repository_path(path: str):
    return _build_data_repository_path(f"linking-results/{MATCHING_THRESHOLD}/{path}")


def get_segment_id_to_segment_text_map(*, from_cache=False):
    cache_file_path = _build_data_repository_path("segment-id-to-segment-text.json")

    if from_cache:
        return IoUtils.read_json(cache_file_path)

    gusev_tei_repository = GusevTeiRepository()
    gusev_documents = gusev_tei_repository.get_documents()

    gusev_bibl_segments = [
        segment
        for document in gusev_documents
        for segment in document.get_bibl_segments()
        if segment.is_source_list_linking_candidate()
    ]

    segment_id_to_segment_text = {
        segment.get_id(): segment.get_text() for segment in gusev_bibl_segments
    }

    IoUtils.save_as_json(
        segment_id_to_segment_text,
        cache_file_path,
        indent=2,
    )

    return segment_id_to_segment_text


def get_source_id_to_source_title_map(*, from_cache=False):
    cache_file_path = _build_data_repository_path("source-id-to-source-title.json")

    if from_cache:
        return IoUtils.read_json(cache_file_path)

    source_list = SourceList()
    sources = source_list.get_entries()

    source_id_to_source_title = {
        source.get_id(): title
        for source in sources
        if (title := source.get_bibliographic_title() or source.get_main_title())
    }

    IoUtils.save_as_json(
        source_id_to_source_title,
        cache_file_path,
        indent=2,
    )

    return source_id_to_source_title


def get_segment_id_to_matching_source_match(
    *,
    segment_id_to_segment_text: dict[str, str],
    source_id_to_source_title: dict[str, str],
):
    """
    Links each segment ID to SourceMatch,
    where SourceMatch is a dictionary
    containing the source list entry ID
    and the cosine similarity in range [0, 1]
    between the source title and the segment text.
    """
    segment_ids = list(segment_id_to_segment_text.keys())
    segment_texts = list(segment_id_to_segment_text.values())

    source_ids = list(source_id_to_source_title.keys())
    source_titles = list(source_id_to_source_title.values())

    corpus = segment_texts + source_titles

    month_to_abbreviation = {
        "январь": "янв",
        "января": "янв",
        "февраль": "фев",
        "февраля": "фев",
        "март": "мар",
        "марта": "мар",
        "апрель": "апр",
        "апреля": "апр",
        "май": "май",
        "мая": "май",
        "июнь": "июн",
        "июня": "июн",
        "июль": "июл",
        "июля": "июл",
        "август": "авг",
        "августа": "авг",
        "сентябрь": "сен",
        "сентября": "сен",
        "октябрь": "окт",
        "октября": "окт",
        "ноябрь": "ноя",
        "ноября": "ноя",
        "декабрь": "дек",
        "декабря": "дек",
    }

    def replace_month_labels_with_abbreviations(string: str):
        for month_label, abbreviation in month_to_abbreviation.items():
            string = string.replace(month_label, abbreviation)

        return string

    vectorizer = TfidfVectorizer(preprocessor=replace_month_labels_with_abbreviations)
    vectorizer.fit(corpus)

    segment_text_vectors = vectorizer.transform(segment_texts)
    source_title_vectors = vectorizer.transform(source_titles)

    similarity_matrix = cosine_similarity(segment_text_vectors, source_title_vectors)

    segment_id_to_source_match = {}

    for segment_index, segment_id in enumerate(segment_ids):
        best_match_index = np.argmax(similarity_matrix[segment_index])
        best_match_score = similarity_matrix[segment_index][best_match_index]

        segment_id_to_source_match[segment_id] = {
            "source_id": source_ids[best_match_index],
            "cosine_similarity": best_match_score,
        }

    IoUtils.save_as_json(
        segment_id_to_source_match,
        os.path.join(
            os.path.dirname(__file__),
            _build_linking_results_repository_path("source-id-to-source-match.json"),
        ),
        indent=2,
    )

    return segment_id_to_source_match


def evaluate_matches(segment_id_to_source_match: dict[str, dict]):
    """
    Converts cosine similarities to probabilities
    by additionally checking if a source title
    is a substring of the segment text,
    evaluates the match against the matching threshold,
    and generates a report table with evaluation results.
    """
    gusev_tei_repository = GusevTeiRepository()
    gusev_documents = gusev_tei_repository.get_documents()

    gusev_bibl_segments = [
        segment
        for document in gusev_documents
        for segment in document.get_bibl_segments()
        if segment.is_source_list_linking_candidate()
    ]

    segments_by_id = {segment.get_id(): segment for segment in gusev_bibl_segments}

    source_list = SourceList()
    sources = source_list.get_entries()
    sources_by_id = {source.get_id(): source for source in sources}

    total_segment_count = len(segment_id_to_source_match)

    matching_results = []
    linked_segment_count = 0

    for i, (segment_id, source_match) in enumerate(segment_id_to_source_match.items()):
        segment_text = segments_by_id[segment_id].get_text()
        source_id = source_match["source_id"]
        source = sources_by_id[source_id]
        source_main_title = source.get_main_title()
        source_bibl_title = source.get_bibliographic_title()
        source_title = source_bibl_title or source_main_title

        matching_probability = float(source_match["cosine_similarity"])

        if not source_title:
            matching_probability = 0.0

        if source_title in segment_text:
            matching_probability = 1.0

        should_match = matching_probability >= MATCHING_THRESHOLD

        matching_results.append(
            {
                "segment": {"id": segment_id, "text": segment_text},
                "source": {
                    "id": source_id,
                    "title": source_bibl_title or source_main_title,
                },
                "matching_probability": matching_probability,
                "should_match": should_match,
            }
        )

        if should_match:
            linked_segment_count += 1

    evaluation_table = {
        "comment": LINKING_APPROACH_COMMENT,
        "statistics": {
            "total_segment_count": total_segment_count,
            "linked_segment_count": linked_segment_count,
        },
        "results": matching_results,
    }

    print(f"Linked segments: {linked_segment_count} out of {total_segment_count}.")

    IoUtils.save_as_json(
        evaluation_table,
        os.path.join(
            os.path.dirname(__file__),
            _build_linking_results_repository_path("evaluation-table.json"),
        ),
        indent=2,
    )

    return evaluation_table


def add_relation_tags_to_bibllist_bio(evaluation_table: dict):
    """
    Adds <relation> tags with <biblpoint> children
    to Gusev <relatedItem> elements in bibllist_bio.xml.

    Additionally, generates a report table for future manual post-evaluation.
    """
    gusev_tei_repository = GusevTeiRepository()
    gusev_documents = gusev_tei_repository.get_documents()

    gusev_bibl_segments = [
        segment
        for document in gusev_documents
        for segment in document.get_bibl_segments()
        if segment.is_source_list_linking_candidate()
    ]

    gusev_bibl_segments_by_id = {
        segment.get_id(): segment for segment in gusev_bibl_segments
    }

    source_list = SourceList()

    bibllist_bio = BibllistBio()
    bibllist_bio_gusev_item = bibllist_bio.get_gusev_item()

    bibllist_bio_gusev_related_items_by_id = (
        bibllist_bio_gusev_item.get_related_items_hashed_by_id()
    )

    bibllist_relation_configurations_by_document_id = defaultdict(list)

    gusev_bibl_segment_page_reference_regex_pattern = re.compile(
        r"стр\.?\s*(?:([IVXLCDM]+|\d+)(?:\s*[-‐‑‒–—―⸺⸻﹘﹣－]\s*([IVXLCDM]+|\d+))?(?:\s*[,.;]\s*|\s+)*)+",
        flags=re.IGNORECASE,
    )

    post_evaluation_table_entries = []

    for match in evaluation_table["results"]:
        should_match = match["should_match"]

        segment = gusev_bibl_segments_by_id[match["segment"]["id"]]
        source = source_list.get_entry_by_id(match["source"]["id"])

        source_bibliographic_title = source.get_bibliographic_title()
        assert source_bibliographic_title, f"Empty source title for {source.get_id()}"

        segment_text = segment.get_text()

        segment_page_references = [
            re.sub(r"[.,\s]+$", "", match.group())
            for match in gusev_bibl_segment_page_reference_regex_pattern.finditer(
                segment_text
            )
        ]

        segment_pages_string = ", ".join(segment_page_references)

        bibl_point_text = (
            source_bibliographic_title.rstrip(".") + ", " + segment_pages_string
        ).strip(", ")

        if re.match(r"\w$", bibl_point_text[-1]):
            bibl_point_text += "."

        segment_document_id = segment.get_tei_document().get_id()

        post_evaluation_table_entries.append(
            {
                "bibl_segment": segment.get_text(),
                "source_title_bibl": source_bibliographic_title,
                "probability": match["matching_probability"],
                "is_linked": should_match,
                "bibl_segment_pages": segment_pages_string,
                "biblpoint": bibl_point_text,
                "parent_bibl": segment.get_parent_bibl_text(),
                "parent_bibl_id": segment.get_parent_bibl_id(),
                "document_id": segment_document_id,
                "bibl_segment_id": segment.get_id(),
                "source_list_item_id": source.get_id(),
            }
        )

        if should_match:
            bibllist_relation_configurations_by_document_id[segment_document_id].append(
                BibllistBioSourceListRelationConfiguration(
                    bibl_segment_id=segment.get_id(),
                    source_list_item_id=source.get_id(),
                    bibl_point_text=bibl_point_text,
                )
            )

    table = pd.DataFrame(
        post_evaluation_table_entries,
        columns=[
            "bibl_segment",
            "source_title_bibl",
            "probability",
            "is_linked",
            "bibl_segment_pages",
            "biblpoint",
            "parent_bibl",
            "parent_bibl_id",
            "document_id",
            "bibl_segment_id",
            "source_list_item_id",
        ],
    )

    table.to_excel(
        _build_linking_results_repository_path("post-evaluation-table.xlsx"),
        index=False,
    )

    for (
        document_id,
        relation_configurations,
    ) in bibllist_relation_configurations_by_document_id.items():
        bibllist_bio_related_item = bibllist_bio_gusev_related_items_by_id[document_id]
        bibllist_bio_related_item.ensure_placeholders()
        bibllist_bio_related_item.set_source_list_relations(relation_configurations)

    bibllist_bio.save()


if __name__ == "__main__":
    main()
