"""
Скрипт для автоматического скачивания коллекции писем Толстой с ФЭБ,
насчитывающую около 500 записей, в папку ../data/source_html.

Ориентируясь на HTML-фрагмент ФЭБ-оглавления, 
автоматически собирает ссылки на письма, сгруппированные по годам,
и скачивает HTML-разметку с сохранением исходного URL.
"""


import collections
import dataclasses
import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.feb.provider import FebHtmlProvider


@dataclasses.dataclass
class LetterSource:
    title: str
    url: str


def main():
    collect_letter_sources_grouped_by_year()


def collect_letter_sources_grouped_by_year():
    table_of_contents_soup = parse_table_of_contents()
    navigation_links_by_year = parse_navigation_links_for_each_year(table_of_contents_soup)
    letter_sources_by_year = parse_letter_sources_by_year(navigation_links_by_year)
    download_letter_sources_by_year(letter_sources_by_year)


def parse_table_of_contents():
    table_of_contents_path = os.path.abspath(os.path.join(__file__, '../raw_table_of_contents.html'))
    with open(table_of_contents_path, 'r', encoding='utf-8') as file:
        content = file.read()
        return bs4.BeautifulSoup(content, 'lxml')
    

def parse_navigation_links_for_each_year(table_of_contents_soup):
    years = table_of_contents_soup.select('div.close')

    urls_by_year = {}

    for year in tqdm(years, desc='Parsing navigation links for each year'):
        link = year.find('a')
        url = f"http://feb-web.ru/feb/common/tree.asp?{remove_query_parameters(link['href'])}"
        year_label = link.text.strip()
        urls_by_year[year_label] = url
    
    return urls_by_year


def remove_query_parameters(url: str) -> str:
    return re.sub(r'\?.*$', '', url)


def parse_letter_sources_by_year(urls_by_year):
    letter_sources_by_year = collections.defaultdict(list)

    for year, url in tqdm(urls_by_year.items(), desc='Parsing letter links for each year'):
        sources = parse_letter_sources(url)
        letter_sources_by_year[year] = sources
    
    return letter_sources_by_year


def parse_letter_sources(navigation_url):
    provider = FebHtmlProvider()
    
    document = provider.get(navigation_url)
    html = document.get_source_html()
    soup = bs4.BeautifulSoup(html, 'lxml')
    letter_list = soup.find_all('div', {'class': 'open'})[-1]

    sources = []

    for letter_element in letter_list.select('.docs'):
        letter_link = letter_element.select_one('a')
        letter_url = letter_link.attrs['href']
        letter_title = letter_link.text.strip().encode('latin-1').decode('windows-1251')
        sources.append(LetterSource(letter_title, letter_url))
    
    return sources


def download_letter_sources_by_year(letter_sources_by_year):
    for year, letters in tqdm(letter_sources_by_year.items(), desc='Saving HTMLs'):
        download_letter_sources(letters, year)


def download_letter_sources(letter_sources, year):
    provider = FebHtmlProvider()

    base_url = 'http://feb-web.ru'
    source_html_saving_path = os.path.abspath(os.path.join(__file__, '../../../data/source_html/raw'))
    normalized_html_saving_path = os.path.abspath(os.path.join(__file__, '../../../data/source_html/normalized'))

    for letter in letter_sources:
        letter_path = f'{year}/{letter.title}.html'
        
        absolute_url = remove_query_parameters(base_url + letter.url)
        letter_document = provider.get(absolute_url)
        letter_document.save_source_html(os.path.join(source_html_saving_path, letter_path))
        letter_document.save_normalized_html(os.path.join(normalized_html_saving_path, letter_path))


if __name__ == '__main__':
    main()
