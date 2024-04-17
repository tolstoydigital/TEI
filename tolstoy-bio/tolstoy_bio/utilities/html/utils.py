import re

import bs4


class HtmlUtils:
    """
    Общие функции обработки HTML-разметки.
    """


    @staticmethod
    def add_base_url(html: str, url: str):
        '''
        Создаёт тег <base> с ссылкой для корректного обращения к медиа-ресурсам.
        '''
        return re.sub(r'<head>', f'<head><base href="{url}">', html, flags=re.IGNORECASE)
    
    @staticmethod
    def normalize(html: str, source_encoding: str = None, normalizer: str = None):
        '''
        Нормализует отображение и корректирует ошибки разметки исходного HTML. 
        '''
        source_encoding = source_encoding or 'utf-8'
        normalizer = normalizer or 'lxml'

        encoded_html = html.encode(source_encoding)
        
        soup = bs4.BeautifulSoup(
            encoded_html, 
            normalizer, 
            from_encoding=source_encoding
        )

        return soup.prettify()
