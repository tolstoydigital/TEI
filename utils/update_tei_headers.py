from datetime import datetime
import os
from pathlib import Path
import re

from lxml import etree
import numpy as np
import pandas as pd

import utils as ut

BASE_PATH = ut.REPO_PATH
SOURCE_PATH = Path(BASE_PATH, 'texts')
RESULT_PATH = Path(BASE_PATH, 'texts')

WORKS_SHEET = Path('reference/works.xlsx')  # надо скачать
LETTERS_SHEET = Path('reference/letters.xlsx')  # надо скачать

AZBUKA_HEADER = Path(BASE_PATH, 'headers', 'header_azbuka.xml')
COMMENTS_HEADER = Path(BASE_PATH, 'headers', 'header_comments.xml')
DIARIES_HEADER = Path(BASE_PATH, 'headers', 'header_diaries.xml')
KRUG_HEADER = Path(BASE_PATH, 'headers', 'header_krug_chtenija.xml')
LETTERS_HEADER = Path(BASE_PATH, 'headers', 'header_letters.xml')
NOTES_HEADER = Path(BASE_PATH, 'headers', 'header_notes.xml')
WORKS_HEADER = Path(BASE_PATH, 'headers', 'header_works.xml')

XMLNS = 'http://www.tei-c.org/ns/1.0'


def prepare_catrefs_for_comments(categories: str) -> str:
    cat_refs = []
    template_cat_ref = '                <catRef ana="#{category}" target="comments_type"/>'
    for category in categories.split(','):
        cat_refs.append(template_cat_ref.format(category=category.strip()))
    return '\n'.join(cat_refs)


def process_comments(row: dict, data: dict) -> None:
    data['comments_type_E'] = prepare_catrefs_for_comments(row['категория комментария'])
    title = data['title90_H']
    title = title.replace('<', '&lt;')
    title = title.replace('>', '&gt;')
    data['title90_H'] = title


def process_diaries(row: dict, data: dict) -> None:
    first_date = row['first_date']
    last_date = row['last_date']
    if isinstance(first_date, datetime):
        first_date = first_date.strftime('%Y-%m-%d')
    if isinstance(last_date, datetime):
        last_date = last_date.strftime('%Y-%m-%d')
    if row['Техническая колонка'] == '1':
        date_H = f'<date when="{first_date}"/>'
    else:
        date_H = f'<date from="{first_date}" to="{last_date}"/>'
    if ':' in first_date:
        not_before, not_after = first_date.split(':')
        date_H = f'<date notBefore="{not_before}" notAfter="{not_after}"/>'
    data['date_H'] = date_H


def process_krug(row: dict, data: dict) -> None:
    months = {
        '1': 'января',
        '2': 'февраля',
        '3': 'марта',
        '4': 'апреля',
        '5': 'мая',
        '6': 'июня',
        '7': 'июля',
        '8': 'августа',
        '9': 'сентября',
        '10': 'октября',
        '11': 'ноября',
        '12': 'декабря',
    }
    subtitle = data['subtitle_I']
    if isinstance(subtitle, datetime):
        day = str(subtitle.day)
        month = months[str(subtitle.month)]
        data['subtitle_I'] = f'{day} {month}'


def process_letters(row: dict, data: dict):
    # make title
    title = f'{row["адресат"]} {row["humane_readable_dates"]}'
    if row["раздел 90-томника"] == 'Письма':
        title = f'Письмо {title}'
    title = title.replace('&', '&amp;')
    data['title_V'] = title

    #
    data['first_publ_J'] = 'Публикуется впервые' if isinstance(row['звездочка (опубликовано впервые)'], str) else ''

    # date
    data['date_OPQ'] = f'<date when="{row["when"]}"/>' if isinstance(
        row["when"], str) else f'<date notBefore="{row["notBefore"]}" notAfter="{row["notAfter"]}"/>'

    # addressees
    if not isinstance(row["Адресат - берем из xml  (берем из колонки H из адресатов)"], str):
        data['pers_name_TU'] = '<persName/>'
    elif not isinstance(row["ID Адресата - вытаскиваем из таблицы Бори"], str):
        data['pers_name_TU'] = '<persName/>'
    else:
        names = row["Адресат - берем из xml  (берем из колонки H из адресатов)"].split('|')
        names_ids = row["ID Адресата - вытаскиваем из таблицы Бори"].split('|')
        pairs = [(n, n_id) for n, n_id in zip(names, names_ids)]
        tags = []
        for name, name_id in pairs:
            tags.append(f'<persName ref="{name_id}">{name}</persName>')
        indent = '\n' + ' ' * 20
        data['pers_name_TU'] = indent.join(tags)

    # language
    data['language_Z'] = 'ru'  # row["язык"]

    #
    data['sent_E'] = 'sent' if row['статус (отпр, неотпр, черн)'] is None else 'not_sent'


