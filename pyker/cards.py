import random

from collections import namedtuple
from typing import Collection, Iterator, List, Optional, Union

from pyker.utils import OrderedEnum


__all__ = ['Card', 'Deck', 'Rank', 'Suit']


class Suit(OrderedEnum):
    spades = (4, '♠︎')
    hearts = (3, '♥︎')
    diamonds = (2, '♦︎')
    clubs = (1, '♣')

    @classmethod
    def for_letter(cls, letter: str) -> Optional['Suit']:
        return {'C': cls.clubs, 'D': cls.diamonds, 'H': cls.hearts, 'S': cls.spades}.get(letter.upper())


class Rank(OrderedEnum):
    two = (2, '2', 'deuce')
    three = (3, '3', 'three')
    four = (4, '4', 'four')
    five = (5, '5', 'five')
    six = (6, '6', 'six')
    seven = (7, '7', 'seven')
    eight = (8, '8', 'eight')
    nine = (9, '9', 'nine')
    ten = (10, '10', 'ten')
    jack = (11, 'J', 'jack')
    queen = (12, 'Q', 'queen')
    king = (13, 'K', 'king')
    ace = (14, 'A', 'ace')

    @property
    def name(self) -> str:
        return self.value[2]

    @property
    def plural_name(self) -> str:
        if self == self.six:
            return 'sixes'
        return self.name + 's'


Card = namedtuple('Card', ['rank', 'suit'])
Card.__str__ = lambda c: f'{c.rank.symbol}{c.suit.symbol}'
Card.__repr__ = Card.__str__


def get_card(rank: str, suit: str) -> Card:
    card_rank = Rank.for_symbol(rank)
    if card_rank is None:
        raise ValueError(f'Unknown rank: {rank}')
    card_suit = Suit.for_letter(suit)
    if card_suit is None:
        card_suit = Suit.for_symbol(suit)
        if card_suit is None:
            raise ValueError(f'Unknown suit: {suit}')
    return Card(card_rank, card_suit)


class Deck(object):

    def __init__(self, shuffle: bool = True) -> None:
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        if shuffle:
            self.shuffle()

    def __iter__(self) -> Iterator[Card]:
        return iter(self.cards)

    def __getitem__(self, item: int) -> Card:
        return self.cards[item]

    def __len__(self) -> int:
        return len(self.cards)

    def __add__(self, other: Union[Card, Collection[Card]]) -> 'Deck':
        self.add(cards=other)
        return self

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop()

    def draw_many(self, count: int) -> List[Card]:
        return [self.draw() for _ in range(count)]

    def add(self, cards: Union[Card, Collection[Card]]) -> None:
        if isinstance(cards, Card):
            cards = [cards]
        self.cards += cards
