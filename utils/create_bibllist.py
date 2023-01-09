from copy import deepcopy
import math
from pathlib import Path
import re

from lxml import etree
import pandas as pd

import utils as ut
import taxonomy_front_utils as txnm


FILES_PATH = ut.REPO_PATH
WORKS_SHEET_PATH = Path('reference/works.xlsx')
COMMENTS_SHEET_PATH = Path('reference/letters.xlsx')
ANNOTATIONS_SHEETS_PATH = Path('reference/annotations.xlsx')
CATALOGUE_PATH = Path('headers/templates/header_catalogue_v3.xml')
RESULT_PATH = Path('reference', 'catalogue.xml')
TAXONOMY_PATH = Path(ut.REPO_PATH, 'reference', 'taxonomy.xml')
NEW_TAXONOMY_PATH = Path(ut.REPO_PATH, 'reference', 'taxonomy_front.xml')

CATEGORIES_ORDER = {
    'finished': 0,
    'not_finished': 1,
    'editions': 2
}

MULTIVOLUME_WORKS = ['Vojna_i_mir', 'Anna_Karenina', 'Voskresenie', 'Na_kazhdyj_den']


def get_list_item(root: etree._Element, work_id: str) -> etree._Element | None:
    for item in root.xpath('//item'):
        ref_tag = item[0]
        if ref_tag.text == work_id:
            return item


def create_new_list_item(work_id: str, data: dict, taxonomies: list[dict]) -> etree._Element:
    item = etree.Element('item')
    ref_tag = etree.Element('ref')
    ref_tag.text = work_id
    item.append(ref_tag)
    title_tag = etree.Element('title')
    title_tag.text = data['title'].rstrip(' ')
    item.append(title_tag)
    item.append(data['date_tag'])

    old_ana = [i.strip('#') for i in data['catrefs'].values()]
    old_ana.append('main')
    new_ana = txnm.old_catrefs_to_new_catrefs(old_ana, taxonomies)
    new_ana = txnm.remove_vse_prosto_ana_for_bibllist(new_ana)
    new_ana.remove('main')
    taxonomy, new_taxonomy = taxonomies
    new_catrefs = {}
    for ana in new_ana:
        try:
            new_catrefs[taxonomy[ana]['target']] = ana
        except KeyError:
            new_catrefs[new_taxonomy[ana]['target']] = ana
    for target, ana in new_catrefs.items():
        item.append(etree.Element('catRef', ana=ana, target=target))

    note_annotation = etree.Element('note')
    note_annotation.text = data.get('annotation')
    note1 = etree.Element('note', {'type': 'entities_number_in_texts'})
    note2 = etree.Element('note', {'type': 'entities_number_in_comments'})
    item.append(note_annotation)
    item.append(note1)
    item.append(note2)

    for related_item, _, _, _ in data['related_items']:
        item.append(related_item)

    if 'comments' in data:
        for comment_data in data['comments']:
            comment_tag = etree.Element('relatedItem')
            ref_tag = etree.Element('ref', ana=f'#comments #{comment_data["category"]}')
            ref_tag.text = comment_data['file_id']
            comment_tag.append(ref_tag)
            title_tag = etree.Element('title', resp="volume_editor")
            title_tag.text = comment_data['title'].strip(' ')
            comment_tag.append(title_tag)

            # add bibliography
            bibl_tag = etree.Element('title', type='bibl')
            bibl_tag.text = comment_data['bibliography']
            comment_tag.append(bibl_tag)

            author = comment_data['author']
            if author is not None:
                author_tag = etree.Element('author')
                author_tag.text = author
                comment_tag.append(author_tag)
            item.append(comment_tag)

    if 'related_works' in data:
        for related_work in data['related_works']:
            item.append(related_work)
    return item


