import requests

from tolstoy_bio.utilities.feb.document import FebHtmlDocument
from tolstoy_bio.utilities.html.provider import HtmlProvider


class FebHtmlProvider(HtmlProvider):
    """
    Скачивает HTML печатной версии документа портала ФЭБ по ссылке
    с подготовленными заголовками для обхода возможной блокировки автоматического парсинга.
    """


    def get(self, url: str) -> FebHtmlDocument:
        response = requests.get(
            url, 
            headers=self.REQUEST_HEADERS,
            params={'cmd': 'p'}, 
        )

        response.raise_for_status()
        
        return FebHtmlDocument(
            url=response.url, 
            html=response.text, 
            source_encoding=response.apparent_encoding
        )
