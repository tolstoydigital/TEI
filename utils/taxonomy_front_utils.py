from pathlib import Path

from lxml import etree

import utils as ut

TAXONOMY_PATH = Path(ut.REPO_PATH, 'reference', 'taxonomy.xml')
NEW_TAXONOMY_PATH = Path(ut.REPO_PATH, 'reference', 'taxonomy_front.xml')

FRONT_CATREFS = {
    'arts_front': (['arts', 'main'], 'Искусство'),
    'autobio_front': (['autobio', 'main'], 'Автобиографическое'),
    'drama_front': (['drama', 'main'], 'Пьеса'),
    'drugoe_front': (['drugoe'], 'Другое'),
    'fiction_front': (['fiction', 'main'], 'Художественные'),
    'kids_front': (['kids', 'main'], 'Для детей'),
    'nonfiction_front': (['nonfiction', 'main'], 'Нехудожественные'),
    'novel_front': (['novel', 'main'], 'Роман'),
    'pedagogika_front': (['pedagogika', 'main'], 'Педагогика'),
    'philosophy_religion_front': (['philosophy_religion', 'main'],
                                  'Философия и религия'),
    'polit_social_front': (['polit_social', 'main'], 'Политика'),
    'povest_front': (['povest', 'main'], 'Повесть'),
    'rasskaz_front': (['rasskaz', 'main'], 'Рассказ'),
    'works_front': (['work', 'main'], 'Произведения')
}

NEPROSTO_CATREFS = {
    'arts_front_np': (['arts', 'main'], 'Искусство'),
    'autobio_front_np': (['autobio', 'main'], 'Автобиографическое'),
    'diaries_np': (['diaries'], 'Дневники'),
    'drama_front_np': (['drama', 'main'], 'Пьеса'),
    'fiction_front_np': (['fiction', 'main'], 'Художественные'),
    'kids_front_np': (['kids', 'main'], 'Для детей'),
    'letters_np': (['letters'], 'Письма'),
    'nonfiction_front_np': (['nonfiction'], 'Нехудожественные'),
    'notes_np': (['notes'], 'Записные книжки'),
    'novel_front_np': (['novel', 'main'], 'Роман'),
    'otryvok_fiction_front': (['otryvok', 'main', 'ficiton'], 'Отрывок'),
    'otryvok_nonfiction_front': (['otryvok', 'main', 'nonficiton'], 'Отрывок'),
    'pedagogika_front_np': (['pedagogika', 'main'], 'Педагогика'),
    'philosophy_religion_front_np': (['philosophy_religion', 'main'],
                                     'Философия и религия'),
    'poem_front_np': (['poem', 'main'], 'Поэзия'),
    'polit_social_front_np': (['polit_social', 'main'], 'Политика'),
    'povest_front_np': (['povest', 'main'], 'Повесть'),
    'rasskaz_front_np': (['rasskaz', 'main'], 'Рассказ'),
    'sbornik_fiction_front': (['sbornik', 'main', 'fiction'], 'Сборник'),
    'sbornik_nonfiction_front': (['sbornik', 'main', 'nonfiction'], 'Сборник'),
    'statja_front': (['statja', 'main'], 'Статья'),
    'traktat_front': (['traktat', 'main'], 'Трактат'),
    'ver': (['ver'], 'Черновики и варианты'),
    'works_front_np': (['work', 'main'], 'Произведения')
}

NEW_CATREFS = FRONT_CATREFS.copy()
NEW_CATREFS.update(NEPROSTO_CATREFS)

NEPROSTO_CATEGORIES = {
    'works_front_np': 'type_neprosto',
    'fiction_front_np': 'sphere_neprosto',
    'novel_front_np': 'genre_neprosto',
    'povest_front_np': 'genre_neprosto',
    'rasskaz_front_np': 'genre_neprosto',
    'drama_front_np': 'genre_neprosto',
    'kids_front_np': 'genre_neprosto',
    'poem_front_np': 'genre_neprosto',
    'otryvok_fiction_front': 'genre_neprosto',
    'sbornik_fiction_front': 'genre_neprosto',
    'nonfiction_front': 'sphere_neprosto',
    'otryvok_nonfiction_front': 'nonfiction_genre',
    'sbornik_nonfiction_front': 'nonfiction_genre',
    'traktat_front': 'nonfiction_genre',
    'statja_front': 'nonfiction_genre',
    'polit_social_front_np': 'topic_neprosto',
    'philosophy_religion_front_np': 'topic_neprosto',
    'arts_front_np': 'topic_neprosto',
    'pedagogika_front_np': 'topic_neprosto',
    'autobio_front_np': 'topic_neprosto',
    'diaries_np': 'type_neprosto',
    'notes_np': 'type_neprosto',
    'letters_np': 'type_neprosto',
}