def get_file_data(data: dict, folder='works') -> dict:
    file_data = {}
    filename = data.get('названия файла')
    file_root = etree.fromstring(ut.read_xml(Path(ut.REPO_TEXTS_PATH, folder, filename), 'rb'))
    try:
        creation_tag = file_root.xpath('//ns:creation', namespaces={'ns': ut.xmlns_namespace})[0]
        date_tag = deepcopy(creation_tag[0])
        date_tag.set('type', 'action')
        file_data['date_tag'] = date_tag
    except IndexError:
        pass
    labels = [t.get('ana') for t in file_root.xpath('//ns:catRef', namespaces={'ns': ut.xmlns_namespace})
              if t.get('ana') != '#main']
    catrefs = {
        'sphere': file_root.xpath('//ns:catRef[@target="sphere"]', namespaces={'ns': ut.xmlns_namespace})[0].attrib.get('ana'),
        'genre': file_root.xpath('//ns:catRef[@target="genre"]', namespaces={'ns': ut.xmlns_namespace})[0].attrib.get('ana'),
        'published': file_root.xpath('//ns:catRef[@target="published"]', namespaces={'ns': ut.xmlns_namespace})[0].attrib.get('ana'),
    }
    try:
        catrefs['topic'] = file_root.xpath('//ns:catRef[@target="topic"]', namespaces={'ns': ut.xmlns_namespace})[0].attrib.get('ana')
    except IndexError:
        pass

    file_data['labels'] = labels
    file_data['catrefs'] = catrefs
    return file_data


def is_nan(value) -> bool:
    if any(
        [
            isinstance(value, str) and value == 'nan',
            isinstance(value, float) and math.isnan(value),
        ]
    ):
        return True
    return False


def create_related_item(row_data: dict, file_data: dict, taxonomy: list[dict]) -> etree._Element:
    related_item_tag = etree.Element('relatedItem')
    ref_tag = etree.Element('ref')
    ref_tag.text = row_data.get('id файлов')
    related_item_tag.append(ref_tag)

    title_tag = etree.Element('title')
    title = row_data.get('  название').rstrip(' ')
    if not is_nan(row_data.get('main')):
        title = row_data.get('НАЗВАНИЕ СЕМЬИ').rstrip(' ')
    title_tag.text = title
    if not is_nan(row_data['название дано редакторами (сверять по списку 91 тома)']):
        title_tag.set('resp', 'volume_editor')
    related_item_tag.append(title_tag)

    title_appendix = row_data.get('дополнение к названию')
    if not is_nan(title_appendix):
        title_tag.set('type', 'main')
        subtitle_tag = etree.Element('title', type='sub')
        if not is_nan((row_data['подзагловок дан редактором'])):
            subtitle_tag.set('resp', 'volume_editor')
        subtitle_tag.text = title_appendix.rstrip(' ')
        related_item_tag.append(subtitle_tag)

    # add bibliography tag
    bibliography = row_data.get('БИБЛ = итог + страницы = cured')
    bibl_tag = etree.Element('title', type='bibl')
    if bibliography:
        related_item_tag.append(bibl_tag)
        bibl_tag.text = bibliography

    if file_data['is_main']:
        date_tag = deepcopy(file_data['date_tag'])
        if 'when' in date_tag.attrib:
            date_tag.text = date_tag.attrib['when']
        elif 'from' in date_tag.attrib:
            date_tag.text = f'{date_tag.attrib["from"]}-{date_tag.attrib["to"]}'
        else:
            pass
        related_item_tag.append(date_tag)

    if file_data['is_main'] or row_data.get('ID связанного произвдения)') in MULTIVOLUME_WORKS:
        volume_tag = etree.Element('volume')
        volume = str(int(row_data.get('volume')))
        volume_tag.text = volume
        related_item_tag.append(volume_tag)

    ana_value = ' '.join(f'{v}' for v in file_data['labels'])
    if file_data['is_main']:
        ana_value = f'#main {ana_value}'
    ana_value = set_ana_value_from_new_taxonomy([i.strip('#') for i in ana_value.split()], taxonomy)
    ref_tag.set('ana', ana_value)
    return related_item_tag


def set_ana_value_from_new_taxonomy(catrefs: list, taxonomies: list[dict]) -> str:
    new_catrefs = txnm.old_catrefs_to_new_catrefs(catrefs, taxonomies)
    return ' '.join([f'#{i}' for i in new_catrefs])


def get_volume_and_pages_range_from_text_id(text_id: str) -> tuple[int, int, int]:
    parts = text_id.split('_')
    volume, left, right = int(parts[0].strip('v')), int(parts[1]), int(parts[2])
    return volume, left, right


