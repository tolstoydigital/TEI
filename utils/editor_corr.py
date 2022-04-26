from lxml import etree
import re
import os
from prereform2modern import Processor

def markup_choices_for_editorial_corrections(text):
    choice_pattern = re.compile(
        r'(<head.*?>[*, ]*)?(\s*(\w*?(\[(.*?)\])\w*)\s*)(?!\">)(</head>)?'
        # r'(<head[^>]*?>[*, ]*)?(\s*(\w*?(\[(.*?)])\w*)\s*)(?!\">)(</head>)?'
    )
    illegible_pattern = re.compile(  # решить, что с этим делать
        r'(\[\d+.*?не\s*разобр.*?\])|'  # [2 неразобр.]
         # вл[иянием?]
        r'(\[\?\])'  # [?]
    )
    crossed_out_pattern = re.compile(
        # r'(<.*?>)?(з|З)ач(е|ё)ркнуто:(<.*?>)?'
        r'(<[^>]*?>)?(з|З)ач(е|ё)ркнуто:(<[^>]*?>)?'
    )
    choice_result = re.findall(choice_pattern, text)

    for i in choice_result:
        if (
                i[0] or  # if inside head
                illegible_pattern.search(i[2]) is not None or
                crossed_out_pattern.search(i[2]) is not None
        ):
            continue
        elif re.search(r'(\w*\[\w+\?\s*\])', i[2]):
            sub_1 = re.sub(r'\[|\]', r'', i[2])
            sub_2 = re.sub(r'\[|\(', r'\\[', i[2])
            sub_3 = re.sub(r'\]|\)', r'\\]', sub_2)
            sub_3 = re.sub("\?", "\?", sub_2)
            sub_4 = re.sub('\[.*?\]', '', i[2])
            sub_4 = re.sub("\?", "", sub_4)
            choice_attribute = re.search('<.*?>(.*?)<.*?>', i[2])  # [<hi>хвастовство</hi>]
            if choice_attribute is None:
                choice_attribute = i[2]
            else:
                choice_attribute = choice_attribute.group(1)
            replacement = (f'<choice original_editorial_correction="{choice_attribute}">'
                           f'<sic>{sub_4}</sic><corr cert="low">{sub_1}</corr></choice>')
            reg_for_repl = f'(?<!="){sub_3}(?!">)'
            text = re.sub(reg_for_repl, replacement, text)
            continue
        sub_1 = re.sub(r'\[|\]', r'', i[2])
        sub_2 = re.sub(r'\[|\(', r'\\[', i[2])
        sub_3 = re.sub(r'\]|\)', r'\\]', sub_2)
        sub_4 = re.sub('\[.*?\]', '', i[2])
        choice_attribute = re.search('<.*?>(.*?)<.*?>', i[2])  # [<hi>хвастовство</hi>]
        if choice_attribute is None:
            choice_attribute = i[2]
        else:
            choice_attribute = choice_attribute.group(1)
        replacement = (f'<choice original_editorial_correction="{choice_attribute}">'
                       f'<sic>{sub_4}</sic><corr>{sub_1}</corr></choice>')
        reg_for_repl = f'(?<!="){sub_3}(?!">)'
        text = re.sub(reg_for_repl, replacement, text)
    return text



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

  
def q_mark_correction(text:str):
    '''функция для разметки редакторских сокращений со знаком вопроса такого вида:
        ко[торого?]'''
    pattern = re.compile(r'(<head.*?>[*, ]*)?(\s*(\w+?(\[[^<\[]+?\?\])\w*)\s*)(?!\">)(</head>)?')
    choice_result = re.findall(pattern, text)
    for result in choice_result:
        sub_1 = re.escape(result[2])
        sub_2 =  re.sub('\[.*?\]', '', result[2])
        sub_3 = re.sub(r'\[|\]|\?', r'', result[2])

        replacement = (f'<choice original_editorial_correction="{result[2]}">'
                           f'<sic>{sub_2}</sic><corr cert="low">{sub_3}</corr></choice>')
        reg_for_repl = f'(?<!="){sub_1}(?!">)'
        #print(reg_for_repl)
        #print(replacement)
        
        text = re.sub(reg_for_repl, replacement, text)

    return text      
  
