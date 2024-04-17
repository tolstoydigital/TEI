import copy
import logging
import re

import bs4

from tolstoy_bio.utilities.io import IoUtils


logging.basicConfig(level=logging.INFO, filename="errors.log", filemode="w")


class FebHtmlToTeiXmlConverter:
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
            self.transform_notes,
            self.transform_footnotes,
            self.transform_styles,
            self.divide_into_letters,
            self.mark_up_letter_datelines,
            self.group_months,
            self.transform_title,
            self.transform_text_body,
            self.remove_html_parts,
            self.transform_linebreaks,
            self.populate_tei_header,
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
                        <author>Маковицкий Душан Петрович</author>
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

        for continuation_paragraph in continuation_paragraphs:
            if continuation_paragraph.parent.name == 'td':
                continue

            page_marker = continuation_paragraph.find_previous('pb')
            starting_paragraph = continuation_paragraph.find_previous_sibling('p', class_=re.compile(r'^text1?$'))
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

            image = images[0]

            try:
                if image.attrs['src'] == '/images/logoPRN.gif':
                    continue
            except:
                print(image)
                raise RuntimeError

            graphic = self.tei_soup.new_tag('graphic', attrs={
                'url': image.attrs['src'],
            })

            if image.has_attr('alt'):
                fig_desc = self.tei_soup.new_tag('figDesc')
                fig_desc.string = image.attrs['alt']
                image.append(fig_desc)

            image.name = 'figure'
            image.append(graphic)

            if image.has_attr('alt'):
                fig_desc = self.tei_soup.new_tag('figDesc')
                fig_desc.string = image.attrs['alt']
                image.append(fig_desc)

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
        note_links = [link for link in links if self.is_href_to_volume_notes(link.attrs['href'])]
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

            if anchor_element is None:
                raise RuntimeError('Failed to find the note')

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

                if re.match(r'^txt8', next_paragraph_class):
                    note_paragraphs.append(next_paragraph)

                next_paragraph = next_paragraph.next_sibling

            for i in range(len(note_paragraphs) - 1, 0, -1):
                prev_note = note_paragraphs[i - 1]
                next_note = note_paragraphs[i]

                if next_note.attrs['class'] == 'txt8-0':
                    prev_note.extend(next_note.contents)
                    prev_note.smooth()
                    note_paragraphs.pop()

            for note_paragraph in note_paragraphs:
                note.append(note_paragraph)

            for paragraph in note.select('p'):
                paragraph.attrs = {}

            note_link_number = note_link.string.strip()
            note_number_container = note.find('sup')

            if note_number_container:
                note_number = note_number_container.string.strip()

                if note_number == note_link_number:
                    note_number_container.decompose()

            note_link.insert_after(note)
    
    @staticmethod
    def is_href_to_volume_notes(value):
        return bool(re.search(r'\.html?#', value))

    def transform_footnotes(self):
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

        for i, footnote in enumerate(footnotes, 1):
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
            if footnote_anchor:
                self.delete_element_and_its_empty_parents(footnote_anchor)

            try:
                footnote_link = next(
                    link for link in links if 'href' in link.attrs and link.attrs['href'] == f'#{footnote_html_id}')
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

    def divide_into_letters(self):
        '''
        Внутреннее структурное разделение документа на блоки-записи.
        '''
        letter_headlines = self.tei_soup.find_all('h4', attrs={'l': '2'})

        for letter_headline in letter_headlines:
            letter_headline.name = 'div'
            letter_headline.attrs['type'] = 'entry'

            current_tag = letter_headline.next_sibling

            while current_tag and current_tag.name != 'h4':
                next_tag = current_tag.next_sibling
                letter_headline.append(current_tag)
                current_tag = next_tag

    def mark_up_letter_datelines(self):
        '''
        Разметка и парсинг указания дат в начале писем.

        Ввиду необходимости структурных трансформаций
        этот шаг должен строго следовать разделению документа на блоки-письма (divide_into_letters)
        '''
        letters = self.tei_soup.find_all('div', attrs={'type': 'entry'})

        for letter in letters:
            letter_dateline_label = letter.attrs['title']
            letter_date_code = letter.attrs['id']
            parsed_date = self.parse_date_code(letter_date_code)

            dateline = letter.find('hi', attrs={'rend': 'bold'})

            if letter_dateline_label not in dateline.string:
                logging.warning(f'Ambiguous dateline. '
                                f'Text "{dateline.string}" marked with date "{letter_dateline_label}"')

            date_container = self.tei_soup.new_tag('date', attrs={'when': parsed_date})
            dateline.wrap(date_container)
            letter.attrs = {'type': 'entry'}
        
    @staticmethod
    def parse_date_code(code):
        '''
        Парсинг даты в ISO-формат.
        '''
        year_label, month_label, date_label = code.lower().split('.')

        month_label_to_index = {
            'январь': '1',
            'февраль': '2',
            'март': '3',
            'апрель': '4',
            'май': '5',
            'июнь': '6',
            'июль': '7',
            'август': '8',
            'сентябрь': '9',
            'октябрь': '10',
            'ноябрь': '11',
            'декабрь': '12'
        }

        month_index = month_label_to_index[month_label]
        day_index_match = re.search('\d+', date_label)

        if day_index_match is None:
            # TODO: 1910.Сентябрь.Сентябрь -- вручную убрать город из <date> в М1910
            logging.warning(f'Failed to parse entry date {code}')
            return f"{year_label}-{month_index.zfill(2)}"

        day_index = day_index_match.group()

        return '-'.join([year_label, month_index.zfill(2), day_index.zfill(2)])

    def group_months(self):
        '''
        Внутреннее структурное разделение документа на блоки-месяцы.
        '''
        month_headlines = self.tei_soup.find_all('h4', attrs={'l': '1'})

        for month_headline in month_headlines:
            month_headline.name = 'div'
            month_headline.attrs = {'type': 'month'}

            current_tag = month_headline.next_sibling

            while current_tag and current_tag.name != 'h4':
                next_tag = current_tag.next_sibling
                month_headline.append(current_tag)
                current_tag = next_tag

    def transform_title(self):
        '''
        Разметка названия годового дневника.
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

        # wrap the contents into <date>
        title_text = title_paragraph.string.strip()
        title_date = self.tei_soup.new_tag('date', attrs={'when': title_text})
        title_date.string = title_text
        title_paragraph.clear()
        title_paragraph.append(title_date)

        title_headline.unwrap()

    def transform_text_body(self):
        '''
        Разметка названия годового дневника.
        '''
        body_headline = self.tei_soup.find('h4', id="Текст")
        body_headline.name = 'div'
        body_headline.attrs = {'type': 'text'}

        current_tag = body_headline.next_sibling

        while current_tag and current_tag.name != 'h4':
            next_tag = current_tag.next_sibling
            body_headline.append(current_tag)
            current_tag = next_tag

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
            href = link.attrs['href']
            link.attrs['target'] = href
            del link.attrs['href']