def is_date_intersection(comment_date: str, date_tag: etree._Element) -> bool:
    if isinstance(comment_date, float) or isinstance(comment_date, int):
        comment_date = str(int(comment_date))
    comment_dates = [int(date.strip(' ')) for date in comment_date.split(',')]
    work_dates = []
    if 'when' in date_tag.attrib:
        when = date_tag.get('when')
        work_dates.append(int(when))
    if 'from' in date_tag.attrib and 'to' in date_tag.attrib:
        _from = date_tag.get('from')
        to = date_tag.get('to')
        work_dates.extend(range(int(_from), int(to) + 1))
    if not date_tag.attrib:
        dates = date_tag.text
        dates = dates.strip('.?г')
        dates = dates.replace('и', ',')
        dates = dates.replace('-', '—')
        dates = dates.replace('–', '—')
        dates = [d.strip() for d in dates.split(',')]
        for date in dates:
            if date.isnumeric():
                work_dates.append(date)
            elif '—' in date:
                _from, to = date.split('—')
                work_dates.extend(range(int(_from), int(to)))
    for date in comment_dates:
        if date in work_dates:
            return True
    return False


def add_comments_to_bibllist(sheet_path: Path, bibllist_items: dict) -> None:
    df = pd.read_excel(sheet_path, sheet_name='Comments')
    df = df.dropna(subset=['ID файла'])
    for row in df.iterrows():
        row_data = row[1]
        category = row_data.get('категория комментария')
        if is_nan(category) or 'comments_works' not in category:
            continue
        work_ids = row_data.get('ID связанного произведения (семьи)')
        if is_nan(work_ids):
            continue
        work_ids = [w_id.strip(' ') for w_id in work_ids.split(', ')]
        for work_id in work_ids:
            file_id = row_data.get('ID файла')
            title = row_data.get('Имя файла для карточки и справочника')
            author = row_data.get('автор комментария')
            bibliography = row_data.get('БИБЛ = ИТОГ')
            if is_nan(author):
                author = None
            data = {
                'file_id': file_id,
                'title': title,
                'author': author,
                'category': category,
                'bibliography': bibliography
            }
            try:
                bibllist_items[work_id]['comments'].append(data)
            except KeyError:
                try:
                    bibllist_items[work_id]['comments'] = [data]
                except KeyError:  # Novaja_Azbuka
                    print(work_id)
                    pass

    for row in df.iterrows():
        row_data = row[1]
        category = row_data.get('категория комментария')
        if is_nan(category) and 'comments_works' in category:
            continue
        comment_date = row_data.get('год для произведения')
        if is_nan(comment_date):
            continue

        file_id = row_data.get('ID файла')
        title = row_data.get('Имя файла для карточки и справочника')
        author = row_data.get('автор комментария')
        bibliography = row_data.get('БИБЛ = ИТОГ')
        if is_nan(author):
            author = None
        data = {
            'file_id': file_id,
            'title': title,
            'author': author,
            'category': category,
            'bibliography': bibliography
        }

        for work_id, family in bibllist_items.items():
            try:  # Ошибки там, где нет крестиков
                date_tag = family['date_tag']
            except KeyError:
                print(work_id)
                continue
            if is_date_intersection(comment_date, date_tag):
                try:
                    bibllist_items[work_id]['comments'].append(data)
                except KeyError:
                    try:
                        bibllist_items[work_id]['comments'] = [data]
                    except KeyError:
                        print(work_id)
                        pass


def create_related_works(row_data: dict, work_id: str) -> list[etree.Element]:
    work_id_raw = row_data.get('связанные произведения')
    work_ids = [w_id.strip(' ') for w_id in work_id_raw.split(',')]
    related_works = []
    for w_id in work_ids:
        related_item = etree.Element('relatedItem')
        ref = etree.Element('ref', ana='related_works')
        ref.text = w_id
        related_item.append(ref)
        related_works.append(related_item)
    return related_works


def fix_unconventional_dates(root: etree._Element) -> None:
    date_tags = root.xpath('//ns:date', namespaces={'ns': ut.xmlns_namespace})
    for tag in date_tags:
        text = tag.text
        if text is not None:
            if re.search(r'^\s*\d{4}\s*$', text):
                continue
            if re.search(r'^\s*\d{4}-\d{4}\s*$', text):
                continue
            years = [i.group() for i in re.finditer(r'\d{4}', tag.text)]
            years.sort(key=int)
            if len(years) == 1:
                tag.text = years[0]
                tag.set('when', years[0])
            else:
                first_date, last_date = years[0], years[-1]
                tag.text = f'{first_date}-{last_date}'
                tag.set('from', first_date)
                tag.set('to', last_date)


