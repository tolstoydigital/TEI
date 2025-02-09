class Source:
    _index: str | None = None
    _id: str | None = None
    _main_title: str | None
    _bibliographic_title: str | None
    _author: str | None
    _editor: str | None
    _work: str | None
    _anthology: str | None
    _publisher: str | None
    _volume: str | None
    _publication_place: str | None
    _publication_date: str | None
    _storage: str | None

    def __init__(
        self,
        index: str | None,
        main_title: str | None,
        bibliographic_title: str | None,
        author: str | None,
        editor: str | None,
        work: str | None,
        anthology: str | None,
        publisher: str | None,
        volume: str | None,
        publication_place: str | None,
        publication_date: str | None,
        storage: str | None,
        id: str | None = None,
    ):
        self._index = index
        self._id = id
        self._main_title = main_title.strip() or None
        self._bibliographic_title = bibliographic_title.strip() or None
        self._author = author.strip() or None
        self._editor = editor.strip() or None
        self._work = work.strip() or None
        self._anthology = anthology.strip() or None
        self._publisher = publisher.strip() or None
        self._volume = volume.strip() or None
        self._publication_place = publication_place.strip() or None
        self._publication_date = publication_date.strip() or None
        self._storage = storage.strip() or None

    def __repr__(self):
        return f"Source(index={self.index}, id={self.id}, main_title={self.main_title}, bibliographic_title={self.bibliographic_title}, author={self.author}, editor={self.editor}, work={self.work}, anthology={self.anthology}, publisher={self.publisher}, volume={self.volume}, publication_place={self.publication_place}, publication_date={self.publication_date}, storage={self.storage})"

    @property
    def index(self) -> str | None:
        return self._index

    @property
    def id(self) -> str | None:
        return self._id

    @property
    def main_title(self) -> str | None:
        return self._main_title

    @property
    def bibliographic_title(self) -> str | None:
        return self._bibliographic_title

    @property
    def author(self) -> str | None:
        return self._author

    @property
    def editor(self) -> str | None:
        return self._editor

    @property
    def work(self) -> str | None:
        return self._work

    @property
    def anthology(self) -> str | None:
        return self._anthology

    @property
    def publisher(self) -> str | None:
        return self._publisher

    @property
    def volume(self) -> str | None:
        return self._volume

    @property
    def publication_place(self) -> str | None:
        return self._publication_place

    @property
    def publication_date(self) -> str | None:
        return self._publication_date

    @property
    def storage(self) -> str | None:
        return self._storage

    def set_id(self, id: str) -> None:
        if self._id is not None:
            raise ValueError("Source id cannot be changed after being set.")

        self._id = id
