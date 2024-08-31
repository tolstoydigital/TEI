from collections import defaultdict


class RecordIdManager:
    id_counter = defaultdict[str, int]

    def __init__(self):
        self.id_counter = defaultdict[str](int)

    def generate_based_on(self, value: str):
        self.id_counter[value] += 1
        count = self.id_counter[value]
        return value if count == 1 else f"{value}_{count}"
