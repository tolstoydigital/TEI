import os

from tolstoy_bio.utilities.io import IoUtils

from .gusev_tei_document import GusevTeiDocument


class GusevTeiRepository:
    _path: str

    _DEFAULT_PATH: str = os.path.join(os.path.dirname(__file__), "../../gusev/data/tei")

    def __init__(self, path: str | None = None) -> None:
        self._path = path if path else self._DEFAULT_PATH

    def get_documents(self) -> list[GusevTeiDocument]:
        paths = IoUtils.get_folder_contents_paths(self._path)
        return [GusevTeiDocument(path) for path in paths]