import os
import sys
from pathlib import Path

from lxml import etree

# Абсолютный путь к текущему файлу
BASE_DIR = Path(__file__).resolve().parent
TOP_DIR = BASE_DIR.parent

def check_xml_file(path):
    """Проверяет XML-файл и возвращает список ошибок."""
    parser = etree.XMLParser(recover=True)
    try:
        etree.parse(path, parser)
    except etree.XMLSyntaxError:
        pass  # ошибки всё равно есть в parser.error_log
    return list(parser.error_log)

def walk_and_check(directory):
    """Рекурсивно обходит папку и проверяет все .xml файлы."""
    for root, _, files in os.walk(directory):
        for name in files:
            if name.lower().endswith(".xml"):
                full_path = os.path.join(root, name)
                errors = check_xml_file(full_path)
                short_path = Path(full_path).relative_to(TOP_DIR)
                if errors:
                    print(f"\n❌ {short_path}")
                    for err in errors:
                        print(f"   Line {err.line}, Column {err.column}: {err.message}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python check_xml_wellformed_all_errors.py /path/to/xml_dir")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Ошибка: {directory} не является директорией.")
        sys.exit(1)

    print(f"Проверяю XML-файлы в каталоге: {directory}\n")
    walk_and_check(directory)
    print("\n✅ Проверка завершена.")
