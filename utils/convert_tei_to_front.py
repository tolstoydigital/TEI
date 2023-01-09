from copy import deepcopy
import os
from pathlib import Path
import re
from uuid import uuid4

from lxml import etree
import roman
from tqdm import tqdm

import taxonomy_front_utils as txnm
import utils as ut

REPO_PATH = ut.REPO_PATH  # {подставить свое}/TEI
REPO_TEXTS_PATH = Path(REPO_PATH, 'texts')
RESULT_PATH = Path(REPO_PATH, 'texts_front')
DICTIONARY_PATH = Path(REPO_PATH, 'reference', 'Dictionary.xml')
PERSON_LIST_PATH = Path(REPO_PATH, 'reference', 'personList.xml')
TAXONOMY_PATH = Path(REPO_PATH, 'reference', 'taxonomy.xml')
NEW_TAXONOMY_PATH = Path(REPO_PATH, 'reference', 'taxonomy_front.xml')

XMLNS = 'http://www.tei-c.org/ns/1.0'


def is_descendant_of_p(tag: etree._Element, tag_type='p') -> bool:
    """Also used for <l>"""
    for parent in tag.iterancestors():
        if parent.tag.replace(f'{{{XMLNS}}}', '') == tag_type:
            return True
    return False


def get_p_ancestor(tag: etree._Element, tag_type='p') -> etree.Element:
    for parent in tag.iterancestors():
        if parent.tag.replace(f'{{{XMLNS}}}', '') == tag_type:
            return parent


def get_all_uuids(path: Path) -> set[str]:
    ids = set()
    ids_list = []
    for path, dirs, files in os.walk(path):
        for filename in files:
            if not filename.endswith('.xml'):
                continue
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())
            paragraphs = root.xpath('//ns:p', namespaces={'ns': XMLNS})
            for p in paragraphs:
                try:
                    ids.add(p.attrib['id'])
                    ids_list.append(p.attrib['id'])
                except KeyError:
                    continue
            lines = root.xpath('//ns:l', namespaces={'ns': XMLNS})
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
        """неправильно работает (но не принципиально)"""
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
    body_tag = root.xpath('//ns:body', namespaces={'ns': XMLNS})[0]
    for tag in body_tag.iterdescendants():
        tag_name = tag.tag.replace(f'{{{XMLNS}}}', '')
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
    tags = root.xpath('//ns:p', namespaces={'ns': XMLNS})
    tags.extend(root.xpath('//ns:l', namespaces={'ns': XMLNS}))
    for tag in tags:
        if 'id' not in tag.attrib:
            tag.set('id', generate_new_uuid(uuids))


def delete_old_orthography(root: etree._Element) -> None:
    """Заменить тег choice на текст тега reg. Проблемы с переносом строк"""
    for reg_tag in root.xpath('//ns:reg', namespaces={'ns': XMLNS}):
        choice_tag = reg_tag.getparent()
        parent = choice_tag.getparent()
        if len(reg_tag) == 0:
            temp_reg = deepcopy(reg_tag)
            choice_tag.addnext(temp_reg)
            remove_tag_save_text(choice_tag)
            remove_tag_save_text(temp_reg)
        else:
            prev = choice_tag.getprevious()
            reg_tag_text = reg_tag.text if reg_tag.text is not None and reg_tag.text.strip(' \n') else ''
            if prev is not None:
                prev.tail = f'{prev.tail}{reg_tag_text}'
                for sub_tag in reg_tag:
                    parent.insert(parent.index(choice_tag), deepcopy(sub_tag))
            else:
                parent.text = f'{parent.text}{reg_tag_text}'
                for sub_tag in reg_tag:
                    parent.insert(parent.index(choice_tag), deepcopy(sub_tag))
            remove_tag_save_text(choice_tag)


def get_title_id_from_root(root: etree._Element) -> str:
    title_tag = root.xpath('//ns:title[@xml:id]', namespaces={'ns': XMLNS})[0]
    return title_tag.attrib['{http://www.w3.org/XML/1998/namespace}id']


