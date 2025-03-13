from typing import Callable


class ArrayUtils:

    
    @staticmethod
    def find_index(array: list, condition: Callable):
        for i, item in enumerate(array):
            if condition(item):
                return i
        
        return -1

