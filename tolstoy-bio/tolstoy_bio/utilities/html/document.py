from tolstoy_bio.utilities.html.utils import HtmlUtils
from tolstoy_bio.utilities.io import IoUtils


class HtmlDocument:
    """
    Сущность HTML-документа с ссылкой на оригинальный ресурс, 
    исходным HTML-кодом и данными об исходной кодировке.

    Позволяет сохранить HTML в файл с предобработкой:
    - добавлением URL ссылки в <base> для упрощения последующего доступа к медиа-ресурсам и ссылкам;
    - автоматической нормализацией и форматированием кода через выбранный парсер;
    - конвертацией в нужную кодировку.
    """


    def __init__(self, html: str, url: str = None, source_encoding: str = None):
        self._html = html
        self.url = url
        self.source_encoding = source_encoding or 'utf-8'

    def get_source_html(self):
        if self.url is None:
            return self._html
        
        return HtmlUtils.add_base_url(self._html, self.url)
    
    def get_normalized_html(self, normalizer: str = None):
        html = self.get_source_html()
        return HtmlUtils.normalize(html, self.source_encoding, normalizer=normalizer)
    
    def save_source_html(self, path: str, target_encoding: str = None) -> None:
        html = self.get_source_html()
        IoUtils.save_textual_data(html, path, target_encoding)

    def save_normalized_html(self, path: str, target_encoding: str = None, normalizer: str = None) -> None:
        html = self.get_normalized_html(normalizer)
        IoUtils.save_textual_data(html, path, target_encoding)