def change_tags(root: etree._Element) -> None:
    # various tags into spans
    for tag_name in ['opener', 'dateline', 'unclear', 'del', 'gap', 'add']:
        for tag in root.xpath(f'//ns:{tag_name}', namespaces={'ns': XMLNS}):
            tag.tag = 'span'
            tag.set('class', tag_name)

    # heads with levels into spans
    for tag in root.xpath(f'//ns:head[@n]', namespaces={'ns': XMLNS}):
        if 'level' not in tag.get('n'):
            continue
        level = tag.get('n').strip('level')
        level = level if int(level) <= 3 else 3
        editorial = tag.get('type') == 'editorial'
        for attr in tag.attrib:
            tag.attrib.pop(attr)
        tag.tag = 'span'
        tag.set('class', f'h{level}')
        if editorial:
            tag.set('resp', 'volume_editor')

    # comments
    note_grp_tags = root.xpath('//ns:noteGrp[@type="comments"]', namespaces={'ns': XMLNS})
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
    rare_words_tags = root.xpath('//ns:ref[@target="slovar"]', namespaces={'ns': XMLNS})
    for tag in rare_words_tags:
        tag.tag = 'a'
        tag.set('href', '../../reference/Dictionary.xml')
        word_id = tag.attrib.pop('id')
        tag.set('data-type', 'slovar')
        tag.set('data-id', word_id)
        tag.attrib.pop('target')

    # dates in the header to format yyyy-mm-dd
    date_tags = root.xpath('//ns:teiHeader//ns:date', namespaces={'ns': XMLNS})
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
            if first_year.split('-')[0] == last_year.split('-')[0] and last_year.split('-')[1] == last_year.split('-')[
                2] == '01':
                tag.set('to', f'{last_year.split("-")[0]}-12-31')

        # temp если глюк, что левая дата больше, то меняем местами даты
        left_date = tag.attrib['from']
        right_date = tag.attrib['to']
        if left_date > right_date:
            tag.set('from', right_date)
            tag.set('to', left_date)

        # check dates (if ok, nothing will be printed)
        for attr in ['from', 'to']:
            if re.search(r'^\d{4}-\d\d-\d\d$', tag.attrib[attr]) is None:
                print(tag.attrib, get_title_id_from_root(root))
        left_date = tag.attrib['from']
        right_date = tag.attrib['to']
        if left_date > right_date:
            print(left_date, right_date, get_title_id_from_root(root))

    # cell tags to td
    cell_tags = root.xpath('//ns:cell', namespaces={'ns': XMLNS})
    for tag in cell_tags:
        tag.tag = 'td'

    # italic razradka in hi tag
    hi_tags = root.xpath('//ns:hi', namespaces={'ns': XMLNS})
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
    for lb_tag in root.xpath('//ns:lb', namespaces={'ns': XMLNS}):
        lb_tag.tag = 'br'

    # remove lg tags
    lg_tags = root.xpath('//ns:lg', namespaces={'ns': XMLNS})
    for lg_tag in lg_tags:
        parent_tag = lg_tag.getparent()
        if parent_tag.tag.replace(f'{{{XMLNS}}}', '') == 'lg':
            continue  # если вложен lg в lg, то не брать, брать только родителей
        l_parent_tag = lg_tag[0] if lg_tag[0].tag.replace(f'{{{XMLNS}}}', '') == 'lg' else lg_tag
        for l_tag in l_parent_tag:
            parent_tag.insert(parent_tag.index(lg_tag), deepcopy(l_tag))
        parent_tag.remove(lg_tag)

    # notes to spans
    note_tags = root.xpath('//ns:text//ns:note', namespaces={'ns': XMLNS})
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
    ref_tags = [t for t in root.xpath('//ns:ref', namespaces={'ns': XMLNS})
                if 'target' in t.attrib and t.attrib['target'].startswith('#note')]
    for tag in ref_tags:
        ref_id = tag.attrib['target'].strip('#')
        tag.tag = 'a'
        tag.attrib.pop('target')
        tag.set('href', '#')
        tag.set('data-type', 'snoska')
        tag.set('id', ref_id)

    # row tags to tr
    for tag in root.xpath('//ns:row', namespaces={'ns': XMLNS}):
        tag.tag = 'tr'

    # None text in sic to '' text — может, это и не нужно
    for tag in root.xpath('//ns:sic', namespaces={'ns': XMLNS}):
        if tag.text is None:
            tag.text = ''


