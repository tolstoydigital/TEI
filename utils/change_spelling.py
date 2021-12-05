def change_spelling(orig_text):
    text_res, changes, s_json = Processor.process_text(
    text=orig_text,
    show=True,
    delimiters=['<choice><reg>', '</reg><orig>', '</orig></choice>'],
    check_brackets=False
    )
    return text_res
