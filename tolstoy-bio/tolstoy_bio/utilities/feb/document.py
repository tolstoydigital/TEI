from tolstoy_bio.utilities.html.document import HtmlDocument


class FebHtmlDocument(HtmlDocument):
    """
    Сущность HTML-ресурса с ФЭБ-портала с оригинальным URL, 
    исходным HTML-кодом и данными об исходной кодировке.

    Повторяет логику HtmlDocument, но умолчанию предусматривает
    исходную кодировку 'windows-1251', свойственную документам ФЭБ.
    """

    def __init__(self, url: str, html: str, source_encoding: str = None):
        super().__init__(
            url=url, 
            html=html, 
            source_encoding=source_encoding or 'windows-1251'
        )