def check_paragraphs(root: etree._Element) -> bool:
    """(also <l> tags) For debug. If ok, nothing will be printed."""
    wrong = False
    # check p
    for p_tag in root.xpath('//ns:p', namespaces={'ns': XMLNS}):
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
    # check l
    for l_tag in root.xpath('//ns:l', namespaces={'ns': XMLNS}):
        if is_descendant_of_p(l_tag) or is_descendant_of_p(l_tag, 'l'):
            wrong = True
        if wrong:
            ancestor = get_p_ancestor(l_tag, 'l') or get_p_ancestor(l_tag)
            print('wrong nested l', get_title_id_from_root(root), ancestor.get('id'), l_tag.get('id'))
    return wrong


def change_epigraphs(root: etree._Element) -> None:
    for epigraph_tag in root.xpath('//ns:epigraph', namespaces={'ns': XMLNS}):
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


def get_ids_from_catalogue(path: Path, regex: str) -> list[str]:
    with open(path) as file:
        catalogue = file.read()
    ids = []
    for _id in re.finditer(regex, catalogue):
        ids.append(_id.group(1))
    return ids


def remove_tag_if_id_not_in_catalogue(
        root: etree._Element,
        ids: list[str],
        tag_name: str,
        xpath_attrs: str,
        id_attr='id'
) -> None:
    tags = root.xpath(f'//ns:{tag_name}[{xpath_attrs}]', namespaces={'ns': XMLNS})
    for tag in tags:
        person_id = tag.attrib[id_attr]
        if person_id not in ids:
            remove_tag_save_text(tag)


def remove_tag_save_text(tag: etree._Element) -> None:
    parent = tag.getparent()
    previous = tag.getprevious()
    ref_tag_text = tag.text.strip(' \n') if tag.text is not None else ''
    ref_tag_tail = tag.tail.strip('\n').lstrip(' ') if tag.tail is not None else ''

    no_space_before_tail = ref_tag_tail and re.search(r'\w', ref_tag_tail[0]) is None and \
                           ref_tag_tail[0] not in ['(']
    space = '' if no_space_before_tail else ' '

    if previous is not None:
        prev_tail = previous.tail.rstrip(" \n") if previous.tail is not None else ''
        previous.tail = f'{prev_tail} {ref_tag_text}{space}{ref_tag_tail}'
    else:
        parent_text = parent.text.rstrip(" \n") if parent.text is not None else ''
        parent.text = f'{parent_text} {ref_tag_text}{space}{ref_tag_tail}'
    parent.remove(tag)


def replace_self_closing_tags(root: etree._Element) -> None:
    body = root.xpath('//ns:body', namespaces={'ns': XMLNS})[0]
    for tag in body.iterdescendants():
        tag_name = tag.tag.replace(f'{{{XMLNS}}}', '')
        if tag.text is None and tag_name != 'br':
            tag.text = ''


def fix_roman_digits_in_page_range(root: etree._Element) -> None:
    pages_tag = root.xpath('//ns:biblScope[@unit="page"]', namespaces={'ns': XMLNS})[0]
    first, last = pages_tag.text.strip().split('-')
    if not first.isnumeric() or not last.isnumeric():
        first = first if first.isnumeric() else roman.fromRoman(first)
        last = last if last.isnumeric() else roman.fromRoman(last)
        pages_tag.text = f'{first}-{last}'


