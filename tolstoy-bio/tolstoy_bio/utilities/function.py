from functools import reduce
from typing import Callable


class FunctionUtils:
    def pipe(data, functions: tuple[Callable]):
        return reduce(lambda x, f: f(x), functions, data)
