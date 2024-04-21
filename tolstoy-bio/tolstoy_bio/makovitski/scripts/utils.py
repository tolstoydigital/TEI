from tolstoy_bio.domain.document_name import DocumentNameGenerator


makovitski_diaries_name_generator = DocumentNameGenerator("makovitski-diaries")


def generate_name(start_date: str, end_date: str = "", postfix: str = ""):
    return makovitski_diaries_name_generator.generate(start_date, end_date, postfix)
