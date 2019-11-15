from enum import Enum
from typing import Any, Optional


# https://docs.python.org/3/library/enum.html#orderedenum
class OrderedEnum(Enum):

    def __ge__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering >= other.ordering
        raise NotImplemented

    def __gt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering > other.ordering
        raise NotImplemented

    def __le__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering <= other.ordering
        raise NotImplemented

    def __lt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering < other.ordering
        raise NotImplemented

    @property
    def ordering(self) -> int:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]

    @classmethod
    def for_symbol(cls, symbol: str) -> Optional['OrderedEnum']:
        return next((value for value in cls if value.symbol == symbol), None)
