from datetime import datetime
import math
from pathlib import Path

from lxml import etree
import pandas as pd

import utils as ut


TEMPLATE_PATH = Path('reference', 'personList_template.xml')
RESULT_PATH = Path('reference', 'personList_result.xml')
SHEET_PATH = Path('reference', 'people.xlsx')
TAXONOMY_PATH = Path(ut.REPO_PATH, 'reference', 'taxonomy.xml')
IMAGES_PATH = Path(ut.REPO_PATH, 'images', 'illustrations')

TAXONOMY_ROOT = etree.fromstring(ut.read_xml(TAXONOMY_PATH, 'rb'))


def is_nan(value) -> bool:
    if any(
        [
            isinstance(value, str) and value == 'nan',
            isinstance(value, float) and math.isnan(value),
        ]
    ):
        return True
    return False


def create_persname_tag(row_data: dict) -> etree._Element:
    persname_tag = etree.Element('persName', type='main')
    wiki_id = row_data['Wikidata']
    if not is_nan(wiki_id):
        persname_tag.set('ref', wiki_id)
    full_name = row_data['Имя исправленное new'].strip('\n ')
    persname_tag.text = f"\n{' '*20}{full_name}\n{' '*20}"
    name = row_data['Имя']
    if not is_nan(name):
        name_tag = etree.Element('forename', sort='2')
        name_tag.text = name
        persname_tag.append(name_tag)
    patronym = row_data['Отчество']
    if not is_nan(patronym):
        patronym_tag = etree.Element('forename', sort='3', type='patronym')
        patronym_tag.text = patronym
        persname_tag.append(patronym_tag)
    surname = row_data['Фамилия']
    if not is_nan(surname):
        surname_tag = etree.Element('forename', sort='1')
        surname_tag.text = surname
        persname_tag.append(surname_tag)
    return persname_tag


def create_relations(row_data: dict, df) -> list[etree._Element]:
    raw = row_data['refered person id']
    if is_nan(raw):
        return []
    relations = []
    people = [i.strip(' ').split(' ', maxsplit=1) for i in raw.split(',')]
    for ref_id, _ in people:
        name_data = df.loc[df['ID по указателю'] == float(ref_id)].to_dict('records')[0]
        name = name_data['Имя исправленное new']
        relation = etree.Element('relation', ref=ref_id)
        relation.text = name
        relations.append(relation)
    return relations


def create_catrefs(row_data: dict) -> list[etree._Element]:
    catrefs = []

    time = row_data['время']
    if not is_nan(time) and not time[0].isnumeric():
        cat_desc = TAXONOMY_ROOT.xpath(f'//catDesc[text()="{time.capitalize()}"]')[0]
        ana = cat_desc.getparent().attrib.get('{http://www.w3.org/XML/1998/namespace}id')
        catrefs.append(etree.Element('catRef', target='time', ana=f'#{ana}'))

    countries = row_data['страна']

    if not is_nan(countries) and countries.strip('?'):
        for country in countries.replace('/', ', ').strip('(?) ').split(','):
            cat_desc = TAXONOMY_ROOT.xpath(f'//catDesc[text()="{country.strip().capitalize()}"]')[0]
            ana = cat_desc.getparent().attrib.get('{http://www.w3.org/XML/1998/namespace}id')
            catrefs.append(etree.Element('catRef', target='country', ana=f'#{ana}'))

    occupation = row_data['сфера деятельности 2.0']
    if not is_nan(occupation) and occupation.strip('[]'):
        for sphere in [i.strip('"\'') for i in occupation.strip('[] ').split(', ')]:
            cat_desc = TAXONOMY_ROOT.xpath(f'//catDesc[text()="{sphere.capitalize()}"]')[0]
            ana = cat_desc.getparent().attrib.get('{http://www.w3.org/XML/1998/namespace}id')
            catrefs.append(etree.Element('catRef', target='occupation', ana=f'#{ana}'))

    correspondent = row_data['корреспондент 2 (из таблицы писем)']
    if not is_nan(correspondent) and correspondent == 'да':
        catrefs.append(etree.Element('catRef', target='correspondent', ana='#correspondent'))

    family = row_data['семья']
    if not is_nan(family) and family == 'да':
        catrefs.append(etree.Element('catRef', target='family', ana='#TolstoyFamily'))
    return catrefs


