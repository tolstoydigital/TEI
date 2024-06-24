from tolstoy_bio.domain.document_name import UniqueDocumentNameGenerator


def get_goldenweiser_document_name_generator():
    return UniqueDocumentNameGenerator("goldenweiser-diaries")
