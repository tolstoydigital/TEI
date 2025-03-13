import os
import uuid
from tqdm import tqdm

foldernames = ["letters_and_diaries_new/diaries"]
old_names = "Мария Картышева, Евгений Можаев, Даниил Скоринкин, Елена Сидорова"
new_names = "Мария Картышева, Евгений Можаев, Даниил Скоринкин, Елена Сидорова, Вероника Файнберг, Кирилл Милинцевич"

for foldername in foldernames:
    for dirpath, dirnames, filenames in os.walk(foldername):
        for filename in tqdm(filenames):
            try:
                xml = open(os.path.join(dirpath, filename), encoding="utf-8").readlines()
                is_header = True
                result = ""
                for line in xml:
                    if "</teiHeader>" in line:
                        is_header = False
                    if is_header == False:
                        if "<p " in line:
                            line = line.replace("<p ", "<p id=\"{}\" ".format(uuid.uuid4()))
                        elif "<p>" in line:
                            line = line.replace("<p>", "<p id=\"{}\">".format(uuid.uuid4()))
                    else:
                        line = line.replace(old_names, new_names)
                    result += line
                with open(os.path.join(dirpath, filename), "w", encoding="utf-8") as f:
                    f.write(result)
            except UnicodeDecodeError:
                print(os.path.join(dirpath, filename))
                continue