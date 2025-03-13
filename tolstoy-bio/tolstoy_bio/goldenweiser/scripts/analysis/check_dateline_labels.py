import os

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.dates import DateUtils
from tolstoy_bio.utilities.io import IoUtils


XML_DOCUMENT_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/goldenweiser-diaries_1896_1910.xml'))

def main():
    check_dateline_labels()


def check_dateline_labels():
    xml = BeautifulSoupUtils.create_soup_from_file(XML_DOCUMENT_PATH, "xml")
    datelines = xml.find_all('dateline')

    for dateline in datelines:
        if not dateline.find('date'):
            print(dateline)

    labels = sorted(set([dateline.find('date').text.strip() for dateline in datelines]))
    dates = [DateUtils.convert_russian_day_month_label_to_date(label) for label in labels]

    IoUtils.save_textual_data(
        content='\n-----\n'.join([f'{label}\n{date}' for label, date in zip(labels, dates)]), 
        path=os.path.abspath(os.path.join(__file__, '../dateline_labels.txt'))
    )


if __name__ == '__main__':
    main()