from lxml import etree
import re
import os

dir = os.getcwd()
PATH =  os.path.join(dir, "TEI/texts/krug_chtenija")


def cit_date_markup(text:str):
    # регулярные выражения для добавления 0 в даты
    date1 = re.compile('(<div\stype="daily"[^<]+when="--)(\d)(-)(\d)(">)')
    date2 = re.compile('(<div\stype="daily"[^<]+when="--\d\d-)(\d)(">)')
    date3 = re.compile('(<div\stype="daily"[^<]+when="--)(\d)(-\d\d">)')
    # регулярное выражение для разметки цитирования
    cit = re.compile('(<div1\s+n="\d+">)(<p[^<]*?>\d+</p>)((<p[^<]*?>([^<]|<pb[^<]*/>|<hi[^<]*>[^<]+</hi>)+</p>|<div type="poem"[^<]*><div>(<p[^<]*?>[^<]+</p>)+?</div></div>)+?)(<p[^<]*?><hi rend="italic">([^<]|<choice[^<]*>.+?</choice>){0,77}</hi></p>)</div1>')
    # удаления пропусков из текста
    text = re.sub("\s{2,}|\n", "", text)
    # применение разметки
    text = cit.sub("\g<1>\g<2><cit>\g<3><bibl>\g<7></bibl></cit></div1>", text)
    text = date1.sub("\g<1>0\g<2>\g<3>0\g<4>\g<5>", text)
    text = date2.sub("\g<1>0\g<2>\g<3>", text)
    text = date3.sub("\g<1>0\g<2>\g<3>", text)
    return text


def div1(file):
    '''Функция для разметки div1 и head'''
    # регулярное выражение для помещения параграфа с датой в человекочитаемом
    #виде в тег <head>
    Razradka = re.compile('(<p[^<]*?>[^<]*?<hi rend="Razradka">[^<]*?</hi>.*?(?=</p>)</p>)')
    tree = etree.parse(file)
    root = tree.getroot()
    text = etree.tostring(root, pretty_print=True, encoding="unicode")
    text = re.sub("\s{2,}|\n", "", text)
    text = Razradka.sub("<head>\g<1></head>", text)
    root = etree.fromstring(text)

    body = root.find(".//{http://www.tei-c.org/ns/1.0}div")
    div = None
    for t in body.findall("./"):
        if t.tag != "{http://www.tei-c.org/ns/1.0}p":
            if div is not None:
                div.append(t)
            continue     
        elif t.text is not None:
            check = t.text
        elif t.find('./{http://www.tei-c.org/ns/1.0}hi') is not None and t.find('./{http://www.tei-c.org/ns/1.0}hi').text is not None:
            check = t.find('./{http://www.tei-c.org/ns/1.0}hi').text
        else:
            continue
        if re.search("^\d+$", check):
            div = etree.Element("div1")
            t.addprevious(div)
            div.append(t)
            div.set("n", check)
        elif re.search("^—+$", check):
            div = etree.Element("div1")
            t.addprevious(div)
            div.append(t)
        else:
            if div is not None:
                div.append(t)
    return root


def pipline():
    os.chdir(PATH)
    files = os.listdir()
    for file in files:
        root = div1(file)
        text = etree.tostring(root, pretty_print=True, encoding="unicode")
        

        root = etree.fromstring(text)
        text = etree.tostring(root, pretty_print=True, encoding="unicode")
        text = cit_date_markup(text)
        new_tag = etree.fromstring(text)
        Element_tree = etree.ElementTree(new_tag)
        Element_tree.write(file, encoding = "utf-8", xml_declaration=True, pretty_print=True)

      
pipline()
