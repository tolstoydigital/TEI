import copy
import logging
import os
import re

import bs4
import requests
import tqdm
import urllib.parse

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.feb.provider import FebHtmlProvider
from tolstoy_bio.utilities.io import IoUtils

logging.basicConfig(level=logging.INFO, filename="errors.log", filemode="w")


MONTH_GENETIVE_LABEL_TO_MONTH_ISO = {
    'января': '01',
    'февраля': '02',
    'марта': '03',
    'апреля': '04',
    'мая': '05',
    'июня': '06',
    'июля': '07',
    'августа': '08',
    'сентября': '09',
    'октября': '10',
    'ноября': '11',
    'декабря': '12'
}


class TolstayaDiariesFebHtmlToTeiXmlConverter:
    """
    Parses the HTML of a FEB document.

    The HTML is taken from printed version of a document,
    which can be accessed by the query parameter "cmd=p"
    added to the document URL at feb.ru.
    """

    @classmethod
    def from_path(cls, document_html_for_printing_path: str):
        '''
        Инициализирует конвертер по пути к документу.
        '''
        with open(document_html_for_printing_path, 'r', encoding='utf-8', errors='replace') as file:
            source_html = file.read()
            return cls(source_html)

    def __init__(self, document_html_for_printing: str):
        '''
        Инициализирует метаданные и подготавливает болванку под XML.
        '''
        self.source_html = document_html_for_printing
        self.html_soup = self.parse_html(document_html_for_printing)
        self.tei_soup = self.parse_as_xml(self.html_soup.prettify())
        self.source_url = self.parse_base_url(self.html_soup)

    @staticmethod
    def parse_html(html: str) -> bs4.BeautifulSoup:
        '''
        Парсит HTML-разметку в объект BeautifulSoup.
        '''
        return bs4.BeautifulSoup(html, 'lxml')
    
    @staticmethod
    def parse_as_xml(content: str) -> bs4.BeautifulSoup:
        '''
        Парсит HTML-разметку в объект BeautifulSoup для работы с XML.
        '''
        return bs4.BeautifulSoup(content, 'xml')

    @staticmethod
    def parse_base_url(html_soup: bs4.BeautifulSoup) -> str | None:
        '''
        Парсит ссылку на источник из тега <base>,
        '''
        base = html_soup.find('base')

        if not base or 'href' not in base.attrs:
            return None

        return base.attrs['href']

    def save_to_file(self, path):
        '''
        Форматирует и сохраняет итоговый TEI/XML в файл,
        заменяя неразрывные пробелы на XML-коды &nbsp;
        '''
        output = self.tei_soup.prettify()
        output = self.replace_byte_nbsp_with_entity_code(output)
        return IoUtils.save_textual_data(output, path)
    
    # def generate_xml_filename(self):
    #     """
    #     Генерация имени XML-файла.

    #     Выполнять строго после конвертации HTML в TEI,
    #     т. е. после выполнения convert_to_tei()
    #     """
    #     creation_element = self.tei_soup.find("creation")
    #     creation_date_element = creation_element.find("date")

    #     scope = "tolstaya-s-a-letters"

    #     start_date_iso = creation_date_element.attrs.get("when", None) or creation_date_element.attrs.get("from", None)
    #     assert start_date_iso is not None, "Failed to parse start date ISO"

    #     iso_components = start_date_iso.split('-')
        
    #     year, month, start_day, end_day = None, None, None, None

    #     if len(iso_components) == 3:
    #         year, month, start_day = iso_components
    #     elif len(iso_components) == 2:
    #         year, month = iso_components
    #     else:
    #         raise RuntimeError(f"Unexpected number of ISO components: {iso_components}")

    #     if 'to' in creation_date_element.attrs:
    #         end_day = creation_date_element.attrs['to'].split('-')[-1]

    #     day = f"{start_day}-{end_day}" if end_day else start_day
    #     return f"{scope}_{year}_{month}_{day}"
    
    @staticmethod
    def replace_byte_nbsp_with_entity_code(content: str) -> str:
        '''
        Заменяет неразрывные пробелы, выраженные байт-символом,
        на XML-код &nbsp; в соответствии со спецификацией XML.
        '''
        return re.sub('\xa0', '&nbsp;', content)

    def convert_to_tei(self):
        '''
        Итеративно применяет скрипты по конвертации фрагментов HTML в TEI/XML эквиваленты.
        '''
        transformations = [
            self.remove_scripts_and_invisible_blocks,
            self.transform_root_element,
            self.transform_head_element,
            self.remove_styles,
            self.transform_body_element,
            self.remove_empty_paragraphs,
            self.transform_pages,
            self.remove_empty_paragraphs,
            self.transform_paragraphs,
            self.transform_tables,
            self.transform_images,
            self.transform_styles,
            self.divide_into_entries,
            self.divide_into_years,
            self.mark_up_year_headings,
            self.mark_up_entries_datelines,
            self.transform_footnotes,
            self.transform_notes,
            self.transform_title,
            self.transform_text_body,
            # self.group_letters,
            self.populate_tei_header,
            # self.mark_up_dates,
            # self.mark_up_closers,

            self.remove_html_parts,
            self.transform_linebreaks,
            self.clear_unknown_paragraph_attributes,
            self.clear_class_attributes,
            self.transform_id_attributes,
            self.transform_links,
        ]

        for transform in transformations:
            print('Action:', getattr(transform, '__name__', 'Unknown'))
            output = transform()

            if output is not None:
                print(output)

    def transform_root_element(self):
        '''
        Конвертация корневого элемента в TEI.
        '''
        root = self.tei_soup.find('html')
        root.name = 'TEI'
        root.attrs = {
            'xmlns': 'http://www.tei-c.org/ns/1.0',
            'xmlns:xi': 'http://www.w3.org/2001/XInclude',
            'xmlns:svg': 'http://www.w3.org/2000/svg',
            'xmlns:math': 'http://www.w3.org/1998/Math/MathML',
        }

    def transform_head_element(self):
        '''
        Конвертация имени элемента меташапки в teiHeader.
        '''
        head = self.tei_soup.find('head')
        head.name = 'teiHeader'

    def transform_body_element(self):
        '''
        Оборачивает содержимое <body> в <text>.
        '''
        body_element = self.tei_soup.find('body')
        text_element = self.tei_soup.new_tag('text')

        body_element.wrap(text_element)
        body_element.attrs = {}

    def populate_tei_header(self):
        '''
        Парсинг названия, библиографического описания и дат для teiHeader.

        Поскольку в шапке учитываются даты,
        функцию применять строго после mark_up_letter_datelines
        '''
        meta_author = self.html_soup.select_one('meta[name="author"]').attrs['content']
        meta_title = self.html_soup.select_one('meta[name="title"]').attrs['content']
        title = f"{meta_author.strip()} {meta_title.strip()}"

        description = copy.copy(self.html_soup.select_one('.description'))
        
        for a in description.find_all('a'):
            a.decompose()

        bibl = re.sub(r'\s+', ' ', description.text.strip())

        dates = self.tei_soup.select('date')
        start_date = dates[1].attrs['when']
        end_date = dates[-1].attrs['when']

        tei_header = bs4.BeautifulSoup(f'''
            <teiHeader>
                <fileDesc>     
                <titleStmt>
                    <title>{title}</title>
                    <title type="bibl">{bibl}</title>
                </titleStmt>
                <sourceDesc>
                    <biblStruct>
                    <analytic>
                        <author>Толстая Софья Андреевна</author>
                    </analytic>
                    </biblStruct>         
                </sourceDesc>
                </fileDesc>
                <profileDesc>
                    <creation>
                        <date from="{start_date}" to="{end_date}" />
                    </creation>
                    <textClass>
                        <catRef ana="#diaries" target="type" />
                    </textClass>
                </profileDesc>  
            </teiHeader>''', 'xml')
        
        self.tei_soup.select_one('teiHeader').replace_with(tei_header)

    def get_start_and_end_date_as_iso(self) -> tuple[str, str]:
        html_title_element = self.html_soup.select_one("title")
        html_title_text = html_title_element.text.strip()
                                          
        month_interval_match = re.search(r"(\d\d?) (\w+) [—-] (\d\d?) (\w+) (\d{4})", html_title_text)

        if month_interval_match:
            raw_start_day, raw_start_month, raw_end_day, raw_end_month, year = month_interval_match.groups()

            padded_start_day = raw_start_day.zfill(2);
            padded_end_day = raw_end_day.zfill(2) if raw_end_day else None;

            assert len(year) == 4 and len(padded_start_day) == 2 and (padded_end_day is None or len(padded_end_day) == 2), f"Unexpected date format, got {year=}, {padded_start_day=}, {padded_end_day=}"

            padded_start_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[raw_start_month.lower()]
            padded_end_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[raw_start_month.lower()]

            iso_start_date = "-".join([year, padded_start_month, padded_start_day])
            iso_end_date = "-".join([year, padded_end_month, padded_end_day])

            return iso_start_date, iso_end_date

        day_interval_match = re.search(r"(\d\d?)(—(\d\d?))? (\w+) (\d{4})", html_title_text)
        assert day_interval_match is not None, "Failed to parse the date string"

        raw_start_day, _, raw_end_day, raw_month, year = day_interval_match.groups()
        
        padded_start_day = raw_start_day.zfill(2);
        padded_end_day = raw_end_day.zfill(2) if raw_end_day else None;

        assert len(year) == 4 and len(padded_start_day) == 2 and (padded_end_day is None or len(padded_end_day) == 2), f"Unexpected date format, got {year=}, {padded_start_day=}, {padded_end_day=}"

        padded_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[raw_month]

        iso_start_date = "-".join([year, padded_month, padded_start_day])
        iso_end_date = "-".join([year, padded_month, padded_end_day]) if padded_end_day else None

        return iso_start_date, iso_end_date

    def remove_styles(self):
        '''
        Удаление конфигурационных HTML-тегов,
        относящихся к CSS-стилям и ссылкам на внешние ресурсы.
        '''
        style_elements = self.tei_soup.select('style, link')

        for style_element in style_elements:
            style_element.extract()

    def remove_scripts_and_invisible_blocks(self):
        '''
        Удаление тегов с JavaScript-логикой.
        '''
        script_elements = self.tei_soup.select('script, noscript')

        for script_element in script_elements:
            script_element.decompose()

        invisible_blocks = self.tei_soup.find_all(style="display:none;")
        
        for element in invisible_blocks:
            element.decompose()

    def remove_empty_paragraphs(self):
        '''
        Удаление пустых абзацев.
        '''
        paragraphs = self.tei_soup.find_all('p')
        removed_paragraph_count = 0

        for paragraph in paragraphs:
            if not paragraph.text.strip():
                paragraph.decompose()
                removed_paragraph_count += 1

        return removed_paragraph_count

    def transform_pages(self):
        '''
        Генерация маркеров смен страниц <pb> вместо HTML-контейнеров.
        '''
        page_blocks = self.tei_soup.select('blockquote.page')
        transformed_pages = []

        for page_block in page_blocks:
            page_anchor = page_block.select_one('span.page')
            page_label = page_anchor.text
            page_number_match = re.search(r'\d+', page_label)

            if page_number_match is None:
                raise RuntimeError('Failed to parse a page number')

            page_number = page_number_match.group()

            page_anchor.name = 'pb'

            page_id = page_anchor['id']

            if not page_id.strip():
                raise RuntimeError('Failed to parse the ID of a page element')

            page_anchor.attrs = {
                'n': page_number,
                'xml:id': f'page{page_number}'
            }

            page_anchor.clear()
            page_anchor.parent.unwrap()
            page_block.unwrap()

            transformed_pages.append(page_number)

        return transformed_pages

    def transform_paragraphs(self):
        '''
        Объединение абзацев, разделённых сменами страниц, и нормализация пробелов.
        '''
        continuation_paragraphs = self.tei_soup.select('p.text0')

        print(continuation_paragraphs)

        for continuation_paragraph in continuation_paragraphs:
            if continuation_paragraph.parent.name == 'td':
                continue

            page_marker = continuation_paragraph.find_previous('pb')
            starting_paragraph = continuation_paragraph.find_previous_sibling('p', class_=re.compile(r'^text(1?|ot)$'))
            continuation_contents = copy.deepcopy(continuation_paragraph.contents)
            try:
                starting_paragraph.extend([page_marker, *continuation_contents])
            except:
                print(continuation_paragraph)
            starting_paragraph.smooth()

            for paragraph_substring in starting_paragraph.find_all(text=True):
                stripped_substring = self.normalize_whitespace(paragraph_substring.string)
                paragraph_substring.replace_with(stripped_substring)

            starting_paragraph.smooth()
            continuation_paragraph.decompose()

        paragraphs = self.tei_soup.select('p.text, p.text1')

        for paragraph in paragraphs:
            paragraph.attrs = {}

    def normalize_whitespace(self, content: str):
        '''
        Удаление повторяющихся пробелов и замена байт-символов 
        неразрывных пробелов на XML-сущность &nbsp;.
        '''
        stripped_content = content.strip()
        content_with_nbsp = self.replace_byte_nbsp_with_entity_code(stripped_content)
        content_with_normalized_whitespaces = re.sub(r'\s+', ' ', content_with_nbsp)
        return self.replace_byte_nbsp_with_entity_code(content_with_normalized_whitespaces)

    def transform_tables(self):
        '''
        Конвертация табличных тегов в TEI 
        и удаление табличных HTML-тегов без аналогов в TEI.
        '''
        table_elements = self.tei_soup.select('table')

        for table_element in table_elements:
            table_element.attrs = {}

        tr_elements = self.tei_soup.select('tr')

        for tr_element in tr_elements:
            tr_element.name = 'row'
            tr_element.attrs = {}

        th_elements = self.tei_soup.select('th')

        for th_element in th_elements:
            th_element.name = 'cell'
            th_element.attrs = {'role': 'label'}

        td_elements = self.tei_soup.select('td')

        for td_element in td_elements:
            td_element.name = 'cell'
            td_element.attrs = {'role': 'data'}

        caption_elements = self.tei_soup.select('caption')

        for caption_element in caption_elements:
            caption_element.name = 'head'
            caption_element.attrs = {}

        colgroup_elements = self.tei_soup.select('colgroup')

        for colgroup_element in colgroup_elements:
            colgroup_element.decompose()

        container_elements = self.tei_soup.select('thead, tbody, tfoot')

        for container_element in container_elements:
            container_element.unwrap()

    def transform_images(self):
        '''
        Конвертация изображений и табличных структур, связанных с изображениями,
        в систему графических TEI-тегов.

        Поскольку графические блоки в ФЭБ-HTML сделаны на таблицах,
        этот шаг должен выполняться строго после трансформации общих таблиц (transform_tables).
        '''
        tables = self.tei_soup.select('table')

        for table in tables:
            rows = table.find_all('row', recursive=False)

            if len(rows) != 1:
                continue

            row = rows[0]
            cells = row.find_all('cell', recursive=False)

            if len(cells) != 1:
                continue

            cell = cells[0]
            images = cell.find_all('img', recursive=False)

            if len(images) > 1:
                raise RuntimeError("More than one image in a row")

            # will be renamed to 'figure' at the end
            image = images[0]

            try:
                if image.attrs['src'] == '/images/logoPRN.gif':
                    continue
            except:
                print(image)
                raise RuntimeError("Image doesn't have an attribute 'src'")

            graphic = self.tei_soup.new_tag('graphic', attrs={
                'url': image.attrs['src'],
            })

            if image.has_attr('alt'):
                fig_desc = self.tei_soup.new_tag('figDesc')
                fig_desc.string = image.attrs['alt']
                image.append(fig_desc)

            image.append(graphic)

            image.name = 'figure'
            image.attrs = {}

            image_title = image.find_next('p')

            if (not image_title
                    or not image_title.has_attr('class')
                    or image_title.attrs['class'] != 'ris8-1'):
                continue

            image_title.name = "head"
            image_title.attrs = {}

            image_descriptions = []
            image_description = image_title.find_next_sibling('p')

            while image_description.has_attr('class') and re.match(r'^ris8-[^1]', image_description.attrs['class']):
                image_description.attrs = {}
                image_descriptions.append(image_description)
                image_description = image_description.find_next_sibling('p')

            image.append(image_title)

            for image_description in image_descriptions:
                image.append(image_description)

            table.unwrap()
            row.unwrap()
            cell.unwrap()

    def transform_notes(self):
        '''
        Перемещение и ассоциация текстов примечаний из тома примечаний
        с абзацами, из которых идёт ссылка на примечание.
        '''
        links = self.tei_soup.select('a')
        note_links = [link for link in links if self.is_non_footnote_anchor_to_volume_notes(link)]
        current_volume_endpoint = None
        current_volume_notes_soup = None

        provider = FebHtmlProvider()

        for note_index, note_link in tqdm.tqdm(
                enumerate(note_links, 1),
                desc="Loading and inserting notes",
                total=len(note_links)
        ):
            note_id = f'note{note_index}'

            note_link_href = note_link.attrs['href']

            note_link.name = 'ref'
            note_link.attrs = {
                'target': f'#{note_id}',
            }

            note = self.tei_soup.new_tag('note', attrs={
                'index': "false",  # TODO: согласовать необходимость этого атрибута
                'resp': "volume_editor",
                'xml:id': note_id,
            })

            note_link_endpoint, node_link_anchor = note_link_href.split('#')

            if note_link_endpoint != current_volume_endpoint:
                path_to_local_volume_notes = os.path.abspath(os.path.join(__file__, f'../tmp/volume_notes/{note_link_endpoint}'))

                if not os.path.exists(path_to_local_volume_notes):
                    volume_notes_url = urllib.parse.urljoin(self.source_url, f'{note_link_endpoint}')
                    volume_notes_document = provider.get(volume_notes_url)
                    volume_notes_html = volume_notes_document.get_source_html()
                    IoUtils.save_textual_data(volume_notes_html, path_to_local_volume_notes)

                volume_notes_source_html = IoUtils.read_as_text(path_to_local_volume_notes)
                current_volume_notes_soup = self.parse_html(volume_notes_source_html)

            for page_wrapper in current_volume_notes_soup.select('blockquote'):
                page_wrapper.unwrap()

            anchor_element = current_volume_notes_soup.find(id=node_link_anchor)
            assert anchor_element, f'Failed to find the note {node_link_anchor}'

            next_anchor_element = anchor_element.find_next_sibling('h5')

            note_paragraphs = []

            next_paragraph = anchor_element.next_sibling

            while next_paragraph is not next_anchor_element:
                if type(next_paragraph) is bs4.NavigableString:
                    next_paragraph = next_paragraph.next_sibling
                    continue

                if 'class' not in next_paragraph.attrs:
                    next_paragraph = next_paragraph.next_sibling
                    continue

                next_paragraph_class = next_paragraph.attrs['class'][0]

                if re.match(r'^comm|^stih|^podstih|^txt8', next_paragraph_class):
                    note_paragraphs.append(next_paragraph)

                next_paragraph = next_paragraph.next_sibling

            for i in range(len(note_paragraphs) - 1, 0, -1):
                prev_note = note_paragraphs[i - 1]
                next_note = note_paragraphs[i]

                if next_note.attrs['class'][0] in ['comm2', 'txt8']:
                    prev_note.extend(next_note.contents)
                    prev_note.smooth()
                    note_paragraphs.pop()
                elif "stih" in next_note.attrs['class'][0]:
                    verse_wrapper = self.tei_soup.new_tag("lg")
                    verse_wrapper.extend(next_note.contents)
                    prev_note.extend(verse_wrapper)
                    note_paragraphs.pop()

            for note_paragraph in note_paragraphs:
                note.append(note_paragraph)

            for paragraph in note.select('p'):
                source_class_name = paragraph.attrs.get("class", None)
                paragraph.attrs = {}

                if source_class_name:
                    paragraph.attrs['class'] = source_class_name

            note_link_number = note_link.text.strip() if note_link.text else None
            assert note_link_number, f"Note link number not found in {note_link}"

            note_number_container = note.find('sup')

            if note_number_container:
                note_number = note_number_container.string.strip()

                if note_number == note_link_number:
                    note_number_container.decompose()

            note_link.insert_after(note)

    def is_non_footnote_anchor_to_volume_notes(self, element):
        is_footnote_child = BeautifulSoupUtils.has_parent_with_tag_name(element, "note")

        if is_footnote_child:
            return False
        
        return self.is_anchor_to_volume_notes(element)

    def is_anchor_to_volume_notes(self, element):
        if element.name != "a":
            return False
        
        if 'href' not in element.attrs:
            return False
        
        return self.is_href_to_volume_notes(element.attrs['href'])
    
    @staticmethod
    def is_href_to_volume_notes(value):
        return bool(re.search(r'\.html?#', value))
    
    def transform_footnotes(self):
        # if self.source_url == "http://feb-web.ru/feb/tolstoy/critics/tpt/tpt20062.htm?cmd=p":
        #     last_footnote_index = self.transform_p_footnotes()
        # else:
        #     last_footnote_index = self.transform_h5_footnotes()

        footnote_container = self.tei_soup.select_one('div.footnotesp')
        assert footnote_container, f"Failed to locate the footnote container at {self.source_url}"
        self.transform_div_footnotes()

    def transform_div_footnotes(self, starting_footnote_index=1):
        '''
        Перемещение и ассоциация текстов сносок с абзацами,
        которые на них ссылаются.

        Логика предусматривает также и объединение фрагментов сноски,
        разделённой в ФЭБ-разметке в разные контейнеры.
        '''
        links = self.tei_soup.select('a')
        footnotes = self.tei_soup.find_all('p', class_=re.compile(r'snos(\d*|ka)'))

        for i in reversed(range(1, len(footnotes))):
            footnote = footnotes[i]
            previous_footnote = footnotes[i - 1]

            if not footnote.has_attr('id'):
                previous_footnote.extend([self.tei_soup.new_tag("br"), *footnote.contents])
                del footnotes[i]

        for i, footnote in enumerate(footnotes, starting_footnote_index):
            footnote_html_id = footnote['id']
            footnote_tei_id = f'footnote{i}'

            footnote.name = 'note'
            footnote.attrs = {
                'index': "false",  # TODO: согласовать необходимость этого атрибута
                'resp': "volume_editor",
                'xml:id': footnote_tei_id,
                'type': 'footnote',
            }

            footnote_anchor = footnote.find('a', href=f'#${footnote_html_id}')
            assert footnote_anchor, "Failed to locate the anchor inside a footnote"

            if footnote_anchor:
                self.delete_element_and_its_empty_parents(footnote_anchor)

            try:
                footnote_link = next(
                    (link for link in links if 'href' in link.attrs and link.attrs['href'] == f'#{footnote_html_id}'),
                    None
                )
                
                assert footnote_link, "Failed to find the footnote reference"

                footnote_link.name = 'ref'
                footnote_link.attrs = {
                    'target': f'#{footnote_tei_id}',
                }

                footnote_link.insert_after(footnote)
            except:
                continue

        try:
            footnote_html_list = self.tei_soup.select_one('div.footnotesp')
            footnote_html_list.decompose()
        except:
            raise RuntimeError('Failed to remove footnote list')

    def transform_h5_footnotes(self) -> int:
        '''
        Перемещение и ассоциация текстов сносок с абзацами,
        которые на них ссылаются.

        Логика предусматривает также и объединение фрагментов сноски,
        разделённой в ФЭБ-разметке в разные контейнеры.
        '''
        footnote_declarations = self.tei_soup.find_all('h5', {
            'id': re.compile(r'Примечания'),
        })
        
        for footnote_declaration in footnote_declarations:
            assert footnote_declaration.text.strip() == "", "Footnote declaration is not empty"

            footnote_paragraph = BeautifulSoupUtils.get_next_tag_sibling(footnote_declaration)
            assert footnote_paragraph is not None, "No continuation found for a footnote declaration"
            assert footnote_paragraph.name == "p", f"Unexpected continuation for a footnote declaration, namely: {footnote_paragraph.name}"
            footnote_declaration.extend(footnote_paragraph.contents)

            footnote_paragraph = BeautifulSoupUtils.get_next_tag_sibling(footnote_paragraph)

            while footnote_paragraph is not None and footnote_paragraph.name != "h5" and not (footnote_paragraph.name == "div" and 'class' in footnote_paragraph.attrs and footnote_paragraph.attrs['class'] == "footnotesp"):
                next_footnote_paragraph = BeautifulSoupUtils.get_next_tag_sibling(footnote_paragraph)

                if footnote_paragraph.name == "pb":
                    footnote_paragraph.decompose()
                else:
                    footnote_declaration.extend([self.tei_soup.new_tag("lb"), *footnote_paragraph.contents])

                footnote_paragraph = next_footnote_paragraph

                assert footnote_paragraph is None or footnote_paragraph.name in ["p", "h5", "pb", "div"], f"Unexpected continuation for a footnote declaration. Expected <p>, found <{footnote_paragraph.name}>"

        links = self.tei_soup.select('a')

        i = 0

        for i, footnote in enumerate(footnote_declarations, 1):
            footnote_html_id = footnote['id'].strip('"')

            footnote_link = next(
                (link for link in links if 'href' in link.attrs and link.attrs['href'] == f'#{footnote_html_id}'), 
                 None
            )

            if footnote_link is None and i == 1:
                footnote_link = next(
                    (link for link in links if 'href' in link.attrs and link.attrs['href'] == '#Примечания'), 
                    None
                )

            if footnote_link is None and footnote_html_id == "Примечания.Le" and footnote.attrs['title'] == "Le roman d'une honnete femme":
                footnote_link = next(
                    (link for link in links if 'href' in link.attrs and link.attrs['href'] == '#Примечания.Le roman'), 
                    None
                )

            assert footnote_link is not None, f"Failed to find a link to a footnote {footnote_html_id}"

            footnote_tei_id = f'footnote{i}'

            footnote.name = 'note'
            footnote.attrs = {
                'index': "false",  # TODO: согласовать необходимость этого атрибута
                'resp': "volume_editor",
                'xml:id': footnote_tei_id,
                'type': 'footnote',
            }
            
            footnote_link.name = 'ref'
            footnote_link.attrs = {
                'target': f'#{footnote_tei_id}',
            }

            footnote_link.insert_after(footnote)

        footnotes_section_headline = self.tei_soup.find('h4', id="Примечания")
        assert len(footnote_declarations) == 0 or footnotes_section_headline is not None, "No footnotes section headline found"

        self.remove_empty_paragraphs()
        
        if footnotes_section_headline:
            BeautifulSoupUtils.for_each_next_tag_sibling(
                footnotes_section_headline, 
                self._wrap_p_as_footnote,
            )

            footnotes_section_headline.decompose()

        return i
    
    def transform_p_footnotes(self, starting_footnote_index=1) -> int:
        footnotes = self.tei_soup.find_all('p', class_="small", id=True)
        links = self.tei_soup.select('a')

        i = starting_footnote_index - 1

        for i, footnote in enumerate(footnotes, starting_footnote_index):
            next_sibling = BeautifulSoupUtils.get_next_tag_sibling(footnote)

            while next_sibling is not None:
                next_next_sibling = BeautifulSoupUtils.get_next_tag_sibling(next_sibling)

                if next_sibling.name == "pb":
                    next_sibling.decompose()
                elif next_sibling.name == "p" and 'class' in next_sibling.attrs and next_sibling.attrs['class'] == "small" and 'id' in next_sibling.attrs:
                    break
                elif next_sibling.name == "p" and 'class' in next_sibling.attrs and next_sibling.attrs['class'] == "small0":
                    footnote.extend(next_sibling.contents)
                    # print(footnote)
                    # raise RuntimeError()
                    break

                next_sibling = next_next_sibling
                

            footnote_html_id = footnote.attrs['id']

            footnote_link = next(
                (link for link in links if 'href' in link.attrs and link.attrs['href'] == f'#{footnote_html_id}'), 
                 None
            )

            assert footnote_link is not None, f"Failed to find a link to a footnote {footnote_html_id}"

            footnote_tei_id = f'footnote{i}'

            footnote.name = 'note'
            footnote.attrs = {
                'index': "false",  # TODO: согласовать необходимость этого атрибута
                'resp': "volume_editor",
                'xml:id': footnote_tei_id,
                'type': 'footnote',
            }

            footnote_link.name = 'ref'
            footnote_link.attrs = {
                'target': f'#{footnote_tei_id}',
            }

            footnote_link.insert_after(footnote)
        
        footnotes_section_headline = self.tei_soup.find('h4', id="Примечания")
        assert len(footnotes) == 0 or footnotes_section_headline is not None, "No footnotes section headline found"

        BeautifulSoupUtils.for_each_next_tag_element(
            footnotes_section_headline, 
            self._remove_if_pb,
        )

        detached_footnote = self.tei_soup.find("p", class_="smallot")
        detached_footnote_continuation = self.tei_soup.find("p", class_="small0")
        detached_footnote.extend(detached_footnote_continuation.contents)
        self._wrap_p_as_footnote(detached_footnote)
        self.remove_empty_paragraphs()

        BeautifulSoupUtils.for_each_next_tag_sibling(
            footnotes_section_headline, 
            self._wrap_p_as_footnote,
        )

        if footnotes_section_headline:
            footnotes_section_headline.decompose()

        return i

    def _remove_if_pb(self, element: bs4.BeautifulSoup) -> None:
        if element.name == "pb":
            element.decompose()

    def _wrap_p_as_footnote(self, element: bs4.BeautifulSoup) -> None:
        if element.name == "p" and not element.find("note"):
            element.name = "note"
            element.attrs = {
                'index': "false",  # TODO: согласовать необходимость этого атрибута
                'resp': "volume_editor",
                'type': 'footnote',
            }

            element.wrap(self.tei_soup.new_tag("p"))
        
    def delete_element_and_its_empty_parents(self, soup):
        '''
        Удаление элемента и рекурсивное удаление пустых родительских элементов.
        '''
        parent = soup.parent
        soup.decompose()

        if type(parent) is bs4.Tag and not parent.text.strip():
            self.delete_element_and_its_empty_parents(parent)

    def transform_styles(self):
        '''
        Конвертация тегов стилевого форматирования текста в TEI-эквиваленты.
        '''
        tag_to_rend = {
            'b': 'bold',
            'em': 'letter-spacing',
            'i': 'italic',
            'u': 'underlined',
            'sup': 'superscript'
        }

        target_tag_names = tag_to_rend.keys()
        target_tags = self.tei_soup.select(', '.join(target_tag_names))

        for tag in target_tags:
            tag.attrs = {'rend': tag_to_rend[tag.name]}
            tag.name = 'hi'

    def divide_into_entries(self):
        '''
        Внутреннее структурное разделение документа на блоки-записи.
        '''
        letter_headlines = self.tei_soup.find_all('h4', attrs={'l': '2'})

        for letter_headline in letter_headlines:
            if letter_headline.attrs['id'] == '1902.Ясная_Поляна_9_декабря_1902_г':
                letter_headline.decompose()
                continue

            letter_headline.name = 'div'
            letter_headline.attrs['type'] = 'entry'

            current_tag = letter_headline.next_sibling

            while current_tag and current_tag.name != 'h4':
                next_tag = current_tag.next_sibling
                letter_headline.append(current_tag)
                current_tag = next_tag

    def divide_into_years(self):
        '''
        Внутреннее структурное разделение документа на блоки-месяцы.
        '''
        target_headlines = self.tei_soup.find_all('h4', attrs={'l': '1'})

        for target_headline in target_headlines:
            target_headline.name = 'div'
            target_headline.attrs = {'type': 'year'}

            current_tag = target_headline.next_sibling

            while current_tag and current_tag.name != 'h4':
                next_tag = current_tag.next_sibling
                target_headline.append(current_tag)
                current_tag = next_tag

    def mark_up_year_headings(self):
        '''
        Разметка годов-заголовков
        '''
        year_divisions = self.tei_soup.find_all('div', {
            'type': 'year'
        })

        for year_division in year_divisions:
            year_marker = BeautifulSoupUtils.get_first_tagged_child(year_division)
            assert year_marker and year_marker.name == 'p', "Unexpected year marker"
            
            year_label = year_marker.text.strip()
            assert re.match(r'^\d{4}$', year_label), "Unexpected year label format"

            year_marker.name = 'date'
            year_marker.attrs = {'when': year_label}

            p_wrapper = year_marker.wrap(self.tei_soup.new_tag("p"))
            p_wrapper.wrap(self.tei_soup.new_tag("head"))

    def mark_up_entries_datelines(self):
        '''
        Разметка и парсинг указания дат в начале записей.

        Ввиду необходимости структурных трансформаций
        этот шаг должен строго следовать разделению документа на блоки-письма (divide_into_entries)
        '''
        year_divisions = self.tei_soup.find_all('div', attrs={'type': 'year'})

        for year_division in year_divisions:
            year_marker = year_division.find('head')
            assert year_marker, "Failed to find the year marker"

            year_label = year_marker.text.strip()
            assert re.match(r'^\d{4}$', year_label), "Unexpected year label format"

            entry_divisions = year_division.find_all('div', attrs={'type': 'entry'})

            for entry_division in entry_divisions:
                assert 'title' in entry_division.attrs, "Failed to parse the entry 'title' attribute"

                date_label = entry_division.attrs['title'].strip()
                entry_id = entry_division.attrs['id'].strip()

                first_paragraph = entry_division.find('p')
                assert first_paragraph, "Unable to find the paragraph inside an entry division"

                if date_label == "Зима":
                    date_element = self.tei_soup.new_tag("date", attrs={
                        'notBefore': f'{year_label}-01-01',
                        'notAfter': f'{year_label}-03-31',
                    })

                    date_element.string = "Зима."
                    first_paragraph.insert(0, date_element)      
                    continue

                if date_label == "Моя поездка в Петербург":
                    date_element = self.tei_soup.new_tag("date", attrs={
                        'notBefore': f'{year_label}-04-22',
                        'notAfter': f'{year_label}-04-23',
                    })

                    first_paragraph.insert(0, date_element)
                    continue

                if date_label == 'Тревожное начало года':
                    date_element = self.tei_soup.new_tag("date", attrs={
                        'notBefore': f'{year_label}-01-01',
                        'notAfter': f'{year_label}-01-02',
                    })

                    first_paragraph.insert(0, date_element)      
                    continue

                if date_label == '20 февраля':
                    date_element = self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-02-20',
                    })

                    first_paragraph.insert(0, date_element)      
                    continue

                date_element = first_paragraph.find('hi')
                assert date_element, f"Unable to find the date element for the entry division '{date_label}'"

                if date_label == "С 27 на 28 апреля":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-04-28',
                    }))
                    
                    continue

                if date_label == "С 16 на 17 мая":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-05-17',
                    }))
                    
                    continue

                if date_label == "На другой день, 26 сентября":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-09-26',
                    }))
                    
                    continue

                if date_label == "Москва, 5 марта":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-03-05',
                    }))
                    
                    continue

                # if date_label == "1 и 2 января":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-01-01',
                #         'to': f'{year_label}-01-02',
                #     }))
                    
                #     continue

                # if date_label == "16 и 17 января":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-01-16',
                #         'to': f'{year_label}-01-17',
                #     }))
                    
                #     continue

                if match := re.match("(\d\d?) и (\d\d?) (\w+)", date_label):
                    start_day, end_day, month = match.groups()
                    assert month in MONTH_GENETIVE_LABEL_TO_MONTH_ISO.keys(), f"Unexpected month format in {date_label}"

                    iso_day = day.zfill(2)
                    iso_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[month]
                    iso_date = f'{year_label}-{iso_month}-{iso_day}'

                    date_element.wrap(self.tei_soup.new_tag("date", attrs={ 
                        'from': f'{year_label}-{iso_month}-{start_day.zfill(2)}',
                        'to': f'{year_label}-{iso_month}-{end_day.zfill(2)}',
                    }))

                    continue

                # if date_label == "2, 3, 4, 5 июня":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-06-02',
                #         'to': f'{year_label}-06-05',
                #     }))
                    
                #     continue

                # if date_label == "17, 18, 19, 20 июля":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-07-17',
                #         'to': f'{year_label}-07-20',
                #     }))
                    
                #     continue

                if match := re.match("(\d\d?, )(\d\d?, )*(\d\d?) (\w+)", date_label):
                    start_day, *_, end_day, month = match.groups()
                    assert month in MONTH_GENETIVE_LABEL_TO_MONTH_ISO.keys(), f"Unexpected month format in {date_label}"

                    iso_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[month]

                    date_element.wrap(self.tei_soup.new_tag("date", attrs={ 
                        'from': f'{year_label}-{iso_month}-{start_day.strip(" ,").zfill(2)}',
                        'to': f'{year_label}-{iso_month}-{end_day.strip(" ,").zfill(2)}',
                    }))

                    continue

                if re.sub(r'\s+', ' ', date_label) == "Как прошел день 28 августа 1898 г.":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-08-28',
                    }))
                    
                    continue

                # if date_label == "7—27 февраля":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-02-07',
                #         'to': f'{year_label}-02-27',
                #     }))
                    
                #     continue

                # if date_label == "13—15 ноября":
                #     date_element.wrap(self.tei_soup.new_tag("date", attrs={
                #         'from': f'{year_label}-11-13',
                #         'to': f'{year_label}-11-15',
                #     }))
                    
                #     continue

                # 16—18 ноября
                if match := re.match("(\d\d?)—(\d\d?) (\w+)", date_label):
                    start_day, end_day, month = match.groups()
                    assert month in MONTH_GENETIVE_LABEL_TO_MONTH_ISO.keys(), f"Unexpected month format in {date_label}"

                    iso_day = day.zfill(2)
                    iso_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[month]
                    iso_date = f'{year_label}-{iso_month}-{iso_day}'

                    date_element.wrap(self.tei_soup.new_tag("date", attrs={ 
                        'from': f'{year_label}-{iso_month}-{start_day.zfill(2)}',
                        'to': f'{year_label}-{iso_month}-{end_day.zfill(2)}',
                    }))

                    continue

                if date_label == "Ноября 19—21":
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'from': f'{year_label}-11-19',
                        'to': f'{year_label}-11-21',
                    }))
                    
                    continue

                if entry_id == '1901.Май_1901_г':
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'notBefore': f'{year_label}-05-04',
                        'notAfter': f'{year_label}-05-18',
                    }))
                    
                    continue

                if date_label == 'Записано после. 23-го вечером':
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-01-23',
                    }))
                    
                    continue

                if date_label == '24-го':
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-01-24',
                    }))
                    
                    continue

                if date_label == '25-го':
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-01-25',
                    }))
                    
                    continue

                if entry_id == '1903.Вечером':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-01-21T16:00:00',
                        'notAfter': f'{year_label}-01-21T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-01-21',
                    }))
                    
                    continue

                if entry_id == '1910.Вечер':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-06-26T16:00:00',
                        'notAfter': f'{year_label}-06-26T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-06-26',
                    }))
                    
                    continue

                if entry_id == '1910.Вечер_2':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-07-07T16:00:00',
                        'notAfter': f'{year_label}-07-07T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-07-07',
                    }))
                    
                    continue

                if entry_id == '1910.Ночь_13_на_14_июля':
                    date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-07-14',
                    }))
                    
                    continue

                if entry_id == '1910.Вечером':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-08-16T16:00:00',
                        'notAfter': f'{year_label}-08-16T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-08-16',
                    }))
                    
                    continue

                if entry_id == '1910.Вечером_3':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-08-27T16:00:00',
                        'notAfter': f'{year_label}-08-27T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-08-27',
                    }))
                    
                    continue

                if entry_id == '1910.Вечер_4':
                    wrapped_date_element = date_element.wrap(self.tei_soup.new_tag("time", attrs={
                        'notBefore': f'{year_label}-08-28T16:00:00',
                        'notAfter': f'{year_label}-08-28T23:59:59',
                    }))

                    wrapped_date_element.wrap(self.tei_soup.new_tag("date", attrs={
                        'when': f'{year_label}-08-28',
                    }))
                    
                    continue

                assert re.match(r'^\d\d? \w+', date_element.text.strip()), f"Unexpected date element content: found {first_paragraph}"

                match = re.search(r"^(\d\d?) (\w+)", date_label)
                assert match, f"Unexpected date label format: found {date_label}"

                day, month = match.groups()
                assert month in MONTH_GENETIVE_LABEL_TO_MONTH_ISO.keys(), f"Unexpected month format in {date_label}"

                iso_day = day.zfill(2)
                iso_month = MONTH_GENETIVE_LABEL_TO_MONTH_ISO[month]
                iso_date = f'{year_label}-{iso_month}-{iso_day}'

                # print('DATE', date_element)
                # raise RuntimeError

                date_element.wrap(self.tei_soup.new_tag("date", attrs={ 'when': iso_date }))

                # print('DATE', wrapped)
                # raise RuntimeError


    def transform_title(self):
        '''
        Разметка названия документа
        '''
        title_headline = self.tei_soup.find('h4', id="Заголовок")
        current_tag = title_headline.next_sibling

        while current_tag and current_tag.name != 'h4':
            next_tag = current_tag.next_sibling
            title_headline.append(current_tag)
            current_tag = next_tag

        title_paragraph = title_headline.find('p')
        title_paragraph.name = 'head'
        title_paragraph.attrs = {}

        title_headline.unwrap()

    def transform_text_body(self):
        '''
        Разметка текста документа
        '''
        assert self.tei_soup.find('h4', id="Текст", l="1") is None, "Text container has level 1 instead of expected level 0"

        body_headline = self.tei_soup.find('h4', id="Текст")
        body_headline.name = 'div'
        body_headline.attrs = {'type': 'text'}

        current_tag = body_headline.next_sibling

        while current_tag and (current_tag.name != 'h4' or current_tag.attrs['l'] != "0"):
            next_tag = current_tag.next_sibling
            body_headline.append(current_tag)
            current_tag = next_tag

        # letter_section = body_headline.find('h4', l="1")

        # if letter_section is None:
        #     return
        
        # current_tag = body_headline.next_sibling

        # while current_tag and (current_tag.name != 'h4' or current_tag.attrs['l'] != "0"):
        #     next_tag = current_tag.next_sibling
        #     body_headline.append(current_tag)
        #     current_tag = next_tag

    def group_letters(self):
        '''
        Внутреннее структурное разделение документа на блоки-письма.

        Выполнять строго после transform_text_body.
        '''
        body = self.tei_soup.find("div", type="text")
        letter_declarations = body.find_all('h4', attrs={'l': '1'})

        for letter_declaration in letter_declarations:
            letter_declaration.name = 'div'
            letter_declaration.attrs['type'] = 'letter'

            current_tag = letter_declaration.next_sibling

            while current_tag and (current_tag.name != 'h4' or current_tag.attrs['l'] != "1"):
                next_tag = current_tag.next_sibling
                letter_declaration.append(current_tag)
                current_tag = next_tag

    def mark_up_dates(self):
        """
        Разметка основных дат

        Выполнять после populate_tei_header,
        т. к. к этому моменту размечена дата внутри <creation>,
        которая тут скопируется в дату <opener>
        """
        date_paragraphs = self.tei_soup.find_all('p', class_=["dat1ot2", "date", "dateot", "dateot2", "dateotr"])
        wrapped_date_paragraphs = []

        for paragraph in date_paragraphs:
            paragraph.name = "date"
            wrapped_paragraph = paragraph.wrap(self.tei_soup.new_tag("p", attrs=paragraph.attrs))
            wrapped_date_paragraphs.append(wrapped_paragraph)
            paragraph.attrs = {}
        
        for paragraph in wrapped_date_paragraphs:
            parent = paragraph.parent
            parent_first_child = BeautifulSoupUtils.get_first_tagged_child(parent)

            if paragraph is parent_first_child:
                paragraph.name = 'dateline'

                opener_wrapper = self.tei_soup.new_tag("opener", attrs={
                    'class': paragraph.attrs['class'] if 'class' in paragraph.attrs else False,
                })

                paragraph.attrs = {}
                paragraph.wrap(opener_wrapper)

                creation_element = self.tei_soup.find("creation")
                creation_date_element = creation_element.find("date")
                opener_date_element = paragraph.find("date")
                opener_date_element.attrs = copy.copy(creation_date_element.attrs)
                

    def mark_up_closers(self):
        """
        Разметка подписей
        """
        sign_classes = ["podp", "podp2ot", "podpot"]

        if self.source_url == "http://feb-web.ru/feb/tolstoy/critics/tpt/tpt2445-.htm?cmd=p":
            sign_classes.append("podp1ot")

        sign_paragraphs = self.tei_soup.find_all('p', class_=sign_classes)

        for paragraph in sign_paragraphs:
            paragraph.name = "signed"
            opener_wrapper = self.tei_soup.new_tag("closer", attrs=paragraph.attrs)
            paragraph.attrs = {}
            paragraph.wrap(opener_wrapper)
    
    def remove_html_parts(self):
        '''
        Удаление второстепенных HTML-элементов.
        '''
        feb_logo_element = self.tei_soup.select_one('center')
        feb_logo_element.decompose()

        body_element = self.tei_soup.select_one('text > body')
        line_breaks = body_element.find_all('br', recursive=False)

        for line_break in line_breaks:
            line_break.decompose()

        description_element = self.tei_soup.select_one('div.description')
        description_element.decompose()

        prose_element = self.tei_soup.select_one('#prose')
        prose_element.unwrap()

    def transform_linebreaks(self):
        '''
        Конвертация тегов переноса строки в TEI-эквивалент.
        '''
        brs = self.tei_soup.select('br')

        for br in brs:
            br.name = 'lb'

    def clear_unknown_paragraph_attributes(self):
        '''
        Удаление не относящихся к спецификации TEI атрибутов абзацев
        '''
        paragraphs = self.tei_soup.select('p')

        for paragraph in paragraphs:
            paragraph.attrs = {}

    def clear_class_attributes(self):
        '''
        Удаление атрибутов class.
        '''
        class_tags = self.tei_soup.select('[class]')

        for class_tag in class_tags:
            del class_tag.attrs['class']
    
    def transform_id_attributes(self):
        '''
        Замена атрибутов id на TEI-эквивалент: xml:id
        '''
        tags_with_id = self.tei_soup.select('[id]')

        for tag in tags_with_id:
            id_value = tag.attrs['id']
            tag.attrs['xml:id'] = id_value
            del tag.attrs['id']
    
    def transform_links(self):
        '''
        Замена HTML-ссылок на TEI-эквивалент
        '''
        links = self.tei_soup.select('a')

        for link in links:
            link.name = 'ref'

            if 'href' in link.attrs:
                href = link.attrs['href']
                link.attrs['target'] = href
                del link.attrs['href']
            elif 'target' not in link.attrs:
                logging.warning(f"A link found with neither 'href' nor 'target' attribute: {repr(link)} - at {self.source_url}")

