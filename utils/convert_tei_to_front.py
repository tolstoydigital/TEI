from copy import deepcopy
import os
from pathlib import Path
import re
from uuid import uuid4

from lxml import etree

"""Надо подставить путь то репозитория"""
REPO_PATH = '..'  # {подставить свое}/TEI
REPO_TEXTS_PATH = Path(REPO_PATH, 'texts')
RESULT_PATH = Path(REPO_PATH, 'texts_front')

XMLNS = 'http://www.tei-c.org/ns/1.0'


def is_descendant_of_p(tag: etree._Element, tag_type='p') -> bool:
    for parent in tag.iterancestors():
        if parent.tag.replace(f'{{{XMLNS}}}', '') == tag_type:
            return True
    return False


def get_p_ancestor(tag: etree._Element) -> etree._Element:
    for parent in tag.iterancestors():
        if parent.tag.replace(f'{{{XMLNS}}}', '') == 'p':
            return parent


def get_all_p_uuids(path: Path) -> set[str]:
    ids = set()
    ids_list = []
    for path, dirs, files in os.walk(path):
        for filename in files:
            if not filename.endswith('.xml'):
                continue
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())
            paragraphs = root.xpath('//ns:p', namespaces={'ns': f'{XMLNS}'})
            for p in paragraphs:
                try:
                    ids.add(p.attrib['id'])
                    ids_list.append(p.attrib['id'])
                except KeyError:
                    continue
            lines = root.xpath('//ns:l', namespaces={'ns': f'{XMLNS}'})
            for l in lines:
                try:
                    ids.add(l.attrib['id'])
                    ids_list.append(l.attrib['id'])
                except KeyError:
                    continue

    # consider uuids in taxonomy
    with open(Path(path, '../../reference/taxonomy.xml'), 'rb') as file:
        root = etree.fromstring(file.read())
    for tag in root.xpath('//category'):
        ids.add(tag.attrib['uuid'])
        ids_list.append(tag.attrib['uuid'])

    # print(len(ids), len(ids_list))
    return ids


def generate_new_uuid(uuids: set[str]) -> str:
    while True:
        uuid = str(uuid4())
        if uuid not in uuids:
            uuids.add(uuid)
            return uuid


def wrap_tag_in_p(tag: etree._Element, uuids: set[str], root: etree._Element) -> None:
    """лажа с индентацией"""

    def get_indentation_level(tag, root, uuid):
        """неправильно работает"""
        text_lines = etree.tostring(root, encoding='unicode').split('\n')
        line = '      '
        for i in text_lines:
            if f'<p id="{uuid}"' in i:
                line = i
                break  # где-то почему-то не находится, проверить
        space = len(line) - len(line.lstrip(' '))
        return space // 2

    parent_tag = tag.getparent()
    uuid = generate_new_uuid(uuids)
    new_p = etree.Element('p', id=uuid)
    parent_tag.insert(parent_tag.index(tag), new_p)
    new_p.insert(0, deepcopy(tag))

    indentation_level = get_indentation_level(tag, root, uuid)
    etree.indent(new_p, space='  ', level=indentation_level)
    new_p.tail = f'\n{"  " * indentation_level}'

    parent_tag.remove(tag)


def wrap_unwrapped_tags_in_p_tag(root: etree._Element, uuids: set[str]) -> None:
    body_tag = root.xpath('//ns:body', namespaces={'ns': f'{XMLNS}'})[0]
    for tag in body_tag.iterdescendants():
        tag_name = tag.tag.replace(f'{{{XMLNS}}}', '')
        # if tag_name in ['p', 'l', 'lg', 'noteGrp', 'div']:
        if tag_name in ['p', 'l', 'lg', 'noteGrp', 'div', 'table', 'cit', 'row', 'cell', 'tr', 'td', 'div1', 'bibl']:
            continue

        if tag.getparent() is body_tag and tag_name == 'div':
            continue
        if tag.getparent().tag.replace(f'{{{XMLNS}}}', '') == 'noteGrp':
            continue
        if not is_descendant_of_p(tag) and not is_descendant_of_p(tag, 'l'):
            wrap_tag_in_p(tag, uuids, root)


