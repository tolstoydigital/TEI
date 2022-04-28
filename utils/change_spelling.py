def markup_choices_for_prereform_spelling(text):
    split_pattern = re.compile(r'(<choice.*?>.*?</choice>)')
    # rus_pattern = re.compile(r'[а-яА-Я\n ]')
    tokens = split_pattern.split(text)
    # print(tokens)
    # print(len(tokens))
    for i, token in enumerate(tokens):
        if split_pattern.search(token) is not None:
            
            corr_pattern = r'<choice(.*?)<corr>(.*?)</corr></choice>'
            matchobj = re.search(corr_pattern, token)
            if not matchobj: 
                matchobj = re.search(r'<choice(.*?)<corr cert="low">(.*?)</corr></choice>', token)
            to_corr = matchobj.group(2)
            text_res, changes, s_json = Processor.process_text(
                text=to_corr,
                show=True,
                delimiters=['<choice><reg>', '</reg><orig>', '</orig></choice>'],
                check_brackets=False
            )
            tokens[i] = f'<choice{matchobj.group(1)}<corr>{text_res}</corr></choice>'
        else:
            in_head_pattern = r'<head[^>].*?>\[.*?\]</head>'  # Иначе странно себя ведет
            if re.search(in_head_pattern, token) is not None:
                continue  # Иначе <head rend="center">[II.]</head> -> <head rend="center"></head>
            text_res, changes, s_json = Processor.process_text(
                text=token,
                show=True,
                delimiters=['<choice><reg>', '</reg><orig>', '</orig></choice>'],
                check_brackets=False
            )
            tokens[i] = text_res
            # print('token', token, '\nresult', text_res)
            # print(tokens)
    return ''.join(tokens)
