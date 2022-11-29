from pathlib import Path


REPO_PATH = Path('..')


def convert_language_to_iso(language: str) -> str:
    languages = {
        'english': 'en',
        'french': 'fr',
        '': 'ru'
    }
    return languages[language] if language in languages else language


def read_xml(xml, mode='r'):
    with open(xml, mode) as file:
        return file.read()