def add_uuids_to_existing_p_and_l(root: etree._Element, uuids: set[str]) -> None:
    """добавить uuid где не было"""
    tags = root.xpath('//ns:p', namespaces={'ns': f'{XMLNS}'})
    tags.extend(root.xpath('//ns:l', namespaces={'ns': f'{XMLNS}'}))
    for tag in tags:
        if 'id' not in tag.attrib:
            tag.set('id', generate_new_uuid(uuids))


def delete_old_orthography(root: etree._Element) -> None:
    """Заменить тег choice на текст тега reg. Проблемы с переносом строк"""
    for reg_tag in root.xpath('//ns:reg', namespaces={'ns': f'{XMLNS}'}):
        choice_tag = reg_tag.getparent()
        reg_text = reg_tag.text.strip(" \n") if reg_tag.text is not None else ''
        text = f'{reg_text}{choice_tag.tail if choice_tag.tail is not None else ""}'.strip(' \n') + ' '
        parent = choice_tag.getparent()
        if parent is not None:
            previous_tag = choice_tag.getprevious()
            if previous_tag is not None:
                previous_tag.tail = (previous_tag.tail or '').rstrip(' \n') + ' ' + text
            else:
                parent_text = (parent.text or '').rstrip(' \n') + ' ' + text
                parent.text = parent_text.rstrip('\n')
            parent.remove(choice_tag)


def get_title_id_from_root(root) -> str:
    title_tag = root.xpath('//ns:title[@xml:id]', namespaces={'ns': f'{XMLNS}'})[0]
    return title_tag.attrib['{http://www.w3.org/XML/1998/namespace}id']


