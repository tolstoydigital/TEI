import os
from typing import Generator

from .tei_document import TeiDocument


class TeiRepository:
    def __init__(self, path: str) -> None:
        self._path = path

    def get_documents(self) -> list[TeiDocument]:
        return list(self.get_document_iterator())
    
    def count_documents(self) -> int:
         return len(list(self._get_document_path_iterator()))

    def _get_document_path_iterator(self):
        for folder_path, _, filenames in os.walk(self._path):
            if not filenames:
                continue

            for filename in filenames:
                if filename == "template.xml":
                    continue

                yield os.path.join(folder_path, filename)

    def get_document_iterator(self) -> Generator[TeiDocument, None, None]:
        for document_path in self._get_document_path_iterator():
            yield TeiDocument(document_path)
