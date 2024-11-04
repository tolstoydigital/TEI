import codecs
import json
import os


class IoUtils:
    """
    Общие функции для работы с файловой системой.
    """


    DEFAULT_TEXT_ENCODING = 'utf-8'

    @classmethod
    def read_as_text(cls, path: str, encoding: str = None) -> str:
        '''
        Выводит содержание текстового файла в заданной кодировке (по умолчанию UTF).
        '''
        target_encoding = encoding or cls.DEFAULT_TEXT_ENCODING
        with open(path, 'r', encoding=target_encoding) as file:
            return file.read()

    @classmethod
    def save_textual_data(cls, content: str, path: str, encoding: str = None) -> str:
        '''
        Сохраняет текст в файл в заданной кодировке (по умолчанию UTF)
        c коррекцией при конвертации из другой кодировки.
        '''
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)

        target_encoding = encoding or cls.DEFAULT_TEXT_ENCODING
        with codecs.open(path, 'w', encoding=target_encoding) as file:
            file.write(content)

    @staticmethod
    def save_as_json(data, path: str, *, indent: int | None = None) -> None:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)

        with open(path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)

    @classmethod
    def get_folder_contents_names(cls, folder_path: str, ignore_hidden=True) -> list[str]:
        names = os.listdir(folder_path)
        
        if ignore_hidden:
            return [name for name in names if not name.startswith('.')]

        return names

    @classmethod
    def get_folder_contents_paths(cls, folder_path: str, ignore_hidden=False) -> list[str]:
        content_names = cls.get_folder_contents_names(folder_path, ignore_hidden)
        return [os.path.join(folder_path, name) for name in content_names]
    
    @staticmethod
    def is_existent_path(path: str) -> bool:
        return os.path.exists(path)
