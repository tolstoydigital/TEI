import requests

from tolstoy_bio.utilities.html.document import HtmlDocument


class HtmlProvider:
    """
    Скачивает HTML по ссылке с подготовленными заголовками 
    для обхода возможной блокировки автоматического парсинга.
    """


    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    def get(self, url: str) -> HtmlDocument:
        """
        Скачивает исходный HTML по ссылке и возвращает объект документа.
        """

        response = requests.get(url, headers=self.REQUEST_HEADERS)
        response.raise_for_status()
        
        return HtmlDocument(
            url=response.url, 
            html=response.text, 
            source_encoding=response.apparent_encoding
        )
