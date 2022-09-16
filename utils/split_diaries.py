import os
from bs4 import BeautifulSoup as BS

FOLDER_PATH = '../letters_and_diaries_new/diaries/'
TEI_STRUCTURE = '''<?xml version='1.0' encoding='UTF-8' standalone='no'?>

<TEI xmlns="http://www.tei-c.org/ns/1.0">
       <teiHeader>
          <fileDesc>
             <titleStmt>
                <title>Дневник</title>
             </titleStmt>
             <publicationStmt>
                <publisher>TolstoyLab</publisher>
                <date when="2015-09-14">14 September 2015</date>
             </publicationStmt>
             <sourceDesc>
                <biblStruct>
                   <analytic>
                      <author>Толстой Л.Н.</author>
                   </analytic>
                   <monogr>
                      <title level="m">Полное собрание сочинений. Том 46</title>
                      <imprint>
                         <pubPlace>Москва</pubPlace>
                         <publisher>Государственное издательство "Художественная литература"</publisher>
                             <date when="1935"/>
                      </imprint>
                   </monogr>
                   <series>
                      <title level="s">Л.Н. Толстой. Полное собрание сочинений</title>
                      <biblScope unit="vol">46</biblScope>
                   </series>
                </biblStruct>
                </sourceDesc>
          </fileDesc>
          <encodingDesc>
             <tagsDecl> </tagsDecl>
          </encodingDesc>
         <profileDesc>
            <creation>
            <date {}>
                {}
            </date>
            <rs/>
            </creation>
            <textClass>
               <catRef target="#дневники и записные книжки" type="sphere"/>
               <catRef target="#None" type="type"/>
               <catRef target="#diaries" type="works_letters_diaries"/>
               <catRef target="#дневник, записная книжка" type="ninetyDef"/>
               <catRef target="#None" type="main_var"/>
            </textClass>
            <preparedness>
            not finished
            </preparedness>
            <settingDesc>
            <time>
            XIX век
            </time>
            </settingDesc>
         </profileDesc>
       </teiHeader>
    <text>
       <body>
       {}
       </body>
    </text>
    </TEI>
'''

def split_diary(doc, filename):
    diaries = {}
    soup = BS(doc)
    filename = filename.split('.')[0] + '_{:02d}.' + filename.split('.')[1]
    for i, entry in enumerate(soup.find_all('div', {'type': 'entry'})):
        new_filename = filename.format(i)
        entry_date = entry.find('date')
        try:
            if entry_date.has_attr('when'):
                date_full = entry_date['when']
                date_tag = f'when="{date_full}"'
            elif entry_date.has_attr('from') and entry_date.has_attr('to'):
                date_full = ''
                date_tag = 'notAfter="{}" notBefore="{}"'.format(entry_date['from'], entry_date['to'])
        except:
            date_full = ''
            date_tag = ''
        diaries[new_filename] = TEI_STRUCTURE.format(date_tag, date_full, entry)
    return diaries

def main():
    for filename in os.listdir(FOLDER_PATH):
        doc = open(os.path.join(FOLDER_PATH, filename), encoding='utf-8').read()
        diaries = split_diary(doc, filename)
        for k, v in diaries.items():
            with open(os.path.join(FOLDER_PATH, k), 'w', encoding='utf-8') as f:
                f.write(v)

if __name__ == "__main__":
    main()