def change_catrefs_to_catrefs_front(root: etree._Element, taxonomy: dict, new_taxonomy: dict) -> None:
    catref_tags = root.xpath('//ns:catRef', namespaces={'ns': XMLNS})
    parent = catref_tags[0].getparent()
    catrefs = [i.get('ana').strip('#') for i in catref_tags]
    new_ana = txnm.old_catrefs_to_new_catrefs(catrefs, [taxonomy, new_taxonomy])
    old_catrefs = []
    for tag in catref_tags:
        if tag.get('ana').strip('#') == 'works' or tag.get('target') in txnm.CATEGORIES_TO_DEL:
            parent.remove(tag)
        else:
            old_catrefs.append(deepcopy(tag))
            parent.remove(tag)
    for ana in new_ana:
        if ana not in catrefs:
            target = new_taxonomy[ana]['target']
            tag = etree.Element('catRef', ana=f'#{ana}', target=target)
            parent.append(tag)
    for tag in old_catrefs:
        parent.append(tag)
    etree.indent(parent, level=3, space='    ')


def remove_or_add_extra_spaces(text: str) -> str:
    # add spaces
    text = re.sub(r'\.(?![\s,.?!\d])', '. ', text)  # '.sdf' -> '. sdf'
    text = re.sub(r',(?![\s—\d])', ', ', text)  # ',sdf' -> ', sdf'
    text = re.sub(r';(?![\s])', '; ', text)  # ';sdf' -> '; sdf'
    text = re.sub(r'\?(?![\s(\[<!.])', '? ', text)  # ';sdf' -> '; sdf'
    text = re.sub(r'\)(?![\s])', ') ', text)  # ')sdf' -> ') sdf'

    # remove spaces
    for char in '.,?!;:])>»”':
        text = text.replace(f' {char}', char)

    for char in '[(<«“':
        text = text.replace(f'{char} ', char)
    return text


def remove_spaces_in_root(root: etree._Element) -> None:
    for tag in root.iterdescendants():
        if tag.text and tag.text.strip():
            tag.text = re.sub(r'\s{2,}', ' ', tag.text)
            tag.text = remove_or_add_extra_spaces(tag.text)
        if tag.tail and tag.tail.strip():
            tag.tail = re.sub(r'\s{2,}', ' ', tag.tail)
            tag.tail = remove_or_add_extra_spaces(tag.tail)


def append_or_not_right_space(text: str, next_text: str) -> str:
    if next_text[0] in '.,?!;:])>»”':
        return text.rstrip(' ')
    return text


def deal_with_next(tag: etree._Element, root: etree._Element, tag_attr: str) -> None:
    if tag_attr == 'text' and tag.tail and tag.tail.strip(' \n'):
        tag.text = append_or_not_right_space(tag.text, tag.tail)
        return
    tag_with_next_text = find_tag_of_nearest_right_text(tag, root)
    if tag_with_next_text is not None:
        text = getattr(tag, tag_attr)
        next_text = tag_with_next_text.text \
            if tag_with_next_text.text and tag_with_next_text.text.strip('\n ') else tag_with_next_text.tail
        new_text = append_or_not_right_space(text, next_text)
        setattr(tag, tag_attr, new_text)


def find_tag_of_nearest_right_text(tag: etree._Element, root: etree._Element) -> etree._Element | None:
    if tag is root:
        return None
    next_tag = tag.getnext()
    while True:
        if next_tag is not None:
            if next_tag.text is not None and next_tag.text.strip():
                return next_tag
            else:
                next_tag = next_tag.getnext()
        else:
            break
    parent = tag.getparent()
    if parent.tail and parent.tail.strip('\n '):
        return parent
    else:
        find_tag_of_nearest_right_text(parent, root)


def change_taxonomy_path(root: etree._Element) -> None:
    tag = root.xpath('//ns:include', namespaces={'ns': 'http://www.w3.org/2001/XInclude'})[0]
    tag.set('href', '../../reference/taxonomy_front.xml')


