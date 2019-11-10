from enum import Enum


# https://docs.python.org/3/library/enum.html#orderedenum
class OrderedEnum(Enum):
    def __ge__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering >= other.ordering
        return NotImplemented

    def __gt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering > other.ordering
        return NotImplemented

    def __le__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering <= other.ordering
        return NotImplemented

    def __lt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering < other.ordering
        return NotImplemented

    @property
    def ordering(self) -> int:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]
