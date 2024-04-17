import os
import re

import bs4
from tqdm import tqdm
from tolstoy_bio.utilities.array import ArrayUtils
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


MONTH_NAMES_IN_GENETIVE_CASE = [
    'января', 
    'февраля', 
    'марта', 
    'апреля', 
    'мая', 
    'июня', 
    'июля', 
    'августа', 
    'сентября', 
    'октября', 
    'ноября', 
    'декабря'
]


SHORTENED_MONTH_NAMES = [
    'янв',
    'фев',
    'мар',
    'апр',
    'мая',
    'июн',
    'июл',
    'авг',
    'сен',
    'окт',
    'ноя',
    'дек',
]


class GoldenweiserIntermediateMarkupGenerator:
    def convert_to_xml(self):
        steps = [
            self.load_raw_source_html,
            self.create_primary_xml_soup,
            self.convert_root_element,
            self.convert_body_element,
            self.create_tei_header,
            self.delete_source_html_body_wrapper,
            self.delete_empty_non_paragraphs,
            self.delete_scripts,
            self.delete_smalls,
            self.delete_comments,
            self.normalize_paragraphs,
            self.mark_up_years,
            self.fix_detached_day_labels,
            self.fix_paragraph_continuations_merged_into_days,
            self.mark_up_dates,
            self.mark_up_letters_mentioning,
            self.mark_up_headings,
        ]

        for step in tqdm(steps):
            step()

    def load_raw_source_html(self) -> str:
        relative_path = '../../../data/source_html/raw/diary.html'
        absolute_path = os.path.abspath(os.path.join(__file__, relative_path))
        assert IoUtils.is_existent_path(absolute_path), "Raw source HTML file does not exist"
        self.raw_source_html = IoUtils.read_as_text(absolute_path)

    def create_primary_xml_soup(self):
        content_start_index = self.raw_source_html.find("<div id='frd'>")
        content_end_index = self.raw_source_html.find("<br><h3>Оглавление</h3>")
        content = self.raw_source_html[content_start_index:content_end_index]
        content_soup = bs4.BeautifulSoup(content, 'html5lib')
        prettified_content = content_soup.prettify()
        self.string_to_xml_soup(prettified_content)

    def convert_root_element(self):
        '''
        Конвертация корневого элемента в TEI.
        '''
        root = self.xml_soup.find('html')

        root.name = 'TEI'
        root.attrs = {
            'xmlns': 'http://www.tei-c.org/ns/1.0',
            'xmlns:xi': 'http://www.w3.org/2001/XInclude',
            'xmlns:svg': 'http://www.w3.org/2000/svg',
            'xmlns:math': 'http://www.w3.org/1998/Math/MathML',
        }

    def convert_body_element(self):
        '''
        Оборачивает содержимое <body> в <text>.
        '''
        body_element = self.xml_soup.find('body')
        text_element = self.xml_soup.new_tag('text')

        body_element.wrap(text_element)
        body_element.attrs = {}

    def create_tei_header(self):
        '''
        Добавляет мета-шапку <teiHeader>
        '''
        tei_header = bs4.BeautifulSoup(f'''
            <teiHeader>
                <fileDesc>     
                <titleStmt>
                    <title>Вблизи Толстого. (Записки за пятнадцать лет)</title>
                    <title xml:id="goldenweiser-diaries_1896_1910"/>
                </titleStmt>
                <sourceDesc>
                    <biblStruct>
                    <analytic>
                        <author>Александр Борисович Гольденвейзер</author>
                    </analytic>
                    </biblStruct>         
                </sourceDesc>
                </fileDesc>
                <profileDesc>
                    <creation>
                        <date from="1896" to="1910" />
                    </creation>
                    <textClass>
                        <catRef ana="#diaries" target="type" />
                    </textClass>
                </profileDesc>  
            </teiHeader>''', 'xml')
        
        self.xml_soup.find('TEI').insert(0, tei_header)

    def delete_source_html_body_wrapper(self):
        '''
        Удаляет исходную HTML-обёртку вокруг содержания.
        '''
        source_wrapper = self.xml_soup.find('div', id='frd')
        source_wrapper.unwrap()

    def delete_empty_non_paragraphs(self):
        '''
        Удаляет все пустые элементы кроме пустых абзацев:
        они далее будут использоваться для нормализации абзацев
        '''
        elements = self.xml_soup.find_all()

        for element in elements:
            if not element.name == 'p' and not element.text.strip():
                element.decompose()
    
    def delete_scripts(self):
        '''
        Удаляет <script>-теги
        '''
        scripts = self.xml_soup.find_all('script')

        for element in scripts:
            element.decompose()

    def delete_smalls(self):
        '''
        Удаляет <small>-элементы.
        В них содержится функционал возвращения назад к оглавлению.
        '''
        scripts = self.xml_soup.find_all('small')

        for element in scripts:
            element.decompose()

    def delete_comments(self):
        '''
        Удаляет технические комментарии.
        В данном документе они не несут смысловой нагрузки.
        '''
        content = self.xml_soup_to_string()
        no_comment_content = re.sub(r'<!--.*?-->', '', content)
        no_empty_line_content = re.sub(r'\n+', '\n', no_comment_content)
        self.string_to_xml_soup(no_empty_line_content)

    def normalize_paragraphs(self):
        '''
        Локализует и оборачивает абзацы в тег <p>
        '''
        content = self.xml_soup_to_string()
        content = re.sub(r'\n+', '\n', content)

        paragraph_separator_marker = '%paragraph_separator%'
        marked_content = re.sub(r'<p>[\n\s]*<\/p>', paragraph_separator_marker, content)
        lines = marked_content.split('\n')

        first_paragraph_separating_line_index = ArrayUtils.find_index(lines, lambda line: paragraph_separator_marker in line)
        assert first_paragraph_separating_line_index >= 1, 'Unexpected paragraph separator position'
        lines.insert(first_paragraph_separating_line_index - 1, '<p>')

        count = 0

        for i, line in enumerate(lines):
            if paragraph_separator_marker in line:
                count += 1
                lines[i] = line.replace(paragraph_separator_marker, '</p><p>')

        self.string_to_xml_soup('\n'.join(lines))

        paragraphs = self.xml_soup.find_all('p')

        for element in paragraphs:
            if not element.text.strip():
                element.decompose()

    def mark_up_years(self):
        '''
        Размечает маркеры годов в утилити-элемент <year>
        '''
        year_elements = self.xml_soup.find_all("h3", class_="book")

        for element in year_elements:
            if re.match(r'\d{4}', element.text.strip()):
                element.name = 'year'
                element.attrs = {}

    def fix_detached_day_labels(self):
        '''
        Исправляет случаи, в которых день отделён от остальной даты.
        Например, 1 <i><b>января</b></i> приводит в <i><b>1 января</b></i>
        '''
        content = self.xml_soup_to_string()
        single_line_content = re.sub(r'\s+', ' ', content)
        fixed_bold_content = re.sub(r'(\d\d?|II?)\s*<i>\s*<b>', r'<i><b>\1', single_line_content)
        fixed_italic_content = re.sub(r'(\d\d?|II?)\s*<i>', r'<i>\1', fixed_bold_content)
        self.string_to_xml_soup(fixed_italic_content)

    def fix_paragraph_continuations_merged_into_days(self):
        '''
        Исправляет случаи, в которых местоимение "Я" слито с датой.
        '''
        content = self.xml_soup_to_string()
        single_line_content = re.sub(r'\s+', ' ', content)
        fixed_bold_content = re.sub(r'(?<=\s)(я)\s*</b>\s*</i>', r'</b></i>\1', single_line_content, flags=re.I)
        fixed_italic_content = re.sub(r'(?<=\s)(я)\s*</i>', r'</i>\1', fixed_bold_content, flags=re.I)
        self.string_to_xml_soup(fixed_italic_content)

    def mark_up_dates(self):
        '''
        Размечает даты внутри <i>-элементов как <susp> или <date>
        '''
        highlighted_elements = self.xml_soup.find_all('i')

        for element in highlighted_elements:
            content = element.text.strip()

            if re.search(r'\d', content):
                element.wrap(self.xml_soup.new_tag("susp"))
        
        for year in self.xml_soup.find_all('year'):
            next_sibling = BeautifulSoupUtils.get_next_tag_sibling(year)

            if next_sibling and next_sibling.name == 'susp':
                next_sibling.name = 'date'

        content = self.xml_soup_to_string()
        content_length_before_transformations = len(content)

        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'<p>\s*(—)?\s*<susp> (.*?) </susp>', r'<p> \1 <suspAfterP> \2 </suspAfterP>', content)
        self.string_to_xml_soup(content)

        for susp_after_p in self.xml_soup.find_all('suspAfterP'):
            if susp_after_p.text.strip().endswith('.'):
                susp_after_p.name = 'date'
            else:
                susp_after_p.name = 'susp'

        assert (content_length_before_transformations := len(self.xml_soup_to_string())) == content_length_before_transformations, f'Content length has changed after the transformation. Was {content_length_before_transformations}, become {content_length_before_transformations}'

        # TODO: доделать разметку дат вне <i>-тегов
        
        # date_pattern = self._get_date_regular_expression()

        # for text in self.xml_soup.find_all(text=True):
        #     if BeautifulSoupUtils.has_parent_with_tag_name(text, 'date', 'susp'):
        #         continue
            
        #     if match := date_pattern.search(text.string):
        #         start_index = match.start()
        #         end_index = match.end()

        #         wrapper = self.xml_soup.new_tag("suspre")
        #         wrapper.string = match.group

        #         text.replace_with(date_pattern.sub(r'<suspre>\0</suspre>', text.string))

    def _get_date_regular_expression(self):
        full_month = '|'.join(MONTH_NAMES_IN_GENETIVE_CASE)
        shortened_month = '|'.join(SHORTENED_MONTH_NAMES)
        return re.compile(rf'(\d\d?(-(о?го|о?е|о?му))?\s+({full_month}|{shortened_month}))', flags=re.IGNORECASE)

    def mark_up_letters_mentioning(self):
        '''
        Находит слова "письмо" и "письмецо" в разных склонениях
        и оборачивает их в тег <ltr>
        '''
        content = self.xml_soup_to_string()
        content = re.sub(r'\s+', ' ', content)
        tokens = content.split()

        for i, token in enumerate(tokens):
            if re.match(r'^(письмом?|письма(х|м|ми)?|писем|письму|письме|письмец[оауе]?|письмец[оа]м|письмецами|письмецах)$', token, flags=re.IGNORECASE):
                tokens[i] = f'<ltr>{token}</ltr>'
        
        content = ' '.join(tokens)
        self.string_to_xml_soup(content)

    def mark_up_headings(self):
        '''
        Разметка тегов <h3 class="book"> в TEI-тег <head>
        '''
        headings = self.xml_soup.find_all('h3')

        for element in headings:
            element.name = 'head'
            element.attrs = {}
    
    def xml_soup_to_string(self):
        return self.xml_soup.prettify()
    
    def string_to_xml_soup(self, string: str):
        self.xml_soup = bs4.BeautifulSoup(string, 'xml')


    