NEW_CATEGORIES = {
    'arts_front': 'topic',
    'autobio_front': 'topic',
    'drama_front': 'genre',
    'drugoe_front': 'genre',
    'fiction_front': 'sphere',
    'kids_front': 'genre',
    'nonfiction_front': 'sphere',
    'novel_front': 'genre',
    'otryvok_fiction_front': 'genre',
    'otryvok_nonfiction_front': 'nonfiction_genre',
    'pedagogika_front': 'topic',
    'philosophy_religion_front': 'topic',
    'polit_social_front': 'topic',
    'povest_front': 'genre',
    'rasskaz_front': 'genre',
    'sbornik_fiction_front': 'genre',
    'sbornik_nonficition_front': 'nonfiction_genre',
    'statja_front': 'nonfiction_genre',
    'traktat_front': 'nonfiction_genre',
    'ver': 'main_draft',
    'works_front': 'type'
}
NEW_CATEGORIES.update(NEPROSTO_CATEGORIES)

CATEGORIES_TO_DEL = [
    'genre',
    'sphere',
    'topic'
]

ORDERED_DESCRIPTIONS = [
    'Произведения',
    'Художественные',
    'Нехудожественные',
    'Роман',
    'Повесть',
    'Рассказ',
    'Пьеса',
    'Для детей',
    'Поэзия',
    'Отрывок',
    'Сборник',
    'Трактат',
    'Статья',
    'Политика',
    'Философия и религия',
    'Искусство',
    'Педагогика',
    'Автобиографическое',
    'Черновики и варианты',
    'Другое',
    'Дневники',
    'Письма',
    'Записные книжки'
]


def get_taxonomy_as_dict(path: Path) -> dict:
    with open(path, 'rb') as file:
        root = etree.fromstring(file.read())

    categories = root.xpath('//category')
    taxonomy_dict = {}
    for category in categories:
        cat_id = category.get('{http://www.w3.org/XML/1998/namespace}id')
        cat_target = category.get('target')
        description = category[0].text
        uuid = category.get('uuid')
        taxonomy_dict[cat_id] = {'target': cat_target, 'description': description, 'uuid': uuid}
    return taxonomy_dict


def create_new_taxonomy_dict(old: dict) -> dict:
    new: dict = old.copy()
    for category in CATEGORIES_TO_DEL:
        for catref, value in old.items():
            if category == value['target']:
                new.pop(catref)
    for new_category, target in NEW_CATEGORIES.items():
        new[new_category] = {'target': target, 'description': NEW_CATREFS[new_category][1]}
    new.pop('works')
    return new


def add_taxonomy_uuids(taxonomy: dict):
    from convert_tei_to_front import get_all_uuids, generate_new_uuid
    uuids = get_all_uuids(ut.REPO_TEXTS_PATH)
    for catref, data in taxonomy.items():
        if 'uuid' not in data:
            new_uuid = generate_new_uuid(uuids)
            taxonomy[catref]['uuid'] = new_uuid


def sorting_function_taxonomy_item(taxonomy_item: tuple) -> int:
    descriptions = {desc: i for i, desc in enumerate(ORDERED_DESCRIPTIONS)}
    catref, data = taxonomy_item
    description = data['description']
    if description in descriptions:
        return descriptions[description]
    else:
        return len(descriptions)


def sorting_function_ana(ana: str):
    descriptions = {desc: i for i, desc in enumerate(ORDERED_DESCRIPTIONS)}
    if ana in NEW_CATREFS:
        description = NEW_CATREFS[ana][1]
        return descriptions[description]
    else:
        return 1000


def create_taxonomy_front(taxonomy: list[str, dict]) -> str:
    categories = []
    for catref, data in taxonomy:
        item = f'\n    <category xml:id="{catref}" target="{data["target"]}" uuid="{data["uuid"]}">' \
               f'\n        <catDesc>{data["description"]}</catDesc>\n    </category>'
        categories.append(item)
    text = ''.join(categories)
    text = f'<taxonomy>{text}\n</taxonomy>'
    return text


def old_catrefs_to_new_catrefs(catrefs: list, taxonomies: list[dict]) -> list:
    taxonomy, new_taxonomy = taxonomies
    new_catrefs = catrefs.copy()

    for catref, data in NEW_CATREFS.items():
        old_catref_set = set(data[0])
        if old_catref_set.issubset(catrefs):
            new_catrefs.append(catref)

    for catref in catrefs:
        if (taxonomy[catref]['target'] in CATEGORIES_TO_DEL and catref not in NEW_CATREFS
        ) or catref == 'works':
            new_catrefs.remove(catref)

    if new_catrefs.count('ver') == 2:
        new_catrefs.remove('ver')
    new_catrefs.sort(key=sorting_function_ana)
    return new_catrefs


def remove_vse_prosto_ana_for_bibllist(ana: list[str]) -> list[str]:
    new_ana = ana.copy()
    for catref in ana:
        if catref.endswith('_np'):
            try:
                new_ana.remove(catref.rstrip('np').rstrip('_'))
            except ValueError:
                pass
    return new_ana