def main():
    root = etree.fromstring(ut.read_xml(CATALOGUE_PATH, 'rb'))
    list_tag = root.xpath('//ns:list', namespaces={'ns': ut.xmlns_namespace})[0]
    df = pd.read_excel(WORKS_SHEET_PATH, sheet_name='Works', header=1)
    df = df.dropna(subset=['volume'])
    annotations_df = pd.read_excel(ANNOTATIONS_SHEETS_PATH, sheet_name='Произведения')
    bibllist_items = {}
    taxonomy = txnm.get_taxonomy_as_dict(TAXONOMY_PATH)
    new_taxonomy = txnm.get_taxonomy_as_dict(NEW_TAXONOMY_PATH)
    for row in df.iterrows():
        row_data = row[1]
        filename = row_data.get("названия файла")
        if is_nan(filename) or filename == 'названия файла':
            continue

        work_id_raw = row_data.get('ID связанного произвдения)')

        work_ids = [w_id.strip(' ') for w_id in work_id_raw.split(',')]
        for work_id_index, work_id in enumerate(work_ids):
            #  Фекла сказала выкинуть этот текст
            if work_id == 'Chastnoe_pismo_roditeljam_doktoram_i_nachalnikam_shkol_Eliza_B_Bernz':
                continue

            text_id = row_data.get('id файлов')
            file_data = get_file_data(row_data, 'works')
            is_main_text = not is_nan(row_data.get('  карточка (изначально - 91-том - указатель)'))  # Если поле не пустое
            file_data['is_main'] = is_main_text
            related_item = create_related_item(row_data, file_data, [taxonomy, new_taxonomy])
            order = CATEGORIES_ORDER[row_data.get('finished / not finished new')]
            sorting_value = row_data.get('  название').strip(' ')  # Для сортировки семей по алфавиту

            related_work_id = row_data.get('связанные произведения')
            try:
                if not is_nan(related_work_id):
                    bibllist_items[work_id]['related_works'] = create_related_works(row_data, work_id)
                    print(work_id, related_work_id)
            except KeyError:
                bibllist_items[work_id] = {}
                if not is_nan(related_work_id):
                    bibllist_items[work_id]['related_works'] = create_related_works(row_data, work_id)
                    print(work_id, related_work_id)

            try:
                bibllist_items[work_id]['related_items'].append((related_item, is_main_text, text_id, order))
            except KeyError:
                if work_id not in bibllist_items:
                    bibllist_items[work_id] = {}
                bibllist_items[work_id]['related_items'] = [(related_item, is_main_text, text_id, order)]

            title = row_data.get('BI = OLD = точки  и main')
            if (is_main_text
            ):
                bibllist_items[work_id]['title'] = title
                bibllist_items[work_id]['date_tag'] = file_data['date_tag']
                bibllist_items[work_id]['sorting_value'] = sorting_value
                bibllist_items[work_id]['catrefs'] = file_data['catrefs']
                annotation = annotations_df.loc[annotations_df['ID - технич информация'] == work_id].to_dict('records')[0]['ОПИСАНИЯ-ЗАГЛУШКИ']
                if not is_nan(annotation):
                    bibllist_items[work_id]['annotation'] = annotation

    # Добавляем к семьям комментарии
    add_comments_to_bibllist(COMMENTS_SHEET_PATH, bibllist_items)

    # Сортируем внутри семьи: сначала главный текст, потом по порядку следования в томе
    for _, family in bibllist_items.items():
        family['related_items'].sort(
            key=lambda x: (-x[1], x[3], get_volume_and_pages_range_from_text_id(x[2]))
        )

    # Сортируем семьи по алфавиту
    families = []
    for w_id, family in bibllist_items.items():
        try:
            families.append((w_id, family['sorting_value']))
        except KeyError:  # Если нет крестика в таблице, Фекла поправит
            continue
    families.sort(key=lambda x: x[1])

    # Cоздаем айтемы-семьи (теги)
    for work_id, _ in families:
        item = create_new_list_item(work_id, bibllist_items[work_id], [taxonomy, new_taxonomy])
        list_tag.append(item)

    fix_unconventional_dates(root)
    etree.indent(list_tag, space='    ', level=2)
    text = etree.tostring(root, encoding='unicode')
    RESULT_PATH.write_text(text)


if __name__ == '__main__':
    ut.change_to_project_directory()
    main()
