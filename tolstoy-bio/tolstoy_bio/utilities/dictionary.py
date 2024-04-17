class DictionaryUtils:
    

    @staticmethod
    def get_value_by_first_existent_key(dictionary: dict, *keys: list[str]):
        for key in keys:
            if key in dictionary:
                return dictionary[key]
        
        return None
