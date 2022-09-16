from lxml import etree
import re
import os

margin_sic = re.compile("(<note[^>]*?><div[^>]*?><head><ref[^>]*?>[^<]+?</ref></head>)(<p[^>]*?>.*?(?=</p>))*(<p[^>]*?>)<hi[^>]*?>(На полях:)</hi>(.*?(?=</p>))(</p>.*?</div></note>)")
pattern_sic = re.compile("(<note[^>]*?><div[^>]*?><head><ref[^>]*?>[^<]+?</ref></head><p[^>]*?>)<hi[^>]*?>(Переправлено из:|Исправлено из:|Исправлено)</hi>(.*?(?=</p>))(</p>.*?</div></note>)")
pattern_sic_without_hi = re.compile("(<note[^>]*?>)\s*(Переправлено из:|Исправлено из:|Исправлено:)(.*?(?=</note>))(</note>)")
pattern_sic_without_p = re.compile("(<note[^>]*?>)\s?<hi[^>]*?>\s*(Переправлено из:|Исправлено из:|Исправлено:)\s*</hi>(.*?(?=</note>))(</note>)")
pattern_crossed_2 = re.compile("<hi>Последние два слова вымараны</hi>")
pattern_crossed_10 = re.compile("<hi>Последние десять слова вымараны</hi>")
avt_pattern_sic = re.compile("(<note[^>]*?><div[^>]*?><head><ref[^>]*?>[^<]+?</ref></head><p[^>]*?>)<hi[^>]*?>(В автографе:)</hi>(.*?(?=</p>))(</p>.*?</div></note>)")
avt_pattern_sic_without_p = re.compile("(<note[^>]*?>)<hi[^>]*?>(В автографе:)</hi>(.*?(?=</note>))(</note>)")
margin_sic_without_p = re.compile("(<note[^>]*?>)<hi[^>]*?>(На полях:)</hi>(.*?(?=</note>))(</note>)")


def editor_changes(text:str):
    text = re.sub("\s{2,}|\n", "", text)
 
    text = pattern_sic_without_p.sub("\g<1><choice><sic>\g<3></sic></choice>\g<4>", text)
    text = pattern_sic_without_hi.sub("\g<1><choice><sic>\g<3></sic></choice>\g<4>", text)
    text = pattern_crossed_2.sub('<gap reason="crossed out" quantity="2" unit="word" />', text)
    text = pattern_crossed_10.sub('<gap reason="crossed out" quantity="10" unit="word" />', text)
    text = pattern_sic.sub("\g<1><choice><sic>\g<3></sic></choice>\g<4>", text)
    text = margin_sic.sub("\g<1>\g<2>\g<3><choice><sic>\g<5></sic></choice>\g<6>", text)
    text = avt_pattern_sic.sub("\g<1><choice><sic>\g<3></sic></choice>\g<4>", text)
    text = avt_pattern_sic_without_p.sub("\g<1><choice><sic>\g<3></sic></choice>\g<4>", text)
    return text


def pipline():
    n = 0
    dir = os.getcwd()
    path = os.path.join(dir, "TEI/texts")
    folders = os.listdir(path)
    for folder in folders:
        new_path = f"{path}/{folder}"
        files = os.listdir(new_path)
        os.chdir(new_path)
        for file in files:
            try:
                tree = etree.parse(file)
                root = tree.getroot()
                text = etree.tostring(root, pretty_print=True, encoding="unicode")
                text = editor_changes(text)
                text = re.sub("\s{2,}|\n", "", text)

                

                tag = etree.fromstring(text)
                Element_tree = etree.ElementTree(tag)
                Element_tree.write(file, encoding = "utf-8", xml_declaration=True, pretty_print=True)
            except etree.XMLSyntaxError as err:
                print(err)
pipline()