def process_notes(row: dict, data: dict) -> None:
    # date_H
    if row['Техническая колонка'] == '1':
        date_H = f'<date when="{row["date"]}"/>'
    elif row['Техническая колонка'] == '0':
        date_from, date_to = row['date'].split('–')
        date_H = f'<date from="{date_from}" to="{date_to}"/>'
    data['date_H'] = date_H


def process_works(row: dict, data: dict) -> None:
    # language
    language = row['language']
    data['language_K'] = 'ru' if language is None else ut.convert_language_to_iso(language)

    for column, value in data.items():
        try:
            data[column] = value.strip(' ')
        except AttributeError:
            pass

    # main/ver
    if data['main_AH'] is not None and data['main_AH'].strip():
        data['main_AH'] = 'main'
    elif data['finished_D'] != 'editions':
        data['main_AH'] = 'ver'

    # drugoe
    if data['genre_drugoe_AG'] is not None and data['genre_drugoe_AG'].strip():
        data['genre_drugoe_AG'] = 'drugoe'


FOLDERS_DATA = {
    'azbuka': {
        'sheetname': 'Азбука',
        'column_names': {
            'volume': 'volume',
            'id': 'ID (Лева)',
            'title_K': 'name',
            'subtitle_M': 'дополнение к названию',
            'title_as_in_90_B': 'название как в 90 томнике',
            'title_level_s_F': 'book',
            'start_page_D': 'start page',
            'end_page_E': 'end page',
            'date_N': 'Год создания (Тим)',
            'genre_Q': 'жанр',
            'sphere_R': 'fiction/nonfiction',
            'finished_S': 'finished/not finished',
            'published_U': 'published TEI',
            'topic_V': 'topic TEI',
            'included_H': 'included',
            'bibliography': 'БИБЛ = итог'
        }
    },
    'comments': {
        'sheetname': 'Comments',
        'special_func': process_comments,
        'column_names': {
            'id': 'ID файла',
            'title_G': 'Имя файла для карточки и справочника',
            'author_L': 'автор комментария',
            'title90_H': 'имя из 90-томника',
            'volume_C': 'volume',
            'date_D': 'Год Тома',
            'start_page_I': 'стр начала',
            'end_page_J': 'стр конца',
            'bibliography': 'БИБЛ = ИТОГ'
        }
    },
    'diaries': {
        'sheetname': 'New MAIN Дневники (копия)',
        'special_func': process_diaries,
        'column_names': {
            'volume': 'volumes',
            'id': 'id',
            'title_N': 'название для сайта',
            'title_T': 'humane readable dates',
            'title_M': 'название в 90-томнике- Фекла',
            'date_L': 'Год тома',
            'start_page_E': 'first_page',
            'end_page_F': 'last_page',
            'bibliography': 'БИБЛ = итог'
        }
    },
    'krug_chtenija': {
        'sheetname': 'Круг чтения',
        'special_func': process_krug,
        'column_names': {
            'volume': 'Том',
            'id': 'id файла',
            'title_G': 'название',
            'subtitle_I': 'дополнение в названию',
            'title_as_in_90_P': 'название как в 90-томнике',
            'start_page_D': 'start page',
            'end_page_E': 'end page',
            'date_O': 'Год создания (Тим)',
            'sphere_S': 'fiction/nonfiction - Фекла',
            'finished_T': 'finished/not finished - Лева',
            'published_U': 'published/not published - Лева',
            'author_K': 'авторство Толстого',
            'bibliography': 'БИБЛ = итог'
        }
    },
    'letters': {
        'sheetname': '59-90 оглав MAIN',
        'special_func': process_letters,
        'column_names': {
            'id': 'ID файла',
            'volume_B': 'том',
            'date_pub_X': 'ГОД ТОМА',
            'start_page_AA': 'start page',
            'end_page_AB': 'end page',
            'place_U': 'Место отправления берем из XML',
            'letter_number_C': '№ номер письма',
            'bibliography': 'БИБЛ = ИТОГ'
        }
    },
    'notes': {
        'sheetname': 'Записные книжки',
        'special_func': process_notes,
        'column_names': {
            'id': 'id файла new',
            'volume': 'volume',
            'title_N': '  название',
            'title_J': 'имя из 90-томника',
            'date_T': 'Год тома',
            'start_page_E': 'стр начала',
            'end_page_F': 'стр конца',
            'bibliography': 'БИБЛ = итог'
        }
    },
    'works': {
        'sheetname': 'Works',
        'special_func': process_works,
        'column_names': {
            'volume_B': 'volume',
            'id': 'id файлов',
            'digital_title_O': 'имя из 90-томника',
            'title_Y': '  название',
            'subtitle_AA': 'дополнение к названию',
            'start_page_P': 'стр начала',
            'end_page_Q': 'стр конца',
            'date_L': 'date',
            'sphere_E': 'fiction/nonfiction',
            'genre_AQ': 'genre TEI',
            'topic_AR': 'topic TEI arts',
            'topic_AS': 'topic2 TEI poiit',
            'topic_AT': 'topic3 TEI soc',
            'topic_AU': 'topic 4 pedagog',
            'topic_AV': 'topic 5 autobio',
            'topic_H': 'topic (nonfiction)',
            'finished_D': 'finished / not finished new',
            'published_AY': '(not) published SIMPLE ',
            'published_date_AL': 'Year of  volume',
            'main_AH': '  MAIN',
            'genre_drugoe_AG': 'Другое (жанр)',
            'bibliography': 'БИБЛ = итог + страницы = cured'
        }
    },
}