def fill_empty_sic_with_asterisks(root: etree._Element) -> None:
    sics = root.xpath('//ns:sic', namespaces={'ns': XMLNS})
    for tag in sics:
        if not tag.text:
            tag.text = '***'


def get_tag_first_text(tag: etree._Element) -> dict[str] | None:
    if tag.text is not None and tag.text.strip(' \n'):
        text = tag.text
        attr = 'text'
    elif tag.tail is not None and tag.tail.strip(' \n'):
        text = tag.tail
        attr = 'tail'
    else:
        return None
    return {'text': text, 'attr': attr}


def get_tag_deepest_descendant_with_text(this_tag, start_from, same_tag=False):
    if this_tag.text is not None and this_tag.text.strip(' \n'):
        if not same_tag:
            return this_tag, 'text'
    if len(this_tag) == 0 and (this_tag.tail is None or not this_tag.tail.strip(' \n')):
        parent = this_tag.getparent()
        grandparent = parent.getparent()
        if parent.tail is not None and parent.tail.strip(' \n'):
            return parent, 'tail'
        # del
        elif grandparent.tail is not None and grandparent.tail.strip(' \n'):
            return grandparent, 'tail'
        return None, None
    if len(this_tag) == 0 and this_tag.tail is not None and this_tag.tail.strip(' \n'):
        if not (same_tag and start_from == 'tail'):
            return this_tag, 'tail'
    for tag in this_tag.iterdescendants():
        if tag.text is not None and tag.text.strip(' \n'):
            return tag, 'text'
        if len(tag) == 0 and (tag.tail is None or not tag.tail.strip(' \n')):
            return None, None
        if len(tag) == 0 and tag.tail is not None and tag.tail.strip(' \n'):
            return tag, 'tail'
        return get_tag_deepest_descendant_with_text(tag, start_from)


def get_tag_with_next_text(root, this_tag, start_from='text') -> tuple[etree._Element | None, str | None]:
    tag_found = False
    this_tag_descendants = [t for t in this_tag.iterdescendants()]
    for tag in root.iterdescendants():
        if not tag_found:
            if tag is this_tag:
                tag_found = True
        if tag_found:
            if start_from == 'tail':
                # надо только то, что идет после хвоста, поэтому потомков пропускаем
                if tag in this_tag_descendants or tag is this_tag:
                    continue
            closest_tag_with_text, attr = get_tag_deepest_descendant_with_text(tag, start_from,
                                                                               same_tag=tag is this_tag)
            if closest_tag_with_text is not None:
                return closest_tag_with_text, attr
    return None, None


def fix_spaces_in_root(root):
    # убрать пробелы по краям текста/хвоста тега
    for tag in root.iterdescendants():
        text = tag.text
        if text is not None:
            text = text.strip(' \n')
            tag.text = text
        tail = tag.tail
        if tail is not None:
            tail = tail.strip(' \n')
            tag.tail = tail

    # поставить пробел с краю, если надо
    for tag in root.iterdescendants():
        tag_with_next_text = None  # обнулить перед итерацией
        # если в теге нет текста и хвоста, пропускаем
        if (tag.text is None or not tag.text.strip(' \n')) and (tag.tail is None or not tag.tail.strip(' \n')):
            continue
        # если есть текст
        if tag.text is not None and tag.text.strip(' \n'):
            tag_with_next_text, next_attr = get_tag_with_next_text(root, tag, 'text')
            if tag_with_next_text is not None:
                next_text = getattr(tag_with_next_text, next_attr)
                this_text, next_text = fix_spaces_in_neighbour_texts(tag.text, next_text, tag, tag_with_next_text,
                                                                     'text', next_attr)
                setattr(tag, 'text', this_text)
                setattr(tag_with_next_text, next_attr, next_text)
        # если есть хвост
        if tag.tail is not None and tag.tail.strip(' \n'):
            tag_with_next_text, next_attr = get_tag_with_next_text(root, tag, 'tail')
            if tag_with_next_text is not None:
                next_text = getattr(tag_with_next_text, next_attr)
                this_text, next_text = fix_spaces_in_neighbour_texts(tag.tail, next_text, tag, tag_with_next_text,
                                                                     'tail', next_attr)
                setattr(tag, 'tail', this_text)
                setattr(tag_with_next_text, next_attr, next_text)

        # поставить пробел в хвосте choice, если надо
        if (tag.tag.replace(f'{{{XMLNS}}}', '') == 'choice' and tag.tail is not None and tag.tail.strip(' \n')) \
                or (tag.get('class') == 'unclear' and tag.tail is not None and tag.tail.strip(' \n')):
            if re.search(r'^[\w\d—*+=‹†×|§“˂(№\[”«]', tag.tail[0]) is not None or tag.tail.startswith('&lt'):
                tag.tail = f' {tag.tail}'

        # убрать пробел внутри тега номера сноски
        if tag.get('data-type') == 'snoska':
            tag.text = tag.text.strip()


