import re
def corretion_tag(string_soup):
    choice_pattern = "\s*([А-Яа-я]*?(\[(.*?)\])[А-Яа-я]*)\s*"

    choice_result = re.findall(choice_pattern, string_soup)

    for i in choice_result:
        sub_1 = re.sub(r"\[|\]", r"", i[0])
        sub_2 = re.sub(r"\[", r"\\[", i[0])
        sub_3 = re.sub(r"\]", r"\\]", sub_2)
        sub_4 = re.sub('\[' + i[2] + "\]", r"", i[0])
        replacement = "<choice" + " original_editorial_correction=" + "\'" + i[0] + "\'" + ">" + "<sic>" + sub_4 + "</sic>" + "<corr>" + sub_1 + "</corr>" + "</choice>"
        reg_for_repl = "(?<!\=\')" + sub_3
        string_soup = re.sub(reg_for_repl,replacement, string_soup)
    return string_soup
