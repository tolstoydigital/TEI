from tolstoy_bio.domain.document_name import DocumentNameGenerator


goldenweiser_diaries_name_generator = DocumentNameGenerator("goldenweiser-diaries")


def generate_name(start_date: str, end_date: str = ""):
    return goldenweiser_diaries_name_generator.generate(start_date, end_date)