def change_tags(root):
    """тоже хрень с индентацией"""
    # various tags into spans
    for tag_name in ['opener', 'dateline', 'unclear', 'del', 'gap', 'add']:
        for tag in root.xpath(f'//ns:{tag_name}', namespaces={'ns': f'{XMLNS}'}):
            tag.tag = 'span'
            tag.set('class', tag_name)

    # comments
    note_grp_tags = root.xpath('//ns:noteGrp[@type="comments"]', namespaces={'ns': f'{XMLNS}'})
    if note_grp_tags:
        note_grp_tag = note_grp_tags[0]
        p_tags = []
        for note_tag in note_grp_tag:
            for p_tag in note_tag:
                p_tags.append(deepcopy(p_tag))
        comments_parent = note_grp_tag.getparent()
        for p_tag in p_tags:
            p_tag.set('class', 'comments')
            p_tag.set('index', 'false')
            comments_parent.insert(comments_parent.index(note_grp_tag), p_tag)
        comments_parent.remove(note_grp_tag)

    # rare words tags
    rare_words_tags = root.xpath('//ns:ref[@target="slovar"]', namespaces={'ns': f'{XMLNS}'})
    for tag in rare_words_tags:
        tag.tag = 'a'
        tag.set('href', '../../reference/Dictionary.xml')
        word_id = tag.attrib.pop('id')
        tag.set('data-type', 'slovar')
        tag.set('data-id', word_id)
        tag.attrib.pop('target')

    # dates in the header to format yyyy-mm-dd
    date_tags = root.xpath('//ns:teiHeader//ns:date', namespaces={'ns': f'{XMLNS}'})
    for tag in date_tags:
        # notBefore notAfter -> from to
        if 'notBefore' in tag.attrib:
            not_before_year = tag.attrib['notBefore']
            tag.attrib.pop('notBefore')
            tag.set('from', not_before_year)
        if 'notAfter' in tag.attrib:
            not_after_year = tag.attrib['notAfter']
            tag.attrib.pop('notAfter')
            tag.set('to', not_after_year)
        # change date format
        for attr in ['when', 'from', 'to']:
            if attr in tag.attrib:
                date = tag.get(attr).strip()
                if re.search(r'^\d{4}-\d\d-\d\d$', date) is not None:
                    continue
                elif re.search(r'^\d{4}$', date) is not None:
                    tag.set(attr, f'{date}-01-01')
                elif re.search(r'^\d{4}-\d\d$', date) is not None:
                    tag.set(attr, f'{date}-01')
                elif re.search(r'^-\d\d-\d\d$', date) is not None:
                    tag.set(attr, f'0001{date}')
                elif date == '?':
                    tag.set(attr, '0001-01-01')
                elif re.search(r'\d{4}', date.strip(' ?')) is not None:
                    tag.set(attr, f'{date.strip(" ?")}-01-01')

        # теги с нестандартными периодами в виде текста
        if tag.text is not None:
            # print(get_title_id_from_root(root))
            # print(tag.attrib)
            years = [i.group() for i in re.finditer(r'\d{4}', tag.text)]
            years.sort(key=int)
            from_year = f'{years[0]}-01-01'
            to_year = f'{years[-1]}-12-31'
            tag.set('from', from_year)
            tag.set('to', to_year)
            tag.text = None

        # для фронта удаляем when и заменяем на from и to
        if 'when' in tag.attrib:
            first_year = tag.attrib['when']
            year = first_year.split('-')[0]
            tag.attrib.pop('when')
            tag.set('from', first_year)
            tag.set('to', f'{year}-12-31')

        if 'from' in tag.attrib:
            first_year = tag.attrib['from']
            last_year = tag.attrib['to']
            if first_year.split('-')[0] == last_year.split('-')[0] and last_year.split('-')[1] == last_year.split('-')[2] == '01':
                tag.set('to', f'{last_year.split("-")[0]}-12-31')

        # temp если глюк, что левая дата больше, то меняю местами даты
        left_date = tag.attrib['from']
        right_date = tag.attrib['to']
        if left_date > right_date:
            tag.set('from', right_date)
            tag.set('to', left_date)

        # check dates
        for attr in ['from', 'to']:
            if re.search(r'^\d{4}-\d\d-\d\d$', tag.attrib[attr]) is None:
                print(tag.attrib, get_title_id_from_root(root))
        left_date = tag.attrib['from']
        right_date = tag.attrib['to']
        if left_date > right_date:
            print(left_date, right_date, get_title_id_from_root(root))

    # cell tags to td
    cell_tags = root.xpath('//ns:cell', namespaces={'ns': f'{XMLNS}'})
    for tag in cell_tags:
        tag.tag = 'td'

    # italic razradka in hi tag
    hi_tags = root.xpath('//ns:hi', namespaces={'ns': f'{XMLNS}'})
    for tag in hi_tags:
        style = []  # .data-attribute
        for attr in tag.attrib:
            for class_value in ['razradka', 'italic']:
                if class_value in tag.attrib[attr].casefold():
                    style.append(class_value)
            tag.attrib.pop(attr)
        if style:
            tag.tag = 'span'
            tag.set('class', 'hi')
            tag.set('data-attribute', ' '.join(style))

    # lb tag
    for lb_tag in root.xpath('//ns:lb', namespaces={'ns': f'{XMLNS}'}):
        lb_tag.tag = 'br'

    # remove lg tags
    lg_tags = root.xpath('//ns:lg', namespaces={'ns': f'{XMLNS}'})
    for lg_tag in lg_tags:
        parent_tag = lg_tag.getparent()
        if parent_tag.tag.replace(f'{{{XMLNS}}}', '') == 'lg':
            continue  # если вложен lg в lg, то не брать, брать только родителей
        l_parent_tag = lg_tag[0] if lg_tag[0].tag.replace(f'{{{XMLNS}}}', '') == 'lg' else lg_tag
        for l_tag in l_parent_tag:
            parent_tag.insert(parent_tag.index(lg_tag), deepcopy(l_tag))
        parent_tag.remove(lg_tag)

    # notes to spans
    note_tags = root.xpath('//ns:text//ns:note', namespaces={'ns': f'{XMLNS}'})
    for note_tag in note_tags:
        if 'class' in note_tag.attrib and note_tag.attrib['class'] == 'comments':
            continue
        note_id = note_tag.attrib.get('{http://www.w3.org/XML/1998/namespace}id') or note_tag.attrib.get('id') \
                  or note_tag.attrib.get('n') or note_tag.attrib.get('{http://www.w3.org/2001/XInclude}id')
        for attr in note_tag.attrib:
            note_tag.attrib.pop(attr)
            note_tag.tag = 'span'
            note_tag.set('class', 'note')
            note_tag.set('id', note_id)

    # ref around notes to a
    ref_tags = [t for t in root.xpath('//ns:ref', namespaces={'ns': f'{XMLNS}'})
                if 'target' in t.attrib and t.attrib['target'].startswith('#note')]
    for tag in ref_tags:
        ref_id = tag.attrib['target'].strip('#')
        tag.tag = 'a'
        tag.attrib.pop('target')
        tag.set('href', '#')
        tag.set('data-type', 'snoska')
        tag.set('id', ref_id)

    # row tags to tr
    for tag in root.xpath('//ns:row', namespaces={'ns': f'{XMLNS}'}):
        tag.tag = 'tr'

    # None text in sic to '' text — может, это и не нужно
    for tag in root.xpath('//ns:sic', namespaces={'ns': f'{XMLNS}'}):
        if tag.text is None:
            tag.text = ''


