from collections import defaultdict
from typing import Callable, Collection, List, Optional, Sized, Tuple

from pyker.cards import Card, Rank
from pyker.constants import HAND_SIZE
from pyker.utils import OrderedEnum


class HandType(OrderedEnum):
    royal_flush = (10, 'Royal flush')  # technically just a nut straight flush, but modeled this way for simplicity
    straight_flush = (9, 'Straight flush')
    four_of_a_kind = (8, 'Four of a kind')
    full_house = (7, 'Full house')
    flush = (6, 'Flush')
    straight = (5, 'Straight')
    three_of_a_kind = (4, 'Three of a kind')
    two_pair = (3, 'Two pair')
    pair = (2, 'Pair')
    high_card = (1, 'High card')

    @property
    def name(self) -> str:
        return self.symbol


def find_highest_n_of_a_kind(cards: Collection[Card], n: int) -> Optional[Tuple[Card]]:
    if n is None or n < 2 or not has_enough_cards(cards, n):
        return None
    sorted_cards = sorted(cards, key=lambda c: c.rank, reverse=True)
    tuples = [
        tuple(sorted_cards[i:(i + n)])
        for i in range(len(sorted_cards) - n + 1)
        if len(set(map(lambda c: c.rank, sorted_cards[i:(i + n)]))) == 1
    ]
    return tuples[0] if tuples else None


def has_pair(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=2) is not None


def has_two_pair(cards: Collection[Card]) -> bool:
    return has_pair(cards) and has_pair(set(cards) - set(find_highest_n_of_a_kind(cards, n=2)))


def has_three_of_a_kind(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=3) is not None


def has_four_of_a_kind(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=4) is not None


def has_full_house(cards: Collection[Card]) -> bool:
    return has_three_of_a_kind(cards) and has_pair(set(cards) - set(find_highest_n_of_a_kind(cards, n=3)))


def find_best_straight(cards: Collection[Card], rank_fn: Callable[[List[Card], List[Card]], int]) -> List[Card]:
    sorted_cards = sorted(cards, key=lambda c: c.rank)
    cards = [card for i, card in enumerate(sorted_cards) if i == 0 or sorted_cards[i - 1].rank != card.rank]
    aces = [card for card in cards if card.rank == Rank.ace]
    if aces:
        cards.insert(0, aces.pop())    # stash an ace at the beginning to check for a wheel

    best_straight = []
    current_straight = [cards[0]]

    for previous, current in zip(cards[:-1], cards[1:]):
        rank_delta = current.rank.ordering - previous.rank.ordering
        if rank_delta == 1 or (current.rank == Rank.two and previous.rank == Rank.ace):
            current_straight.append(current)
        else:
            if rank_fn(current_straight, best_straight) > 0:
                best_straight = current_straight
            current_straight = [current]

    if rank_fn(current_straight, best_straight) > 0:
        best_straight = current_straight

    return best_straight


def find_highest_straight(cards: Collection[Card]) -> List[Card]:
    def rank_function(current: List[Card], best_so_far: List[Card]) -> int:
        if not best_so_far or (len(best_so_far) == 1 and best_so_far[0].rank == Rank.ace):
            return 1
        return current[0].rank.ordering - best_so_far[0].rank.ordering

    return find_best_straight(cards, rank_function)


def find_longest_straight(cards: Collection[Card]) -> List[Card]:
    return find_best_straight(cards, lambda c, b: len(c) - len(b))


def has_straight(cards: Collection[Card]) -> bool:
    return has_enough_cards(cards, size=HAND_SIZE) and len(find_longest_straight(cards)) >= HAND_SIZE


def find_biggest_flush(cards: Collection[Card]) -> List[Card]:
    suits = defaultdict(list)
    for card in cards:
        suits[card.suit].append(card)
    return max(suits.values(), key=lambda l: len(l))


def has_flush(cards: Collection[Card]) -> bool:
    return has_enough_cards(cards, size=HAND_SIZE) and len(find_biggest_flush(cards)) >= HAND_SIZE


def has_straight_flush(cards: Collection[Card]) -> bool:
    return has_flush(cards) and has_straight(find_biggest_flush(cards))


def has_enough_cards(cards: Sized, size: int = 1) -> bool:
    return cards is not None and len(cards) >= size


def rate_hand(cards: Collection[Card]) -> HandType:
    if has_straight_flush(cards):
        return HandType.royal_flush if find_highest_straight(cards)[0].rank == Rank.ten else HandType.straight_flush
    if has_four_of_a_kind(cards):
        return HandType.four_of_a_kind
    if has_full_house(cards):
        return HandType.full_house
    if has_flush(cards):
        return HandType.flush
    if has_straight(cards):
        return HandType.straight
    if has_three_of_a_kind(cards):
        return HandType.three_of_a_kind
    if has_two_pair(cards):
        return HandType.two_pair
    if has_pair(cards):
        return HandType.pair
    return HandType.high_card