def normalize_row(row: dict) -> dict:
    for column, value in row.items():
        if isinstance(value, float) or isinstance(value, int):
            row[column] = str(int(value))
    return row


def fix_date_tag(root: etree.Element) -> None:
    header_tag = root.xpath('//ns:teiHeader', namespaces={'ns': XMLNS})[0]
    date_tags = [tag for tag in root.xpath('//ns:date', namespaces={'ns': XMLNS})
                 if tag in header_tag.iterdescendants()]
    for tag in date_tags:
        if not tag.text:
            continue
        single_date_match = re.search(r'^\s*(\d+)\s*$', tag.text)
        range_match = re.search(r'^\s*(\d+)(-|–|—|,\s*)(\d+)\s*$', tag.text)
        if single_date_match is not None:
            tag.set('when', single_date_match.group(1))
            tag.text = None
        elif range_match is not None:
            tag.set('from', range_match.group(1))
            tag.set('to', range_match.group(3))
            tag.text = None


def remove_empty_catref(root: etree.Element) -> None:
    cat_refs = root.xpath(f'//ns:catRef', namespaces={'ns': XMLNS})
    for tag in cat_refs:
        value = tag.get('ana')
        if value.strip('#') == 'None':
            tag.getparent().remove(tag)


def remove_header_tags_with_none_text(root: etree.Element) -> None:
    """If tag has text 'None' (not {is None}!), remove the tag."""
    header_tag = root.xpath('//ns:teiHeader', namespaces={'ns': XMLNS})[0]
    for tag in header_tag.iterdescendants():
        if tag.text is not None and tag.text.strip() == 'None':
            tag.getparent().remove(tag)


def indent_header_tag(root: etree.Element) -> None:
    header_tag = root.xpath('//ns:teiHeader', namespaces={'ns': XMLNS})[0]
    etree.indent(header_tag)


def restore_p_uuid_in_header(root: etree.Element, path_to_folder: Path, filename: str) -> None:
    old_root = etree.fromstring(ut.read_xml(Path(SOURCE_PATH, Path(path_to_folder).name, filename), 'rb'))
    old_p_tag = old_root.xpath('//ns:availability//ns:p', namespaces={'ns': XMLNS})[0]
    old_id = old_p_tag.attrib['id']
    p_tag = root.xpath('//ns:availability//ns:p', namespaces={'ns': XMLNS})[0]
    p_tag.set('id', old_id)