def editor_changes(text:str):
     #убрать все пропуски между тегами
    text = re.sub("\s{2,}|\n", "", text) 
    # паттерн для примечаний, где слово Зачеркнуто выделено тегом hi
    # Здесь есть вопрос: ([^>]+?) - мне нужно, чтобы в середине выражения матчилась и слова и теги <choice>,
    # но не никакой другой открывающийся тег
    pattern_hi = re.compile("(<note[^>]*?><div[^>]*?><head><ref[^>]*?>[^<]+?</ref></head><p[^>]*?>)<hi[^>]*?>(Зач\.[:;]|Зач[её]ркнуто[:;])</hi>(.*?(?=</p>))(</p>.*?</div></note>)")

    text = pattern_hi.sub("\g<1><del>\g<3></del>\g<4>", text)

   
    # [?] перед квадратными скобками
    text = re.sub("\s([^\s^<>]+?)\s+\[\?\]", "<unclear>\g<1></unclear>", text)
    # [?] перед словом в тегах редакторской коррекции
    text = re.sub("(<choice[^<]+?>(<sic>[^<]+?</sic>|<sic/>)<corr>[^<]+?</corr></choice>)\s+\[\?\]", "<unclear>\g<1></unclear>", text)
    # [?] перед словом в тегах дореволюционной орфографии
    text = re.sub("(<choice><reg>[^<>]+?</reg><orig>[^<>]+?</orig></choice>)\s+\[\?\]", "<unclear>\g<1></unclear>", text)
    # для [1 неразбор.]
    text = re.sub("\[([0-9])\s*не\s*разобр\.\]", "<gap reason='illegible' quantity='\g<1>' unit='word' />", text)
    text = q_mark_correction(text)
    return text
def change_editor_notes(file:str):
    tree = etree.parse(file)
    root = tree.getroot()
    text = etree.tostring(root, pretty_print=True, encoding="unicode")
    text = editor_changes(text)
    root = etree.fromstring(text)
    for note in root.findall(".//{http://www.tei-c.org/ns/1.0}note"):
        # для примечаний в самом теге note

        if note.text is not None:
            if re.search("([Зз]ач\.[:;]|Зач[её]ркнуто[:;])\s*(.+)", note.text):
                note.text = markup_choices_for_editorial_corrections(note.text)
                note.text = markup_choices_for_prereform_spelling(note.text)

                note.text = re.sub("([Зз]ач\.[:;]|Зач[её]ркнуто[:;])\s*(.+)", "<del>\g<2></del>", note.text)
            
        else:
            # для примечаний в тегах p
            for p in note.findall(".//{http://www.tei-c.org/ns/1.0}p"):
               
                if p.text is not None:
                    if re.search("([Зз]ач\.[:;]|Зач[её]ркнуто[:;])\s*(\w+)", p.text):
                        p.text = markup_choices_for_editorial_corrections(p.text)
                        p.text = markup_choices_for_prereform_spelling(p.text)
                        p.text = re.sub("([Зз]ач\.[:;]|Зач[ёе]ркнуто[:;])\s*(.+)", "<del>\g<2></del>", p.text)
                        p.text = re.sub("&lt;(.+?)&gt;", "<del>\g<1></del>", p.text)
                    
    Element_tree = etree.ElementTree(root)
    Element_tree.write(file, encoding = "utf-8", xml_declaration=True, pretty_print=True)
def pipline():
    path = "/content/TEI/files_with_updated_headers"
    folders = os.listdir(path)
    for folder in folders:
        new_path = f"{path}/{folder}"
        files = os.listdir(new_path)
        os.chdir(new_path)
        for file in files:
            change_editor_notes(file)
if __name__ == "__main__":
    pipline()            