def create_person_tag(row_data: dict, df) -> etree._Element:
    person_tag = etree.Element('person')
    ref_id = str(int(row_data['ID по указателю']))
    person_tag.set('id', ref_id)
    person_tag.append(create_persname_tag(row_data))

    persname_latin_tag = etree.Element('persName', type='latin')
    person_tag.append(persname_latin_tag)
    if not is_nan(row_data['LATIN']) and row_data['LATIN'].strip('xх'):
        persname_latin_tag.text = row_data['LATIN']

    born_tag = etree.Element('genName', type='born')
    person_tag.append(born_tag)

    add_name_nick_tag = etree.Element('addName', type='nick')
    person_tag.append(add_name_nick_tag)
    add_name_note_tag = etree.Element('addName', type='note')
    person_tag.append(add_name_note_tag)

    sex_tag = etree.Element('sex')
    if not is_nan(row_data['Пол']):
        sex_tag.set('value', row_data['Пол'])

    born_tag = etree.Element('event', type='born')
    person_tag.append(born_tag)
    born_date = row_data['дата рождения']
    if not is_nan(born_date):
        born_date = str(int(born_date)) if isinstance(born_date, float) else born_date
        born_date = str(born_date).split()[0] if isinstance(born_date, datetime) else born_date
        born_tag.set('when', born_date)

    died_tag = etree.Element('event', type='died')
    person_tag.append(died_tag)
    died_date = row_data['дата смерти']
    if not is_nan(died_date):
        died_date = str(int(died_date)) if isinstance(died_date, float) else died_date
        died_date = str(died_date).split()[0] if isinstance(died_date, datetime) else died_date
        died_tag.set('when', died_date)

    life_period_tag = etree.Element('event', type='life_period')
    person_tag.append(life_period_tag)
    if not is_nan(row_data['life-period']):
        # if is_nan(born_date):
        #     start = '?'
        # else:
        #     year = born_date.split('-')[0].lstrip('0') if born_date[0] != '-' else born_date.split('-')[1].lstrip('0')
        #     start = year if not born_date.startswith('-') else f"{year} год до н.э. "
        #
        # if is_nan(died_date):
        #     end = '?'
        # else:
        #     year = died_date.split('-')[0].lstrip('0') if died_date[0] != '-' else died_date.split('-')[1].lstrip('0')
        #     end = year if not died_date.startswith('-') else f" {year} год до н.э."
        #     if end == year and 'до н.э.' in start:
        #         end = f' {end}'
        # life_period_tag.text = f'{start}–{end}'
        life_period_tag.text = row_data['life-period']

    relations = create_relations(row_data, df)
    for relation in relations:
        person_tag.append(relation)

    note_desc_tag = etree.Element('note', type='description')
    person_tag.append(note_desc_tag)
    note_value = row_data['Description new.']
    if not is_nan(note_value) and note_value.strip(',. '):
        note_desc_tag.text = note_value

    person_tag.append(etree.Element('note', type='description2'))

    comment_90_tag = etree.Element('note', type='90v_comment')
    person_tag.append(comment_90_tag)
    if not is_nan(row_data['Комментарий из ПСС new']) and row_data['Комментарий из ПСС new'].strip('., -'):
        comment_90_tag.text = row_data['Комментарий из ПСС new']

    catrefs = create_catrefs(row_data)
    for catref in catrefs:
        person_tag.append(catref)

    image_path = Path(IMAGES_PATH, f'{int(row_data["ID по указателю"])}.png')
    if not is_nan(row_data['URL photo']) and image_path.exists():
        storage_path = row_data['URL photo'].strip(' ')
        if image_path.exists():
            person_tag.append(etree.Element('image', url=storage_path))

    note_entities_texts_tag = etree.Element('note', type='entities_number_in_texts')
    note_entities_texts_tag.text = ''
    person_tag.append(note_entities_texts_tag)

    note_entities_comments_tag = etree.Element('note', type='entities_number_in_comments')
    note_entities_comments_tag.text = ''
    person_tag.append(note_entities_comments_tag)
    return person_tag


def main():
    df = pd.read_excel(SHEET_PATH, sheet_name='MAIN (3075) (16.06.2023)', header=1)
    root = etree.fromstring(ut.read_xml(TEMPLATE_PATH, 'rb'))

    person_tags = []
    for row in df.iterrows():
        row_data = row[1].to_dict()
        if is_nan(row_data['Имя исправленное new']):
            continue

        person_tag = create_person_tag(row_data, df)
        person_tags.append(person_tag)

    list_person_tag = root.xpath('//ns:listPerson', namespaces={'ns': f'{ut.xmlns_namespace}'})[0]
    for person_tag in person_tags:
        list_person_tag.append(person_tag)

    etree.indent(list_person_tag, level=2, space='    ')
    text = etree.tostring(root, encoding='unicode')
    RESULT_PATH.write_text(text)


if __name__ == '__main__':
    ut.change_to_project_directory()
    main()
