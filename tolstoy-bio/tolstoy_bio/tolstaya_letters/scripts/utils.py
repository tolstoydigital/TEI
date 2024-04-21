from tolstoy_bio.domain.document_name import DocumentNameGenerator


tolstaya_letters_name_generator = DocumentNameGenerator("tolstaya-s-a-letters")


def generate_name(start_date: str, end_date: str = "", postfix: str = ""):
    return tolstaya_letters_name_generator.generate(start_date, end_date, postfix)