def check_paragraphs(root):
    wrong = False
    for p_tag in root.xpath('//ns:p', namespaces={'ns': f'{XMLNS}'}):
        # if is_descendant_of_p(p_tag):
        if is_descendant_of_p(p_tag) or is_descendant_of_p(p_tag, 'l'):
            parent = p_tag.getparent()
            # add
            # if parent.tag.replace(f'{{{XMLNS}}}', '') == 'span' and 'class' in parent.attrib and parent.get('class') == 'add':
            #     continue
            # note
            # is_note_descendant = False
            # for tag in p_tag.iterancestors():
            #     if tag.tag.replace(f'{{{XMLNS}}}', '') == 'span' and 'class' in tag.attrib and tag.get('class') == 'note':
            #         is_note_descendant = True
            # if is_note_descendant:
            #     continue
            #
            wrong = True
            ancestor = get_p_ancestor(p_tag)
            if wrong:
                # print(get_title_id_from_root(root), ancestor.get(f'id'))
                # print(p_tag.getparent().attrib, p_tag.getparent().tag)
                # print(p_tag.get('id'))
                pass

    # check l tags
    # for l_tag in root.xpath('//ns:l', namespaces={'ns': f'{XMLNS}'}):
    #     for tag in l_tag.iterdescendants():
    #         if tag.tag.replace(f'{{{XMLNS}}}', '') == 'p':
    #             print(get_title_id_from_root(root))
    return wrong


def change_epigraphs(root):
    for epigraph_tag in root.xpath('//ns:epigraph', namespaces={'ns': f'{XMLNS}'}):
        future_spans = []
        for tag in epigraph_tag.iterdescendants():
            if tag.tag.replace(f'{{{XMLNS}}}', '') == 'p':
                future_spans.append(deepcopy(tag))
        paragraphs = []
        for span in future_spans:
            new_p = etree.Element('p', **span.attrib)
            new_p.append(span)
            for attr in span.attrib:
                span.attrib.pop(attr)
            span.set('class', 'epigraph')
            span.tag = 'span'
            paragraphs.append(new_p)
        for new_p in paragraphs[::-1]:
            epigraph_tag.addnext(new_p)
        epigraph_tag.getparent().remove(epigraph_tag)


def main():
    uuids = get_all_p_uuids(REPO_TEXTS_PATH)
    wrongs = 0
    for path, _, files in os.walk(REPO_TEXTS_PATH):
        for filename in files:
            if not filename.endswith('.xml'):
                continue
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())

            add_uuids_to_existing_p_and_l(root, uuids)
            change_epigraphs(root)
            delete_old_orthography(root)
            wrap_unwrapped_tags_in_p_tag(root, uuids)
            change_tags(root)
            wrongs += check_paragraphs(root)

            text = etree.tostring(root, encoding='unicode')
            etree.fromstring(text.encode())  # для проверки, что не ломается
            Path(RESULT_PATH, Path(path).name, filename).write_text(text)
    print('files with wrong paragraphs: ', wrongs)


if __name__ == '__main__':
    main()
