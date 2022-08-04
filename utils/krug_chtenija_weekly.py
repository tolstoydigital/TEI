from lxml import etree
import re
import os
import pandas as pd
dir = os.getcwd()


data_table = "NEW of Metadata Tolstoy 2018-2022 - Круг чтения.csv"
path2table = os.path.join(dir, data_table)
PATH =  os.path.join(dir, "TEI/texts/krug_chtenija")
df = pd.read_csv(path2table)
files = df[df["авторство Толстого"] == "NotTolstoy"].loc[:,"названия файла"].tolist()
exclude = ["v41_050_052_Krug_chtenija_weekly_jan_3_Sovershenstvovanie.xml",
"v42_119_128_Krug_chtenija_weekly_oct_1_Zhivye_moschi.xml"]


def add_cit(file):
    tree = etree.parse(file)
    root = tree.getroot()
    body = root.find(".//{http://www.tei-c.org/ns/1.0}div")
    cit = None
    l = len(body.findall("./")) - 1
    for n, t in enumerate(body.findall("./")):
        if t.tag == "{http://www.tei-c.org/ns/1.0}head":
            cit = etree.Element("cit")
            t.addprevious(cit)
            cit.append(t)
        elif cit is not None:
            cit.append(t)
        if n == l:
            bibl = etree.Element("bibl")
            t.addprevious(bibl)
            bibl.append(t)

    Element_tree = etree.ElementTree(root)
    Element_tree.write(file, encoding = "utf-8", xml_declaration=True, pretty_print=True)

    


def pipline(files):
    os.chdir(PATH)
    for file in files:
        if file in exclude:
            continue
        add_cit(file)
pipline(files)
