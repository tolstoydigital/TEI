from copy import deepcopy
import os
from pathlib import Path
from uuid import uuid4

from lxml import etree


"""Надо подставить путь то репозитория"""
REPO_PATH = ...  # {подставить свое}/TEI
REPO_TEXTS_PATH = Path(REPO_PATH, 'texts')
RESULT_PATH = Path(REPO_PATH, 'texts_front')

XMLNS = 'http://www.tei-c.org/ns/1.0'


def is_descendant_of_p(tag: etree._Element) -> bool:
    for parent in tag.iterancestors():
        if parent.tag.replace(f'{{{XMLNS}}}', '') == 'p':
            return True
    return False


def get_all_p_uuids(path: Path) -> set[str]:
    ids = set()
    for path, dirs, files in os.walk(path):
        for filename in files:
            if not filename.endswith('.xml'):
                continue
            print(filename)
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())
            paragraphs = root.xpath('//ns:p', namespaces={'ns': f'{XMLNS}'})
            for p in paragraphs:
                try:
                    ids.add(p.attrib['id'])
                except KeyError:
                    continue
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
    new_p.tail = f'\n{"  "*indentation_level}'

    parent_tag.remove(tag)


def wrap_unwrapped_tags_in_p_tag(root: etree._Element, uuids: set[str]) -> None:
    body_tag = root.xpath('//ns:body', namespaces={'ns': f'{XMLNS}'})[0]
    for tag in body_tag.iterdescendants():
        # print(tag.tag.replace(f'{{{XMLNS}}}', ''))
        if tag.tag.replace(f'{{{XMLNS}}}', '') in ['p', 'l', 'lg', 'comments', 'div']:
            continue
        if tag.getparent() is body_tag and tag.tag.replace(f'{{{XMLNS}}}', '') == 'div':
            continue
        if not is_descendant_of_p(tag):
            wrap_tag_in_p(tag, uuids, root)


def fix_existing_p(root: etree._Element, uuids: set[str]) -> None:
    """добавить uuid где не было"""
    ps = root.xpath('//ns:p', namespaces={'ns': f'{XMLNS}'})
    for p in ps:
        if 'id' not in p.attrib:
            p.set('id', generate_new_uuid(uuids))


def delete_old_orthography(root: etree._Element) -> None:
    """тут хрень с индентацией и новыми строками, разобраться"""
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


def change_tags(root):
    """тоже хрень с интендацией"""
    for tag_name in ['opener', 'dateline', 'unclear', 'del', 'gap', 'add']:
        for tag in root.xpath(f'//ns:{tag_name}', namespaces={'ns': f'{XMLNS}'}):
            tag.tag = 'span'
            tag.set('class', tag_name)

    comments_tags = root.xpath('//ns:comments', namespaces={'ns': f'{XMLNS}'})
    if comments_tags:
        comments_tag = comments_tags[0]
        comments_tags = []
        for tag in comments_tag:
            comments_tags.append(deepcopy(tag))
        comments_parent = comments_tag.getparent()
        for tag in comments_tags:
            new_p = etree.Element('p', **tag.attrib, index='false')
            new_p.append(tag)
            for key in tag.attrib:
                tag.attrib.pop(key)
            tag.tag = 'span'
            tag.set('class', 'comments')
            comments_parent.insert(comments_parent.index(comments_tag), new_p)

        comments_parent.remove(comments_tag)

    rare_words_tags = root.xpath('//ns:ref[@target="slovar"]', namespaces={'ns': f'{XMLNS}'})
    for tag in rare_words_tags:
        tag.tag = 'a'
        tag.set('href', '../../reference/Dictionary.xml')
        word_id = tag.attrib.pop('id')
        tag.set('data-type', 'topic_slovar')
        tag.set('data-id', word_id)
        tag.attrib.pop('target')


def main():
    uuids = get_all_p_uuids(REPO_TEXTS_PATH)
    for path, _, files in os.walk(REPO_TEXTS_PATH):
        for filename in files:
            if not filename.endswith('.xml'):
                continue
            with open(Path(path, filename), 'rb') as file:
                root = etree.fromstring(file.read())

            fix_existing_p(root, uuids)
            wrap_unwrapped_tags_in_p_tag(root, uuids)
            delete_old_orthography(root)
            change_tags(root)

            text = etree.tostring(root, encoding='unicode')
            etree.fromstring(text.encode())  # для проверки, что не ломается
            Path(RESULT_PATH, Path(path).name, filename).write_text(text)


if __name__ == '__main__':
    main()
