from tolstoy_bio.domain.document_name import DocumentNameGenerator


tolstaya_s_a_diaries_name_generator = DocumentNameGenerator("tolstaya-s-a-diaries")
tolstaya_s_a_journals_name_generator = DocumentNameGenerator("tolstaya-s-a-journals")


def generate_diary_name(start_date: str, end_date: str = "", postfix: str = ""):
    return tolstaya_s_a_diaries_name_generator.generate(start_date, end_date, postfix)


def generate_journal_name(start_date: str, end_date: str = None, postfix: str = None):
    return tolstaya_s_a_journals_name_generator.generate(start_date, end_date, postfix)
