import random

from collections import namedtuple
from typing import Collection, List, Union

from pyker.utils import OrderedEnum


class Suit(OrderedEnum):
    spades = (4, '♠︎')
    hearts = (3, '♥︎')
    diamonds = (2, '♦︎')
    clubs = (1, '♣')


class Rank(OrderedEnum):
    two = (2, '2')
    three = (3, '3')
    four = (4, '4')
    five = (5, '5')
    six = (6, '6')
    seven = (7, '7')
    eight = (8, '8')
    nine = (9, '9')
    ten = (10, '10')
    jack = (11, 'J')
    queen = (12, 'Q')
    king = (13, 'K')
    ace = (14, 'A')


Card = namedtuple('Card', ['suit', 'rank'])
Card.__str__ = lambda c: f'{c.rank.symbol}{c.suit.symbol}'
Card.__repr__ = Card.__str__


class Deck(object):
    def __init__(self, shuffle=True):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        if shuffle:
            self.shuffle()

    def __iter__(self):
        return iter(self.cards)

    def __getitem__(self, item):
        return self.cards[item]

    def __len__(self):
        return len(self.cards)

    def __add__(self, other):
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