def fix_spaces_in_neighbour_texts(left_text: str, right_text: str,
                                  left_tag=None, right_tag=None,
                                  left_attr=None, right_attr=None) -> tuple[str, str]:
    if (re.search(r'^[\w\d—*+=‹†×|§“˂(№\[”«]', right_text) is not None) \
            and (right_tag.get('data-type') != 'snoska') \
            and not (left_text.rstrip(' ')[-1] == '['):
        if (
                (left_tag.tag.replace(f'{{{XMLNS}}}', '') == 'name' and left_attr == 'text')
                or (left_tag.tag.replace(f'{{{XMLNS}}}', '') == 'span' and left_tag.get('class') == 'del' and
                    left_attr == 'text')
        ):
            # иначе выделяется на фронте лишний пробел
            right_text = f' {right_text}'
        else:
            left_text = f'{left_text} '
    return left_text, right_text


def main():
    uuids = get_all_uuids(REPO_TEXTS_PATH)
    wrongs = 0
    rare_words_ids = get_ids_from_catalogue(DICTIONARY_PATH, r'<word xml:id="(.*?)">')
    person_ids = get_ids_from_catalogue(PERSON_LIST_PATH, r'<person id="(.*?)">')
    taxonomy, new_taxonomy = txnm.get_taxonomy_as_dict(TAXONOMY_PATH), txnm.get_taxonomy_as_dict(NEW_TAXONOMY_PATH)

    for path, _, files in os.walk(REPO_TEXTS_PATH):
        for filename in tqdm(files):
            if not filename.endswith('.xml'):
                continue
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())

            add_uuids_to_existing_p_and_l(root, uuids)
            fix_roman_digits_in_page_range(root)
            change_epigraphs(root)
            delete_old_orthography(root)
            remove_tag_if_id_not_in_catalogue(root, rare_words_ids, 'ref', '@target="slovar"', 'id')
            remove_tag_if_id_not_in_catalogue(root, person_ids, 'name', '@type="person"', 'ref')
            wrap_unwrapped_tags_in_p_tag(root, uuids)
            change_tags(root)
            change_catrefs_to_catrefs_front(root, taxonomy, new_taxonomy)
            change_taxonomy_path(root)
            replace_self_closing_tags(root)
            fill_empty_sic_with_asterisks(root)
            remove_spaces_in_root(root)  # inside text/tail (not edges)
            fix_spaces_in_root(root)
            wrongs += check_paragraphs(root)

            etree.indent(root)
            text = etree.tostring(root, encoding='unicode')
            text = f"<?xml version='1.0' encoding='UTF-8'?>\n{text}"

            # check that xml is valid
            etree.fromstring(text.encode())

            Path(RESULT_PATH, Path(path).name, filename).write_text(text)
    print('files with wrong paragraphs: ', wrongs)  # should be zero


if __name__ == '__main__':
    main()
