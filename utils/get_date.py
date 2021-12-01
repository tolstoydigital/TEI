from bs4 import BeautifulSoup
import re
import dateparser
def get_date(p):
    bibl_pattern = "(Датируется|Впервые опубликовано|Автограф|Год в дате|На копии письма помечено|Печатается по|опубликовано| опубликовано в|Написано рукой|Написано на обороте|Публикуемый отрывок|Приписка к письму|абзац вписан|Ответ на письмо Страхова|Год устанавливается|Публикуемый отрывок|Написано на гранке|Личность адресата|по рукописной копии)"
    choice_pattern = "\s*([А-Яа-я]*?(\[(.*?)\])[А-Яа-я]*)\s*"
    choice_pattern2 = "\s*([А-Яа-я]*?(\[(.*?)\])[А-Яа-я]*?)\s*"
    data1 = "1862? г. Июля 1."
    data2 = "1864 г."
    data3 = "1856—1859 гг."
    data4 = "1874 г. февраль — март, до 15. я. п."
    data5  = "1840 г. июля 20."
    date_pattern1 = "(1[0-9]{3})\s*\?*\s*(-|—)\s*(1[0-9]{3})\s*\?*\s*гг.{0,2}$"
    date_pattern2 = "—"
    date_pattern3 = "(начало|середина|конец|первая половина|)"
    date_pattern4 = "до\s*[1-90]{1,2}"
    place_pattern =  "\s*(я. п.|москва|петербург|козлова засека.|бегичевка.|гриневка)"
    date_pattern5 = "(1[1-90]{3}) или (1[1-90]{3}) г.*"
    date_pattern6 = "^(1[1-90]{3})-е гг."
    date_pattern7 = "^(1[1-90]{3})\?* г."
    date_pattern8 = "(1[1-90]{3})—(1[1-90]{3})-е\s*.*\s*.(начало|середина|конец|первая половина|вторая половина).+"
    date_pattern9 = "(1[1-90]{3})—(1[1-90]{3})-е гг."
    part_pattern = ",*\s*(начало|середина|конец|первая половина|вторая половина).{0,2}$"
    part_pattern2 = ".*\s*(начало|середина|конец|первая половина|вторая половина).{0,2}"
    month_parts_dic = {"начало": ["01 01", "04 30"], "середина" : ["05 01", "08 31"], "конец": ["09 01", "12 31"], "первая половина":["01 01", "05 31"], "вторая половина":["06 01", "12 31"]}
    month_pattern = ".*(январ.{0,2}|феврал.{0,2}|апрел.{0,}|март.{0,2}|ма.{0,2}|июн.{0,2}|июл.{0,2}|август.{0,2}|сентябр.{0,2}|октябр.{0,2}|ноябр.{0,2}|декабр.{0,2})\s([0-9]{0,2})"
    month_pattern2 = ".*(январ.{0,1}|феврал.{0,1}|апрел.{0,1}|март.{0,1}|ма.{0,1}|июн.{0,1}|июл.{0,1}|август.{0,1}|сентябр.{0,1}|октябр.{0,1}|ноябр.{0,2}|декабр.{0,1})\s*([0-9]{0,2})"
    month_pattern3 = ".*(январ.{0,2}|феврал.{0,2}|апрел.{0,}|март.{0,2}|ма.{0,2}|июн.{0,2}|июл.{0,2}|август.{0,2}|сентябр.{0,2}|октябр.{0,2}|ноябр.{0,2}|декабр.{0,2})\s*([0-9]{1,2})\s*—\s*([0-9]{1,2})"
    year_part_dic = {"начало": [0, 4], "середина":[4, 7], "конец": [7, 9]}
    day_part_dic = {"начало": ["01", "10"], "середина" : ["11", "20"], "первая половина":["01", "15"]}
    season_dic = {"лето":["06 01"]}
    date_pattern10 = "((1[1-90]{3}).?\sг.)\s*" + month_pattern2 + "\s*.*\s*после\s*([1-90]{1,2})"
    date_pattern11 = "((1[1-90]{3}).?\sг.)\s*" + month_pattern2 + "\s*—\s*" + month_pattern2 + "\s*.*\s*до\s*([1-90]{1,2})"
    date_pattern12 = "((1[1-90]{3}).?\sг.).*" + part_pattern2 + "\s—\s((1[1-90]{3}).?\sг.)." + part_pattern2
    spes_date_pattern = "1896\? г., 1904\? г. сентябрь или 1905\? г. январь."
    result = re.search("(1[0-9]{3})\sг\.," + part_pattern2 + "\s*—\s*(1[0-9]{0,3})\sг.",  "1901 г., конец — 1902 г.")    










    for pp in p.findAll("p",{"class":"Data left"}):
        a = re.sub(place_pattern,r"",pp.text.lower())
                
        if re.search(date_pattern1, a):                   
            result = re.search(date_pattern1, a)
            date_from = result.group(1) + " 01 01"
            date_to = result.group(3) + " 12 31"
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]
        elif re.search("1893 г., до июля.", a):
            date_from = "1893-01-01"
            date_to = "1893-06-30"
            date_final = ["Not_B_A", {"notBefore":"1893-01-01", "notAfter": "1893-06-30"}]

        elif re.search("1870-е\? гг. сентября 13.", a):
            date_when = "-10-13"
            date_from = "1871-09-13"
            date_to = "1880-09-13"
            date_final = ["Not_B_A_when", {"notBefore":date_from, "notAfter": date_to, "when":date_when}]


        elif re.search("1892 г. апрель, около 20.", a):
            date_from = "1892-03-15"
            date_to = "1892-03-25"
            date_final = ["Not_B_A", {"notBefore":"1892-03-15", "notAfter": "1892-03-25"}]

        elif re.search(date_pattern6 + "\sлето$", a):
            result = re.search(date_pattern6 + "\sлето$")
            date_from = result.group(1) + " 06 01"
            date_to = str(int(result.group(1) + 10)) + " 08 31" 
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search("1890 г. — 1891 г., октябрь, до 26.", a):
            date_from = "1890-10-01"
            date_to = "1891-10-26"
            date_final = ["Not_B_A", {"notBefore":"1890-10-01", "notAfter": "1891-10-26"}]

        elif re.search(date_pattern6 + part_pattern[:-1] + "\s*—\s*(1[0-9]{3})-е\s*гг.$" , a):
            result = re.search(date_pattern6 + part_pattern[:-1] + "\s*—\s*(1[0-9]{3})-е\s*гг.$" ,  a)
            date_from = str(int(result.group(1)) +  year_part_dic[result.group(2)][0]) + " 01 01"
            date_to = str(int(result.group(3)) + 10)  + " 12 31"
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search("1888\? г. ноябрь — 1889 г. апрель..", a):
            date_from = "1888-11-01"
            date_to = "1889-04-30"
            date_final = ["Not_B_A", {"notBefore":date_from, "notAfter": date_to}]

        elif re.search("(1[0-9]{3})\s*г\.\?*\s*(-|—)\s*(1[0-9]{3})\sг\.\s*" + part_pattern2,  a):
            result = re.search("(1[0-9]{3})\s*г\.\?*\s*(-|—)\s*(1[0-9]{3})\sг\.\s*" + part_pattern2,  a)
            date_from = result.group(1) + " " + " 01 01"
            date_to = result.group(3) + " " + month_parts_dic[result.group(4)][1]
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

                      
        elif re.search("1900 г. октябрь, после 13—1901 г., апрель.", a):
            date_from = "1900-10-13"
            date_to = "1901-03-01"
            date_final = ["Not_B_A", {"notBefore":date_from, "notAfter": date_to}]

        elif re.search(date_pattern7 + month_pattern2 + ",\sдо\s([0-9]{1,2})" ,  a):
            result = re.search(date_pattern7 + month_pattern2 + ",\sдо\s([0-9]{1,2})" ,  a)
            date_from = result.group(1) + " " + result.group(2) + "01"
            date_to =  result.group(1) + " " + result.group(2) + " " + result.group(4)
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern1[:-1] + ", лето",a):

            result = re.search(date_pattern1[:-1] + ", лето", a)
            date_from = result.group(1) + " 06 01"
            date_to = result.group(3) + " 08 31"
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern1[:-1] + month_pattern2,a):
            result = re.search(date_pattern1[:-1] + month_pattern2,a)    
            date_from = result.group(1) + " " + result.group(4) + " " + result.group(5)
            date_to = result.group(3) + " " + result.group(4) + " " + result.group(5)
            date_from = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})

            if result.group(5):
                date_when = "-" + result.group(4) + " " + result.group(5)
            else: 
                date_when = "-" + result.group(4) + " " + "-"
                date_when = dateparser.parse(date_when, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                date_final = ["Not_B_A_when", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d"), "when":date_when.strftime("-%m-%d")}]

                    
        elif re.search("(1[0-9]{3}) г\., лето.", a):
            result = re.search("(1[0-9]{3}) г\., лето.", a)
            date_from = result.group(1) + " 06 01"
            date_to = result.group(1) + " 08 31"
            date_from = dateparser.parse(date_from, languages = ["ru"])
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search("1874 г\. февраль — март, до 15\.", a):
            date_from = "1874-02-01"
            date_to = "1874-03-15"
            date_final = ["Not_B_A", {"notBefore":date_from, "notAfter": date_to}]

        elif re.search(spes_date_pattern, a):
            date_when = ["1896-09-", "1904-09-", "1905-01-"]
            date_final = ["Not_B_A", {"notBefore":"1896-09-01", "notAfter": "1905-01-31"}]

        elif re.search(date_pattern10, a):
            result = re.search(date_pattern10, a)
            date_from = result.group(1) + " " + result.group(3) + " " + result.group(5) 
            date_to = result.group(1) + " " + result.group(3)
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern11, a):
            result = re.search(date_pattern11, a)
            date_from = result.group(1) + " " + result.group(3) 
            date_to = result.group(1) + " " + result.group(5) + " " + result.group(7)
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern12, a):
            result = re.search(date_pattern12, a)
            date_from = result.group(1) + " " + month_parts_dic[result.group(3)][0] 
            date_to = result.group(4) + " " + month_parts_dic[result.group(6)][1] 
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern5, a):
            result = re.search(date_pattern5, a)
            date_from = result.group(1)
            date_to = result.group(2) 
            if re.search(month_pattern, a):
                result2 = re.search(month_pattern, a)
                date_from = date_from + " " + result2.group(1)
                date_to = date_to + " " + result2.group(1)
                if result2.group(2):
                     date_from = date_from + " " + result2.group(2)
                     date_to = date_to + " " + result2.group(2)
            else: 
                date_from = date_from + " " + "01 01"
                date_to = date_to + " " + "12 31"
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]


        elif re.search(date_pattern6, a):
            result = re.search(date_pattern6, a)
            date_from = str(int(result.group(1)))   
            date_to = str(int(result.group(1))) 
            if re.search(part_pattern, a):
                result2 = re.search(part_pattern, a)
                if result2.group(1) in year_part_dic:
                    date_from = str(int(date_from) +  year_part_dic[result2.group(1)][0])
                    date_to = str(int(date_to) + year_part_dic[result2.group(1)][1])
                        
                else:
                    date_from = str(int(result.group(1)) + 1)   
                    date_to = str(int(result.group(1)) + 10)     
            date_from = date_from + " " + "01 01"
            date_to = date_to + " " + "12 31"    


            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

        elif re.search(date_pattern7, a):
            result = re.search(date_pattern7, a)
            if re.search("(1[0-9]{3})\sг\.," + part_pattern2 + "\s*—\s*[0-9]{0,3}\sг.$", a):
                result = re.search("(1[0-9]{3})\sг\.," + part_pattern2 + "\s*—\s*[0-9]{0,3}\sг.", a)
                date_from = result.group(1) + month_parts_dic[0] 
                date_to = result.group(3) + ' 12 31'
                date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})
                date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

            elif re.search(month_pattern2 + " — " + month_pattern2, a):
                spes_result = re.search(month_pattern2 + " — " + month_pattern2, a)
                date_from = result.group(1) + " " + spes_result.group(1) + " " + spes_result.group(2)
                date_to = result.group(1) + " " + spes_result.group(3) + " " + spes_result.group(4)
                date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})
                date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

            elif re.search(month_pattern2, a):
                result2 = re.search(month_pattern2, a)
                if result2.group(2):
                    if re.search(month_pattern3, a):
                        result3 = re.search(month_pattern3, a)
                        date_from = result.group(1) + " " + result2.group(1) + " " + result3.group(2)
                        date_to = result.group(1) + " " + result2.group(1) + " " + result3.group(3)
                        date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                        date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})
                        date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]
                    else:
                        date_when = dateparser.parse(a, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                        date_final = ["date_when", {"when":date_when.strftime("%Y-%m-%d")}]
                elif re.search(part_pattern, a):
                    result3 = re.search(part_pattern, a)
                    if result3.group(1) == "конец":
                        date_from = result.group(1) + " " + result2.group(1) + " " + "21"
                        date_to = result.group(1) + " " + result2.group(1)
                        date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                        date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})
                        date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

                    elif result3.group(1) == "вторая половина":
                        date_from = result.group(1) + " " + result2.group(1) + " " + "16"
                        date_to = result.group(1) + " " + result2.group(1)
                        date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                        date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'}) 
                        date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

                    else:
                        date_from = result.group(1) + " " + result2.group(1) + " " + day_part_dic[result3.group(1)][0]
                        date_to = result.group(1) + " " + result2.group(1) + " " + day_part_dic[result3.group(1)][1]
                        date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                        date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'}) 
                        date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]


                          
                else:
                    if re.search("1898 г\. май — 1899\? г\.", a):
                        date_final = ["Not_B_A", {"notBefore":"1898-05-01", "notAfter":"1899-01-01"}]
                        continue
                    date_from = dateparser.parse(a, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                    date_to = dateparser.parse(a, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'last', 'DATE_ORDER': 'YMD'})
                    date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]
                     
            elif re.search(part_pattern, a):
                result2 = re.search(part_pattern, a)
                date_from = result.group(1) + " "  + month_parts_dic[result2.group(1)][0]
                date_to = result.group(1) + " "  + month_parts_dic[result2.group(1)][1]
                date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first',  'DATE_ORDER': 'YMD'})
                date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

            else:
                date_from = result.group(1) + " " + " 01 01"
                date_to = result.group(1) + " " + " 12 31"   
                date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
                date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first',  'DATE_ORDER': 'YMD'})
                date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]



        elif re.search(date_pattern8, a):
            result = re.search(date_pattern8, a)
            date_from = result.group(1) + " " + "01 01"
            date_to = str(int(result.group(2)) + year_part_dic[result.group(3)][1]) + " " + "12 31"
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]


        elif re.search(date_pattern9, a):
            result = re.search(date_pattern9, a)
            date_from = result.group(1) + " " + "01 01"
            date_to = str(int(result.group(2)) + 10) + " " + "12 31"
            date_from = dateparser.parse(date_from, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_to = dateparser.parse(date_to, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first',  'DATE_ORDER': 'YMD'})
            date_final = ["Not_B_A", {"notBefore":date_from.strftime("%Y-%m-%d"), "notAfter": date_to.strftime("%Y-%m-%d")}]

                
        else: 
            date_when = dateparser.parse(a, languages = ["ru"], settings={'PREFER_DAY_OF_MONTH': 'first', 'DATE_ORDER': 'YMD'})
            date_final = ["date_when", {"when":date_when.strftime("%Y-%m-%d")}]
    return date_final           
