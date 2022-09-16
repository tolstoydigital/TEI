import os
import re

OLD_FORMAT = re.compile(r'(<hi style="npnumber">)(\d+)(</hi>)')
NEW_FORMAT = r'<pb n="\2"/>'
FOLDER_PATH = '../letters_and_diaries_new/letters/'

def fix_pages(doc):
    doc = re.sub(OLD_FORMAT, NEW_FORMAT, doc)
    return doc


def main():
    for filename in os.listdir(FOLDER_PATH):
        doc = open(os.path.join(FOLDER_PATH, filename), encoding='utf-8').read()
        doc = fix_pages(doc)
        with open(os.path.join(FOLDER_PATH, filename), 'w', encoding='utf-8') as f:
            f.write(doc)

if __name__ == "__main__":
    main()