def add_resp_to_title(root: etree.Element, row: dict) -> None:
    title_big = root.xpath('//ns:title[@xml:id]', namespaces={'ns': XMLNS})[0]
    title_main = root.xpath('//ns:title[@type="main"]', namespaces={'ns': XMLNS})[0]
    if row['название дано редакторами (сверять по списку 91 тома)'] is not None and \
            row['название дано редакторами (сверять по списку 91 тома)'].strip():
        title_main.set('resp', 'volume_editor')
        title_big.set('resp', 'volume_editor')
    try:
        title_sub = root.xpath('//ns:title[@type="sub"]', namespaces={'ns': XMLNS})[0]
        if row['подзагловок дан редактором'] is not None and row['подзагловок дан редактором'].strip():
            title_sub.set('resp', 'volume_editor')
    except IndexError:
        pass


def fix_special_entities(text: str) -> str:
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('&', '&amp;')
    return text


def add_old_orthographyh_tag(root: etree.Element) -> None:
    # Если есть orig, то добавляем
    orig_tags = root.xpath('//ns:orig', namespaces={'ns': XMLNS})
    if not orig_tags:
        return
    try:
        lang_tag = root.xpath('//ns:langUsage', namespaces={'ns': XMLNS})[0]
    except IndexError:
        text_class_tag = root.xpath('//ns:textClass', namespaces={'ns': XMLNS})[0]
        lang_tag = etree.Element('langUsage')
        text_class_tag.addprevious(lang_tag)
    old_orthography_tag = etree.Element('language', ident='ru-petr1708')
    old_orthography_tag.text = None
    lang_tag.append(old_orthography_tag)
    etree.indent(lang_tag)


def update_folder(path_to_folder: Path, path_to_sheet: Path, path_to_header_template: Path) -> None:
    foldername = path_to_folder.name
    df = pd.read_excel(path_to_sheet, sheet_name=FOLDERS_DATA[foldername]['sheetname'],
                       header=1 if foldername == 'works' else 0)
    df = df.replace(np.nan, None)
    # pd.set_option('display.max_columns', 500)
    # pd.set_option('display.width', 1000)

    column_names = FOLDERS_DATA[foldername]['column_names']
    template = path_to_header_template.read_text()
    for filename in os.listdir(path_to_folder):
        file_id = filename.replace('.xml', '')
        if file_id == 'test-front_new':
            continue
        row = df.loc[df[column_names['id']] == file_id].to_dict('records')[0]
        row = normalize_row(row)
        data = {mapping: row[column] for mapping, column in column_names.items()}
        data['bibliography'] = fix_special_entities(data['bibliography'])
        try:
            FOLDERS_DATA[foldername]['special_func'](row, data)
        except KeyError as e:
            pass

        root = etree.fromstring(ut.read_xml(f'{path_to_folder}/{filename}', 'rb'))
        text_tag = root.xpath('//ns:text', namespaces={'ns': XMLNS})[0]
        text = etree.tostring(text_tag, encoding='unicode').strip('\n')
        data['text'] = text
        result_text = template.format(**data)

        root = etree.fromstring(result_text.encode())

        fix_date_tag(root)
        remove_empty_catref(root)
        remove_header_tags_with_none_text(root)
        if foldername == 'works':
            add_resp_to_title(root, row)
        restore_p_uuid_in_header(root, path_to_folder, filename)
        add_old_orthographyh_tag(root)
        result_text = etree.tostring(root, encoding='unicode').strip('\n')
        result_text = f"<?xml version='1.0' encoding='UTF-8'?>\n{result_text}"

        # check that xml is valid
        etree.fromstring(result_text.encode())

        Path(RESULT_PATH, foldername, filename).write_text(result_text)


def main():
    update_folder(Path(SOURCE_PATH, 'azbuka'), WORKS_SHEET, AZBUKA_HEADER)
    update_folder(Path(SOURCE_PATH, 'comments'), LETTERS_SHEET, COMMENTS_HEADER)
    update_folder(Path(SOURCE_PATH, 'diaries'), WORKS_SHEET, DIARIES_HEADER)
    update_folder(Path(SOURCE_PATH, 'krug_chtenija'), WORKS_SHEET, KRUG_HEADER)
    update_folder(Path(SOURCE_PATH, 'letters'), LETTERS_SHEET, LETTERS_HEADER)
    update_folder(Path(SOURCE_PATH, 'notes'), WORKS_SHEET, NOTES_HEADER)
    update_folder(Path(SOURCE_PATH, 'works'), WORKS_SHEET, WORKS_HEADER)


if __name__ == '__main__':
    ut.change_to_project_directory()
    main()
